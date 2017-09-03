import os, logging as L
import striga.core.exception
import striga.server.application
from ._stsvcsb_utils import PathLimiter, LoabableObject

###

class View(PathLimiter, LoabableObject):
	'''
Process bus object that executes Striga views
	'''

	def __init__(self, rootdir, source, mode, entry = 'main', pathlimit = '==0'):
		app = striga.server.application.GetInstance()
		loadable = app.Services.Loader.LoadStrigaFile(os.path.abspath(os.path.join(rootdir, source)), buildmode = mode, doload = False)

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

			if self.LoabableObject.IsLoaded():
				L.warning("Striga view file '%s' is loaded but is doesn't provide striga view interface" % (str(self.LoabableObject)))
				raise striga.core.exception.StrigaBusError('NotFound')

			L.warning("Striga view '%s' is not loaded (yet) - it is in status '%s'" % (str(self.LoabableObject), self.LoabableObject.GetStatusString()))
			raise striga.core.exception.StrigaBusError('NotLoaded')

		ctx.res.SetContentType('text/html')
		ctx.res.SetCacheAge(0)
		out = self.LoabableObject.OutClass(ctx.res.Write)
		self.EntryPoint(ctx, out, *args, **kwargs)


	def _OnLOLoaded(self, strigafile):
		self.EntryPoint = None

		module = self.LoabableObject.GetModule()
		if not hasattr(module, self.Entry):
			L.warning("Striga file '%s' do not contain entry point '%s'" % (str(self.LoabableObject), self.Entry))
			return

		EntryPoint = getattr(module, self.Entry)
		if not callable(EntryPoint):
			L.warning("Striga file '%s' entry point '%s' is not callable" % (str(self.LoabableObject), self.Entry))
			return

		if not hasattr(EntryPoint ,'StrigaViewEntry'):
			L.warning("Striga file '%s' entry point '%s' is not Striga entry (use decorator @StrigaViewEntry)" % (str(self.LoabableObject), self.Entry))
			return

		self.EntryPoint = EntryPoint
		L.info("Striga view '%s' loaded" % str(strigafile))


	def _OnLOFailed(self, strigafile):
		self.EntryPoint = None
		L.info("Striga view '%s' unloaded" % str(strigafile))
