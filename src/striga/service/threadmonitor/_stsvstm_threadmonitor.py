import sys, os, traceback, threading, logging
import striga.server.service, striga.server.application

###

L = logging.getLogger('ThreadMonitor')
L.setLevel(logging.NOTSET)

###

class ThreadMonitorService(striga.server.service.Service):


	def __init__(self, parent, name='ThreadMonitor', startstoppriority = 100):
		striga.server.service.Service.__init__(self, parent, name, startstoppriority)


	def GetConfigDefs(self):
		return {'threadmonitor' : self.__configure }


	def __configure(self, conffilename, interval=5, cntrlfilename='dumpthreads', logfilename='dumpthreads.log'):
		self.__conf_Interval = interval
		self.__conf_CntrlFilename = cntrlfilename
		self.__conf_LogFilename = logfilename
		self._ChangeServiceStateToConfigured()


	def _DoStart(self):
		app = striga.server.application.GetInstance()
		app.Scheduler.AddJob(striga.server.scheduler.PeriodicJob(self.__conf_Interval, self.__Tick))


	def _DoStop(self):
		app = striga.server.application.GetInstance()
		app.Scheduler.RemoveAllJobsFor(self.__Tick)


	def __Tick(self):
		if os.path.exists(self.__conf_CntrlFilename):

			L.info("Dumping threads info to '%s'" % self.__conf_LogFilename)

			os.unlink(self.__conf_CntrlFilename)

			code = []

			code.append("Threads names:")
			for t in threading.enumerate():
				code.append("\t" + t.getName())


			code.append("\n\nThreads tracebacks:")
			for threadId, stack in sys._current_frames().items():
				code.append("\n")

				code.append("ThreadID: %s" % threadId)
				for filename, lineno, name, line in traceback.extract_stack(stack):
					code.append('File: "%s", line %d, in %s' % (filename, lineno, name))
					if line:
						code.append("  %s" % (line.strip()))

			code.append("\n")

			file(self.__conf_LogFilename, 'w').write('\n'.join(code))

