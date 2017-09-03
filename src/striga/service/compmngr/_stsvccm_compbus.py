import logging as L
from striga.server.service import Service
from striga.service.sitebus import Bus

###

class ComponentBus(Service, Bus):


	def __init__(self, parent, name = 'ComponentBus', startstoppriority = 500):
		Service.__init__(self, parent, name, startstoppriority)
		Bus.__init__(self)
		self.__references = 0


	def _configure_finished(self):
		self._ChangeServiceStateToConfigured()


	def __call__(self, ctx, path):
		'''
		Entry point to this bus object
		'''
		self.ServiceStartCheck()
		Bus.__call__(self, ctx, path)


	def _DoStart(self):
		#We will not start underlaying bus object as we want to load (and compile)
		#views only when referenced from real process bus
		if self.__references > 0:
			Bus.BusStart(self)


	def _DoStop(self):
		if self.__references > 0:
			Bus.BusStop(self)


	def IncreaseRefs(self):
		if self.__references == 0:
			Bus.BusStart(self)
		self.__references += 1


	def DecreaseRefs(self):
		if self.__references == 0:
			L.warning("Component bus references are already zeroed - cannot decrease it")
			return

		self.__references -= 1
		if self.__references == 0:
			Bus.BusStop(self)
