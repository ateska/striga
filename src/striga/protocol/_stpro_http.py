# HTTP protocol
import re, mimetools, cgi, select, cStringIO, tempfile, logging as L
from httplib import responses as StatusCodeMap

import striga.core.exception, striga.core.context
from striga.core.variables import MultiDict
from ._stpro_httpcookie import CookieJar
###

#TODO: Based on security settings send only partial information (no version)
StrigaVersion = 'Striga Server %s' % striga.Version

###

class StatusCode(object):

	# informational
	Continue = 100
	SwitchingProtocols = 101
	Processing = 102

	# successful
	OK = 200
	Created = 201
	Accepted = 202
	NonAuthoritativeInformation = 203
	NoContent = 204
	ResetContent = 205
	PartialContent = 206
	MultiStatus = 207

	# redirection
	MultipleChoices = 300
	MovedPermanently = 301
	Found = 302
	SeeOther = 303
	NotModified = 304
	UseProxy = 305
	TemporaryRedirect = 307

	# client error
	BadRequest = 400
	Unauthorized = 401
	PaymentRequired = 402
	Forbidden = 403
	NotFound = 404
	MethodNotAllowed = 405
	NotAcceptable = 406
	ProxyAuthenticationRequired = 407
	RequestTimeout = 408
	Conflict = 409
	Gone = 410
	LenghtRequired = 411
	PreconditionFailed = 412
	RequestEntityTooLarge = 413
	RequestURITooLong = 414
	UnsupportedMediaType = 415
	RequestedRangeNotSatisfiable = 416
	ExpectationFailed = 417
	UnprocessableEntity = 422
	Locked = 423
	FailedDependency = 424
	UpgradeRequired = 426

	# server error
	InternalServerError = 500
	NotImplemented = 501
	BadGateway = 502
	ServiceUnavailable = 503
	GatewayTimeout = 504
	HTTPVersionNotSupported = 505
	InsufficientStorage = 507
	NotExtended = 510


###

class Request(striga.core.context.Request):
	#TODO: Move all _XX method outside of the class (prevent unnecessary pollution of Request dictionary)


	def __init__(self, Path, RemoteAddress, Method, Input, ContentLenght, ContentType = None):
		striga.core.context.Request.__init__(self, Path, RemoteAddress)
		self.Method = Method
		self.Input = Input
		self.ContentLength = int(ContentLenght)
		if ContentType is not None:
			self.ContentType = cgi.parse_header(ContentType)
		else:
			self.ContentType = None

		self.CookieJar = CookieJar()

		self.Vars.AddVarSet('GET', MultiDict())
		self.Vars.AddVarSet('POST', MultiDict())
		if self.Method == 'POST': ReadPOSTdata(self)


###
# HTTP Request support functions ...

def ReadPOSTdata(req):
	if req.ContentType[0] == 'application/x-www-form-urlencoded':
		respdata = req.Input.read(req.ContentLength)
		req.Vars.POST.Update(cgi.parse_qs(respdata, keep_blank_values=True))
	elif req.ContentType[0] == 'multipart/form-data':
		ParseMultipart(req)
	else:
		raise striga.core.exception.StrigaRuntimeException("Cannot handle content type '%s'!" % req.ContentType[0])

	# some browsers send 2 more bytes...
	[ready_to_read,_,_] = select.select([req.Input],[],[],0)
	if ready_to_read:
		req.Input.read(2)

#

