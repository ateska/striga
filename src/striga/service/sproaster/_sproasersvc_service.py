import os, time, logging
import striga.server.service
import striga.server.application

from ._sproasersvc_process import OneShotSubprocess, ResidentSubprocess, RepeatingSubprocess

###
'''
Subprocess roaster service
--------------------------

This service allows you to launch subprocesses from Striga environment.
Service is taking care about subprocess life-cycle including post-mortem cleanup.

There are three kind of subprocesses that can be manages by this service:

* OneShotSubprocess
This subprocess will be launched, monitored and after its exits Striga will collect subprocess return code.

* ResidentSubprocess 
This subprocess represent permanently-running task. It has also fast-respawn protection mechanism built-in.

* RepeatingSubprocess
(not implemented yet)

It is possible to schedule launch of subprocess in the roaster declaratively from Striga server configuration or imperatively from Striga code (by function call).
'''
###

L = logging.getLogger('sproaster')

###

class SubprocessRoasterServiceFactory(striga.server.service.ServiceFactory):

	def __init__(self, parent, name = 'SubprocessRoasterServiceFactory', startstoppriority = 50):
		striga.server.service.ServiceFactory.__init__(self, SubprocessRoasterService, 'SubprocessRoaster', 'subprocessroaster', parent, name, startstoppriority)

###

class SubprocessRoasterService(striga.server.service.Service):

	#TODO: Allow kill/restart processes in the roaster from within striga application

	def __init__(self, parent, name, startstoppriority = 100):
		if name is None: name = "SubprocessRoasterService"
		striga.server.service.Service.__init__(self, parent, name, startstoppriority)

		#TODO: Allow to configure following item
		self.__conf_Interval = 0 # Go as fast as possible (ehm 2 secs is minimum)
		
		self.__Roaster = dict()

		self.__Environment = os.environ.copy()


	def _configure(self, conffilename):
		return {
			'oneshotsubprocess' : self.__configure_oneshotsubprocess,
			'repeatingsubprocess' : self.__configure_repeatingsubprocess,
			'residentsubprocess' : self.__configure_residentsubprocess,

			'setenv' : self.__configure_setenv,

			'!' : self._configure_finished,
		}


	def __configure_oneshotsubprocess(self, conffilename, cmdline, workdir=None, sudouser=None):
		p = OneShotSubprocess(
				args = ExpandVars(cmdline),
				WorkDir = workdir,
				Environment = self.__Environment,
				SudoUser = sudouser,
				)
		self.Register(p)


	def __configure_repeatingsubprocess(self, conffilename, cmdline, workdir=None, sudouser=None):
		#TODO: Correct arguments
		p = RepeatingSubprocess(
				args = ExpandVars(cmdline),
				WorkDir = workdir,
				Environment = self.__Environment,
				SudoUser = sudouser,
				)
		self.Register(p)


	def __configure_residentsubprocess(self, conffilename, cmdline, workdir=None, rescheduledelay = 1, sudouser=None):
		p = ResidentSubprocess(
				args = ExpandVars(cmdline),
				WorkDir = workdir,
				Environment = self.__Environment,
				RescheduleDelay = int(rescheduledelay),
				SudoUser = sudouser,
				)
		self.Register(p)


	def __configure_setenv(self, conffilename, name, value):
		self.__Environment[name] = value


	def _configure_finished(self):
		self._ChangeServiceStateToConfigured()


	def _DoStart(self):
		app = striga.server.application.GetInstance()
		app.Scheduler.AddJob(striga.server.scheduler.PeriodicJob(self.__conf_Interval, self.__Tick))


	def _DoStop(self):
		app = striga.server.application.GetInstance()
		app.Scheduler.RemoveAllJobsFor(self.__Tick)

		# TODO: Terminate all running processes in roaster and delete them


	def Register(self, process):
		'Introduces process into roaster - process object is copied (you can register the same object several times)'
		L.debug("Registering %s", process)

		processclone = process.Clone(True)
		assert not self.__Roaster.has_key(processclone.UID)
		self.__Roaster[processclone.UID] = processclone

		if self.ServiceState > self.States.Configured:
			self.__CheckProcessState(processclone, time.time())


	def __CheckProcessState(self, p, curtime):
		for _ in range(5):
			retst = p._CheckProcessState(curtime)
			if retst: return	
			if retst is None: 
				self.__Roaster.pop(p.UID)
				return
		

	def __Tick(self):
		curtime = time.time()
		for p in self.__Roaster.values():
			self.__CheckProcessState(p, curtime)


	def __iter__(self):
		# Return frozen copy of the roaster values ...
		return iter(self.__Roaster.values())


	def Terminate(self, uid):
		'''
This function propagates subprocess.terminate() call to relevant subprocess in the roaster.

Calling Terminate() on ResidentSubprocess will cause restart of particular subprocess (resident subprocess tends to stale in running condition).
Also subprocess roaster evaluates exit of subprocess running longer than 5 seconds and inducted by SIGTERM or SIGINT as non-error exit.
		'''
		sp = self.__Roaster.get(uid)
		if sp is None: raise KeyError("Subprocess '{0}' not found".format(uid))

		sp.Terminate()


	def ErrorRecovery(self, uid, trgstate):
		'''
This function enables user to resolve stalled error state (e.g. resident subprocess entry in 'E') state.

Currently works only for resident subprocesses (trgstate -> D or S).
		'''
		sp = self.__Roaster.get(uid)
		if sp is None: raise KeyError("Subprocess '{0}' not found".format(uid))

		sp.ErrorRecovery(trgstate)

###

def ExpandVars(cmdline):
	if cmdline.find('{') > 0:
		app = striga.server.application.GetInstance()
		return cmdline.format(**app.ConfigDictionary)
	return cmdline
