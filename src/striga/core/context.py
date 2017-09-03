import cStringIO, logging.handlers, itertools, socket, errno, time, logging as L
import striga.core.variables

###

class Context(object):
	'''
Major Striga class - each request is handled by it's own context object (instance of this class)

Attributes:
	app (Application)
	req (Request)
	res (Response)
	fre (Frontend)
	svv (Server variables) * class variable

	Stack (Stack variable)
	UniqueNumberGenerator (Simple sequence generator)

	err (Errors)

	ctime - Context create time
	'''

	svv = dict()
	Counter = 0

	def __init__(self, Application, Request, Response, Frontend):
		Context.Counter += 1
		self.app = Application
		self.req = Request
		self.res = Response
		self.fre = Frontend
		self.err = Error()
		
		self.stime = time.time()

		self.log = Logger("ContextLogger%d" % Context.Counter)
		self.LogBuffer = logging.handlers.MemoryHandler(100)
		self.log.addHandler(self.LogBuffer)

		self.Application = self.app
		self.Request = self.req
		self.Response = self.res
		self.Frontend = self.fre

		self.Stack = striga.core.variables.StackDict()
		self.UniqueNumberGenerator = itertools.count(1)

###

class Request(object):
	'''
Attributes:
	Path
	RemoteAddress
	Vars (Request variables: POST, GET, HEADER, SITEBUS)

	Method [HTTP only] (POST, GET etc.)
	Input [HTTP only] - input stream from client
	ContentLength [HTTP only] - lenght of data sent from client
	ContentType [HTTP only] - Content type of data sent from client

	CGIEnv [CGI only] - CGI environment dictionary\
	CookieJar [HTTP only]
	'''

	def __init__(self, Path, RemoteAddress):
		self.Path = Path
		self.RemoteAddress = RemoteAddress
		self.Vars = striga.core.variables.SetVariables()

###

class Response(object):
	'''
Method:
	Write - Write an output data for client
	WriteFile - Write an data from file object for client
	Flush - Ensure that data are sent to client
	SetBufferSize - Set size of output buffer (only in Buffered*Request)
	SetContentType - self-explanatory (HTTP only)

Attributes:
	MaxBufferSize - Size of output buffer (read-only) (only in Buffered*Request)
	HeaderSent - Boolean; has header been sent to client already? (read-only)
	Status - Status like 200, 404 etc. (HTTP only)
	ContentType - self-explanatory (HTTP only)
	ContentLength - self-explanatory, can be None (HTTP only)
	CustomHTTPHeader - dictionary to define custom header items in (HTTP only)
	'''


	def __init__(self, contenttype='text/plain', **kwargs):
		self.__dict__.update(kwargs)
		self.ContentType = contenttype


	def __del__(self):
		try:
			self.Flush()
		except:
			pass


	def Write(self, data):
		'''
Overriden by particular response implementation
		'''
		raise NotImplementedError("Write method called on virtual class LoadableBase")


	def WriteFile(self, inpfile):
		'''
Overriden by particular response implementation
		'''
		raise NotImplementedError("WriteFile method called on virtual class LoadableBase")


	def Flush(self):
		'''
Overriden by particular response implementation
		'''
		raise NotImplementedError("Flush method called on virtual class LoadableBase")


	def SetContentType(self, contenttype, charset=None):
		if contenttype is None:
			self.ContentType = None
		else:
			if charset is None:
				self.ContentType = str(contenttype)
				if self.ContentType == 'text/html':
					self.ContentType = 'text/html; charset=utf-8'
			else:
				self.ContentType = str(contenttype) + '; charset=' + str(charset)

###

class BufferedSocketResponseWithHeader(Response):


	def __init__(self, OutputSocket, MaxBufferSize = 2 * 1024, **kwargs):
		striga.core.context.Response.__init__(self, **kwargs)
		self.__OutputBuffer = cStringIO.StringIO()
		self.__OutputSocket = OutputSocket
		self.__MaxBufferSize = MaxBufferSize
		self.__HeaderSent = False


	def Write(self, data):
		if self.__MaxBufferSize == 0:
			self.__DoWrite(data)
		else:
			self.__OutputBuffer.write(data)
			if self.__OutputBuffer.tell() > self.__MaxBufferSize:
				self.__FlushBuffer()


	def WriteFile(self, inpfile):
		self.Flush()
		bufsize = self.__MaxBufferSize if (self.__MaxBufferSize > 0) else 1024
		while 1:
			buf = inpfile.read(bufsize)
			if len(buf) == 0:
				break
			self.__DoWrite(buf)


	def Flush(self):
		if not self.__HeaderSent: self.__DoWriteHeaders()
		if (self.__MaxBufferSize > 0) and (self.__OutputBuffer.tell() > 0):
			self.__FlushBuffer()


	def SetBufferSize(self, newsize):
		self.__MaxBufferSize = newsize
		if newsize == 0:
			self.Flush()
		else:
			self.Write('')


	def __FlushBuffer(self):
		self.__DoWrite(self.__OutputBuffer.getvalue())
		self.__OutputBuffer.truncate(0)


	def __DoWriteHeaders(self):
		genheaders = self._GenerateHeader()
		self.__OutputSocket.sendall(genheaders)
		self._LockHeaders()
		self.__HeaderSent = True


	def __DoWrite(self, data):
		if not self.__HeaderSent: self.__DoWriteHeaders()

		# Following is equivalent to "self.__OutputSocket.sendall(data)" but it can handle EAGAIN error condition
		failsafecnt = 0
		while len(data):

			failsafecnt += 1
			if failsafecnt == 20: raise RuntimeError("Exceeded number of retries when sending data to client")

			try:
				sentsize = self.__OutputSocket.send(data)
				failsafecnt = 0 # Restart fail-safe counter
			except socket.error, e:
				if e.args[0] == errno.EAGAIN:
					time.sleep(0.01) # Be gentle with retry
					continue
				
				if e.args[0] == errno.ECONNRESET:
					# Silently ignore "Connection reset by peer" condition and finalize page output
					failsafecnt = 0 # Restart fail-safe counter
					continue
				
				raise

			data = data[sentsize:]


	def _GenerateHeader(self):
		'''
Override by particular response implementation
Return data (string) to be sent to client as header
		'''
		raise NotImplementedError("_GenerateHeader method called on virtual class LoadableBase")


	def _LockHeaders(self):
		'''
Override by particular response implementation
Prevent headers from being written
		'''
		raise NotImplementedError("_LockHeaders method called on virtual class LoadableBase")

###

class Error(object):

	def __init__(self):
		self.exctype = None
		self.excvalue = None

###

#TODO: Replace by simplier logger not depending on logging module (too heavy for this ...)
class Logger(L.Logger):

	def __init__(self, name):
		L.Logger.__init__(self, name)

