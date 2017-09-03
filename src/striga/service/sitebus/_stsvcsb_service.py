import striga.server.service

from ._stsvcsb_bus import Bus

###

class SiteBusFactory(striga.server.service.ServiceFactory):

	def __init__(self, parent, name = 'SiteBusFactory', startstoppriority = 500):
		striga.server.service.ServiceFactory.__init__(self, SiteBus, 'SiteBus', 'sitebus', parent, name, startstoppriority)

###

class SiteBus(striga.server.service.Service, Bus):
	#Changes here should be also made in ComponentBus

	def __init__(self, parent, name = 'SiteBus', startstoppriority = 500):
		striga.server.service.Service.__init__(self, parent, name, startstoppriority)
		Bus.__init__(self)


	def _DoStart(self):
		self.BusStart()


	def _DoStop(self):
		self.BusStop()


	def GetConfigDefs(self):
		return {
			'sitebus' : self._configure,
		}


	def _configure_finished(self):
		self._ChangeServiceStateToConfigured()


	def __call__(self, ctx, path):
		'''
		Entry point to this bus object
		'''

		self.ServiceStartCheck()
		Bus.__call__(self, ctx, path)
