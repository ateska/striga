import logging
import striga.core.exception
from ._mdcntrl import MethodDrivenController

###

L = logging.getLogger("adcntrl")

###

class Action(object):
	'''
Action decorator
	
Usage:

# Simple example
<input type="submit" name="!login" value="Login"

# Example with value (passed as 'val' parameter of the action)
<input type="submit" name="!delete:{0}".format(33) value="Delete item 33"

# Active tag example
<exihtmltag.actionbtn action="login" label="Login"

# Active tag example with value
<exihtmltag.actionbtn action="delete" value=33 label="Delete item 33"

WARNING: Do not use <button type="submit" -> it does NOT work in Internet Explorer

class DemoController(ActionController):

	def OnMethodGET(self, ctx, path):
		return CallView()

	@Action('login')
	def OnActionLogin(self, ctx, path, _act, _val):
		return CallView()

	@Action('delete')
	def OnActionDelete(self, ctx, path, _act, val):
		model.DeleteItem(val)
		return CallView()

	'''

	def __new__(cls, actionname):
		'''Decorator factory - ensures correct creation of the Action decorator'''
		dec = object.__new__(cls)
		def wrapper(function):
			dec.__init__(actionname, function)
			return dec
		return wrapper


	def __init__(self, actionname, function):
		'''Created decorator instance that is bound to particular controller class'''
		self.ActionName = actionname
		if isinstance(function, Action):
			self.Function = None
			self.ChainedAction = function
		else:
			self.Function = function
			self.ChainedAction = None


	def __call__(self, cntrl, ctx, path, act, val, *args, **kwargs):
		'''Handles actual call prior entering controller'''
		# Here it is possible to prepare additional variables for action method (extracted POST/GET variables, filled form instance e.g.)
		if self.ChainedAction is not None:
			return self.ChainedAction(cntrl, ctx, path, act, val, *args, **kwargs)
		else:
			m = self.Function.__get__(cntrl, cntrl.__class__)
			return m(ctx, path, act, val, *args, **kwargs)

###

class ActionDrivenController(MethodDrivenController):
	'''
	This version supports chained @Actions
	
	@Action('unpublish')
	@Action('publish')
	def OnActionMulti(self, ctx, path, act, val):
		...
		
	'''


	def __init__(self):
		MethodDrivenController.__init__(self)

		# Prepare action map
		self.ActionMap = dict()
		for m in dir(self):
			v = getattr(self, m)
			while isinstance(v, Action):
				self.ActionMap[v.ActionName] = v
				if v.ChainedAction is None: break
				v = v.ChainedAction


	def OnMethodPOST(self, ctx, path, *args, **kwargs):
		for act in ctx.req.Vars.POST.iterkeys():
			if act.find('!') == 0: break
		else:
			# Cannot find action
			L.warning("Haven't find action ('!<action>') in the POST variables.")
			raise striga.core.exception.StrigaBusError("NotFound")

		vpos = act.find(':')
		if vpos == -1:
			val = None
			act = act[1:]
		else:
			val = act[vpos+1:]
			act = act[1:vpos]

		m = self.ActionMap.get(act)
		if m is None:
			# Cannot find action 
			L.warning("Unknown/undefined action '{0}' in the POST variables.".format(act))
			raise striga.core.exception.StrigaBusError("NotFound")

		return m(self, ctx, path, act, val, *args, **kwargs)
