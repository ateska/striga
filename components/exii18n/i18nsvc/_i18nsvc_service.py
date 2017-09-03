import logging, re, gettext
import striga.server.application, striga.server.service
import striga.service.sitebus

# import babel (lazy way) ...
# See http://babel.edgewall.org/
babel = None

#

L = logging.getLogger('I18n')

###

#TODO: http://babel.edgewall.org/wiki/Documentation/0.9/dates.html (date/time formating)
#TODO: http://babel.edgewall.org/wiki/Documentation/0.9/numbers.html

###

class I18nService(striga.server.service.Service):


	def __init__(self, parent, name, startstoppriority = 100):
		if name is None: name = "I18nService"
		striga.server.service.Service.__init__(self, parent, name, startstoppriority)

		#TODO: Check if there is babel locale data present (presence of i18n/libs/babel/global.dat and i18n/libs/babel/localedata/*.dat) -> CRITICAL error
		#TODO: Check if pytz module is installed -> WARNING

		self.AvailableLocales = None # List of strings
		self.Translations = None


	def Configure(self):
		return {
			'!' : self.__configure_finished,
		}


	def __configure_finished(self):
		striga.service.sitebus.Bus.CustomSiteBusDefs.update({
			'i18nhandler' : self.__configure_i18nhandler,
		})
		self._ChangeServiceStateToConfigured()


	def __configure_i18nhandler(self, bus, conffilename, deflocale = None):
		'''
		i18nhandler([deflocale=None])

		default locale - string like 'en' or 'en_US'. None to use system default
		'''
		bus.IntroBusItems.append(I18nManager(self, deflocale))


	def _DoStart(self):
		# Lazy import of babel (unfortunate construction caused by problematic component library path evaluation order)
		global babel
		if babel is None:
			import babel

		self.AvailableLocales = babel.localedata.list()

		import babel.support
		
		# TODO: More than one domain  ...
		domain = 'messages'
		self.Translations = dict()
		for locale in self.AvailableLocales:
			filename = gettext.find(domain, './files/locale/', [locale])
			if not filename: continue

			self.Translations[locale] = babel.support.Translations(fileobj=open(filename, 'rb'), domain=domain)
		

###

class I18nManager(striga.server.service.Service):


	_qrg = re.compile(';\s*q=\s*(\d+|\d+\.\d+)\s*$')


	def __init__(self, parent, deflocale, name = "I18nManager", startstoppriority = 100):
		striga.server.service.Service.__init__(self, parent, name, startstoppriority)
		self._ChangeServiceStateToConfigured()
		self.DefaultLocaleName = deflocale 


	def __call__(self, ctx, path):
		self.ServiceStartCheck()

		sessionstore = hasattr(ctx,'Session')

		if sessionstore:
			loc = ctx.Session.Vars.get('_Locale', None)
			if loc is not None:
				ctx.Locale = ctx.Session.Vars.get('_Locale', None)
				self._ConfigureContextTranslation(ctx)
				return
		
		ctx.Locale = self._DetectLocale(ctx)

		if sessionstore:
			ctx.Session.Vars['_Locale'] = ctx.Locale
		
		self._ConfigureContextTranslation(ctx)


	def _ConfigureContextTranslation(self, ctx):
		ctx.Translation = self.ParentServiceRef().Translations[str(ctx.Locale)]


	def _DetectLocale(self, ctx):
		L.debug('Detecting request locale ...')

		allist = [] 
		for al in filter(lambda x: len(x) > 0, ','.join(ctx.req.Vars.HEADER.GetAll('HTTP_ACCEPT_LANGUAGE', '')).split(',')):
			qrgm = self._qrg.search(al)
			if qrgm is None:
				q = 1.0
			else:
				q = float(qrgm.group(1))
				al = al[:qrgm.start(0)]

			allist.append( (al, q) )

		allist.sort(key=lambda x: x[1], reverse=True)

		# Find matching locale
		loc = babel.Locale.negotiate([x[0] for x in allist], self.ParentServiceRef().Translations.keys())
		if loc is not None: return loc

		# Use default if none was found
		return self.DefaultLocale


	def _DoStart(self):
		try:
			if self.DefaultLocaleName is None:
				self.DefaultLocale = babel.Locale.default()
			else:
				self.DefaultLocale = babel.Locale(self.DefaultLocaleName)

		except babel.UnknownLocaleError:
			self.DefaultLocale = babel.Locale('en')
