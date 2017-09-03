import os, logging
import win32file, win32event, win32con
import striga.server.service

###

L = logging.getLogger("loader")

###


class FSWatchdogService(striga.server.service.Service):


	def __init__(self, parent, name='FSWatchdog', startstoppriority = 100):
		striga.server.service.Service.__init__(self, parent, name, startstoppriority)
		self._ChangeServiceStateToConfigured()
		self.__watchedDirs = {}


	def _DoStart(self):
		app = striga.server.application.GetInstance()
		app.Scheduler.AddJob(striga.server.scheduler.PeriodicJob(1, self.__Tick))


	def _DoStop(self):
		#Remove scheduler task
		app = striga.server.application.GetInstance()
		app.Scheduler.RemoveAllJobsFor(self.__Tick)


	def __Tick(self):
		if len(self.__watchedDirs) == 0: return

		changes = set()

		while 1:
			#TODO: Split wds if longer that 256 (?) - check limit for WaitForMultipleObjects
			wds = self.__watchedDirs.values()
			handles = [x.ChangeHandle for x in wds]
			result = win32event.WaitForMultipleObjects(handles, 0, 0)
			if result == win32con.STATUS_TIMEOUT: break

			win32file.FindNextChangeNotification(handles[result])
			changes.add(wds[result])

		if len(changes) > 0:
			L.debug("Loader FS Watchdog discovered '%d' change(s) on filesystem" % len(changes))

		for wds in changes:
			wds.OnChangeInDir()


	def WatchFile(self, filename, callback):
		dirname = os.path.abspath(os.path.dirname(filename))
		wd = self.__watchedDirs.get(dirname, None)
		if wd is None:
			wd = WatchedDirectory(dirname)
			self.__watchedDirs[dirname] = wd

		wd.AddFile(filename, callback)

###

class WatchedDirectory(object):


	def __init__(self, dirname):
		self.DirName = dirname
		self.Files = {}

		self.ChangeHandle = win32file.FindFirstChangeNotification (
		  self.DirName,
		  0,
		  win32con.FILE_NOTIFY_CHANGE_LAST_WRITE | win32con.FILE_NOTIFY_CHANGE_FILE_NAME
		)


	def AddFile(self, filename, callback):
		filename = os.path.abspath(filename)
		fl = self.Files.get(filename, None)
		if fl is None:
			fl = WatchedFile(filename)
			self.Files[filename] = fl
		fl.AddCallback(callback)


	def OnChangeInDir(self):
		for fl in self.Files.values():
			fl.Check()

###

class WatchedFile(object):


	def __init__(self, filename):
		self.FileName = filename
		self.Callbacks = []
		if os.path.isfile(self.FileName):
			self.MTime = os.path.getmtime(self.FileName)
		else:
			self.MTime = None


	def AddCallback(self, callback):
		self.Callbacks.append(callback)


	def Check(self):
		if self.MTime is None:
			if not os.path.isfile(self.FileName):
				return

			self._sendMessage('C')
			self.MTime = os.path.getmtime(self.FileName)
			return


		if not os.path.isfile(self.FileName):
			self._sendMessage('D')
			self.MTime = None
			return


		MTime = os.path.getmtime(self.FileName)
		if MTime != self.MTime:
			self._sendMessage('M')
			self.MTime = MTime


	def _sendMessage(self, msg):
		for cb in self.Callbacks:
			cb(self.FileName, msg)
