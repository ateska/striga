import os, sys, imp, compiler, gc, weakref, logging
import striga.core.exception
from . import _stsvcld_lobj

###

L = logging.getLogger("loader")

###

class LoadablePythonSource(_stsvcld_lobj.LoadableFileBase):

	def __init__(self, loader, filename):
		_stsvcld_lobj.LoadableFileBase.__init__(self, loader, filename)
		self.__trgpycname = os.path.splitext(filename)[0] + LoadablePython.CompiledSuffix


	def _DoLoad(self):
		#If source file is not existing, do not launch compiler
		newstatus, error = _stsvcld_lobj.LoadableFileBase._DoLoad(self)
		if newstatus != self.States.Loaded:
			L.warning("Python source file '%s' not found" % self._filename)
			return newstatus, error

		#Compile (only if Python compiled file is older that Python source file)
		if not self.IsOlderThan(self.__trgpycname):
			try:
				compiler.compileFile(self._filename)
			except Exception, e:
				return(self.States.NotLoaded, [str(e)]) #TODO: Better error reporting

		return self.States.Loaded, None

###

class LoadablePythonCompiled(_stsvcld_lobj.LoadableFileBase):


	def __init__(self, loader, filename):
		_stsvcld_lobj.LoadableFileBase.__init__(self, loader, filename)
		self.__impmod = None
		self.__impmodts = None
		self.__loaderref = weakref.ref(loader)


	def _DoLoad(self):
		#If source file is not existing, do not launch compiler
		newstatus, error = _stsvcld_lobj.LoadableFileBase._DoLoad(self)
		if newstatus != self.States.Loaded:
			L.warning("Python compiled file '%s' not found" % self._filename)
			return newstatus, error

		#If file is changed, do unload and then we will do clean load again
		if (os.path.getmtime(self._filename) != self.__impmodts):
			self._DoUnload()

		if (self.__impmod is None):
			path, name = os.path.split(self._filename)
			name = os.path.splitext(name)[0]

			L.debug("Importing '%s'" % self._filename)

			if name in sys.modules:
				#TODO: IMPORTANT - it can happen that modules are in sys.modules as imp.load_module bellow can recursively invoke this function
				L.warning("Python file '%s' already loaded - cannot load!" % (name))
				return self.States.NotLoaded, ["Python file '%s' already loaded - cannot load!" % (name)]

			try:
				fp, pathname, description = imp.find_module(name, [path])
			except ImportError:
				return self.States.NotFound, ["Cannot find python file '%s' in '%s'!" % (name, path)]

			#Remove all dependencies created by TagImport (etc.) - they will be recreated by load
			loader = self.__loaderref()
			loader.RemoveAllDependencies(self, LoadablePython)

			try:
				self.__impmod = imp.load_module(name, fp, pathname, description)

			except Exception, e:
				L.exception("Exception when loading module")

				if sys.modules.has_key(name):
					del sys.modules[name]

				self.__impmod = None
				self.__impmodts = None
				return self.States.NotLoaded, [str(e)] #TODO: Better error reporting

			finally:
				fp.close()

			#We are keeping separated list of loaded views
			#Looks strange but works
			del sys.modules[name]

		self.__impmodts = os.path.getmtime(self._filename)
		return self.States.Loaded, None


	def _DoUnload(self):
		module = self.__impmod
		self.__impmod = None
		self.__impmodts = None

		newstatus, error = _stsvcld_lobj.LoadableFileBase._DoUnload(self)

		if module is not None:
			gc.collect()

			if len(gc.get_referrers(module)) > 1:
				L.warning("Python file '%s' seems to be still referenced from somewhere (probably not unloaded)" % self._filename)
				for ref in gc.get_referrers(module):
					if isinstance(ref, dict):
						print ref
					else:
						print type(ref)
				return newstatus, ["Python file '%s' seems to be still referenced from somewhere (probably not unloaded)" % self._filename]

		return newstatus, error


	def GetModule(self):
		if not self.IsLoaded(): return None
		return self.__impmod

###

class LoadablePython(_stsvcld_lobj.LoadableBase):
	'''
	This class is virtual loadable that handles loading from 2 possible sources (python source, python compiled)
	'''

	#Determine suffix for compiled python modules
	for CompiledSuffix, CompiledMode, CompiledType in imp.get_suffixes():
		if CompiledType == imp.PY_COMPILED:
			break
	else:
		del CompiledSuffix
		del CompiledMode
		del CompiledType
		raise striga.core.exception.StrigaRuntimeException("Could not find compiled Python files extension")


	def __init__(self, loader, source):
		_stsvcld_lobj.LoadableBase.__init__(self, loader)

		self._source = source

		self._PythonCompiled = loader.Load(LoadablePythonCompiled, source + self.CompiledSuffix, doload = False)
		self._PythonCompiled.AddDependant(self)

		self._PythonSource = loader.Load(LoadablePythonSource, source + '.py', doload = False)
		self._PythonSource.AddDependant(self._PythonCompiled)


	def _DoLoad(self):
		#First try to load (compile) Python source file
		if not self._PythonSource.Load():
			if self._PythonSource.GetStatus() != self.States.NotFound:
				return self._PythonSource.GetStatusAndError()

		#Then load Python compiled file
		if not self._PythonCompiled.Load():
			if self._PythonCompiled.GetStatus() != self.States.NotFound:
				return self._PythonCompiled.GetStatusAndError()

		return self._PythonCompiled.GetStatusAndError()


	def _DoUnload(self):
		ok = True

		if self._PythonCompiled.IsLoaded():
			ok &= self._PythonCompiled.Unload()

		if self._PythonSource.IsLoaded():
			ok &= self._PythonSource.Unload()

		if not ok:
			return self.GetStatus(), ["Unload failed on loader object '%s'" % str(self)]

		return self.States.NotLoaded, None


	def GetSource(self):
		return self._source


	def GetModule(self):
		return self._PythonCompiled.GetModule()


	def GetPythonCompiledLoadable(self):
		return self._PythonCompiled


	def __repr__(self):	return '<%s object at 0x%X [%s] _source: %s>' % (self.__class__.__name__, id(self), self.GetStatusStr(), self._source)


	def GetStatusString(self):
		ret = _stsvcld_lobj.LoadableBase.GetStatusString(self)
		ret += '\n >>>> Python compiled: ' + self._PythonCompiled.GetStatusString()
		ret += '\n >>>> Python source: ' + self._PythonSource.GetStatusString()
		return ret
