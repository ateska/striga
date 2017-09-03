import sys, os, atexit, re, StringIO, time, datetime, logging as L, logging.handlers
import striga.server.service, striga.server.application

from ._stsvclg_handler import ManagedRotatingFileHandler

###

class LoggerService(striga.server.service.Service):


	def __init__(self, parent, name='Logger', startstoppriority = 1):
		striga.server.service.Service.__init__(self, parent, name, startstoppriority)
		self.RootLogger = L.getLogger('')
		self.Formater = Formatter()
		self.Handlers = []
		self.TickBase = 0

		#Nasty hack to get rid of 'I/O operation on closed file' - writing to log file after closing file descriptors
		atexit.register(self._DoStop)

		#Consume log messages before this service is configured
		self.DummyHandler = L.StreamHandler(StringIO.StringIO())
		self.DummyHandler.setFormatter(self.Formater)
		self.RootLogger.addHandler(self.DummyHandler)


	def GetConfigDefs(self):
		return {'logging' : self.__configure}


	def __configure(self, conffilename, level="INFO", tick=3600):
		'''
		tick is parameter that specifies number of seconds between TICK line in the log; 0 means that this feature is disabled
		'''
		if isinstance(level, basestring):
			level = level.upper()

		self.TickBase = int(tick)

		#Commandline option Debug has absolute priority
		if striga.server.application.GetInstance().CommandLineOptions.Debug: level = 10
		#Commandline option has precedence
		elif striga.server.application.GetInstance().CommandLineOptions.QuietLogging: level = 40
		elif level == 'CRITICAL': level = 50
		elif level == 'ERROR': level = 40
		elif level == 'WARNING': level = 30
		elif level == 'INFO': level = 20
		elif level == 'DEBUG': level = 10

		if not isinstance(level, int):
			raise RuntimeError("Unknown logging level '%s'" % str(level))

		self.RootLogger.setLevel(level)

		return {
			'file' : self.__configure_file,
			'dir' : self.__configure_dir,
			'stderr' : self.__configure_stderr,
			'!' : self.__configure_finished,
		}


	def __configure_file(self, conffilename, path='./logs/striga.log', rotateWhen='midnight', interval='1d', backupCount = 3):

		#TODO: Implement rotateWhen and interval parsing

		rotateWhen = datetime.time(hour = 0, minute = 0, second = 0)
		interval = datetime.timedelta(days = 1)

		lh = ManagedRotatingFileHandler(path, rotateWhen, interval, int(backupCount))
		lh.setFormatter(self.Formater)
		self.RootLogger.addHandler(lh)
		self.Handlers.append(lh)


	def __configure_dir(self, conffilename, dirname='./logs/', filename='striga.log', rotateWhen='midnight', interval='1d', backupCount = 3):
		'''This is just an extension to 'file' directive, this allows to use log directory configuration separately from log file name - this is useful in larger project with more than one logging sources'''
		return self.__configure_file(conffilename, os.path.join(dirname, filename), rotateWhen, interval, backupCount)


	def __configure_stderr(self, conffilename):
		lh = L.StreamHandler()
		lh.setFormatter(self.Formater)
		self.RootLogger.addHandler(lh)
		self.Handlers.append(lh)


	def __configure_finished(self):
		if self.ServiceState > striga.server.service.Service.States.Loaded:
			return

		self.RootLogger.removeHandler(self.DummyHandler)
		del self.DummyHandler

		L.info('Logging level set to %s', L.getLevelName(self.RootLogger.getEffectiveLevel()))
		self._ChangeServiceStateToConfigured()


	def _DoStart(self):
		if self.TickBase > 0:
			self.LastTickValue = int(time.time()) / self.TickBase
		app = striga.server.application.GetInstance()
		app.Scheduler.AddJob(striga.server.scheduler.PeriodicJob(1, self.__Tick))


	def _DoStop(self):
		#Remove scheduler task
		app = striga.server.application.GetInstance()
		app.Scheduler.RemoveAllJobsFor(self.__Tick)

		for lh in self.Handlers:
			self.RootLogger.removeHandler(lh)
			lh.flush()
			lh.close()

		self.Handlers = []

		self.RootLogger.setLevel(sys.maxint) #Be silent


	def __Tick(self):
		curtime = datetime.datetime.now()

		if self.TickBase > 0:
			ctval = int(time.mktime(curtime.timetuple())) / 3600
			if self.LastTickValue < ctval:
				self.LastTickValue = ctval
				L.info('---- TICK ----')

		for h in self.Handlers:
			if hasattr(h, 'CheckRollover'):
				h.CheckRollover(curtime)

###


class Formatter(L.Formatter):


	def __init__(self):
		L.Formatter.__init__(self,
			'%(asctime)s %(levelname)s %(name)s %(process)d(%(threadName)s:%(thread)d) ==========================\n%(message)s\n'
			)
