import os, logging

import striga.core.exception
from striga.external.enum import Enum

###

L = logging.getLogger("loader")

###

class LoadableBase(object):

	States = Enum("NotFound", "Loaded", "NotLoaded")

	def __init__(self, loader):
		self.__error = None
		self.__status = None
		self.__callbacks = {}
		self.__status = self.States.NotLoaded
		self.__dependants = set()


	def __changeStatus(self, newstatus, newerror):
		if newstatus not in self.States:
			raise striga.core.exception.StrigaRuntimeException("Invalid state '%s' for loadable" % str(newstatus))

		if self.__status == newstatus:
			if (newstatus != self.States.NotLoaded) or (newerror != None):
				self.__error = newerror
			return

		self.__status = newstatus
		if (newstatus != self.States.NotLoaded) or (newerror != None):
			#When unloading, do not reset an error
			self.__error = newerror

		#Callbacks
		for cb in self.__callbacks.get(self.__status, []):
			cb(self)


	def _DoUnload(self):
		'''
		Internal inteface - override this in implementation, return new status / None (if there is no change)
		'''
		if self.__status == self.States.Loaded:
			return self.States.NotLoaded, None

		return self.__status, self.__error


	def _DoLoad(self):
		'''
		Internal inteface - override this in implementation, return new status / None (if there is no change)
		'''
		raise NotImplementedError("Load method called on virtual class LoadableBase")


	def Load(self):
		'''
		External inteface - override this in implementation, return new status
		'''

		#Prevent calling Load on already loaded object
		if self.IsLoaded(): return True

		try:
			L.debug("Loading '%s'" % str(self))
			ret = self._DoLoad()
		except Exception, e:
			L.exception("Exception when loading loader object '%s'" % str(self))
			self._DoUnload()
			self.__changeStatus(self.States.NotLoaded, [str(e)])
			raise

		newstatus, error = ret

		#When loading fails, do unload (clean-up)
		if (self.__status == self.States.Loaded) and (newstatus != self.States.Loaded):
			self._DoUnload()

		self.__changeStatus(newstatus, error)

		#Load dependants
		if self.IsLoaded():
			for dep in self.__dependants:
				if not dep.Load():
					L.warning("Dependant '%s' not loaded" % dep)

		return self.IsLoaded()


	def Unload(self):
		'''
		External inteface - override this in implementation, return new status
		'''

		#Prevent calling Unload on already uloaded object
		if (self.__status == self.States.NotLoaded) and (self.__error is None): return True

		#Unload dependants
		olddependants = self.__dependants
		self.__dependants = set()

		try:
			for dep in olddependants:
				dep.Unload()
		finally:
			self.__dependants = olddependants

		#Prevent calling Unload on already unloaded object (again - this is antirecursion protection)
		if (self.__status == self.States.NotLoaded) and (self.__error is None): return True

		try:
			L.debug("Unloading '%s'" % str(self))
			ret = self._DoUnload()
		except Exception, e:
			L.exception("Exception when unloading loader object '%s'" % str(self))
			self.__changeStatus(self.States.NotLoaded, [str(e)])
			raise

		if ret is not None:
			newstatus, error = ret
			self.__changeStatus(newstatus, error)

		return (self.__status == self.States.NotLoaded)


	def ForceLoad(self):
		if not self.Unload(): return False
		return self.Load()


	def GetStatus(self): return self.__status
	def GetError(self): return self.__error
	def GetStatusAndError(self): return self.__status, self.__error
	def GetStatusString(self):
		if self.__status == self.States.Loaded:
			return "Loaded"
		elif self.__status == self.States.NotLoaded:
			if self.__error is None:
				return "Not loaded"
			else:
				return "Not loaded with error:\n" + '\n'.join(self.__error)
		elif self.__status == self.States.NotFound:
			if self.__error is None:
				return "Not found"
			else:
				return "Not found with error:\n" + '\n'.join(self.__error)

	def GetStatusStr(self):
		if self.__status == self.States.Loaded:
			ret = "LOADED"
		elif self.__status == self.States.NotLoaded:
			ret = "NOT LOADED"
		elif self.__status == self.States.NotFound:
			ret = "NOT FOUND"

		if self.__error is not None:
			ret += ' WITH ERROR'

		return ret

	def IsLoaded(self): return self.__status == self.States.Loaded

	# Callbacks
	def RegisterCallback(self, status, fnct):
		self.__callbacks.setdefault(status, []).append(fnct)

	# Representation
	def __repr__(self):	return '<%s object at 0x%X [%s]>' % (self.__class__.__name__, id(self), self.GetStatusStr())


	# Dependencies
	def AddDependant(self, loadable):
		self.__dependants.add(loadable)

	def DiscardDependant(self, loadable):
		self.__dependants.discard(loadable)

	def GetDependants(self):
		return iter(self.__dependants)


###

class LoadableFileBase(LoadableBase):

	def __init__(self, loader, filename):
		LoadableBase.__init__(self, loader)
		self._filename = os.path.abspath(filename)
		self._lastloadmtime = 0
		loader.FSWatchdog.WatchFile(filename, self._FSWatchdogCallback)


	def _DoLoad(self):
		self._lastloadmtime = os.path.getmtime(self._filename)

		if not os.path.isfile(self._filename):
			return(self.States.NotFound, ["File '%s' not found" % self._filename])
		else:
			return self.States.Loaded, None


	def _FSWatchdogCallback(self, filename, action):
		L.debug("Loader object '%s' received FS watchdog callback type '%s'" %(str(self), action))
		if action == 'D':
			self.Load()
			return

		#Do not react on notification that was already handled (events caused by compilation process itself)
		try:
			if self._lastloadmtime == os.path.getmtime(self._filename):
				L.debug("Ignoring watchdog callback type '%s' on loader object '%s' - already handled" %(action, str(self)))
				return
		except:
			pass

		if action == 'M':
			self.ForceLoad()
			return

		if action == 'C':
			self.ForceLoad()
			return

		raise striga.core.exception.StrigaRuntimeException("Unknown file system watchdog activity '%s'" % action)


	def IsOlderThan(self, filename):
		'''
		There is a logic behind using 'IsOlderThan' over 'IsNewerThan' - because if trg file is not existing, we will get False response
		and this will work in Load decision making
		'''
		fileXMTime = os.path.getmtime(self._filename)
		if not os.path.isfile(filename): return False
		if fileXMTime > os.path.getmtime(filename): return False
		return True


	def GetFileName(self): return self._filename

	def __repr__(self):	return '<%s object at 0x%X [%s] _filename: %s>' % (self.__class__.__name__, id(self), self.GetStatusStr(), self._filename)

###