def ParseMultipart(req, maxlen = 1024*1024*32):

	boundary = req.ContentType[1]['boundary']
	if not ValidBoundaryRE.match(boundary):
		raise ValueError('Invalid boundary in multipart form: %r' % (boundary))

	nextpart = "--" + boundary
	lastpart = "--" + boundary + "--"

	#Read till next boundary
	while 1:
		line = req.Input.readline().strip()
		if line == lastpart: return
		if line == nextpart: break
		L.warning("Trashing HTTP POST data line '%s'" % line)

	rlen = 0
	while 1:
		#Read header
		headers = mimetools.Message(req.Input)
		contdis = headers.getheader('content-disposition')
		if contdis is not None:
			contdiskey, contdisparams = cgi.parse_header(contdis)
			if 'filename' in contdisparams:
				datamf = MultipartFile(contdisparams['filename'],headers.getheader('content-type'))
				data = datamf.GetFile()
			else:
				data = cStringIO.StringIO()
				datamf = None
		else:
			contdiskey = None
			contdisparams = None
			data = DevNullFile()
			datamf = None

		clength = headers.getheader('content-length')
		if clength is not None:
			raise NotImplementedError("Content-Length in multipart data is not yet supported - send me a test case!")

		#Read data
		lines = []
		while 1:
			line = req.Input.readline()
			if not line:
				L.warning("POST multiform data feed ended prematurely")
				data.close()
				return
			rlen += len(line)
			if rlen > maxlen:
				raise striga.core.exception.StrigaRuntimeException("HTTP POST multipart is too long")

			if line[:2] == "--":
				rline = line.strip()
				if rline in (nextpart, lastpart):
					if len(lines) > 0:
						#Strip final line terminator
						line = lines[-1]
						if line[-2:] == "\r\n":
							line = line[:-2]
						elif line[-1:] == "\n":
							line = line[:-1]
						lines[-1] = line
						#And flush buffer into a file
						while len(lines) > 0:
							data.write(lines.pop(0))
					break

			lines.append(line)
			while len(lines) > 1:
				data.write(lines.pop(0))

		if contdiskey != 'form-data':
			L.warning("Received POST multiform data with unknown part '%s'", contdiskey)
			data.close()

		if 'name' in contdisparams:
			name = contdisparams['name']
		else:
			L.warning("Received POST multiform data without field name")
			data.close()

		if isinstance(data, DevNullFile):
			pass
		elif isinstance(datamf, MultipartFile):
			#File parameter
			req.Vars.POST.Add(name, datamf)
			datamf.RewindFile()
		else:
			#Plain parameter
			req.Vars.POST.Add(name, data.getvalue())
			data.close()

		if rline == lastpart: return

#

ValidBoundaryRE = re.compile("^[ -~]{0,200}[!-~]$")

###

class MultipartFile(object):


	def __init__(self, remotefilename, contenttype):
		self.RemoteFilename = remotefilename
		self.ContentType = contenttype
		self.__inputfile = tempfile.TemporaryFile()


	def GetFile(self):
		return self.__inputfile

	def RewindFile(self):
		self.__inputfile.seek(0,0)

###

class DevNullFile(object):

	def write(self, data): pass
	def close(self): pass

###

class Response(striga.core.context.BufferedSocketResponseWithHeader):

	StatusCodeMap = StatusCodeMap.copy()
	StatusCodeMap[207] = 'Multi-Status' #Adding for WebDav

	StatusCode = StatusCode

	def __init__(self, OutputSocket, MaxBufferSize, **kwargs):
		striga.core.context.BufferedSocketResponseWithHeader.__init__(self, OutputSocket, MaxBufferSize, contenttype='text/plain', **kwargs)

		self.Status = self.StatusCode.OK # From RFC3875: "200" | "302" | "400" | "501" | extension-code
		self.ContentLength = None #Unknown by default (when None is set, chunked transfer is used) 
		self.CustomHTTPHeader = HTTPHeader()
		self.CookieJar = CookieJar()


	def SetStatusCode(self, statuscode):
		if not self.StatusCodeMap.has_key(statuscode):
			L.warning("Invalid/unknown status code '%s' given!" % str(statuscode))
		self.Status = statuscode


	def SetContentLength(self, length):
		if length is None:
			self.ContentLength = None
		else:
			self.ContentLength = int(length)


	def SetCacheAge(self, age):
		'''
		@param age: Number of seconds defining how long to store result in the cache. None for indefinite caching, negative or zero means prevent caching
		'''
		if age is None:
			self.CustomHTTPHeader.Set('Cache-Control', 'store, cache')
			self.CustomHTTPHeader.Remove('Pragma', 'no-cache')
		elif age <= 0:
			self.CustomHTTPHeader.Set('Cache-Control', 'no-store, no-cache, must-revalidate')
			self.CustomHTTPHeader.Add('Pragma', 'no-cache')
		else:
			self.CustomHTTPHeader.Set('Cache-Control', 'store, cache, max-age=%d' % age)
			self.CustomHTTPHeader.Remove('Pragma', 'no-cache')


	def _GenerateHeader(self):
		#TODO: This is actually CGI header
		header = [
			'Status: %d %s' % (self.Status, self.StatusCodeMap[self.Status]),
				]

		if self.ContentType is not None:
			header.append('Content-Type: ' + self.ContentType,)

		if self.ContentLength is not None:
			header.append('Content-Length: %d' % self.ContentLength)

		header.extend(self.CustomHTTPHeader.GenerateHTTPHeader())

		co = self.CookieJar.HTTPOutput()
		if len(co) > 0: header.append(co)

		return '\r\n'.join(header) + '\r\n\r\n'


	def _LockHeaders(self):
		self.CustomHTTPHeader.Lock()

