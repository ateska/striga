import os, logging
import striga.server.service
import pyinotify
import errno

###

L = logging.getLogger("loader")

###


class FSWatchdogService(striga.server.service.Service):


	def __init__(self, parent, name='FSWatchdog', startstoppriority = 100):
		striga.server.service.Service.__init__(self, parent, name, startstoppriority)
		self._ChangeServiceStateToConfigured()
		self.__watchManager = pyinotify.WatchManager()
		self.__notifier = pyinotify.Notifier(self.__watchManager, timeout=10)
		self.__callbacks = dict()
		self.__watches = dict()


	def _DoStart(self):
		app = striga.server.application.GetInstance()
		app.Scheduler.AddJob(striga.server.scheduler.PeriodicJob(1, self.__Tick))


	def _DoStop(self):
		#Remove scheduler task
		app = striga.server.application.GetInstance()
		app.Scheduler.RemoveAllJobsFor(self.__Tick)


	def __Tick(self):
		self.__notifier.process_events()
		while self.__notifier.check_events():  #loop in case more events appear while we are processing
			self.__notifier.read_events()
			self.__notifier.process_events()
		

	def WatchFile(self, filename, callback):
		if not self.__watches.has_key(filename):
			watch = self.__watchManager.add_watch(filename, pyinotify.IN_MODIFY, proc_fun=self.__handleFileChange)
			self.__watches.update(watch)
			
		if not self.__callbacks.has_key(filename):
			self.__callbacks[filename] = list()
		self.__callbacks[filename].append(callback)


	def __handleFileChange(self, event):
		for cb in self.__callbacks.get(event.pathname):
			# TODO: So far we are handling IN_MODIFY events only and sending "M" flagged callbacks
			# only. if there is a need to extend this, also remember to change the input mask
			# in add_watch  
			if event.mask == pyinotify.IN_MODIFY:
				cb(event.pathname, "M")
		
