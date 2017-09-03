import sys, os, logging as L
import striga.core.exception
import striga.server.application
from ._stsvcsb_utils import PathLimiter, LoabableObject

###

class Exec(PathLimiter, LoabableObject):
	'''
Process bus object executes Python files
	'''

	def __init__(self, rootdir, source, entry, pathlimit = '==0'):
		#TODO: Currently, configuration cannot state 'rootdir' to be passed here - and it should
		app = striga.server.application.GetInstance()
		loadable = app.Services.Loader.LoadPythonFile(os.path.abspath(os.path.join(rootdir, source)), doload = False)

		PathLimiter.__init__(self, pathlimit)
		LoabableObject.__init__(self, loadable)

		self.Entry = entry
		self.EntryPoint = None


	def __call__(self, ctx, path, *args, **kwargs):
		self.CheckPath(path)

		if self.EntryPoint is None:
			#TODO: Here is a correct place for lazy loading (when self.LoabableObject.IsLoaded is False and self.LoabableObject.GetError is None)
			# - launch worker that will call self.LoabableObject.Load() (retry option bellow must be implemented)

			#TODO: Implement error reporting (Striga file is not loaded - can contain error)

			#TODO: Handle a possiblity that loader is still running (error in self.LoabableObject is None)
			# - wait for some reasonable amount of time and retry

			L.warning("Python file '%s' is not loaded (yet) - it is in status '%s'" % (str(self.LoabableObject), self.LoabableObject.GetStatusString()))
			raise striga.core.exception.StrigaBusError('NotLoaded')

		ctx.res.SetCacheAge(0)
		self.EntryPoint(ctx, path, *args, **kwargs)


	def _OnLOLoaded(self, pythonfile):
		self.EntryPoint = None

		module = self.LoabableObject.GetModule()
		if not hasattr(module, self.Entry):
			L.warning("Python file '%s' do not contain entry point '%s'" % (str(self.LoabableObject), self.Entry))
			return

		EntryPoint = getattr(module, self.Entry)
		if not callable(EntryPoint):
			L.warning("Python file '%s' entry point '%s' is not callable" % (str(self.LoabableObject), self.Entry))
			return

		self.EntryPoint = EntryPoint
		L.debug("Python file '%s' loaded" % str(pythonfile))


	def _OnLOFailed(self, pythonfile):
		self.EntryPoint = None
		L.debug("Python file '%s' unloaded" % str(pythonfile))