###

class HTTPHeader(object):

	ForbidenItems = frozenset(['Status','Content-Type','Content-Length']) # 'Set-Cookie',

	def __init__(self, initload = []):
		self.__locked = False
		self.__mdict = MultiDict(initload)
		self.Set('X-Powered-By', StrigaVersion)


	def Lock(self):
		self.__locked = True


	def __len__(self):
		return len(self.__mdict)


	def __getitem__( self, key):
		return self.Get(key)


	def __setitem__( self, key, value):
		return self.Set(self, key, value)


	def __delitem__( self, key):
		return self.RemoveAll(key)


	def Set(self, key, value, **params):
		self.__mdict.Set(key, self.__prepareParam(key, value, **params))


	def Add(self, key, value, **params):
		self.__mdict.Add(key, self.__prepareParam(key, value, **params))


	def Get(self, key, index = 0, *values):
		return self.__mdict.Get(key, index, *values)


	def GetAll(self, key, *values):
		return self.__mdict.GetAll(key, *values)


	def RemoveAll(self, key):
		if self.__locked:
			raise striga.core.exception.StrigaRuntimeException("Headers are locked (probably already sent to client)!")

		try:
			del self.__mdict[key]
		except KeyError:
			pass


	def Remove(self, key, item):
		if self.__locked:
			raise striga.core.exception.StrigaRuntimeException("Headers are locked (probably already sent to client)!")


		self.__mdict.Remove(key, item)


	def GenerateHTTPHeader(self):
		return ["%s: %s" % (k, v) for k, v in self.__mdict.iteritems()]


	def __prepareParam(self, key, value, **params):
		if self.__locked:
			raise striga.core.exception.StrigaRuntimeException("Headers are locked (probably already sent to client)!")
		if key in self.ForbidenItems:
			raise striga.core.exception.StrigaRuntimeException("Cannot set '%s' as this value is forbidden to manipulate in HTTP header!" % key)

		if len(params) == 0:
			return value

		parts = []
		for k, v in params.items():
			if v is None: parts.append(k.replace('_', '-'))
			else: parts.append(self.__formatparam(k.replace('_', '-'), v))

		return value + '; ' + '; '.join(parts)


	_tspecials = re.compile(r'[ \(\)<>@,;:\\"/\[\]\?=]')

	@classmethod
	def __formatparam(cls, param, value=None, quote=1):
		"""Convenience function to format and return a key=value pair.
		This will quote the value if needed or if quote is true.
		"""
		if value is not None and len(value) > 0:
			if quote or cls._tspecials.search(value):
				value = value.replace('\\', '\\\\').replace('"', r'\"')
				return '%s="%s"' % (param, value)
			else:
				return '%s=%s' % (param, value)
		else:
			return param
