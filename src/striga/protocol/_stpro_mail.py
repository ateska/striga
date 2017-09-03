import re, cStringIO, logging
import striga.core.context

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

try:
	import html2text
except:
	html2text = None

###

#TODO: Based on security settings send only partial information (no version)
StrigaVersion = 'Striga Server %s' % striga.Version

###

L = logging.getLogger('mail.context')

###

class Request(striga.core.context.Request):

	
	def __init__(self, Path, RemoteAddress):
		striga.core.context.Request.__init__(self, Path, RemoteAddress)
		

###

class Response(striga.core.context.Response):


	def __init__(self):
		striga.core.context.Response.__init__(self, contexttype='text/plain')
		
		self.Subject = None
		self.From = None
		self.To = []
		self.CC = []
		self.BCC = []
		self.ReplyTo = None
		self.Attachments = []

		self.__OutputBuffer = cStringIO.StringIO() 


	def SetCacheAge(self, age):
		#TODO: Generalize this ...
		pass


	def Write(self, data):
		self.__OutputBuffer.write(data)


	def WriteFile(self, inpfile):
		bufsize = 32*1024 
		while 1:
			data = inpfile.read(bufsize)
			if len(data) == 0:
				break
			self.__OutputBuffer.write(data)


	def Flush(self):
		pass


	def AddAttachment(self, mimeobj, filename):
		mimeobj.add_header('Content-Disposition', 'attachment', filename=filename)
		self.Attachments.append(mimeobj)


	def AddContent(self, mimeobj, contentid):
		mimeobj.add_header('Content-ID', "<"+contentid+">")
		self.Attachments.append(mimeobj)

	ContentTypeRG = re.compile('[a-zA-Z0-9]+/[a-zA-Z0-9]+') 

	def GetMessage(self):

		assert self.Subject is not None, "You need to set ctx.res.Subject for mail"
		assert self.From is not None, "You need to set ctx.res.From for mail"

		ct = self.ContentTypeRG.findall(self.ContentType)[0]

		msg = MIMEMultipart('related', charset='utf-8')
		msg.preamble = 'This is a multi-part message in MIME format.'
		msg['X-Powered-By'] = StrigaVersion
		msg['Subject'] = self.Subject
		msg['From'] = self.From
		msg['To'] = ', '.join(self.To)
		if len(self.CC) > 0: msg['CC'] = ', '.join(self.CC)
		if self.ReplyTo is not None: msg['Reply-To'] = self.ReplyTo

		if ct == 'text/html':
			msgAlternative = MIMEMultipart('alternative')
			msg.attach(msgAlternative)

			if html2text is not None:
				txt = self.__OutputBuffer.getvalue()
				#TODO: Following code is quite heavy - but as html2text has problem handling utf-8, we need to convert to Unicode and then back
				txt = txt.decode('utf-8') # Convert to Unicode
				txt = html2text.html2text(txt)
				txt = txt.encode('utf-8') # Convert to UTF-8
				part1 = MIMEText(txt, 'plain', _charset='utf-8')
				del txt
				msgAlternative.attach(part1)
				del part1
			else:
				L.warning("Python module html2text not found - use 'easy_install-2.7 html2text' to install that")

			part2 = MIMEText(self.__OutputBuffer.getvalue(), 'html', _charset='utf-8')
			self.__OutputBuffer.close()
			msgAlternative.attach(part2)
			del part2

		#TODO: Implement support for 'text/plain' and binaries (images) ...
		else:
			raise NotImplementedError("Mail response cannot handle content type of '{0}' (yet)".format(ct))

		for atta in self.Attachments:
			msg.attach(atta)

		return msg.as_string()

	