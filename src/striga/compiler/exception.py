import striga.core.exception

###

class StrigaCompilerError(striga.core.exception.StrigaRuntimeException):
	pass

###

class StrigaParserError(StrigaCompilerError):
	pass

