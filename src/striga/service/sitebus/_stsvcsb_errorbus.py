from ._stsvcsb_bus import Bus

###

class ErrorBus(Bus):

	def __call__(self, ctx, exc):
		path = [exc]
		Bus.__call__(self, ctx, path)
