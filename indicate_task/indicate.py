import sys

REQUIRED_CAPABILITIES = ('actions', 'persistence')
class NoSuitableImplementation(StandardError): pass

class Indicator(object):
	def __new__(cls, *a, **k):
		if cls is Indicator:
			import pynotify
			capabilities = set(pynotify.get_server_caps())
			if set(REQUIRED_CAPABILITIES).issubset(capabilities):
				cls = PyNotifyIndicator
			else:
				try:
					import appindicator
				except ImportError:
					raise NoSuitableImplementation("the `appindicator` module was not found (try installing python-appindicator?)\n"
						"And your notification server lacks the required capabilities for this program.\n"
						"I need: %r\nbut you only have: %r" % (REQUIRED_CAPABILITIES, tuple(pynotify.get_server_caps())))
				cls = AppIndicator
			return super(Indicator, cls).__new__(cls)

	def __init__(self, name, description, icon, id=None):
		self.name = name
		self.description = description
		self.icon = icon
		self.actions = []
		self.id = id or str(name)
		self.indicator = self._make_indicator()

	def add_action(self, name, callback):
		self.actions.append((name, lambda *a: callback()))

	def show(self):
		pass

	def close(self):
		pass

class PyNotifyIndicator(Indicator):
	def _make_indicator(self):
		import pynotify
		pynotify.init(self.id)
		indicator = pynotify.Notification(self.name, self.description, self.icon)
		indicator.set_hint_double('resident', 1)
		return indicator
	
	def show(self):
		for name, action in self.actions:
			self.indicator.add_action(name, name, action, None)
		self.indicator.show()
	
	def close(self):
		self.indicator.close()

class AppIndicator(Indicator):
	def _make_indicator(self):
		import appindicator
		indicator = appindicator.Indicator(self.id,
			self.icon,
			appindicator.CATEGORY_APPLICATION_STATUS)

		indicator.set_status(appindicator.STATUS_ACTIVE)
		if self.description is not None:
			try:
				indicator.set_label(self.name)
			except (AttributeError, RuntimeError):
				print >> sys.stderr, "Warning: Unable to set label - your libindicator version may be too old."
		return indicator

	def show(self):
		import gtk
		if not (self.actions or self.description): return
		menu = gtk.Menu()
		if self.description:
			label = gtk.MenuItem(self.description)
			label.set_sensitive(False)
			label.show()
			menu.append(label)
		for name, action in self.actions:
			item = gtk.MenuItem(name)
			item.connect('activate', action, None)
			item.show()
			menu.append(item)
		self.indicator.set_menu(menu)
	
	def close(self):
		#TODO
		pass
