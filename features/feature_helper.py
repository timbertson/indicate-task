import logging
logging.basicConfig(level=logging.DEBUG)

def assertEquals(actual, expected):
	if actual != expected:
		raise RuntimeError("expected %r, got: %r" % (expected, actual))
