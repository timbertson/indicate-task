from pea import step, world
import os, sys
import signal
from StringIO import StringIO
import threading, Queue
import subprocess
from time import sleep

import pynotify

from indicate_task import main
from indicate_task.indicate import Indicator

RealPopen = subprocess.Popen
RealSys = sys
input_wait_time = 0.2
sleep_time = 0.2


class Object(object): pass

class MockIndicator(Indicator):
	def __init__(self, *a, **k):
		self.real_indicator = Indicator(*a, **k)
		super(MockIndicator, self).__init__(*a, **k)
		world.indicator = self

	def _make_indicator(self):
		pass

class MockSys(object):
	def __init__(self):
		#self.stdin = Stream()
		self.stdout = Stream()
		self.stderr = Stream()

class Stream(object):
	def __init__(self):
		self.value = ""
		self.queue = Queue.Queue()
		self.eof = threading.Event()
	
	def write(self, s):
		lines = s.splitlines()
		map(self.queue.put, lines)
		self.value += s
	
	@property
	def empty(self):
		return self.queue.empty()

	def wait_until_empty(self):
		if self.queue.empty():
			return
		sleep(sleep_time)
	
	def __iter__(self):
		while True:
			try:
				yield self.queue.get(False, 1)
			except Queue.Empty:
				if self.eof.is_set():
					raise StopIteration()
	
class MockPopen(object):
	def __init__(self):
		self.children = []
	
	def __call__(self, *a, **k):
		child = MockChildProcess(*a, **k)
		self.children.append(child)
		return child

	def __contains__(self, cmd):
		try:
			self[cmd]
			return True
		except KeyError:
			return False

	@property
	def zenities(self):
		return filter(lambda x: isinstance(x.proc, MockZenity), self.children)

	def __getitem__(self, cmd):
		tries = 0
		maxtries = 5
		def get():
			if isinstance(cmd, int):
				return self.children[cmd]
			else:
				return filter(lambda child: child.cmd[0] == cmd, self.children)[0]

		while True:
			tries += 1
			try:
				return get()
			except IndexError:
				if tries >= maxtries:
					cmds = map(lambda child: child.cmd[0], self.children)
					raise KeyError("No such task found (%s). Current processes are: %s" % (
						cmd, ", ".join(cmds)))
				else:
					sleep(sleep_time)
	
class MockChildProcess(object):
	def __init__(self, *a, **k):
		self.cmd = a[0]
		self.args = a
		self.kwargs = a
		if self.cmd[0] == 'zenity':
			# stub out zenity, as it's not part of the test
			self.proc = MockZenity(self.cmd)
		else:
			k['stdin'] = subprocess.PIPE
			self.proc = RealPopen(*a, **k)

	def __getattr__(self, name):
		return getattr(self.proc, name)

	def __repr__(self):
		return "<#MockChildProcess: %r>" % (self.cmd,)

class MockNotify(object):
	def __init__(self, name, desc, icon):
		self.name = name
		self.description = desc
		self.icon = icon
		self.notification = pynotify.Notification(name, desc, icon)
		self.hints = {}
	
	def show(self):
		world.notifications.append(self)
		self.notification.show()
	
	def set_hint_double(self, name, value):
		self.hints[name] = value
		self.notification.set_hint_double(name, value)
	
	def set_timeout(self, millis):
		self.timeout_in_millis = millis

class MockZenity(object):
	def __init__(self, args):
		self.args = args
		self.stdin = StringIO()
		self.done = threading.Event()
	
	def finish(self):
		self.done.set()
	
	def poll(self):
		if self.done.is_set():
			return 0

	@property
	def returncode(self):
		return self.poll()


@step
def I_run_indicate_task(*args):
	world.returncode_queue = returncode_queue = Queue.Queue()
	world.popen = popen = MockPopen()
	running = threading.Event()
	world.sys = mock_sys = MockSys()
	world.notifications = []
	class Run(threading.Thread):
		daemon = True
		def run(self):
			main.Indicator = MockIndicator
			main.Notification = MockNotify
			main.sys = mock_sys
			main.subprocess.Popen = popen
			real_main = main.gtk.main
			def _stub_main(*a):
				running.set()
				real_main()
			main.gtk.main = _stub_main
			returncode_queue.put(main.main(map(str, args)))
	world.run = Run()
	world.run.start()
	running.wait()

@step
def I_run(*args):
	proc = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
	world.external_process = proc

@step
def I_wait_for_the_task_to_complete():
	world.run.join()
	world.stdout = world.sys.stdout.value.rstrip()
	world.stderr = world.sys.stderr.value.rstrip()
	world.returncode = world.returncode_queue.get()

@step
def there_should_be_an_indicator_named(name):
	world.assertEquals(world.indicator.name, name)

@step
def it_should_notify_the_user_of_the_tasks_completion():
	assert len(world.notifications) >= 1, world.notifications

@step
def it_should_not_notify_the_user_of_the_tasks_completion():
	assert len(world.notifications) == 0, world.notifications

@step
def the_return_code_should_not_be(code):
	assert world.returncode != code

@step
def the_return_code_should_be(code):
	assert world.returncode == code

@step
def it_should_have_no_icon():
	assert world.indicator.icon is None

@step
def it_should_have_a_description_of(group1):
	assert world.indicator.description == group1

@step
def I_kill_the_external_process():
	print "killing: %s" % (world.external_process.pid,)
	world.external_process.kill()
	world.external_process.wait()
	print "done"
	del world.external_process
