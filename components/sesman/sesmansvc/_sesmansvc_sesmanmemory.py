import threading, time, logging
import striga.core.exception
import striga.server.application, striga.server.service

from . import _sesmansvc_session

###

L = logging.getLogger('SesMan')

###

class MemorySessionManager(striga.server.service.Service):

	#TODO: Add support for cookies in "GET" part on Query...
	#TODO: We have problem with 3xx (Redirects) internal redirection of mod_scgi in Apache (Set-Cookies are not passed to client/handled correctly)

	def __init__(self, parent, sesid, seslifetime, domain=None, pool=None, name="SessionManager", startstoppriority=100):
		striga.server.service.Service.__init__(self, parent, name, startstoppriority)
		self._ChangeServiceStateToConfigured()
		self.SesId = sesid
		self.SessionLifetime = seslifetime
		self.SessionsLock = threading.Lock()
		self.Domain = domain
		if pool is None: pool = None
		self.Sessions = parent.SessionPools.setdefault(pool, {})


	def __call__(self, ctx, path):
		self.ServiceStartCheck()

		if ctx.req.Vars.GET.has_key(self.SesId):
			sesuin = ctx.req.Vars.GET.Get(self.SesId)
		else:
			sesuin = ctx.req.CookieJar.Get(self.SesId, None)
			if sesuin is not None: sesuin = sesuin.value
		
		if sesuin is not None:
			ses = self.Sessions.get(sesuin, None)
		else:
			#New session
			ses = None

		if ses is None:
			self.CreateNewSession(ctx)
			return
		else:
			if ses.Check(ctx):
				ses.Touch()
			else:
				#TODO: Double-think here !!! - IP changed; throwing an error causes problems on mobile IPs - new session will cause logouts ... what to do here?
				L.warning("New session created as session check for session '%s' found some issues" % ses.SIN)
				self.CreateNewSession(ctx)
				# This is a correct place to transfer data from old session object to new one - BUT BE CAREFULL it is security risk 
				self._DeleteSession(sesuin)
				return

		ctx.Session = ses


	def CreateNewSession(self, ctx):
		'''Create new session and add that into a context or request
			@return newly created session (used in inherited classes)'''
		self.SessionsLock.acquire()
		try:
			while 1:
				ses = _sesmansvc_session.Session(ctx, self.SessionLifetime, self)
				if not self.Sessions.has_key(ses.SIN): break

			self.Sessions[ses.SIN] = ses
		finally:
			self.SessionsLock.release()

		secure = ctx.req.CGIEnv.get('HTTPS', '') == 'on'
		ctx.res.CookieJar.Add(self.SesId, ses.SIN, path='/', domain=self.Domain, httponly=True, secure=secure)
		ctx.Session = ses
		return ses


	def RemoveSession(self, ctx, sin):
		'''Remove session from context'''
		ses = self._DeleteSession(sin)
		if ses is not None:
			ctx.res.CustomHTTPHeader.Add('Set-Cookie','%s=' % self.SesId, Expires='01-Jan-1977 00:00:01 GMT', Version='1', Path='/', Domain=self.Domain)


	def _DeleteSession(self, sin):
		''' Delete session object from Session dictionary'''
		self.SessionsLock.acquire()
		try:
			ret = self.Sessions.pop(sin, None)
			return ret
		finally:
			self.SessionsLock.release()


	def CleanOldSessions(self):
		acttime = time.time()

		for sin in self.Sessions.keys():
			ses = self.Sessions.get(sin, None)
			if ses is None: continue

			if (ses.LastActivity + ses.LifeTime) < acttime:
				ses = self._DeleteSession(sin)
				L.info("Session '%s' expired (global cleaning)" % sin)


	def _DoStart(self):
		app = striga.server.application.GetInstance()
		app.Scheduler.AddJob(striga.server.scheduler.PeriodicJob(10, self.CleanOldSessions))


	def _DoStop(self):
		app = striga.server.application.GetInstance()
		app.Scheduler.RemoveAllJobsFor(self.CleanOldSessions)
