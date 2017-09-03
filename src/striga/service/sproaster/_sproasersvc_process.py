import sys, os, time, copy, subprocess, itertools, logging

###

L = logging.getLogger('sproaster')

###

class ProcessRunResult(object):

	def __init__(self):
		self.Pid = None
		self.ReturnCode = None
		self.RunningTime = None


	def __repr__(self):
		return "<{0} Pid={1} ReturnCode={2} RunningTime={3}>".format(self.__class__.__name__, self.Pid, self.ReturnCode, self.RunningTime)

###

class _Process(object):
	'''
State:
t - Template
S - Standby
R - Running
D - Delete (me)
E - Error
	'''

	_Counter = itertools.count(1)

	def __init__(self, args, WorkDir=None, Environment=None, SudoUser=None):
		self.Args = args.split(' ') if isinstance(args, basestring) else args
		self.SudoUser = SudoUser 
		argext = os.path.splitext(self.Args[0])[1]
		if argext.lower() == '.py':
			#Add current python interpreter as first argument
			self.Args.insert(0,sys.executable) 

		self.__State = 't' # There is a property to allow other to read this (and prevent writing)
		self.P = None
		self.NoStateChangeTill = None # This postpones next state check till given UTC Unix time (None to avoid check postponing)
		self.Results = []
		self.LaunchTime = None
		self.UID = _Process._Counter.next()

		self.WorkDir = WorkDir
		self.Environment = Environment.copy() if Environment is not None else None

	def __del__(self):
		if self.__State != 't': L.debug("Removing %s", self)


	def __repr__(self):
		pname = ' '.join(self.Args)
		if len(pname) > 20: pname = '...' + pname[-18:]
		return "<{0} '{1}' uid={3} state={2}>".format(self.__class__.__name__, pname, self.__State, self.UID)


	def Clone(self, AlsoSwitchToStandBy = True):
		'Create clone of the process object - or instance from template'
		if self.__State != 't':
			raise RuntimeError("Only template of process can be cloned")
		
		cloned = copy.deepcopy(self)
		cloned.UID = _Process._Counter.next()
		if AlsoSwitchToStandBy: cloned.__State = 'S'
		return cloned


	def Terminate(self):
		if self.__State != 'R':
			raise RuntimeError('Only process in RUNNING state can be terminated (actual state={0})'.format(self.__State))
		
		self.P.terminate()


	def _CheckProcessState(self, curtime):
		'''Check state of the process and change state if needed
		Returns:
			True if status was NOT changed
			False if status was changed
			None if process object should be deleted
		'''

		if self.NoStateChangeTill is not None:
			if self.NoStateChangeTill >= curtime: return True
			self.NoStateChangeTill = None

		try:
			if self.__State == 'S':
				r = self._LaunchCondition()
				if r is None:
					return True
				elif r == 'R':
					self._Launch()
				elif r == 'E':
					self._Error('_LaunchCondition')
				else:
					raise RuntimeError("Unknown _LaunchCondition return value '%s'" % str(r))
				return False

			elif self.__State == 'R':
				
				# Check if subprocess is running - if yes, then return with 'no change'	
				ret = self._Exit()
				if ret is None: return True
	
				r = self._ExitCondition()
				if r == 'S':
					self._Schedule()
				elif r == 'D':
					self._Delete()
					return None
				elif r == 'E':
					self._Error('_ExitCondition')
				else:
					raise RuntimeError("Unknown _ExitCondition return value '%s'" % str(r))
				return False

			elif self.__State == 'E':
				r = self._ErrorCondition()
				if r is None:
					return True
				elif r == 'S':
					self._Schedule()
				elif r == 'D':
					L.warning("%s is removed from roaster due to previous errors", self)
					self._Delete()
					return None
				else:
					raise RuntimeError("Unknown _ErrorCondition return value '%s'" % str(r))
				return False

			elif self.__State == 'D':
				return None

			elif self.__State == 't':
				raise RuntimeError("Invalid use of template process!")

			else:
				raise RuntimeError("Invalid state of the process '%s'" % str(self.__State))

		except:
			L.exception("Exception raised during subprocess roaster operations (process state switched to error)")
			_,e,_ = sys.exc_info()
			self._Error(e)


	def _Launch(self):
		assert(self.P is None)
		assert(self.__State == 'S')

		resultlenlimit = 10 
		if len(self.Results) > resultlenlimit: self.Results = self.Results[-resultlenlimit:] 
		self.Results.append(ProcessRunResult())
		
		L.debug("Launching %s", self)
		try:
			if self.SudoUser is None:
				a = self.Args
			else:
				# sudo -n ... non-interactive mode of sudo 
				a = ['sudo','-u',self.SudoUser,'-n','-s','--'] + self.Args
			self.P = subprocess.Popen(a, cwd=self.WorkDir, env=self.Environment, close_fds=True) # close_fds=True is mandatory for UNIXes, otherwise descriptors from SCGI are passed to launched childs (which leads to prolonged responses to clients)
		except OSError, e:
			L.error("%s launch failed due to following error: %s", self, e)
			self._Error(e)
			return False

		self.LaunchTime = time.time()
		self.Results[-1].Pid = self.P.pid
		self.__State = 'R'
		return True


	def _Exit(self):
		rc = self.P.poll()
		if rc is None: return None
		self.P = None

		self.Results[-1].RunningTime = time.time() - self.LaunchTime
		self.Results[-1].ReturnCode = rc
		return rc


	def _Schedule(self):
		assert(self.P is None)
		L.debug("Rescheduling %s", self)
		self.__State = 'S'


	def _Delete(self):
		assert(self.P is None)
		self.__State = 'D'


	def _Error(self, errdescr):
		assert(self.P is None)
		L.error('{0} is now in error state ({1})'.format(self, errdescr))
		self.__State = 'E'


	def _LaunchCondition(self):
		'Possible returns: R (runnable), E (error) or None (no change)'
		raise NotImplementedError("Pure virtual method '_LaunchCondition' called (missing implementation?) in {0}".format(self.__class__.__name__))


	def _ExitCondition(self):
		'Possible returns: S (schedule), D (delete) or E (error)'
		raise NotImplementedError("Pure virtual method '_ExitCondition' called (missing implementation?) in {0}".format(self.__class__.__name__))


	def _ErrorCondition(self):
		'Possible returns: S (schedule), D (delete) or None (no change)'
		raise NotImplementedError("Pure virtual method '_ErrorCondition' called (missing implementation?) in {0}".format(self.__class__.__name__))


	def ErrorRecovery(self, trgstate):
		raise NotImplementedError("Pure virtual method 'ErrorRecovery' called (missing implementation?) in {0}".format(self.__class__.__name__))


	def GetState(self):
		return self.__State

	State = property(GetState)

