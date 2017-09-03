import logging as L

def main(ctx, path):
	ctx.res.Status = 307
	ctx.res.CustomHTTPHeader.Set('Location', ctx.err.excvalue.URL)
	ctx.res.SetContentType(None)
	ctx.res.SetContentLength(None)
