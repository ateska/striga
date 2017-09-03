from striga.core.mvc import CallView

###

class Controller(object):


	def __call__(self, ctx, path):
		return CallView(ControllerGreeting ='Msg from controller')
