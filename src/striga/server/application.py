import sys, weakref, optparse, logging as L
import striga.core.cmdlineopts, striga.core.config, striga.core.exception, striga.core.executor
import striga.server.service, striga.server.scheduler
import striga.service.log

###

class Application(striga.core.executor.Executor):


	_singleton = None


	#Here we define reachable modules/services; key for this dict is configuration directive
	#Module will be loaded only if this directive is seen on top level of configuration file
	LateLoadServices = {
		#TODO: This is here as connection must be defined for SQLObjects - even for compiler
		#  ... not sure what exactly we should do here ...
		'sqlobject' : ('striga.service.sqlobjectsvc','SQLObjectFactory'),
		'jasperserver' : ('striga.service.jasperserversvc','JasperServerServiceFactory'),
		'subprocessroaster' : ('striga.service.sproaster','SubprocessRoasterServiceFactory'),
		}


	#Top-level config definitions
	ConfigDefinitions = {}


	#List of options to be passed to optparse (see Python manual)
	CmdLineOptionList = [
		optparse.make_option(
					"-c", "--config",
					action="store", dest="Config", metavar="CONFIGFILE",
					help="Read configuration from CONFIGFILE"
		),

		optparse.make_option(
					"-D", "--debug",
					action="store_true", dest="Debug",
					help="Set logging level to debug"
		),

		optparse.make_option(
					"-Q", "--quiet",
					action="store_true", dest="QuietLogging",
					help="Set logging level to quiet"
		),

	]

	#Dictionary with default options
	CmdLineDefaultOptions = {}


	def __init__(self, appname):
		if self._singleton is not None:
			raise striga.core.exception.StrigaRuntimeException("Application is already instantiated!")

		# Prepare configuration
		self.ConfigDictionary = {}

		#Parse command-line arguments
		self.CommandLineOptions = striga.core.cmdlineopts.CommandLineOptions(self.CmdLineOptionList, self.CmdLineDefaultOptions)

		striga.core.executor.Executor.__init__(self)

		Application._singleton = weakref.ref(self)
		self.ApplicationName = appname

		self.Scheduler = striga.server.scheduler.Scheduler()

		#Prepare root service
		self.Services = striga.server.service.Service(None, 'Root',1)

		#Prepare core services (= services that are always present)
		self._PrepareCoreServices()

		self._StartExecutor()

		#Read configuration and configure application
		for s in self.Services.ChildServices.itervalues():
			self.ConfigDefinitions.update(s.GetConfigDefs())

		striga.core.config.Config(self.Services, self.CommandLineOptions.Config, self.ConfigDefinitions, self.LateLoadServices)
		self.Services._ChangeServiceStateToConfigured()


	def __del__(self):
		Application._singleton = None


	def _PrepareCoreServices(self):
		'''
Override this in application constructor to add more 'core' services
		'''
		striga.service.log.LoggerService(self.Services)


	def Run(self):

		L.info("Python interpreter details:\n\tsys.version: %s\n\tsys.version_info: %s\n\tsys.subversion: %s\n\tsys.platform: %s\n\tsys.executable: %s", sys.version.replace('\n',''), sys.version_info, sys.subversion, sys.platform, sys.executable)

		try:
			self.Services.Start()

			L.info("%s is running ...", self.ApplicationName)

			while True:
				try:
					if not self.ExecuteWorker(timeout = 2):
						break

					self.Scheduler.Tick()

				except KeyboardInterrupt:
					L.warning("Received Ctrl-C - exiting ...")
					break;

		finally:
			self.Services.Stop()
			#Remove all tasks from Executor queue (we are only thread that is still working)
			self._DiscardAllPendingWorkers()
			self._StopExecutor()


	@classmethod
	def GetInstance(cls):
		if Application._singleton is None: return None
		return Application._singleton()

	@classmethod
	def GetInstanceRef(cls):
		return Application._singleton

#Shortcut
GetInstance = Application.GetInstance
GetInstanceRef = Application.GetInstanceRef
