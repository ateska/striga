import os, optparse, mimetypes
import striga.server.application
import striga.service.loader
import striga.service.compmngr
import striga.service.threadpool
import striga.service.threadmonitor

###

class ServerApplication(striga.server.application.Application):

	#Services to be load when seen in configuration
	striga.server.application.Application.LateLoadServices.update({
		'scgifrontend' : ('striga.service.frontend_scgi','SCGIServiceFactory'),
		'mailfrontend' : ('striga.service.frontend_mail','MailServiceFactory'),
		'sitebus' : ('striga.service.sitebus','SiteBusFactory'),
	})

	CmdLineOptionList = striga.server.application.Application.CmdLineOptionList + [

		optparse.make_option(
					"-p", "--path",
					action="append", dest="ComponentPath", metavar="COMPPATH",
					help="Add COMPPATH to component search path (more options can be given)"
		),

	]

	CmdLineDefaultOptions = dict(Config = 'striga-server.conf', **striga.server.application.Application.CmdLineDefaultOptions)

	def __init__(self):
		self.Mimetypes = []

		#Config definitions to be added
		striga.server.application.Application.ConfigDefinitions.update({
			'mimetypes' : self.__configure_mimetypes,
			'!' : self.__configure_finished,
		})

		striga.server.application.Application.__init__(self, 'Striga Server')


	def _PrepareCoreServices(self):
		striga.server.application.Application._PrepareCoreServices(self)
		striga.service.threadpool.ThreadPoolService(self.Services)
		striga.service.threadmonitor.ThreadMonitorService(self.Services)
		striga.service.loader.LoaderService(self.Services)
		striga.service.compmngr.ComponentManagerService(self.Services, self.CommandLineOptions.ComponentPath)


	def __configure_mimetypes(self, conffilename, path):
		self.Mimetypes = path.split(';')


	def __configure_finished(self):
		mimetypes.init(self.Mimetypes)
