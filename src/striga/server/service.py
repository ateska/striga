import weakref, logging as L
import striga.core.exception
from striga.external.enum import Enum

###

#TODO: Service dependencies

class Service(object):

	States = Enum('Loaded', 'Configured', 'Started')

	def __init__(self, parent, name, startstoppriority):
		self.ChildServices = {}
		if parent is not None:
			self.ParentServiceRef = weakref.ref(parent)
		else:
			self.ParentServiceRef = None

		self.ServiceName = name

		if parent is not None:
			if parent.ChildServices.has_key(self.ServiceName):
				i = 2
				while parent.ChildServices.has_key(self.ServiceName + '%d' % i):
					i+=1
				self.ServiceName = self.ServiceName + '%d' % i

		self.ServiceState = Service.States.Loaded
		self.ServiceStartStopPriority = startstoppriority

		#Register service
		if parent is not None:
			parent._RegisterService(self)


	def __del__(self):
		#Destroy all childs ...
		if hasattr(self, 'ChildServices'):
			while 1:
				for k in self.ChildServices.keys():
					self.UnregisterService(k)

				if len(self.ChildServices) == 0:
					break

		#Destroy self
		if hasattr(self, 'ServiceState'):
			if self.ServiceState > Service.States.Configured:
				self.Stop()


	def _ChangeServiceStateToLoaded(self):
		self.ServiceState = Service.States.Loaded


	def _ChangeServiceStateToConfigured(self):
		self.ServiceState = Service.States.Configured


	def _ChangeServiceStateToStarted(self):
		self.ServiceState = Service.States.Started


	def Start(self, alsochilds = True):
		#TODO: Check what happens when starting already started services
		if self.ServiceState < Service.States.Configured:
			raise RuntimeError("Service '%s' is not configured" % self.ServiceName)

		if self.ServiceState <= Service.States.Configured:
			self._DoStart()

			self._ChangeServiceStateToStarted()
			L.info("Service '%s' started" % str(self.GetServiceFullName()))

		if alsochilds:
			services = self.ChildServices.values()
			services.sort(cmp=lambda x,y: cmp(x.ServiceStartStopPriority, y.ServiceStartStopPriority))
			for s in services:
				s.Start(True)


	def Stop(self, alsochilds = True):
		if alsochilds:
			services = self.ChildServices.values()
			services.sort(cmp=lambda x,y: cmp(x.ServiceStartStopPriority, y.ServiceStartStopPriority), reverse = True)
			for s in services:
				s.Stop(True)

		#TODO: Check what happens when starting already started services
		if self.ServiceState < Service.States.Started:
			return #Already stopped

		self._DoStop()

		self._ChangeServiceStateToConfigured()
		L.info("Service '%s' stopped" % str(self.GetServiceFullName()))


	def _DoStart(self):
		'''Override me'''
		pass


	def _DoStop(self):
		'''Override me'''
		pass


	def GetConfigDefs(self):
		'''
		No interaction with configuration engine by default (you can override this)
		'''
		return {}


	def ServiceStartCheck(self):
		if self.ServiceState != self.States.Started:
			striga.core.exception.StrigaRuntimeException("Service '%s' is not started" % self.ServiceName)

	### Service tree


	def GetServiceFullName(self):
		rns = []
		i = self
		while i is not None:
			rns.insert(0,i.ServiceName if i.ServiceName is not None else 'None')
			if i.ParentServiceRef is None: i = None
			else: i = i.ParentServiceRef()
		if len(rns) > 1: del rns[0]
		return '.'.join(rns)


	def _RegisterService(self, childservice):
		if self.ChildServices.has_key(childservice.ServiceName):
			raise KeyError("Service '%s' already contains child service '%s'" % (self.ServiceName, childservice.ServiceName))
		self.ChildServices[childservice.ServiceName] = childservice


	def UnregisterService(self, ServiceName):
		del self.ChildServices[ServiceName]
		L.debug("Service '%s' unregistered" % ServiceName)


	def __getattr__(self, name):
		try:
			return self.ChildServices[name]
		except KeyError:
			raise AttributeError("Cannot find '%s' in %s" % (name, str(self)))


	def __hasattr__(self, name):
		if self.ChildServices.has_key(name): return True
		else: return object.__hasattr__(self, name)

###

class ServiceFactory(Service):
	'''
This (pseudo) service allows to have more frontends of same class configured and running
	'''

	def __init__(self, managedclass, defaultServiceName, configDefinitionName, parent, name, startstoppriority):
		Service.__init__(self, parent, name, startstoppriority)
		self.ManagedClass = managedclass
		self.DefaultServiceName = defaultServiceName
		self.ConfigDefinitionName = configDefinitionName
		self._ChangeServiceStateToConfigured()
		self._ChangeServiceStateToStarted()


	def GetConfigDefs(self):
		return {
			self.ConfigDefinitionName : self._configure
		}


	def _configure(self, conffilename, name = None, **kwargs):
		if name is None: name = self.DefaultServiceName
		ns = self.ManagedClass(self.ParentServiceRef(), name = name)
		return ns._configure(conffilename, **kwargs)
