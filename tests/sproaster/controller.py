import os, sys, time, logging as L
import exihtmllib

from striga.core.mvc import CallView
from striga.core.exception import StrigaClientSeeOther, StrigaBusError
from striga.service.sproaster import ResidentSubprocess, RepeatingSubprocess, OneShotSubprocess

###

def Test_OneShot(ctx):
	SubprocessRoaster = ctx.app.Services.SubprocessRoaster

	testprocess = OneShotSubprocess(['/usr/sbin/iostat','-c','3'])
	 
	SubprocessRoaster.Register(testprocess)

###

def Test_OneShot_Error(ctx):
	SubprocessRoaster = ctx.app.Services.SubprocessRoaster

	testprocess = OneShotSubprocess(['XXX','a','b','c'])
	 
	SubprocessRoaster.Register(testprocess)

###

def Test_OneShot_Python(ctx):
	SubprocessRoaster = ctx.app.Services.SubprocessRoaster

	testapp = os.path.join(os.path.dirname(__file__), 'test_child.py')
	testprocess = OneShotSubprocess([sys.executable, testapp])
	 
	SubprocessRoaster.Register(testprocess)

###

def Test_OneShot_Sudo(ctx):
	SubprocessRoaster = ctx.app.Services.SubprocessRoaster

	testprocess = OneShotSubprocess(['whoami'], SudoUser='root')
	 
	SubprocessRoaster.Register(testprocess)


###

def Test_Resident(ctx):
	SubprocessRoaster = ctx.app.Services.SubprocessRoaster

	testprocess = ResidentSubprocess(['/usr/sbin/iostat','-c','3'])
	 
	SubprocessRoaster.Register(testprocess)

###

def Test_Resident_Error(ctx):
	SubprocessRoaster = ctx.app.Services.SubprocessRoaster

	testprocess = ResidentSubprocess(['ls'])
	 
	SubprocessRoaster.Register(testprocess)

###

def Terminate(ctx, uid):
	SubprocessRoaster = ctx.app.Services.SubprocessRoaster
	try:
		SubprocessRoaster.Terminate(int(uid))
	except:
		L.exception("Error when terminating subprocess (uid={0})".format(uid))

###

def ErrorRecovery(ctx, uid, trgstate):
	SubprocessRoaster = ctx.app.Services.SubprocessRoaster
	try:
		SubprocessRoaster.ErrorRecovery(int(uid), trgstate)
	except:
		L.exception("Error when error-recovering subprocess (uid={0})".format(uid))

###

class Controller(exihtmllib.MethodDrivenController):

	def OnMethodGET(self, ctx, path):
		SubprocessRoaster = ctx.app.Services.SubprocessRoaster
		return CallView(SubprocessRoaster)

	def OnMethodPOST(self, ctx, path):
		if ctx.req.Vars.POST.GetOne('test_oneshot',default=None) == '1':
			Test_OneShot(ctx)
		elif ctx.req.Vars.POST.GetOne('test_oneshot_error',default=None) == '1':
			Test_OneShot_Error(ctx)
		elif ctx.req.Vars.POST.GetOne('test_oneshot_python',default=None) == '1':
			Test_OneShot_Python(ctx)
		elif ctx.req.Vars.POST.GetOne('test_oneshot_sudo',default=None) == '1':
			Test_OneShot_Sudo(ctx)
		elif ctx.req.Vars.POST.GetOne('test_resident',default=None) == '1':
			Test_Resident(ctx)
		elif ctx.req.Vars.POST.GetOne('test_resident_error',default=None) == '1':
			Test_Resident_Error(ctx)

		elif ctx.req.Vars.POST.GetOne('terminate',default=None) is not None:
			Terminate(ctx, ctx.req.Vars.POST.GetOne('terminate'))
		elif ctx.req.Vars.POST.GetOne('errorrec_del',default=None) is not None:
			ErrorRecovery(ctx, ctx.req.Vars.POST.GetOne('errorrec_del'), 'D')
		elif ctx.req.Vars.POST.GetOne('errorrec_sch',default=None) is not None:
			ErrorRecovery(ctx, ctx.req.Vars.POST.GetOne('errorrec_sch'), 'S')

		else:
			raise StrigaBusError("NotFound")

		raise StrigaClientSeeOther('sproaster')
