import os, sys, glob, logging as L
import striga.core.config
import logging as L
import striga.server.application, striga.server.service

from . import _stsvccm_import

###

class Component(striga.server.service.Service):

	def __init__(self, directorypath, parent, name, startstoppriority = 110):
		striga.server.service.Service.__init__(self, parent, name, startstoppriority)

		self.DirectoryPath = os.path.abspath(directorypath)
		self.ConfigFilePath = os.path.join(self.DirectoryPath, 'striga-component.conf')
		self.PublicLibrariesDirs = []
		self.PublicTagLibrariesDirs = []
		self.BuildModes = {}

		ConfigDefinitions = {
			'componentbus' : self.__configure_componentbus,
			'libs' : self.__configure_libs,
			'taglibs' : self.__configure_taglibs,
			'buildmodes' : self.__configure_buildmodes,
			'components' : parent._configure,
			'service' : self.__configure_service,
			'!' : self.__configure_finished,
		}

		#Configuration
		app = striga.server.application.GetInstance()
		striga.core.config.Config(app.Services, self.ConfigFilePath, ConfigDefinitions, {})


	def _DoStart(self):
		sys.path.extend(self.PublicLibrariesDirs)


	def _DoStop(self):
		for libdir in self.PublicLibrariesDirs:
			sys.path.remove(libdir)


	def __configure_finished(self):
		self._ChangeServiceStateToConfigured()


	def __configure_componentbus(self, conffilename, rootdir, index = None, name="componentbus"):
		from . import _stsvccm_compbus
		ncb = _stsvccm_compbus.ComponentBus(self, name)
		return ncb._configure(conffilename = conffilename, index = index, rootdir = os.path.normpath(os.path.join(self.DirectoryPath, rootdir)))


	def __configure_taglibs(self, conffilename, path):
		path = os.path.normpath(os.path.join(self.DirectoryPath, path))

		if not os.path.isdir(path):
			L.warn("Tag library path '%s' is not existing" % path)

		self.PublicTagLibrariesDirs.append(path)


	def __configure_buildmodes(self, conffilename, path):
		buildmodespath = os.path.normpath(os.path.join(self.DirectoryPath, path))

		if os.path.isdir(buildmodespath):
			for bmm in glob.glob(os.path.join(buildmodespath,"buildmode_*.py")):
				if os.path.isfile(bmm):
					self.BuildModes[os.path.splitext(os.path.basename(bmm))[0][10:]] = bmm
		else:
			L.warn("Build modes path '%s' is not existing" % path)


	def __configure_libs(self, conffilename, path):
		path = os.path.normpath(os.path.join(self.DirectoryPath, path))

		if not os.path.isdir(path):
			L.warn("Library path '%s' is not existing" % path)

		self.PublicLibrariesDirs.append(path)


	def __configure_service(self, conffilename, source, name = None, path = '', **kwargs):
		svcmod = _stsvccm_import.DoImport(source, [os.path.join(os.path.dirname(conffilename), path)], '')
		svc = svcmod.Service(self, name, **kwargs)
		return svc.Configure()
