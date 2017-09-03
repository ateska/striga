import re, logging

###

L = logging.getLogger("striga.brwdtc")

###

class DetectBrowser(object):

	#TODO: Opera
	#TODO: KDE Konqueror
	#TODO: Camino
	#TODO: Mobile devices

	UABrowser = [
		('chrome', 'chrome', None),
		('omniweb', 'omniweb', None),
		('safari', 'safari', re.compile('version/([^ ]+)')),
		('opera mini', 'opera-mini', re.compile(r'version/([^ ]+)')),
		('opera', 'opera', re.compile(r'version/([^ ]+)')),
		('firefox', 'firefox', None),
		('netscape', 'netscape', None),
		('msie', 'msie', None),
		('gecko', 'mozilla', None),
		('mozilla', 'mozilla', None),
		('blackberry', 'blackberry', re.compile(r'blackberry8520/([^ ]+)')),

		('uci dav explorer', 'uci dav explorer', None),

		('python-urllib', 'python-urllib', None),
		('curl', 'curl', None),
		('wget', 'wget', None),

	]

	#TODO: Android
	#TODO: Windows mobile
	#TODO: iOS on IPod

	UAOS = [
		('iphone', 'ios'),
		('ipad', 'ios'),
		('darwin', 'macosx'),
		('win', 'windows'),
		('os x', 'macosx'),
		('mac', 'mac'),
		('android', 'android'),
		('linux', 'linux'),
		('blackberry', 'blackberry'),
		('uci dav explorer', 'java'),
		('python-urllib', 'python')
	]

	def __init__(self, ctx):
		self.Type = 'unknown'
		self.Version = 'unknown'
		self.OS = 'unknown'

		try:
			self.UA = ctx.req.Vars.HEADER.GetOne('HTTP_USER_AGENT', None)
		except AttributeError:
			# To support unit testing
			if isinstance(ctx, basestring):
				self.UA = ctx
			else: raise
		if self.UA is None:
			self.UA =''
			return

		ua = self.UA.lower()

		# Detect browser type
		for ts, res, vsrch in self.UABrowser:
			pos = ua.find(ts)
			if pos < 0: continue
		
			self.Type = res

			if vsrch is None:
				self.Version = ua[pos+len(ts)+1:].split(' ', 1)[0]
			else:
				res = vsrch.search(ua)
				if res is not None:
					self.Version = res.group(1)

			break

		# Detect os
		for ts, res in self.UAOS:
			if ua.find(ts) >= 0:
				self.OS = res
				break

		## Special cases

		# It seems that webkit browser reports as safari on Android
		if self.OS == 'android' and self.Type == 'safari':
			self.Type = 'webkit'

		if self.Type == 'curl' and self.OS == 'unknown':
			self.OS = 'N/A'

		if self.Type == 'unknown' or self.Version == 'unknown' or self.OS == 'unknown':
			L.debug("Failed detection of at least one browser info from user agent string: '{0}' -> {1}".format(ua, self))


	def __str__(self):
		return "<{0} Type={1} Version={2} OS={3}>".format(self.__class__.__name__, self.Type, self.Version, self.OS)


	def GetMajorVersion(self):
		if self.Version is None: return None
		try:
			mv, _ = self.Version.split('.', 1)
			return int(mv)
		except:
			return None

	#

	MobileOS = set([
		'blackberry', 'ios', 'android'
	])

	def IsMobile(self, detailed=False):
		'''
		Returns:
			False - If browser is not considered as mobile (smartphone, tablet, ...)
			True - If browser is considered as mobile and parameter 'detailed' is False (default)
			True - If browser is considered as mobile on 'generic' mobile device (detailed set to True)
			't' - If browser is considered as mobile on tablet (detailed set to True)
			'p' - If browser is considered as mobile on phone (detailed set to True)
		'''
		#TODO: Extend detection for common platforms ...
		if self.OS not in self.MobileOS: return False
		if not detailed: return True

		if self.OS == 'ios':
			if self.UA.find(' (iPad;') > 0: return 't'
			if self.UA.find(' (iPhone;') > 0: return 'p'

		if self.OS == 'android':
			# From: http://stackoverflow.com/questions/5341637/how-do-detect-android-tablets-in-general-useragent
			if self.UA.find(' Mobile ') > 0: return 'p'
			elif self.Type == 'webkit': return 't'
			else: return True

		return True

	#TODO: IsHTML5Capable() method

###

