import os, sys, re, functools, copy, logging as L
import striga.core.exception

###

class Bus(object):

	CustomSiteBusDefs = {}
	PathCheckRE = re.compile(r'^[^//]*$')

	def __init__(self):
		self.IntroBusItems = []	#Iterate thru this (call each) in the begining
		self.CrossroadBusItems = {} #Check path against this, if ok, call item from that
		self.DefaultBusItem = None #Call when not found anything in self.CrossroadBusItems

		self.RootDir = None
		self.Index = None
		self.ErrorBus = None


	def _InsertBusItem(self, path, createitemfnct):
		if path is None:
			if self.DefaultBusItem is not None:
				raise striga.core.exception.StrigaConfigurationError("Default bus item is already configured!")
			self.DefaultBusItem = createitemfnct()
			return self.DefaultBusItem

		if self.PathCheckRE.match(path) is None:
			raise striga.core.exception.StrigaConfigurationError("Invalid path '%s' given!" % path)

		if self.CrossroadBusItems.has_key(path):
			raise striga.core.exception.StrigaConfigurationError("Bus item for '%s' is already configured!" % path)

		nbi = createitemfnct()
		self.CrossroadBusItems[path] = nbi
		return nbi


	def _configure(self, conffilename, index = None, rootdir = None):
		if rootdir is None:	rootdir = os.path.dirname(conffilename)
		self.RootDir = os.path.normpath(os.path.abspath(rootdir))
		if not os.path.isdir(self.RootDir):
			if os.path.exists(self.RootDir):
				L.warning("Bus item root directory is not directory: '%s'" % (self.RootDir))
			else:
				L.warning("Bus item root directory doesn't exist: '%s'" % (self.RootDir))

		self.Index = index

		defs = {}
		for key, fn in self.CustomSiteBusDefs.iteritems():
			defs[key] = functools.partial(fn, self)

		defs.update({
			'location' : self.__configure_location,
			'errorbus' : self.__configure_errorbus,
			'var' : self.__configure_var,
			'serve' : self.__configure_serve,
			'view' : self.__configure_view,
			'exec' : self.__configure_exec,
			'controller' : self.__configure_controller,
			'componentbus' : self.__configure_componentbus,
			'!' : self._configure_finished,
		})

		return defs


	def __configure_location(self, conffilename, path = None, index = None, rootdir = '.'):
		'''
		@param path - can be None as location can be default sitebus item too
		'''
		from ._stsvcsb_location import Location
		l = self._InsertBusItem(path, Location)

		rootdir = os.path.join(self.RootDir, rootdir)
		return l._configure(conffilename = conffilename, index = index, rootdir = rootdir)


	def __configure_errorbus(self, conffilename, rootdir = '.'):
		if self.ErrorBus is not None:
			L.warning("Bus item has already one errorbus defined - overwriting")

		from ._stsvcsb_errorbus import ErrorBus
		self.ErrorBus = ErrorBus()
		rootdir = os.path.join(self.RootDir, rootdir)
		return self.ErrorBus._configure(conffilename = conffilename, rootdir = rootdir)


	def __configure_var(self, conffilename, name, default = 0):
		self.IntroBusItems.append(functools.partial(BusVar, name, default))


	def __configure_serve(self, conffilename, pattern, path = None, buffersize = 64*1024):
		'''
		Config keyword - serve
		'''
		from ._stsvcsb_serve import Serve
		self._InsertBusItem(path, functools.partial(Serve, self.RootDir, pattern, buffersize))


	def __configure_view(self, conffilename, source, mode, path = None, entry='main', pathlimit='==0'):
		'''
		Config keyword - view
		'''
		from ._stsvcsb_view import View
		self._InsertBusItem(path, functools.partial(View, self.RootDir, source, mode, entry, pathlimit))


	def __configure_componentbus(self, conffilename, component, path = None, busname = 'componentbus'):
		'''
		Config keyword - componentbus
		'''
		from ._stsvcsb_compbusref import ComponentBusRef
		self._InsertBusItem(path, functools.partial(ComponentBusRef, component, busname))


	def __configure_exec(self, conffilename, source, entry, path = None, pathlimit = '==0', rootdir = '.'):
		'''
		Config keyword - exec
		'''
		from ._stsvcsb_exec import Exec
		rootdir = os.path.join(self.RootDir, rootdir)
		self._InsertBusItem(path, functools.partial(Exec, rootdir, source, entry, pathlimit))


	def __configure_controller(self, conffilename, source, controllerclass = 'Controller', path = None, pathlimit = '==0', rootdir = '.'):
		'''
		Config keyword - Controller
		'''
		from ._stsvcsb_cntrlr import Controller
		rootdir = os.path.join(self.RootDir, rootdir)
		nbi = self._InsertBusItem(path, functools.partial(Controller, rootdir, source, controllerclass, pathlimit))
		return nbi._configure(conffilename = conffilename)


	def _configure_finished(self):
		pass


	def __call__(self, ctx, path):
		'''
		Entry point to this bus object
		'''

		SiteBusVar = ctx.req.Vars.SITEBUS
		SiteBusVar['RootDir'] = self.RootDir
		SiteBusVar['Location'] = self

		try:
			#First iterate thru IntroBusItems
			for ibm in self.IntroBusItems:
				ibm(ctx, path)

			#Check again as IntroBusItems can change path array
			if len(path) == 0:
				if self.Index is not None:
					path.append(self.Index)
				else:
					raise striga.core.exception.StrigaBusError("NotFound")

			#Then find item in CrossroadBusItems & DefaultBusItem
			bm = self.CrossroadBusItems.get(path[0], None)
			if bm is None:
				bm = self.DefaultBusItem
				if bm is None:
					L.warning("Site bus path not found: {0}".format(path))
					raise striga.core.exception.StrigaBusError('NotFound')
			else:
				ctx.req.Vars.SITEBUS['LastPath'] = path.pop(0)

			bm(ctx, path)

		except striga.core.exception._StrigaClientRedirectBase:
			# Redirections are not solved thru ErrorBus
			raise

		except:
			ctx.err.exctype, ctx.err.excvalue = sys.exc_info()[:2]
			prev_excvalue = copy.copy(ctx.err.excvalue)

			if self.ErrorBus is not None:
				if isinstance(ctx.err.excvalue, striga.core.exception.StrigaBusError):
					epath = ctx.err.excvalue.Name
				else:
					L.exception("Generic exception during bus processing (you should use StrigaBusError exceptions)")
					epath = str(ctx.err.exctype)
				try:
					self.ErrorBus(ctx, epath)
					return False
				except:
					L.exception("Exception during error bus processing:")

				raise prev_excvalue

			else:
				raise


	def BusStart(self):
		for bm in self.IntroBusItems:
			if hasattr(bm, 'BusStart'): bm.BusStart()

		for bm in self.CrossroadBusItems.itervalues():
			if hasattr(bm, 'BusStart'): bm.BusStart()

		if (self.DefaultBusItem is not None) and hasattr(self.DefaultBusItem, 'BusStart'):
			self.DefaultBusItem.BusStart()

		if self.ErrorBus is not None: self.ErrorBus.BusStart()


	def BusStop(self):
		if self.ErrorBus is not None: self.ErrorBus.BusStop()

		if (self.DefaultBusItem is not None) and hasattr(self.DefaultBusItem, 'BusStop'):
			self.DefaultBusItem.BusStop()

		for bm in self.CrossroadBusItems.itervalues():
			if hasattr(bm, 'BusStop'): bm.BusStop()

		for bm in self.IntroBusItems:
			if hasattr(bm, 'BusStop'): bm.BusStop()

###

def BusVar(name, default, ctx, path):
	if len(path) == 0: raise striga.core.exception.StrigaBusError('NotFound') 
	val = path.pop(0)
	if val == '': val = default
	ctx.req.Vars.SITEBUS[name] = val
