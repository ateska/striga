import os, sys, logging
import striga.core.sfinfo
import striga.server.service, striga.server.application, striga.core.exception

pyinotifyLoaded = False
try:
	import pyinotify
	pyinotifyLoaded = True
except ImportError:
	pass
	

from . import _stsvcld_striga
from . import _stsvcld_python

###

L = logging.getLogger("loader")

###

class LoaderService(striga.server.service.Service):


	def __init__(self, parent, name='Loader', startstoppriority = 110):
		striga.server.service.Service.__init__(self, parent, name, startstoppriority)

		if sys.platform == 'win32':
			from . import _stsvcld_fswwin32
			_stsvcld_fswwin32.FSWatchdogService(self)
		elif pyinotifyLoaded:
			from . import _stsvcld_pyinotify
			_stsvcld_pyinotify.FSWatchdogService(self)
		else:
			from . import _stsvcld_fswuni
			_stsvcld_fswuni.FSWatchdogService(self)

		self.__loaderCache = {}
		self.StrigaImplicitPathsGenerators = []

		self._ChangeServiceStateToConfigured()


	def _DoStop(self):
		for l in self.__loaderCache.itervalues():
			l.Unload()


	#TODO: Periodic check on loader cache - count number of references, if low, remove loadable


	def Load(self, loadableclass, *args, **kwargs): #Has also hidden keyword argument doload=True
		self.ServiceStartCheck()

		#Extract doload argument
		doload = kwargs.pop('doload', True)

		#Check if not loaded already
		key = tuple([loadableclass] + list(args) + kwargs.items())
		cret = self.__loaderCache.get(key, None)
		if cret is not None:
			#Even when cached, it can be not loaded, so load
			if doload: cret.Load()
			return cret

		#L.debug("Loading '%s' with args %s" % (loadableclass.__name__, str(list(args) + kwargs.items())))

		nl = loadableclass(self, *args, **kwargs)
		self.__loaderCache[key] = nl

		if doload:
			try:
				nl.Load()
			except:
				try: del self.__loaderCache[key]
				except: pass
				raise

		return nl


	def LoadStrigaFile(self, source, buildmode, doload):
		'''Shortcut function'''
		return self.Load(_stsvcld_striga.LoadableStriga, source, buildmode = buildmode, doload = doload)


	def LoadPythonFile(self, source, doload):
		'''Shortcut function'''
		return self.Load(_stsvcld_python.LoadablePython, source, doload = doload)


	def TagImport(self, sfinfo, *params):
		'''
		Params is array of 2 items tuples (modulename, first)
		Module name is possibly dotted notation of striga file to find;
		is boolean - True means return first module form dotted sequence, False is return last (for 'as' statements)
		'''
		self.ServiceStartCheck()

		buildmode = sfinfo.BuildModeName
		reffile = sfinfo.FileName

		#Find my loader
		modulesource =  os.path.splitext(os.path.abspath(reffile))[0]

		#Do not make dependency net when compiling
		if isinstance(sfinfo, striga.core.sfinfo.CompileTimeStrigaFileInfo):
			loadable = None
		else:
			for loadable in self.__loaderCache.itervalues():
				if isinstance(loadable, _stsvcld_python.LoadablePython):
					if loadable.GetSource() == modulesource:
						loadable = loadable.GetPythonCompiledLoadable() #Dependency is created to compiled Python
						break
			else:
				raise striga.core.exception.StrigaRuntimeException("Tag import called from module not managed by loader service")

		#Start importing
		startdir = os.path.dirname(reffile)
		retmods = []
		for modulename, first in params:

			rstartdir = startdir
			mods = []
			strigafiles = []
			for partmodname in modulename.split('.'):
				if (len(mods) > 0) and (hasattr(mods[-1], partmodname)):
					mods.append(getattr(mods[-1], partmodname))
				else:
					source = self.FindStrigaFile(rstartdir, partmodname, buildmode, useimplicitpaths = (len(mods) == 0))
					strigafile = self.LoadStrigaFile(source, buildmode, doload = True)
					mod = strigafile.GetModule()

					if mod is None:
						raise striga.core.exception.StrigaRuntimeException("Importing invalid striga file '%s'" % str(strigafile))

					mods.append(mod)
					if loadable is not None:
						strigafile.AddDependant(loadable)

				rstartdir = os.path.dirname(mods[-1].__file__)

			#Handle 'first' ...
			if first:
				retmods.append(mods[0])
			else:
				retmods.append(mods[-1])

		return retmods


	def FindStrigaFile(self, startdir, modulename, mode, useimplicitpaths):
		(strigafilename, pythonfilename, comppyfilename) = _stsvcld_striga.LoadableStriga.PrepareSourceFilenames(modulename, mode)
		(dirstrigafilename, dirpythonfilename, dircomppyfilename) = _stsvcld_striga.LoadableStriga.PrepareSourceFilenames(modulename + '/__init__', mode)

		dirs = [startdir]
		if useimplicitpaths:
			for imppgen in self.StrigaImplicitPathsGenerators:
				dirs.extend(imppgen())

		for sdir in dirs:

			#File as module
			if		os.path.isfile(os.path.join(sdir, strigafilename)) \
				or	os.path.isfile(os.path.join(sdir, pythonfilename)) \
				or	os.path.isfile(os.path.join(sdir, comppyfilename)):
				return os.path.join(sdir, modulename)

			#Directory as module
			if		os.path.isfile(os.path.join(sdir, dirstrigafilename)) \
				or	os.path.isfile(os.path.join(sdir, dirpythonfilename)) \
				or	os.path.isfile(os.path.join(sdir, dircomppyfilename)):
				return os.path.join(sdir, modulename, '__init__')

		raise striga.core.exception.StrigaRuntimeException("Cannot find striga file '%s' - Python or Striga source file not found" % modulename)


	def IterLoaderCache(self):
		return self.__loaderCache.iteritems()


	def RemoveAllDependencies(self, fromloadable, ltype):
		for loadable in self.__loaderCache.itervalues():
			if isinstance(loadable, ltype):
				loadable.DiscardDependant(fromloadable)
