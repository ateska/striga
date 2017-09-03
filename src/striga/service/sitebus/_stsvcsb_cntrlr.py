import os, re, logging as L
import striga.core.exception, striga.core.mvc
import striga.server.application

from ._stsvcsb_utils import PathLimiter, LoabableObject

###

class Controller(PathLimiter, LoabableObject):
	'''
Process bus object handles controlling for MVC architecture
	'''

	PathCheckRE = re.compile(r'^[^//]*$')

	def __init__(self, rootdir, source, controllerclass, pathlimit = '==0'):
		app = striga.server.application.GetInstance()
		loadable = app.Services.Loader.LoadPythonFile(os.path.abspath(os.path.join(rootdir, source)), doload = False)

		PathLimiter.__init__(self, pathlimit)
		LoabableObject.__init__(self, loadable)

		self.RootDir = rootdir
		self.ControllerClassName = controllerclass
		self.Controller = None

		#TODO: Can be view or exec
		self.DefaultView = None
		self.Views = {}


	def _configure(self, conffilename):
		return{
			'view' : self.__configure_view,
			'exec' : self.__configure_exec,
			'!' : self._configure_finished,
		}


	def __configure_view(self, conffilename, source, mode, path = None, entry='main'):
		'''
		Config keyword - view
		'''
		from ._stsvcsb_view import View

		if path is not None:
			if self.PathCheckRE.match(path) is None:
				raise striga.core.exception.StrigaConfigurationError("Invalid path '%s' given!" % path)

			if self.Views.has_key(path):
				raise striga.core.exception.StrigaConfigurationError("Bus item for '%s' is already configured!" % path)

			self.Views[path] = View(self.RootDir, source, mode, entry, pathlimit = '==1')

		else:
			if self.DefaultView is not None:
				raise striga.core.exception.StrigaConfigurationError("Default view for controller is already configured!")

			self.DefaultView = View(self.RootDir, source, mode, entry, pathlimit = '==0')


	#TODO: __configure_view and __configure_exec is copy&paste...
	def __configure_exec(self, conffilename, source, entry, path = None, pathlimit = '==0'):
		'''
		Config keyword - exec
		'''
		from ._stsvcsb_exec import Exec

		if path is not None:
			if self.PathCheckRE.match(path) is None:
				raise striga.core.exception.StrigaConfigurationError("Invalid path '%s' given!" % path)

			if self.Views.has_key(path):
				raise striga.core.exception.StrigaConfigurationError("Bus item for '%s' is already configured!" % path)

			self.Views[path] = Exec(self.RootDir, source, entry, pathlimit = '==1')

		else:
			if self.DefaultView is not None:
				raise striga.core.exception.StrigaConfigurationError("Default view for controller is already configured!")

			self.DefaultView = Exec(self.RootDir, source, entry, pathlimit = '==0')


	def _configure_finished(self):
		pass


	def BusStart(self):
		for bm in self.Views.itervalues():
			if hasattr(bm, 'BusStart'): bm.BusStart()

		if hasattr(self.DefaultView, 'BusStart'): self.DefaultView.BusStart()

		LoabableObject.BusStart(self)


	def BusStop(self):
		LoabableObject.BusStop(self)

		for bm in self.Views.itervalues():
			if hasattr(bm, 'BusStop'): bm.BusStop()

		if hasattr(self.DefaultView, 'BusStop'): self.DefaultView.BusStop()


	def __call__(self, ctx, path):
		self.CheckPath(path)

		if self.Controller is None:
			L.warning("Controller python file '%s' is not loaded (yet) - it is in status '%s'" % (str(self.LoabableObject), self.LoabableObject.GetStatusString()))
			raise striga.core.exception.StrigaBusError('NotLoaded')


		viewspecs = self.Controller(ctx, path)

		if isinstance(viewspecs, striga.core.mvc.CallViewWithPath):
			try:
				bm = self.Views[viewspecs.Path]
			except KeyError:
				raise striga.core.exception.StrigaBusError('NotFound')
			path = [viewspecs.Path]

		elif isinstance(viewspecs, striga.core.mvc.CallView):
			bm = self.DefaultView
			if bm is None:
				raise striga.core.exception.StrigaBusError('NotFound')
			path = []

		elif viewspecs is None:
			L.warning("MVC View returned None - translating that into StrigaNoContent exception")
			raise striga.core.exception.StrigaNoContent()

		elif viewspecs is False:
			# If controller returns False, it means there is no View produced (assuming controller already provided response data)
			return

		else:
			L.warning("Controller returned unknown type '%s'", str(type(viewspecs)))
			raise striga.core.exception.StrigaBusError('NotFound')

		bm(ctx, path, *viewspecs.Args, **viewspecs.KWArgs)


	def _OnLOLoaded(self, pythonfile):
		module = self.LoabableObject.GetModule()
		if not hasattr(module, self.ControllerClassName):
			L.error("Python file '%s' does not contain controller class '%s'" % (str(self.LoabableObject), self.ControllerClassName))
			raise striga.core.exception.StrigaRuntimeException("Python file '%s' does not contain controller class '%s'" % (str(self.LoabableObject), self.ControllerClassName))

		self.Controller = getattr(module, self.ControllerClassName)()

		L.debug("Python file '%s' loaded" % str(pythonfile))


	def _OnLOFailed(self, pythonfile):
		self.Controller = None
		L.debug("Python file '%s' unloaded" % str(pythonfile))