if __name__ == '__main__':
	tests = [
		('mozilla/5.0 (macintosh; intel mac os x 10_6_8) applewebkit/535.2 (khtml, like gecko) chrome/15.0.874.121 safari/535.2',
		'chrome', '15.0.874.121', 'macosx', 15, False
		),

		('mozilla/5.0 (macintosh; intel mac os x 10_6_8) applewebkit/534.51.22 (khtml, like gecko) version/5.1.1 safari/534.51.22',
		'safari', '5.1.1', 'macosx', 5, False
		),

		('mozilla/5.0 (macintosh; u; intel mac os x 10.6; en-us; rv:1.9.2.24) gecko/20111103 firefox/3.6.24',
		'firefox', '3.6.24', 'macosx', 3, False
		),

		('Opera/9.80 (Macintosh; Intel Mac OS X; U; en) Presto/2.5.24 Version/10.53',
		'opera', '10.53', 'macosx', 10, False
		),

		('BlackBerry8520/5.0.0.681 Profile/MIDP-2.1 Configuration/CLDC-1.1 VendorID/170',
		'blackberry', '5.0.0.681', 'blackberry', 5, True
		),

		# Default iOS browser on iPhone 4GS
		('Mozilla/5.0 (iPhone; CPU iPhone OS 5_0_1 like Mac OS X) AppleWebKit/534.46 (KHTML, like Gecko) Version/5.1 Mobile/9A405 Safari/7534.48.3',
		'safari', '5.1', 'ios', 5, 'p'
		),

		# Default iOS browser on iPhone 3GS
		('Mozilla/5.0 (iPhone; CPU iPhone OS 5_0_1 like Mac OS X) AppleWebKit/534.46 (KHTML, like Gecko) Version/5.1 Mobile/9A405 Safari/7534.48.3',		
		'safari', '5.1', 'ios', 5, 'p'
		),

		# Default iOS browser on iPad (emulator)
		('Mozilla/5.0 (iPad; CPU OS 6_1 like Mac OS X) AppleWebKit/536.26 (KHTML, like Gecko) Version/6.0 Mobile/10B141 Safari/8536.25',
		'safari', '6.0', 'ios', 6, 't'
		),

		# Default Android OS browser (webkit) on Android 2.3.5 Samsung Galaxy SII
		('Mozilla/5.0 (Linux; U; Android 2.3.5; en-us; GT-I9100 Build/GINGERBREAD) AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1',
		'webkit', '4.0', 'android', 4, 'p'
		),

		# Firefox on Android 2.3.5 Samsung Galaxy SII
		('Mozilla/5.0 (Android; Linux armv7l; rv:10.0.1) Gecko/20120208 Firefox/10.0.1 Fennec/10.0.1',
		'firefox', '10.0.1', 'android', 10, True
		),

		# Opera Mobile on Android 2.3.5 Samsung Galaxy SII
		('Opera/9.80 (Android 2.3.5; Linux; Opera Mobi/ADR-1202011015; U; en) Presto/2.9.201 Version/11.50',
		'opera', '11.50', 'android', 11, True
		),

		# Opera Mini on Android 2.3.5 Samsung Galaxy SII
		('Opera/9.80 (Android; Opera Mini/6.5.27452/27.1188;U; en) Presto/2.8.119 Version/11.10',
		'opera-mini', '11.10', 'android', 11, True
		),


		# Default Android OS browser (webkit) on Android 3.1 Samsung Galaxy Tab 10.1
		('Mozilla/5.0 (Linux; U; Android 3.1; en-gb; GT-P7500 Build/HMJ37) AppleWebKit/534.13 (KHTML, like Gecko) Version/4.0 Safari/534.13',
		'webkit', '4.0', 'android', 4, 't'
		),

		# Firefox on Android 3.1 Samsung Galaxy Tab 10.1
		('Mozilla/5.0 (Android; Linux armv7l; rv:10.0.1) Gecko/20120208 Firefox/10.0.1 Fennec/10.0.1',
		'firefox', '10.0.1', 'android', 10, True
		),

		# Opera Mobile on Android 3.1 Samsung Galaxy Tab 10.1
		('Opera/9.80 (Android 3.1; Linux; Opera Tablet/ADR-1202011015; U; en) Presto/2.9.201 Version/11.50',
		'opera', '11.50', 'android', 11, True
		),

		# Opera Mini on Android 3.1 Samsung Galaxy Tab 10.1
		('Opera/9.80 (Android; Opera Mini/6.5.27452/27.1188; U; en) Presto/2.8.119 Version/11.10',
		'opera-mini', '11.10', 'android', 11, True
		),

		# Curl 
		('curl/7.28.1',
		'curl', '7.28.1', 'N/A', 7, False
		),

		]

	for ua, rbr, rvr, ros, rmv, rmobos in tests:
		bd = DetectBrowser(ua)
		print bd, bd.IsMobile()
		assert bd.Type == rbr, "Browser '{0}' != '{1}'".format(bd.Type, rbr)
		assert bd.Version == rvr, "Version '{0}' != '{1}'".format(bd.Version, rvr)
		assert bd.OS == ros, "OS '{0}' != '{1}'".format(bd.OS, ros)
		
		assert bd.GetMajorVersion() == rmv, bd
		assert bd.IsMobile(True) == rmobos, bd
