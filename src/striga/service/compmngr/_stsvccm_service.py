import os, logging as L
import striga.core.exception
import striga.server.service, striga.server.application

from _stsvccm_component import Component
from _stsvccm_import import DoImport

###

class ComponentManagerService(striga.server.service.Service):


	def __init__(self, parent, searchpaths, name='ComponentManager', startstoppriority = 100):
		striga.server.service.Service.__init__(self, parent, name, startstoppriority)

		self.Paths = searchpaths
		self.LoadedBuildModes = {}

		if os.environ.has_key('STRIGAROOT'):
			if self.Paths is None: self.Paths = []
			self.Paths.append(os.path.join(os.environ['STRIGAROOT'],'components'))

		if self.Paths is None:
			raise striga.core.exception.StrigaConfigurationError("No component search path defined (e.g. configure STRIGAROOT environment variable)")


	def GetConfigDefs(self):
		#TODO: _configure & __configure_finished must be called even 'components' directive is not given!
		return {'components' : self._configure}


	def _configure(self, conffilename, paths = None):
		basedirname = os.path.dirname(conffilename)
		if paths is not None:
			for path in paths.split(';'):
				path = os.path.normpath(os.path.join(basedirname, path))
				if os.path.isdir(path):
					self.Paths.append(path)
				else:
					L.warn("Components configuration is referring to non-existing path '%s'" % path)

		#Remove duplicates
		self.Paths = set(self.Paths)
		L.debug("Components configuration paths: %s" % ';'.join(self.Paths))

		#Load implicit component
		self.LoadComponent("__builtin")

		return {
			'component' : self.__configure_component,
			'!' : self.__configure_finished,
		}


	def __configure_component(self, conffilename, name):
		self.LoadComponent(name)


	def __configure_finished(self):
		self._ChangeServiceStateToConfigured()


	def _DoStart(self):
		striga.server.application.GetInstance().Services.Loader.StrigaImplicitPathsGenerators.append(self.GetPublicTagLibraries)


	def _DoStop(self):
		self.LoadedBuildModes.clear()
		striga.server.application.GetInstance().Services.Loader.StrigaImplicitPathsGenerators.remove(self.GetPublicTagLibraries)


	def LoadComponent(self, name):
		self.ServiceStartCheck()

		#Check if component is already loaded - if yes, return
		if self.ChildServices.has_key(name):
			return False

		L.info("Component manager is loading component '%s'" % name)

		#Find a directory with component
		for compdirpath in self.Paths:
			compdirpath = os.path.join(compdirpath, name)
			if os.path.isdir(compdirpath):
				compconfpath = os.path.join(compdirpath, 'striga-component.conf')
				if os.path.isfile(compconfpath):
					break
		else:
			raise striga.core.exception.StrigaConfigurationError("Component '%s' not found" % name)

		#Construct the component - it will be automagically added as subservice ...
		Component(compdirpath, self, name)

		return True


	def GetBuildMode(self, buildmode):
		buildmodes = {}
		for comp in self.ChildServices.itervalues():
			buildmodes.update(comp.BuildModes)

		if not buildmodes.has_key(buildmode):
			raise striga.core.exception.StrigaRuntimeException("Unknown build mode '%s'" % buildmode)

		buildmodepath = buildmodes[buildmode]

		if self.LoadedBuildModes.has_key(buildmodepath):
			return self.LoadedBuildModes[buildmodepath]

		L.debug("Loading 'buildmode_%s' from %s" % (buildmode, buildmodepath))

		buildmodemodule = DoImport('buildmode_' + buildmode, [os.path.dirname(buildmodepath)], "__STRIGA__BuildMode__")
		self.LoadedBuildModes[buildmodepath] = buildmodemodule

		return buildmodemodule


	def GetPublicTagLibraries(self):
		ret = []
		for comp in self.ChildServices.itervalues():
			ret.extend(comp.PublicTagLibrariesDirs)

		return ret
