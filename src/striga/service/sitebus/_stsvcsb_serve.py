import os, mimetypes, fnmatch, re, stat, time, logging as L
import striga.core.exception

###

class Serve(object):
	'''
Process bus object that sends plain files from disk to client
	'''

	#TODO: Possibility of serving files from subdirectories
	def __init__(self, rootdir, pattern, buffersize):
		regex = fnmatch.translate(pattern)
		self.RootDir = rootdir
		self.Pattern = re.compile(regex)
		self.BufferSize =  buffersize


	def __call__(self, ctx, path):
		if len(path) > 0:
			raise striga.core.exception.StrigaBusError("NotFound")

		if self.Pattern.match(path[0]) is None:
			raise striga.core.exception.StrigaBusError("NotFound")

		fname = os.path.join(self.RootDir, path[0])

		try:
			fstats = os.stat(fname)
		except:
			raise striga.core.exception.StrigaBusError("NotFound")

		if not stat.S_ISREG(fstats.st_mode): return True

		fMType, fContentEncoding =  mimetypes.guess_type(fname)
		ctx.res.SetContentType(fMType)
		ctx.res.SetContentLength(fstats.st_size)
		ctx.res.CustomHTTPHeader.Set('Last-Modified', time.ctime(fstats.st_mtime))
		ctx.res.SetBufferSize(0) #Do not buffer output - writes will be called in large pieces anyway

		fin = file(fname,'rb')
		while True:
			buffer = fin.read(self.BufferSize)
			if len(buffer) == 0: break
			ctx.res.Write(buffer)