###

class ResidentSubprocess(_Process):

	def __init__(self, args, WorkDir=None, Environment=None, RescheduleDelay=1, SudoUser=None):
		_Process.__init__(self, args,
			WorkDir = WorkDir,
			Environment = Environment,
			SudoUser = SudoUser,
			)

		self.RescheduleDelay = RescheduleDelay
		self.ErrorRecoveryTrg = None
		self.TerminateRequested = False


	def Terminate(self):
		try:
			return _Process.Terminate(self)
		finally:
			self.TerminateRequested = True


	def _LaunchCondition(self):
		self.TerminateRequested = False
		return 'R'


	def _ExitCondition(self):
		# Fast-respawning protection
		if len(self.Results) > 5:
			s = sum(x.RunningTime for x in self.Results) / len(self.Results)
			if s < 5:
				L.error("{0} respawned to fast for resident subprocess - switching to error state".format(self))
				return 'E'

		if self.TerminateRequested:
			L.debug("{0} exited (requested) - will be scheduled for restart".format(self))
		else:
			L.warning("{0} exited - will be scheduled for restart".format(self))

		self.NoStateChangeTill = time.time() + self.RescheduleDelay
		
		return 'S'


	def _ErrorCondition(self):
		ret, self.ErrorRecoveryTrg = self.ErrorRecoveryTrg, None
		return ret


	def ErrorRecovery(self, trgstate):
		assert trgstate in ('D', 'S')
		self.ErrorRecoveryTrg = trgstate
		if trgstate == 'S':
			self.Results = []


###

class RepeatingSubprocess(_Process):

	def __init__(self, args, WorkDir=None, Environment=None, SudoUser=None):
		_Process.__init__(self, args,
			WorkDir = WorkDir,
			Environment = Environment,
			SudoUser = SudoUser,
			)

	#TODO:This ...

###

class OneShotSubprocess(_Process):

	def __init__(self, args, WorkDir=None, Environment=None, SudoUser=None):
		_Process.__init__(self, args,
			WorkDir = WorkDir,
			Environment = Environment,
			SudoUser = SudoUser,
			)


	def _LaunchCondition(self):
		return 'R'


	def _ExitCondition(self):
		return 'D'


	def _ErrorCondition(self):
		return 'D'

###
