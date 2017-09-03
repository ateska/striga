from striga.core.mvc import CallView
import striga.core.exception

###

class Controller(object):
	'''
	Inherit from this controller if you want to implement exiform controller

	Entry in site bus conf => controller(path='XXX', source='controller', rootdir='XXX', pathlimit="in (1,2)"):
	'''

	FormDescriptor = None # This class attribute must be overloaded by implementation (content is class of FormDescriptor subclass)

	ViewModeShowName = 'show'
	ViewModeEditName = 'edit'
	ViewModeNewName = 'new'

	DefaultViewMode = ViewModeShowName


	ExitURL = None			# This should be overloaded by implementation if it uses exit URLs; None means CGI/script mount point
	ControllerBaseURL = None	# This should be overloaded by implementation


	#TODO: Form items prefix (to allow two or more forms on the same screen)


	def SelectFromModel(self, ctx, objid): # This should be overloaded by implementation
		raise NotImplementedError()


	def InsertIntoModel(self, ctx): # This should be overloaded by implementation
		raise NotImplementedError()


	def UpdateToModel(self, ctx, objid, formd): # This should be overloaded by implementation
		#raise NotImplementedError()
		pass


	def DeleteFromModel(self, ctx, objid): # This should be overloaded by implementation
		raise NotImplementedError()


	def _CallView(self, ctx, formd):
		return CallView(formd=formd)


	def _ItemsFromRequest(self, ctx, objid):
		values = {self.FormDescriptor.IDItemDef.Name : objid}
		for a in self.FormDescriptor.ItemDefs:
			try:
				value = ctx.req.Vars.POST[a.Name]
			except KeyError:
				#TODO: Maybe we should throw better exception when value was not present
				raise striga.core.exception.StrigaBusError("NotFound")

			values[a.Name] = value
		return values


	def _HandleActionDelete(self, ctx, path, prevret):
		self.DeleteFromModel(ctx, prevret if prevret is not None else path[-1])


	def _HandleActionInsert(self, ctx, path, prevret):
		# First step is to read data from form descriptor ...
		formd = self.FormDescriptor(self, "new")
		formd.InitItems(self._ItemsFromRequest(ctx, objid))

		# Second step is to validate them
		#TODO: ...

		return self.InsertIntoModel(ctx) # This should return new id for eventual redirect to that resource


	def _HandleActionUpdate(self, ctx, path, prevret):
		objid = prevret if prevret is not None else path[-1]

		# First step is to read data from form descriptor ...
		formd = self.FormDescriptor(self, "edit")
		formd.InitItems(self._ItemsFromRequest(ctx, objid))

		# Second step to to validate and transform (change type to appropriate one) them
		formd.ValidateAndTransform(ctx)

		self.UpdateToModel(ctx, objid, formd)


	def _HandleActionCancel(self, ctx, path, prevret):
		pass


	def _RedirectTo(self, ctx, url):
		'''
The response to the request can be found under a different URI and SHOULD be retrieved using a GET method on that resource.
This method exists primarily to allow the output of a POST-activated script to redirect the user agent to a selected resource.
The new URI is not a substitute reference for the originally requested resource.
The 303 response MUST NOT be cached, but the response to the second (redirected) request might be cacheable.

The different URI SHOULD be given by the Location field in the response.
Unless the request method was HEAD, the entity of the response SHOULD contain a short hypertext note with a hyperlink to the new URI(s).

      Note: Many pre-HTTP/1.1 user agents do not understand the 303
      status. When interoperability with such clients is a concern, the
      302 status code may be used instead, since most user agents react
      to a 302 response as described here for 303.
      		'''

		if url is None:
			#TODO: This will probably not work on lighttpd
			url = ctx.req.Vars.HEADER['SCRIPT_NAME']

		if url[0] == '/':
			#TODO: HTTPS support !
			url = "http://" + ctx.req.Vars.HEADER['HTTP_HOST'] + url

		if ctx.req.Vars.HEADER['SERVER_PROTOCOL'] == 'HTTP/1.0':
			raise striga.core.exception.StrigaClientFound(url)
		else:
			raise striga.core.exception.StrigaClientSeeOther(url)


	def _HandleRedirectToExit(self, ctx, path, prevret):
		self._RedirectTo(ctx, self.ExitURL)


	def _HandleRedirectToNew(self, ctx, path, prevret):
		self._RedirectTo(ctx, self.ControllerBaseURL + '/' + self.ViewModeNewName)


	def _HandleRedirectToEdit(self, ctx, path, prevret):
		self._RedirectTo(ctx, self.ControllerBaseURL + '/' + self.ViewModeEditName + '/' + str(prevret if prevret is not None else path[-1]))


	def _HandleRedirectToShow(self, ctx, path, prevret):
		self._RedirectTo(ctx, self.ControllerBaseURL + '/' + self.ViewModeShowName + '/' + str(prevret if prevret is not None else path[-1]))


	ActionMap = {
		'_action-delete': (_HandleActionDelete, _HandleRedirectToExit),

		'_action-insert-exit' : (_HandleActionInsert, _HandleRedirectToExit),
		'_action-insert-new'  : (_HandleActionInsert, _HandleRedirectToNew),
		'_action-insert-edit' : (_HandleActionInsert, _HandleRedirectToEdit),
		'_action-insert-show' : (_HandleActionInsert, _HandleRedirectToShow),

		'_action-update-exit' : (_HandleActionUpdate, _HandleRedirectToExit),
		'_action-update-edit' : (_HandleActionUpdate, _HandleRedirectToEdit),
		'_action-update-show' : (_HandleActionUpdate, _HandleRedirectToShow),

		'_action-cancel-exit' : (_HandleActionCancel, _HandleRedirectToExit),
		'_action-cancel-edit' : (_HandleActionCancel, _HandleRedirectToEdit),
		'_action-cancel-show' : (_HandleActionCancel, _HandleRedirectToShow),
		}


	def _HandlePOST(self, ctx, path):

		actionname = None
		for n,v in ctx.req.Vars.POST.iteritems():
			if n.find('_action-') != 0: continue
			if len(v) == 0: continue

			#TODO: Test this with Internet Explorer
			actionname = n
			break

		if actionname is None:
			raise striga.core.exception.StrigaBusError("NotFound")


		acs = self.ActionMap.get(actionname, None)
		if acs is None:
			raise striga.core.exception.StrigaBusError("NotFound")

		ret = None
		for ac in acs:
			ret = ac(self, ctx, path, ret)

		if ret is not None:
			return ret
		else:
			raise striga.core.exception.StrigaBusError("NotFound")


	def _HandleShowViewMode(self, ctx, objid):
		formd = self.FormDescriptor(self, "show")
		formd.InitItems(self.SelectFromModel(ctx, objid))
		return self._CallView(ctx, formd)


	def _HandleEditViewMode(self, ctx, objid):
		formd = self.FormDescriptor(self, "edit")
		formd.InitItems(self.SelectFromModel(ctx, objid))
		return self._CallView(ctx, formd)


	def _HandleNewViewMode(self, ctx):
		formd = self.FormDescriptor(self, "new")
		formd.InitItemsAsNew(ctx)
		return self._CallView(ctx, formd)


	def _HandleGET(self, ctx, path):
		pathlen = len(path)
		path0 = path[0]

		if pathlen == 2:
			if path0 == self.ViewModeShowName:
				return self._HandleShowViewMode(ctx, path[1])
			elif path0 == self.ViewModeEditName:
				return self._HandleEditViewMode(ctx, path[1])
			else:
				raise striga.core.exception.StrigaBusError("NotFound")
		elif pathlen == 1:
			if path0 == self.ViewModeNewName:
				return self._HandleNewViewMode(ctx)
			else:
				if self.DefaultViewMode == self.ViewModeEditName:
					return self._HandleEditViewMode(ctx, path0)
				else:
					return self._HandleShowViewMode(ctx, path0)
		else:
			raise striga.core.exception.StrigaBusError("NotFound")


	def __call__(self, ctx, path):
		if ctx.req.Method == 'POST':
			return self._HandlePOST(ctx, path)
		elif ctx.req.Method == 'GET':
			return self._HandleGET(ctx, path)
		else:
			raise striga.core.exception.StrigaBusError("NotFound")
