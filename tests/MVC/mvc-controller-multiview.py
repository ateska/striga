from striga.core.mvc import CallViewWithPath

###

class Controller(object):


	def __call__(self, ctx, path):
		view=ctx.req.Vars.GET.Get('view', 0, '1')
		if view == '2':
			return CallViewWithPath('mvc-view2', ControllerGreeting ='Msg from controller')
		else:
			return CallViewWithPath('mvc-view1', ControllerGreeting ='Msg from controller')
