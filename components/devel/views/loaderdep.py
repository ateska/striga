import logging as L
import striga.server.application

###

def main(ctx):
	app = striga.server.application.GetInstance()

	ctx.res.SetContentType('text/plain')
	ctx.res.SetContentType('application/octet-stream')
	ctx.res.CustomHTTPHeader.Set("Content-Disposition", "attachment", filename="loaderdep.dot")

	ctx.res.Write('digraph loaderdep {\n')
	ctx.res.Write('\tnode [shape=record, style=filled, fontname=Consolas];\n')

	for key, loadable in app.Services.Loader.IterLoaderCache():
		label = '{' + key[0].__name__
		for i in key[1:]:
			label += '|'
			label += str(i).replace('\\','/')
		label = label.replace('"',"'") + '}'

		if loadable.GetStatus() == loadable.States.Loaded:
			status = 'green'
		elif loadable.GetStatus() in (loadable.States.NotLoaded, loadable.States.NotFound) and loadable.GetError() is None:
			status = 'yellow'
		else:
			status = 'red'

		ctx.res.Write('\tLoadable%d [shape=record, color=%s, style=bold, label="%s"];\n' % (id(loadable) , status, label))

	for key, tloadable in app.Services.Loader.IterLoaderCache():
		for sloadable in tloadable.GetDependants():
			ctx.res.Write('\tLoadable%d -> Loadable%d;\n' % (id(sloadable), id(tloadable)))

	ctx.res.Write('}')
