import os, sys, time, subprocess, StringIO, threading, logging
from . import _stsvcld_lobj, _stsvcld_python

import striga.core.exception

###

L = logging.getLogger("loader")

###

class LoadableStrigaSource(_stsvcld_lobj.LoadableFileBase):
	#TODO: Single compiler instance protection (worker etc.)

	def __init__(self, loader, filename, buildmode):
		_stsvcld_lobj.LoadableFileBase.__init__(self, loader, filename)
		self.__buildmode = buildmode
		self.__trgpyname = os.path.splitext(filename)[0] + '_' + buildmode + '.py'


	def _DoLoad(self):
		'''Compile Striga file to Python source file'''

		#QA check - compiler should be called only form main thread
		if not isinstance(threading.currentThread(), threading._MainThread):
			raise striga.core.exception.StrigaRuntimeException("Compiler must be launched from main thread - use worker if you need to load anything")

		#If source file is not existing, do not launch compiler
		newstatus, error = _stsvcld_lobj.LoadableFileBase._DoLoad(self)
		if newstatus != self.States.Loaded:
			L.warning("Striga source file '%s' not found" % self._filename)
			return newstatus, error

		#Compile (only if Python source file is older that Striga source file)
		if not self.IsOlderThan(self.__trgpyname):

			L.info("Launching striga compiler on '%s'" % self._filename)

			if os.environ.has_key('STRIGAROOT'):
				compiler = os.path.join(os.environ['STRIGAROOT'],'striga-compiler.py')
			else:
				compiler =  'striga-compiler.py'

			compexec = os.environ.get('STRIGAPYTHON')
			if compexec is None: compexec= sys.executable

			compilerargs = [compexec, compiler, '-b', self.__buildmode, self._filename]
			if _stsvcld_python.LoadablePython.CompiledSuffix.lower() == '.pyo':
				compilerargs.insert(1, "-O")

			p = subprocess.Popen(compilerargs, stderr=subprocess.PIPE, shell = False, bufsize=-1)

			tmperrlog = StringIO.StringIO()

			while p.poll() is None:
				tmperrlog.write(p.stderr.read())
				time.sleep(0.1)

			#TODO: Read tmperrlog till stderr is closed

			ret = p.wait()

			L.info("Striga compiler on '%s' returned %d", self._filename, ret)

			if ret != 0:
				#TODO: Better error reporting ...
				errlogfn = os.path.splitext(self._filename)[0] + '-comp.log'
				errlog = file(errlogfn, 'wb')
				errlog.write(tmperrlog.getvalue())
				errlog.close()

				L.warning("Striga compiler on '%s' returned error - see '%s' for details" % (self._filename, errlogfn))
				return self.States.NotLoaded, ["Striga compiler on '%s' returned error - see '%s' for details" % (self._filename, errlogfn)]

		return self.States.Loaded, None

###

class LoadableStriga(_stsvcld_python.LoadablePython):
	'''
	This class is virtual loadable that handles loading from 3 possible sources (Striga source, python source, python compiled)
	'''

	def __init__(self, loader, source, buildmode):
		_stsvcld_python.LoadablePython.__init__(self, loader, source + '_' + buildmode)

		self._PythonCompiled.RegisterCallback(self.States.Loaded, self.__OnPythonCompiledLoaded)

		self._StrigaSource = loader.Load(LoadableStrigaSource, source + '.stpy', buildmode = buildmode, doload = False)
		self._StrigaSource.AddDependant(self._PythonSource)

		self.OutClass = None


	def _DoLoad(self):
		#First try to load striga source file
		if not self._StrigaSource.Load():
			if self._StrigaSource.GetStatus() != self.States.NotFound:
				return self._StrigaSource.GetStatusAndError()

		#Then load Python
		return _stsvcld_python.LoadablePython._DoLoad(self)


	def _DoUnload(self):
		self.OutClass = None

		newstatus, error = _stsvcld_python.LoadablePython._DoUnload(self)

		ok = True
		if self._StrigaSource.IsLoaded():
			ok &= self._StrigaSource.Unload()

		if not ok:
			return self.GetStatus(), ["Unload failed on loader object '%s'" % str(self)]

		return newstatus, error


	def __OnPythonCompiledLoaded(self, fl):
		module = self.GetModule()
		self.OutClass = module.StrigaFileInfo.DefaultOut


	def GetStatusString(self):
		ret = _stsvcld_python.LoadablePython.GetStatusString(self)
		ret += '\n >>>> Striga source: ' + self._StrigaSource.GetStatusString()
		return ret


	@classmethod
	def PrepareSourceFilenames(cls, source, buildmode):
		strigafilename = source + '.stpy'
		pythonfilename = source + '_' + buildmode + '.py'
		comppyfilename = source + '_' + buildmode + cls.CompiledSuffix
		return (strigafilename, pythonfilename, comppyfilename)
