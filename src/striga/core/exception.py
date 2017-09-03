
class StrigaException(Exception):
	pass

###

class StrigaRuntimeException(StrigaException):
	pass

###

class StrigaConfigurationError(StrigaException):


	def __init__(self, msg, configname = None, lineno = None):
		StrigaException.__init__(self, msg)
		self.ConfigName = configname
		self.LineNo = lineno


	def __str__(self):
		if (self.LineNo is None) and (self.ConfigName is None):
			msg = "Error during configuration\n"
		elif (self.LineNo is None):
			msg = "Error during processing configuration file %s\n" % self.ConfigName
		else:
			msg = "Error during processing configuration file %s line %d\n" % (self.ConfigName, self.LineNo)
		return msg + StrigaException.__str__(self)

###

class StrigaProtocolError(StrigaException):
	'''
	Used in frontends to indicate error in incomming communication
	'''
	pass

###

class StrigaFatalError(StrigaRuntimeException):
	'''
	Force workers to stop; application also
	'''
	#TODO: Check if this is correctly implemented (obviously not) - it should really force application to stop
	pass

###

class StrigaBusError(StrigaException):

	def __init__(self, name):
		StrigaException.__init__(self, "Bus error %s" % name)
		self.Name = name

###

class _StrigaClientRedirectBase(StrigaBusError):
	#TODO: There should be better name than this - it is common base for solving redirections, authorizing and other interleaved responses from server

	def __init__(self, statuscode, url, name):
		StrigaBusError.__init__(self, name)
		self.StatusCode = statuscode
		self.URL = url

	def UpdateResponse(self, ctx):
		ctx.Response.SetStatusCode(self.StatusCode)
		ctx.Response.CustomHTTPHeader.Set('Location', self.URL)

###

class StrigaClientSeeOther(_StrigaClientRedirectBase):
	#TODO: Move to HTTP specific section

	def __init__(self, url):
		_StrigaClientRedirectBase.__init__(self, 303, url, "SeeOther")

###

class StrigaClientMovedPermanently(_StrigaClientRedirectBase):
	#TODO: Move to HTTP specific section

	def __init__(self, url):
		_StrigaClientRedirectBase.__init__(self, 301, url, "MovedPermanently")

###

class StrigaClientFound(_StrigaClientRedirectBase):
	#TODO: Move to HTTP specific section

	def __init__(self, url):
		_StrigaClientRedirectBase.__init__(self, 302, url, "Found")

###

class StrigaClientTemporaryRedirect(_StrigaClientRedirectBase):
	#TODO: Move to HTTP specific section

	def __init__(self, url):
		_StrigaClientRedirectBase.__init__(self, 307, url, "TemporaryRedirect")

###

class StrigaClientUnauthorized(_StrigaClientRedirectBase):
	#TODO: Move to HTTP specific section

	def __init__(self, challenge):
		_StrigaClientRedirectBase.__init__(self, 401, None, "Unauthorized")
		self.Challenge = challenge

	def UpdateResponse(self, ctx):
		ctx.Response.SetStatusCode(self.StatusCode)
		ctx.Response.CustomHTTPHeader.Set('WWW-Authenticate', self.Challenge)

###

class StrigaStackEmptyException(StrigaException):
	pass

###

class StrigaNoContent(StrigaException):
	'''
	Used in site bus to indicate that there is no content produced by site bus items.
	This is usefull for example in situation when MailController decided not to produce mail.
	'''
	pass

###
