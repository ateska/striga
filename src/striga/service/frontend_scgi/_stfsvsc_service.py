#Service SCGI_Frontend
import sys, urlparse, logging, errno, socket as SOCKET
import striga.core.context
import striga.core.exception
import striga.server.frontendservice
import striga.protocol._stpro_cgi as cgi
import striga.protocol._stpro_netstring as netstring

import _stfsvsc_error

###

L = logging.getLogger('SCGIFrontend')
L.setLevel(logging.NOTSET)

###

#TODO: Check against http://freshmeat.net/projects/pyscgi/ implementation
#TODO: We can generalize this to split this class to SCGI and CGI service
class SCGIService(striga.server.frontendservice.FrontendService):


	def __init__(self, parent, name = 'SCGIFrontend', startstoppriority = 2000):
		striga.server.frontendservice.FrontendService.__init__(self, parent, name, startstoppriority)
		self.BaseURL = None


	def _configure(self, conffilename, basepath = None, maxoutputbuffersize = 2 * 1024):
		#TODO: Basepath should be renamed to baseurl (but this will result in huge change in striga configuration)
		if basepath is not None:
			self.BaseURL = urlparse.urlsplit(basepath)
			
			#Sanity checks
			if (self.BaseURL.path[-1] != '/'):
				raise striga.core.exception.StrigaConfigurationError("Basepath URL '%s' must end with '/'!" % self.BaseURL.path)
			if (self.BaseURL.username is not None) or (self.BaseURL.password is not None) or (self.BaseURL.query != '') or (self.BaseURL.fragment != ''):
				raise striga.core.exception.StrigaConfigurationError("Invalid format of basepath URL '%s'! - (no usernames, no passwords, no query and fragment parts are allowed)" % basepath)

		self.ResponseMaxBufferSize = maxoutputbuffersize
		return striga.server.frontendservice.FrontendService._configure(self, conffilename)


	def _socketReady(self, socket):
		#! TIME CRITICAL !
		self.ThreadPool().ScheduleWorker(self.__handleSCGIRequest, socket)


	def __handleSCGIRequest(self, socket):
		#! TIME CRITICAL !
		context = None #Deleted at the end

		try:
			socket.settimeout(60)	# Timeout is set to 1 minute

			headers = netstring.ReadNetstring(socket)
			headers = headers.split('\x00')[:-1]
			if len(headers) % 2 != 0:
				raise striga.core.exception.StrigaProtocolError('Invalid SCGI headers')

			environ = {}
			for i in range(0, len(headers), 2):
				environ[headers[i]] = headers[i+1]

			clen = environ.get('CONTENT_LENGTH')
			if clen is None:
				raise striga.core.exception.StrigaProtocolError('SCGI headers miss CONTENT_LENGTH')
			try:
				clen = int(clen)
				if clen < 0:
					raise ValueError
			except ValueError:
				raise striga.core.exception.StrigaProtocolError('SCGI headers contains invalid CONTENT_LENGTH')

			#TODO: In SCGI environment only "PATH_INFO" and "QUERY_STRING" are the important ones ...
			#The only issue is when application is mounted on '/' (root) of web server tree:
			#
			#	Test URL: http://eiclocal/0path/1path/2path?a=1&b=2
			#	Apache mod_scgi:
			#		- Config: "SCGIMount / 127.0.0.1:4099"
			#		- PATH_INFO: '/0path/1path/2path'
			#		- SCRIPT_NAME: ''
			#		- QUERY_STRING: 'a=1&b=2'
			#		- SCRIPT_FILENAME: Not found
			#
			#	Apache mod_proxy_scgi:
			#		- Config: "ProxyPass / scgi://127.0.0.1:4099/"
			#		- PATH_INFO: /0path/1path/2path'
			#		- SCRIPT_NAME: ''
			#		- QUERY_STRING: 'a=1&b=2'
			#		- SCRIPT_FILENAME: 'proxy:scgi://127.0.0.1:4099/0path/1path/2path'
			#
			#	lighttpd :
			#		- Config: "scgi.server = ( "/" => ..."
			#		- PATH_INFO: '/1path/2path'
			#		- SCRIPT_NAME: '/0path'
			#		- QUERY_STRING: 'a=1&b=2'
			#		- SCRIPT_FILENAME: '/Users/.../.../.../0path'
			#		- !! Problem here is that we are effectivelly lose first part of path in PATH_INFO, using SCRIPT_NAME is then problematic when app is not on the '/' of web


			Path = environ.get('SCRIPT_FILENAME', None) #This is from lighttpd + scgi,
			if Path is None: Path = environ['SCRIPT_NAME'] #This from apache + scgi
			Path += environ['PATH_INFO']

			if self.BaseURL is not None:
				#Base path allows to strip path from Path start
				if (Path.find(self.BaseURL.path) != 0) and (Path != self.BaseURL.path[:-1]):
					raise striga.core.exception.StrigaProtocolError("Path '%s'does not start with base path '%s'." % (Path, self.BaseURL.path))
				Path = Path[len(self.BaseURL.path):]
				
				#TODO: We can also check BaseURL scheme and hostname

			context = striga.core.context.Context(
				Application = self.ApplicationRef(),
				Request = cgi.Request(
					Path = Path,
					Input = socket.makefile('r'),
					ContentLenght = clen,
					CGIEnv = environ
				),
				Response = cgi.Response(
					OutputSocket = socket,
					MaxBufferSize = self.ResponseMaxBufferSize
				),
				Frontend = self,
			)

			if self.SiteBusRef is None:
				raise striga.core.exception.StrigaRuntimeException("Frontend service '%s' is not connected to site bus" % self.ServiceName)

			sb = self.SiteBusRef()
			if sb is None:
				self.SiteBusRef = None
				raise striga.core.exception.StrigaRuntimeException("Frontend service '%s' is not connected to site bus (process bus died)" % self.ServiceName)

			context.req.Vars.AddVarSet('SITEBUS', dict())

		except:
			#TODO: Exception handling (report exceptions with-in worker to user)
			#Configurable - print just plain error message or exception stack
			#THIS IS HANDLER FOR EXCEPTIONS BEFORE SITE BUS ENTER

			L.exception("Exception during context preparation")

			try: _stfsvsc_error.SendErrorPage(socket, *sys.exc_info())
			except:	pass

			try: socket.close()
			except:	pass

			try: del context
			except: pass

			return

		try:
			Path = Path.strip('/').split('/')

			#Remove strange slashing
			try:
				while 1:
					Path.remove('')
			except ValueError:
				pass

			sb(context, Path)

		except striga.core.exception.StrigaNoContent:
			L.warning("SCGI frontend received striga.core.exception.StrigaNoContent exception from sitebus - this is probably not correct.")
			return

		except striga.core.exception._StrigaClientRedirectBase, e:
			# URL for redirection SHOULD BE given as absolute path (see section 14.30 in the HTTP specs),
			# if not there is 'local' redirection at scgi module for apache which will consume communication with browser
			e.UpdateResponse(context)
			context.Response.Flush()

		except SOCKET.error, e:
			if e.errno == errno.EPIPE:
				# Ignoring this error silently (upstream socket to SCGI client closed by peer)
				# Context is removed and socket is closed in finally section bellow
				return
			L.exception("Exception in site bus - ignoring:")

		except:
			#TODO: Exception handling (report exceptions with-in worker to user)
			#Configurable - print just plain error message or exception stack
			#THIS IS HANDLER FOR EXCEPTIONS FROM SITE BUS and its childs (views, execs, etc.)
			L.exception("Exception in site bus - ignoring:")

		finally:
			del context
			try:
				socket.close()
			except:
				pass
