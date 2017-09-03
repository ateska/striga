import threading, time, logging, errno
import glob, os, tempfile, weakref
import pickle

import striga.core.exception
import striga.server.application, striga.server.service

from . import _sesmansvc_session
from ._sesmansvc_sesmanmemory import MemorySessionManager

###

L = logging.getLogger('SesManFile')

###

class FileSessionManager(MemorySessionManager):
	''' !!!WARNING!!! This session manager SHOULD NEVER be used in the production use!
	It is not guearanteed to work in all cases, e.g. when storing complex objects to session.
	It contains a potention flaw, which could be misused by a potential attacker. The problem is that the session is not
	properly able to determine, whether it is "dirty" when some nested data in the Vars are changed. The mechanism used
	to determine the "dirtiness" of Vars data is "hash" of keys and values of the Vars dictionary, but because the hash function 
	can be used	only on the "hashable" objects, the result will not always reflect the reality and may claim something
	is "clean" although some data in Vars changed.
	
	This session manager is aimed to development use, where the developer can benefit from session persistency after striga
	server restart.
	''' 
	 

	# TODO: Consider using Tempfile and keeping filename: SIN map. This would ensure filename uniqueness, 
	# but searching for existing session in __LoadSessions()

	def __init__(self, parent, sesid, seslifetime, domain=None, pool=None, sessdir=None, sessprefix="strigasess_", sesswriteperiod=30, name = "SessionManager", startstoppriority = 100):
		MemorySessionManager.__init__(self, parent, sesid, seslifetime, domain=domain, pool=pool, name=name, startstoppriority=startstoppriority)
		self.SessionsDir = sessdir if sessdir is not None else tempfile.gettempdir()
		self.SessionsPrefix = sessprefix
		self.SessionWritePeriod = sesswriteperiod
		app = striga.server.application.GetInstance()
		if not isinstance(app, striga.compiler.compilerapp.CompilerApplication):
			app.ScheduleWorker(self.__LoadSessions)
		
		

	def __LoadSessions(self):
		for sessfile in glob.glob(self.__FormFilename("*")):
			try:
				session = pickle.load(open(sessfile, "rb"))
			except:
				L.warning("Session file {0} is invalid, ignoring it.".format(sessfile))
				try:
					os.unlink(sessfile)
				except:
					pass
				continue
			
			assert isinstance(session, _sesmansvc_session.Session)
			session.SessionManagerRef = weakref.ref(self)
			self.Sessions[session.SIN] = session
			L.info("Loaded session {0} from file {1}".format(session.SIN, sessfile))
	
	def __FormFilename(self, postfix):
		return os.path.join(self.SessionsDir, self.SessionsPrefix + postfix)
	
	def _DeleteSession(self, sin):
		ses = MemorySessionManager._DeleteSession(self, sin)
		if ses is not None:
			filename = self.__FormFilename(ses.SIN)
			L.info("Removing session file {0}".format(filename))
			try:
				os.unlink(filename)
			except OSError, e:
				if e.errno != errno.ENOENT:
					raise
		return ses
	

	def __StoreSessionToFile(self, ses):
		with os.fdopen(os.open(self.__FormFilename(ses.SIN), (os.O_WRONLY | os.O_CREAT), 0600), "wb") as f:
			pickle.dump(ses, f, pickle.HIGHEST_PROTOCOL)
		ses.SetDirty(False)

	
	def __StoreSessions(self, force = False):
		'''Store sessions to filesystem
		@param force: If False (default), only dirty session are stored to filesystem, if True, 
			all sessions including the potentionally clean sessions are stored to session.
		This method should be called with force=True at striga shutdown to ensure all sessions are properly stored
		to filesystem. This is because the IsDirty() method on the session method can work inproperly, due to
		the characteristics of hash function used to determine dirtyness of Sessions.Vars dictionary.
		'''
		for sin, ses in self.Sessions.items():
			if force or ses.IsDirty():
				L.info("Storing session {0} to file{1}".format(sin, " (forced)" if force else ""))
				self.__StoreSessionToFile(ses)


	def _DoStart(self):
		MemorySessionManager._DoStart(self)
		app = striga.server.application.GetInstance()
		app.Scheduler.AddJob(striga.server.scheduler.PeriodicJob(self.SessionWritePeriod, self.__StoreSessions))


	def _DoStop(self):
		MemorySessionManager._DoStop(self)
		# Store all session when shutting down (stoping service)
		self.__StoreSessions(True)
		app = striga.server.application.GetInstance()
		app.Scheduler.RemoveAllJobsFor(self.__StoreSessions)
