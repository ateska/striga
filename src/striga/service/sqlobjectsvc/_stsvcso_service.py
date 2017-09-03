import striga.server.service
import sqlobject

###

class SQLObjectFactory(striga.server.service.ServiceFactory):

	def __init__(self, parent, name = 'SQLObjectFactory', startstoppriority = 50):
		striga.server.service.ServiceFactory.__init__(self, SQLObjectService, 'SQLObject', 'sqlobject', parent, name, startstoppriority)


###

class SQLObjectService(striga.server.service.Service):

	def __init__(self, parent, name = 'SQLObject', startstoppriority = 50):
		striga.server.service.Service.__init__(self, parent, name, startstoppriority)
		self.Connection = None


	def _DoStart(self):
		self.Connection = sqlobject.connectionForURI(self.DBURI)
		if self.ToHub:
			sqlobject.sqlhub.processConnection = self.Connection


	def _DoStop(self):
		if self.ToHub:
			sqlobject.sqlhub.processConnection = None
		self.Connection = None


	def _configure(self, conffilename, dburi, tohub="1", model=None):
		tohub = int(tohub)
		self.DBURI = dburi
		self.ToHub = (tohub != 0)
		self._ChangeServiceStateToConfigured()
