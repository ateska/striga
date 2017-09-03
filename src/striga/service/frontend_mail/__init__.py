import logging
import striga.server.service

from . import _mailfrd_service

###

L = logging.getLogger('MailFrontend')

###
'''
Mailing frontend allows Striga users to send emails constructed using standard Striga environment.

It is represented by frontend(-like) service that expose .SendMail() method. This method raises Striga request, 
that goes to linked sitebus and eventually produces HTML output (or different type) that will be send by SMTP (or similar) protocol.

To send email use following code:
	ctx.app.Services.MailFrontend.SendMail(path)

To pass arguments use:
	ctx.app.Services.MailFrontend.SendMail(path, arg1='foo', arg2='bar')
Arguments are available in ctx.req.Vars.MAIL (e.g  ctx.req.Vars.MAIL['arg1']).


Configuration of mailing frontend in sitebus - you need to configure mailfrontend including SMTP connection and sitebus with mail templates:

mailfrontend:
	smtp(host='gateway.dhl.com', port=25)
	sitebus(name="mail-sitebus")


sitebus(rootdir='tests', index='test', name="mail-sitebus"):
	view(path='testmail1', source='testmail1', mode='xhtml')

You can freely use all Striga sitebus features.

Context response object has few important attributes, that needs to be filled:
ctx.res.Subject - Subject of the email (string, UTF-8)
ctx.res.From - Sender email address (string; UTF-8)
ctx.res.To - Array of email recipients (array of strings; UTF-8)
ctx.res.CC - Array of email CC recipients (array of strings; UTF-8) - can be empty
ctx.res.BCC - Array of email BCC recipients (array of strings; UTF-8) - can be empty

Also following methods are available:
ctx.res.AddAttachment(mimeobj, filename) - adds attachment into email, please use Python mime objects like email.mime.image.MIMEImage
ctx.res.AddContent(mimeobj, contentid) - adds embedded content (file), this content is then accessible by "cid:<contentid" URL -> <img src="cid:image1">


To disable SMTP traffic use (in server configuration):
mailfrontend:
	smtp(host='0',...)

In such a case mails will be generated but discarded.
This option is useful in development environments.

'''
###

class MailServiceFactory(striga.server.service.ServiceFactory):

	def __init__(self, parent, name = 'MailFrontendFactory', startstoppriority = 200):
		striga.server.service.ServiceFactory.__init__(self, _mailfrd_service.MailFrontendService, 'MailFrontend', 'mailfrontend', parent, name, startstoppriority)
