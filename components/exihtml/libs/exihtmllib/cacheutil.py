import os, stat, hashlib, time, collections, re
import logging as L
from striga.server import scheduler, application
import striga.compiler.compilerapp

try:
	import cssmin #External dependency
	# From https://github.com/zacharyvoase/cssmin
except ImportError:
	cssmin = None 

try:
	import rjsmin #External dependency
	#From http://opensource.perlig.de/rjsmin/
except ImportError:
	rjsmin = None 


###

class _CacheManager(collections.MutableMapping):

	CacheNamesRG = re.compile(r"^([0-9a-v][0-9a-f]*)-[0-9a-f]+\.[a-z]+$")

	def __init__(self):
		self.Cache = {}
		self.CacheDir = None

		app = application.GetInstance()
		if not isinstance(app, striga.compiler.compilerapp.CompilerApplication):
			self.CacheDir = app.ConfigDictionary.get('EXIHTMLCACHEDIR', None)
			
			if self.CacheDir is not None:
				# Check cache validity every 5 seconds
				app.Scheduler.AddJob(scheduler.PeriodicJob(5, self.RefreshAll))
				
				# Execute cache clean-up evry 300 seconds
				app.Scheduler.AddJob(scheduler.PeriodicJob(300, self.CleanUp))


	def RefreshAll(self):
		for cacheentry in self.Cache.itervalues():
			try:
				recreate = max(os.stat(fname).st_mtime for fname in cacheentry.Files) >= os.stat(cacheentry.CacheFile).st_mtime
			except OSError:
				recreate = True
			
			if recreate:
				L.debug("Cached files changed - recreating cache entry!")
				try:
					cacheentry.Recreate()
				except:
					L.exception("Error when recreating cache:")


	def CleanUp(self):

		fgroups = {}

		for item in os.listdir(self.CacheDir):
			irgm = self.CacheNamesRG.match(item)
			if irgm is None: continue
			ipath = os.path.join(self.CacheDir, item)
			istat = os.stat(ipath)
			if not stat.S_ISREG(istat[stat.ST_MODE]): continue			

			cachetag =irgm.group(1)
			if cachetag[0] > 'f':
				cachetag = '-{0:x}'.format(ord(cachetag[0])-103) + cachetag[1:]
			cachetag = int(cachetag, 16)

			if cachetag not in self.Cache:
				# Delete files which hash is not in self.Cache and are older than 1 hour
				if (time.time() - istat[stat.ST_MTIME]) > 3600:
					try:
						os.unlink(ipath)
					except:
						pass

			else:
				# Find group of files with same hash (first part of filename)
				grp = fgroups.get(cachetag)
				if grp is None: fgroups[cachetag] = grp = dict()

				grp[ipath] = istat


		for cachetag, grp in fgroups.iteritems():
			if len(grp) < 2: continue

			try:
				grp.pop(self.Cache[cachetag].CacheFile)
			except KeyError:
				L.warning("Cannot find cache file entry in temporary group dict - strange!")
				continue

			for ipath, istat in grp.iteritems():
				# Delete files if they are not fresh in the group and older than 1 hour
				if (time.time() - istat[stat.ST_MTIME]) > 3600:
					try:
						os.unlink(ipath)
					except:
						pass
				


	def __getitem__(self, a): return self.Cache.__getitem__(a)
	def __setitem__(self, a, b): return self.Cache.__setitem__(a, b)
	def __delitem__(self, a): return self.Cache.__delitem__(a)
	def __len__(self): return self.Cache.__len__()
	def __iter__(self): return self.Cache.__iter__()


CacheManager = _CacheManager()

###

class _CacheEntryBase(object):

	def __init__(self, cachetag, files, cacheurl, minimize):
		assert CacheManager.CacheDir is not None, "Provide EXIHTMLCACHEDIR configuration item in your site config (to use ExiHTML loaders/cache)."

		self.Files = files
		self.CacheTag = cachetag
		self.CacheURL = cacheurl

		self.Minimize = minimize
		self.URL = None
		self.Touch = None
		self.CacheFile = None

		self.Recreate()

		CacheManager[cachetag] = self


	def Recreate(self):
		raise NotImplementedError("You have to override this")

###

class CSSCacheEntry(_CacheEntryBase):

	def Recreate(self):
		css = ""
		for cssfile in self.Files:
			css += open(cssfile, 'r').read()

		if self.Minimize:
			if cssmin is not None:
				css = cssmin.cssmin(css)
			else:
				L.warning("Active tag 'cssloader' was asked to minimalize CSS files but 'cssmin' module not found")

		csshash = hashlib.md5(css).hexdigest()

		cachefname = '{0:x}'.format(self.CacheTag) + '-' + csshash + '.css'
		if cachefname[0] == '-': cachefname = chr(int(cachefname[1], 16) + 103) + cachefname[2:]

		self.CacheFile = os.path.join(CacheManager.CacheDir, cachefname)
		open(self.CacheFile, 'w').write(css)

		self.URL = self.CacheURL + cachefname

		self.Touch = time.time()

###

class JSCacheEntry(_CacheEntryBase):

	def Recreate(self):
		jvs = ""
		for jvsfile in self.Files:
			jvs += open(jvsfile, 'r').read()
			jvs += '\n'

		if self.Minimize:
			if rjsmin is not None:
				jvs = rjsmin.jsmin(jvs)
			else:
				L.warning("Active tag 'jsloader' was asked to minimalize JS files but 'rjsmin' module not found")

		jshash = hashlib.md5(jvs).hexdigest()

		cachefname = '{0:x}'.format(self.CacheTag) + '-' + jshash + '.js'
		if cachefname[0] == '-': cachefname = chr(int(cachefname[1], 16) + 103) + cachefname[2:]

		self.CacheFile = os.path.join(CacheManager.CacheDir, cachefname)
		open(self.CacheFile, 'w').write(jvs)

		self.URL = self.CacheURL + cachefname

		self.Touch = time.time()
