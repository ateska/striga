import striga.server.application, striga.server.service
import striga.service.sitebus

import logging as L

###

#TODO: Add 'enhanced' attributes to sessionhandler (secure cookie, path ...)

class SessionManagerService(striga.server.service.Service):


	def __init__(self, parent, name, startstoppriority = 100):
		if name is None: name = "SessionManagerService"
		striga.server.service.Service.__init__(self, parent, name, startstoppriority)
		self.SessionPools = {}


	def Configure(self):
		return {
			'!' : self.__configure_finished,
		}


	def __configure_finished(self):
		striga.service.sitebus.Bus.CustomSiteBusDefs.update({
			'sessionhandler' : self.__pbconfigure_sessionhandler,
		})
		self._ChangeServiceStateToConfigured()


	def __pbconfigure_sessionhandler(self, bus, conffilename, sesid='STRIGASIN', lifetime=15*60, domain=None, pool=None, type="memory", \
									sessdir=None, sessprefix="strigasess_", sesswriteperiod=30):
		'''
		@param sesid: String to be used as cookie name for session identificator
		@param lifetime: Integer (in seconds) expressing longevity of the session
		@param param: Optional string argument specifying DNS domain of the session cookie
		@param pool: Optional string argument that specify session pool used by given handers (sessions pools can be shared across different session handlers)
		@param type: Session manager type, [memory|file]
		@param sessdir: Directory where the session files are stored
		@param sessprefix: Prefix for the session files
		@param sesswriteperiod: Time period in seconds between write of session data to disk


		Two (or more) site buses are sharing sessions:

sitebus(name="sitebus-1", rootdir='root1', index='&'):
	sessionhandler(sesid="SIN", lifetime=1200, domain=".foo.com", pool="foo.com")
	...

sitebus(name="sitebus-2", rootdir='root2', index='&'):
	sessionhandler(sesid="SIN", lifetime=1200, domain=".foo.com", pool="foo.com")
	...

		''' 
		if type == 'file':
			from ._sesmansvc_sesmanfile import FileSessionManager
			bus.IntroBusItems.append(FileSessionManager(self, sesid, int(lifetime), domain=domain, pool=pool, sessdir=sessdir, sessprefix=sessprefix, sesswriteperiod=sesswriteperiod))
		elif type =='oneoff':
			from ._sesmansvc_sesmanoneoff import OneOffSessionManager
			bus.IntroBusItems.append(OneOffSessionManager(self))
		else:
			if type != "memory":
				L.warning("Uknown session manager type '{0}', falling back to 'memory'".format(type))
			from ._sesmansvc_sesmanfile import MemorySessionManager
			bus.IntroBusItems.append(MemorySessionManager(self, sesid, int(lifetime), domain=domain, pool=pool))
