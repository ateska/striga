import logging
import striga.server.service

from . import _stfsvsc_service

###

L = logging.getLogger('SCGIFrontend')

###

class SCGIServiceFactory(striga.server.service.ServiceFactory):

	def __init__(self, parent, name = 'SCGIFrontendFactory', startstoppriority = 200):
		striga.server.service.ServiceFactory.__init__(self, _stfsvsc_service.SCGIService, 'SCGIFrontend', 'scgifrontend', parent, name, startstoppriority)
