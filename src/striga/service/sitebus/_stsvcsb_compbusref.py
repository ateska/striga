import weakref, logging as L
import striga.core.exception
import striga.server.application

###

class ComponentBusRef(object):
	'''
Process bus object that passes control to component subbus (componentbus) (componentbus reference)
	'''

	def __init__(self, component, busname):
		self.Component = component
		self.BusName = busname
		self.BusRef = None


	def __call__(self, ctx, path):
		self.BusRef()(ctx, path)


	def BusStart(self):
		app = striga.server.application.GetInstance()

		try:
			comp = getattr(app.Services.ComponentManager, self.Component)
		except AttributeError:
			raise striga.core.exception.StrigaConfigurationError("Cannot find component '%s' when resolving reference to component bus" % self.Component)

		try:
			cbus = getattr(comp, self.BusName)
		except AttributeError:
			raise striga.core.exception.StrigaConfigurationError("Cannot find component bus '%s' in component '%s' when resolving reference to component bus" % (self.BusName, self.Component))

		cbus.IncreaseRefs()

		self.BusRef = weakref.ref(cbus)


	def BusStop(self):
		if self.BusRef is not None:
			cbus = self.BusRef()
			self.BusRef = None
			cbus.DecreaseRefs()
		else:
			L.warning("Component bus object already dereferenced")
