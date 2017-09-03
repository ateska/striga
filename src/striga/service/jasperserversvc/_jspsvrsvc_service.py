import striga.server.application, striga.server.service, striga.core.exception, logging as L
import urllib2, cgi, cStringIO, xml.sax.saxutils, os, tempfile, shutil, time

###

RequestParamString = \
'''<parameter name="%s">%s</parameter>'''

#

RequestXMLString = \
'''
<request operationName="runReport" locale="en">
	<argument name="RUN_OUTPUT_FORMAT">%s</argument>
	<resourceDescriptor name="" wsType="" uriString="%s" isNew="false">
		<label>null</label>
		%s
	</resourceDescriptor>
</request>
'''

#

RequestBody = \
'''<SOAP-ENV:Envelope xmlns:SOAP-ENC="http://schemas.xmlsoap.org/soap/encoding/" xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" xmlns:ZSI="http://www.zolera.com/schemas/ZSI/" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" SOAP-ENV:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
<SOAP-ENV:Header></SOAP-ENV:Header>
<SOAP-ENV:Body xmlns:ns1="http://axis2.ws.jasperserver.jaspersoft.com">
<ns1:runReport>
<requestXmlString>
%s
</requestXmlString></ns1:runReport>
</SOAP-ENV:Body>
</SOAP-ENV:Envelope>'''

###

class JasperServerServiceFactory(striga.server.service.ServiceFactory):


	def __init__(self, parent, name = 'JasperServerFactory', startstoppriority = 50):
		striga.server.service.ServiceFactory.__init__(self, JasperServerService, 'JasperServer', 'jasperserver', parent, name, startstoppriority)

###

class JasperServerService(striga.server.service.Service):


	def __init__(self, parent, name = 'JasperServer', startstoppriority = 50):
		striga.server.service.Service.__init__(self, parent, name, startstoppriority)
		self.Connection = None
		self.Workers = {}

		self.TmpDir = os.path.join(tempfile.gettempdir(), 'custlist-reps')


	def _DoStart(self):
		if os.path.exists(self.TmpDir):
			shutil.rmtree(self.TmpDir)
		os.makedirs(self.TmpDir)


	def _DoStop(self):
		if os.path.exists(self.TmpDir):
			shutil.rmtree(self.TmpDir)


	def _configure(self, conffilename, uri, user=None, password=None):
		self.URI = uri

		handlers = []

		# Create an OpenerDirector with support for Basic HTTP Authentication...
		if (user is not None) and (password is not None):
			auth_handler = urllib2.HTTPBasicAuthHandler()
			auth_handler.add_password(realm='Protected Area', uri=uri, user=user, passwd=password)
			handlers.append(auth_handler)

		self.Opener = urllib2.build_opener(*handlers)

		self._ChangeServiceStateToConfigured()


	def LaunchReport(self, reportpath, SOAPAction, format='PDF', prefix='', **kwargs):

		params = ''
		for key, value in kwargs.iteritems():
			params += RequestParamString % (key, str(value))

		rxmlstr = RequestXMLString % (format, reportpath, params)

		req = urllib2.Request(self.URI, data=(RequestBody % xml.sax.saxutils.escape(rxmlstr)))
		req.add_header('SOAPAction',SOAPAction)

		njrw = JasperReportWorker(self.Opener, req, prefix, self.TmpDir, self)
		self.Workers[njrw.ID] = njrw

		app = striga.server.application.GetInstance()
		app.ScheduleWorker(njrw)

		L.info("Report worker '%s' created ...", njrw.ID)

		return njrw.ID


	def ReportReady(self, jrw):
		del self.Workers[jrw.ID]


	def GetResult(self, jrwid):
		while self.Workers.has_key(jrwid):
			time.sleep(1)

		RepPath = os.path.join(self.TmpDir, jrwid)

		if not os.path.isfile(RepPath):
			raise striga.core.exception.StrigaBusError("NotFound")

		return os.path.getsize(RepPath), file(RepPath,'rb')

###

class JasperReportWorker(object):


	def __init__(self, opener, request, prefix, tmpdir, service):
		self.Opener = opener
		self.Request = request
		self.TmpDir = tmpdir
		self.ID = prefix + '-' + str(id(self))
		self.ResultFileName = os.path.join(self.TmpDir, self.ID)
		self.Service = service


	def __call__(self):
		try:
			r = self.Opener.open(self.Request)

			ContentType = cgi.parse_header(r.headers['Content-Type'])

			if ContentType[0] == 'text/xml':
				print r.read()
				raise RuntimeError('Invalid format')

			CStart = ContentType[1]['start']
			CBoundary = ContentType[1]['boundary']

			#Read till header
			while 1:
				line = r.readline()
				if line.find(CBoundary) != -1: break

			Cont = True
			Output = file(self.ResultFileName,'wb')

			while Cont:

				#Read header
				headers = {}
				while 1:
					line = r.readline()
					if line.strip() == "": break
					key, value = line.split(": ", 1)
					headers[key] = cgi.parse_header(value)

				captureoutput = headers['Content-Type'][0] == 'application/pdf'

				#Read body
				buffer = []
				while 1:
					buffer.append(r.read(1))
					if len(buffer) > len(CBoundary) + 3:
						b = buffer.pop(0)
						if captureoutput:
							Output.write(b)

					if (buffer[0] == '\n') and (buffer[1] == '-') and (buffer[2] == '-'):
						if ''.join(buffer).find(CBoundary) == 3:
							line = r.readline()
							if (line == '\r\n'):
								Cont = True
								break
							if (line == '--\r\n'):
								Cont = False
								break
							raise RuntimeError('Invalid input from web service')

			Output.close()
		finally:
			self.Service.ReportReady(self)
