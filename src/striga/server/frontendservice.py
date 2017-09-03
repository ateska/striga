import logging, weakref
import striga.core.exception
import striga.server.application, striga.server.service
import striga.service.socketserver

###

L = logging.getLogger('Frontend')
L.setLevel(logging.NOTSET)

###

class FrontendService(striga.server.service.Service):
	'''
	Base class for frontend service
	'''

	def __init__(self, parent, name, startstoppriority):
		striga.server.service.Service.__init__(self, parent, name, startstoppriority)
		self.ApplicationRef = weakref.ref(striga.server.application.GetInstance())
		self.SiteBusRef = None
		self.SiteBusName = 'SiteBus'


	def _configure(self, conffilename):
		return {
			'tcpipv4' : self.__configure_tcpipv4,
			'sitebus' : self.__configure_sitebus,
			'!' : self._configure_finished,
		}


	def __configure_tcpipv4(self, conffilename, host = '0.0.0.0', port = 4000):
		#Here we are creating 'child' service ...
		striga.service.socketserver.TCPIPv4TCPServerService(
			host, port,
			self._socketReady,
			self, 'TCPIPv4Server', 201)


	def __configure_sitebus(self, conffilename, name):
		self.SiteBusName = str(name)


	def _configure_finished(self):
		#Obtain thread pool ...
		app = striga.server.application.GetInstance()

		#This actually creates dependency on thread pool service ...
		#TODO: Service dependency handling
		self.ThreadPool = weakref.ref(app.Services.ThreadPool)

		self._ChangeServiceStateToConfigured()


	def _DoStart(self):
		app = striga.server.application.GetInstance()

		if not hasattr(app.Services, self.SiteBusName):
			raise striga.core.exception.StrigaConfigurationError("Cannot start frontend service '%s' as there is no sitebus '%s'" % (self.ServiceName, self.SiteBusName))

		self.SiteBusRef = weakref.ref(getattr(app.Services, self.SiteBusName))
		L.debug("Frontend service '%s' connected to '%s'" % (self.ServiceName, self.SiteBusRef().ServiceName))


	def _DoStop(self):
		self.SiteBusRef = None


	def _socketReady(self, socket):
		'''
		Override this in implementation
		'''
		pass
