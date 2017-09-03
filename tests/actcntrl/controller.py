import os, time, logging as L
import exihtmllib

from striga.core.mvc import CallView
from striga.core.exception import StrigaClientSeeOther, StrigaBusError

###

class Controller(exihtmllib.ActionDrivenController):


	def OnMethodGET(self, ctx, path):
		return CallView(color='?')


	@exihtmllib.Action('red')
	def OnActionRed(self, ctx, path):
		return CallView(color='red')


	@exihtmllib.Action('yellow')
	def OnActionYellow(self, ctx, path):
		return CallView(color='yellow')


	@exihtmllib.Action('green')
	def OnActionGreen(self, ctx, path):
		return CallView(color='green')
