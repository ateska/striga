import logging as L
import striga.core.exception

###

class MethodDrivenController(object):

	def __call__(self, ctx, path):

		# See http://www.w3.org/Protocols/rfc2616/rfc2616-sec9.html for Method Definitions
		if ctx.req.Method == 'GET':
			return self.OnMethodGET(ctx, path)
		elif ctx.req.Method == 'POST':
			return self.OnMethodPOST(ctx, path)
		elif ctx.req.Method == 'OPTIONS':
			return self.OnMethodOPTIONS(ctx, path)
		elif ctx.req.Method == 'HEAD':
			return self.OnMethodHEAD(ctx, path)
		elif ctx.req.Method == 'PUT':
			return self.OnMethodPUT(ctx, path)
		elif ctx.req.Method == 'DELETE':
			return self.OnMethodDELETE(ctx, path)
		elif ctx.req.Method == 'TRACE':
			return self.OnMethodTRACE(ctx, path)
		elif ctx.req.Method == 'CONNECT':
			return self.OnMethodCONNECT(ctx, path)


	def __OnMethodNULL(self, ctx, path):
		L.warning("MethodDrivenController {0} doesn't implement method {1}".format(self, ctx.req.Method))
		raise striga.core.exception.StrigaBusError("NotFound")


	OnMethodGET = __OnMethodNULL # Override this your controller implementation
	OnMethodPOST = __OnMethodNULL # Override this your controller implementation
	OnMethodOPTIONS = __OnMethodNULL # Override this your controller implementation
	OnMethodHEAD = __OnMethodNULL # Override this your controller implementation
	OnMethodDELETE = __OnMethodNULL # Override this your controller implementation
	OnMethodTRACE = __OnMethodNULL # Override this your controller implementation
	OnMethodCONNECT = __OnMethodNULL # Override this your controller implementation
