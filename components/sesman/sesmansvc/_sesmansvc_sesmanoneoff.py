import logging
import striga.server.application, striga.server.service

from . import _sesmansvc_session

###

L = logging.getLogger('SesMan')

###

class OneOffSessionManager(striga.server.service.Service):

	def __init__(self, parent, name = "OneOffSessionManager", startstoppriority = 100):
		striga.server.service.Service.__init__(self, parent, name, startstoppriority)
		self._ChangeServiceStateToConfigured()


	def __call__(self, ctx, path):
		self.CreateNewSession(ctx)


	def CreateNewSession(self, ctx):
		'''Create new session and add that into a context or request
			@return newly created session (used in inherited classes)'''
		ses = _sesmansvc_session.Session(ctx, 1200, self)
		ctx.Session = ses
		return ses


	def RemoveSession(self, ctx, sin):
		'''Remove session from context'''
		return
