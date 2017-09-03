import smtplib, weakref, logging

import striga.server.application, striga.server.service
import striga.core.exception

import striga.protocol._stpro_mail as mail

###

L = logging.getLogger('MailFrontend')

###

class MailFrontendService(striga.server.service.Service):
	# Intentionally not inherited from striga.server.frontendservice.FrontendService - there is very little functionality reusable

	def __init__(self, parent, name = 'MailFrontend', startstoppriority = 2000):
		striga.server.service.Service.__init__(self, parent, name, startstoppriority)
		self.ApplicationRef = weakref.ref(striga.server.application.GetInstance())
		self.SiteBusRef = None
		self.SiteBusName = 'SiteBus'
		self.SMTPConnection = None


	def _configure(self, conffilename):
		return {
			'smtp' : self.__configure_smtp,
			'sitebus' : self.__configure_sitebus,
			'!' : self._configure_finished,
		}


	def __configure_sitebus(self, conffilename, name):
		self.SiteBusName = str(name)


	def __configure_smtp(self, conffilename, host, port, proto="SMTP", user=None, password=None):
		assert self.SMTPConnection is None

		if host == '0':
			self.SMTPConnection = -1
	
		else:
			if proto == 'SMTP':
				self.SMTPConnection = (smtplib.SMTP, (host, port))
			elif proto == 'SMTP_SSL':
				self.SMTPConnection = (smtplib.SMTP_SSL, (host, port))
			elif proto == 'LMTP':
				self.SMTPConnection = (smtplib.LMTP (host, port))
			else:
				raise striga.core.exception.StrigaConfigurationError("Unknown SMTP protocol (use one SMTP, SMTP_SSL or LMTP")

		self.User = user
		self.Password = password
		if self.User is not None: assert self.Password is not None


	def _configure_finished(self):
		if self.SMTPConnection is None:
			raise striga.core.exception.StrigaConfigurationError("Missing mailfrontend SMTP configuration")

		self._ChangeServiceStateToConfigured()


	def _DoStart(self):
		app = striga.server.application.GetInstance()

		if not hasattr(app.Services, self.SiteBusName):
			raise striga.core.exception.StrigaConfigurationError("Cannot start frontend service '%s' as there is no sitebus '%s'" % (self.ServiceName, self.SiteBusName))

		self.SiteBusRef = weakref.ref(getattr(app.Services, self.SiteBusName))
		L.debug("Frontend service '%s' connected to '%s'" % (self.ServiceName, self.SiteBusRef().ServiceName))


	def _DoStop(self):
		self.SiteBusRef = None


	def SendMail(self, path, **mailvars):
		ctx = None #Deleted at the end

		try:
			ctx = striga.core.context.Context(
				Application = self.ApplicationRef(),
				Request = mail.Request(Path=path, RemoteAddress='localhost'),
				Response = mail.Response(),
				Frontend = self,
			)

			if self.SiteBusRef is None:
				raise striga.core.exception.StrigaRuntimeException("Frontend service '%s' is not connected to site bus" % self.ServiceName)

			sb = self.SiteBusRef()
			if sb is None:
				self.SiteBusRef = None
				raise striga.core.exception.StrigaRuntimeException("Frontend service '%s' is not connected to site bus (process bus died)" % self.ServiceName)

			ctx.req.Vars.AddVarSet('SITEBUS', dict())
			ctx.req.Vars.AddVarSet('MAIL', mailvars)

		except:
			L.exception("Exception during context preparation")
			return False


		try:
			path = path.strip('/').split('/')
			sb(ctx, path)
		
		except  striga.core.exception.StrigaNoContent:
			return True

		except:
			L.exception("Exception in site bus - ignoring:")
			return False

		if self.SMTPConnection is not -1:
			toarr = ctx.res.To + ctx.res.CC + ctx.res.BCC
			if len(toarr) == 0:
				L.error("No recipients (ctx.res.To, ctx.res.CC, ctx.res.BCC) given for path {0} - mail is discarted.".format(path))
				return False

			if ctx.res.From is None:
				L.error("No sender (ctx.res.From) given for path {0} - mail is discarted.".format(path))
				return False			

			#Connect to SMTP and send email ...
			try:
				s = self.SMTPConnection[0](*self.SMTPConnection[1])
				if self.User is not None: s.login(self.User, self.Password)
				s.sendmail(ctx.res.From, toarr, ctx.res.GetMessage())
				s.quit()
			except:
				L.exception("Exception in mail frontend (SMTP connectivity) - ignoring:")
				return False

			L.info("Mail sent to '{}'".format(', '.join(toarr)))

			return True

		else:
			L.warning("Mail frontend is configured to discard generated emails - and one email was just discarded.\nEmail subject: {0}".format(ctx.res.Subject))
			return False

