from Cookie import SimpleCookie

import striga.core.exception

###

#TODO: Rewrite this - must be connected to req.CustomHeader to support cookies deletion
class CookieJar(SimpleCookie):


	def __init__(self, input=None):
		SimpleCookie.__init__(self, input)


	def Add(self, name, value, path = None, comment = None, domain = None, maxage = None, secure = False, version = None, httponly = False):
		SimpleCookie.__setitem__(self, name, value)

		if path is not None:
			self[name]['Path'] = path

		if version is not None:
			version = int(version)
			if (version < 0) and (version > 9):
				raise striga.core.exception.StrigaRuntimeException("Version for cookie must be single digit (see RFC 2109)")
			self[name]['Version'] = version
		else:
			self[name]['Version'] = 1

		if comment is not None:
			self[name]['Comment'] = comment

		if domain is not None:
			domain = str(domain)

			if (len(domain) == 0) or (domain[0] != '.'):
				raise striga.core.exception.StrigaRuntimeException("Domain for cookie must start with dot (see RFC 2109)")

			self[name]['Domain'] = domain

		if maxage is not None:
			self[name]['Max-Age'] = int(maxage)


		if secure:
			self[name]['Secure'] = 'Secure'

		if httponly:
			self[name]['HttpOnly'] = 'HttpOnly'


	Get = SimpleCookie.get
	HTTPInput = SimpleCookie.load
	HTTPOutput = SimpleCookie.output
