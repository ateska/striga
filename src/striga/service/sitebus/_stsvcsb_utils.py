import striga.core.exception

###

class PathLimiter(object):

	def __init__(self, pathlimit):
		self.__PathLimit = compile('len(path) ' + pathlimit, '<string>', 'eval')


	def CheckPath(self, path):
		if not eval(self.__PathLimit):
			raise striga.core.exception.StrigaBusError("NotFound")

###

class LoabableObject(object):

	def __init__(self, loadable):
		self.LoabableObject = loadable
		self.LoabableObject.RegisterCallback(self.LoabableObject.States.Loaded, self._OnLOLoaded)
		self.LoabableObject.RegisterCallback(self.LoabableObject.States.NotLoaded, self._OnLOFailed)
		self.LoabableObject.RegisterCallback(self.LoabableObject.States.NotFound, self._OnLOFailed)


	def BusStart(self):
		#TODO: This can be optional (lazy loading of views)
		self.LoabableObject.Load()


	def BusStop(self):
		self.LoabableObject.Unload()


	def Reload(self):
		self.LoabableObject.ForceLoad()


	def _OnLOLoaded(self, lofile):
		pass

	def _OnLOFailed(self, lofile):
		pass
