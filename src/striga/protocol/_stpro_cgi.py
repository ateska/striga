# CGI protocol
import cgi
import striga.protocol._stpro_http as http
from striga.core.variables import MultiDict

###

class Request(http.Request):


	def __init__(self, Path, Input, ContentLenght, CGIEnv):
		http.Request.__init__(self, Path, CGIEnv['REMOTE_ADDR'], CGIEnv['REQUEST_METHOD'], Input, ContentLenght, CGIEnv.get('CONTENT_TYPE', None))

		self.CGIEnv = CGIEnv #TODO: This becomes obsolete by self.Vars.HEADER variables.multidict

		#TODO: Check if it is necessary to have HEADER as multidict, it can be simple dict() object
		#TODO: Check if it possible to move this into striga.protocol._stpro_http.Request
		self.Vars.AddVarSet('HEADER', MultiDict([(key,[value]) for key, value in CGIEnv.iteritems()]))

		cookie = CGIEnv.get('HTTP_COOKIE', None)
		if cookie is not None:
			self.CookieJar.HTTPInput(cookie)

		qs = CGIEnv.get('QUERY_STRING', None)
		if qs is not None:
			self.Vars.GET.Update(cgi.parse_qs(qs, keep_blank_values=1))

###

Response = http.Response

