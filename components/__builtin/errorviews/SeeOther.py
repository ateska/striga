import logging as L

def main(ctx, path):
	ctx.res.Status = 303
	ctx.res.CustomHTTPHeader.Set('Location', ctx.err.excvalue.URL)
	ctx.res.SetContentType(None)
	ctx.res.SetContentLength(None)
