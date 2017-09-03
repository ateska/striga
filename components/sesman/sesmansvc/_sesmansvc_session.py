import uuid, time, random, string, weakref, itertools, logging
import collections

import os
import pickle

###

L = logging.getLogger('SesMan')
L.setLevel(logging.NOTSET)

###

class Session(object):


	def __init__(self, ctx, lifetime, sesman):
		self.SIN = str(uuid.uuid4()).replace('-','')
		self.RemoteAddr = ctx.req.RemoteAddress
		self.RemoteAddrCheck = True
		self.LifeTime = lifetime #In sec.
		self.CreateAt = time.time()
		self.LastActivity = self.CreateAt
		self.Vars = SessionDict()
		self.__VarsHash = None
		self.Dirty = None
		self.SetDirty(False)
		L.info("New session '{0}' created for '{1}'".format(self.SIN, self.RemoteAddr))
		
		self.SessionManagerRef = weakref.ref(sesman)
		self.User = None # Placeholder for session authentication
		self.UniqueNumberGenerator = itertools.count(1)


	def IsDirty(self):
		return self.Dirty or (self.__VarsHash != hash(self.Vars))
	
	
	def SetDirty(self, dirty=True):
		''' Explicitly set session as dirty. This has to be called if some complex objects are stored into session vars
		(e.g.: dict of dict or objects). Session is not able to determine change of such values and would consider the values
		as unchanged''' 
		if not dirty:
			self.__VarsHash = hash(self.Vars)
			self.Dirty = False
		else:
			self.Dirty = True


	def Touch(self):
		self.LastActivity = time.time()
		self.Dirty = True


	def Check(self, ctx):
		# Check if session is not expired - if yes, then recycle
		acttime = time.time()
		if (self.LastActivity + self.LifeTime) < acttime:
			L.info("Session '%s' expired (request check)" % self.SIN)
			return False


		if self.RemoteAddrCheck:
			if self.RemoteAddr != ctx.req.RemoteAddress:
				L.warning("Session '%s' check failed - remote address not match - '%s' != '%s'" % (self.SIN, self.RemoteAddr, ctx.req.RemoteAddress))
				return False

		return True


	def AddUniqueVar(self, prefix, value, samplecnt=2, samplespace = string.letters+string.digits):
		'''This function finds unique variable within session variables dictionary, stores given value in that and return its name'''

		placeholder = object()

		for i in range(1000):
			uniqid = ''.join([random.choice(samplespace) for _ in range(samplecnt)])
			x = self.Vars.setdefault(prefix + uniqid, placeholder)
			if x == placeholder: break
		else:
			raise RuntimeError("Cannot find free unique session variable name")

		self.Vars[prefix + uniqid] = value
		return uniqid
	
	
	def __getstate__(self):
		p = self.__dict__.copy()
		del p['SessionManagerRef']
		return p
	
	def __setstate__(self, state):
		self.__dict__.update(state)
		self.SetDirty(False)

###

class SessionDict(dict):
	
	def __hash__(self):
		hv = long(id(self))
		for k, v in self.iteritems():
			try:
				hv += hash(k)
			except TypeError:
				pass
			try:
				hv += hash(v)
			except TypeError:
				pass
				
		return hv
			