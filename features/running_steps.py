from lettuce import step, world, after
import os, sys
from feature_helper import *

import indicate_task
import signal
from StringIO import StringIO
import threading, Queue
import subprocess
from time import sleep
import appindicator
RealAppIndicator = appindicator.Indicator
RealPopen = subprocess.Popen
RealSys = sys
input_wait_time = 0.2
sleep_time = 0.2


class Object(object): pass

class MockAppIndicator(object):
	instance = None
	def __call__(self, *a, **k):
		assert self.instance is None
		self.instance = RealAppIndicator(*a, **k)
		self.menu_description = None
		self.icon = None
		self.label = None
		return self
	
	def set_label(self, l):
		self.label = l
		self.instance.set_label(l)
	
	def set_icon(self, i):
		self.set_icon(i)
		self.instance.set_icon(i)
	
	def set_menu(self, m):
		self.menu_description = m.get_children()[0].get_label()
		# a bug in (presumably) appindicator causes a dbus error when you do this
		# twice in a process. Fortunately non-test code never does so
		pass
	
	def __getattr__(self, attr):
		return getattr(self.instance, attr)

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
		elif self.cmd[0] == 'notify-send':
			self.proc = MockNotify(self.cmd)
		else:
			k['stdin'] = subprocess.PIPE
			self.proc = RealPopen(*a, **k)

	def __getattr__(self, name):
		return getattr(self.proc, name)

	def __repr__(self):
		return "<#MockChildProcess: %r>" % (self.cmd,)

class MockNotify(object):
	def __init__(self, args):
		pass

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

@step(u'I run indicate-task (.*)')
def when_i_run_indicate_task(step, cmd):
	world.returncode_queue = returncode_queue = Queue.Queue()
	world.popen = popen = MockPopen()
	running = threading.Event()
	world.indicator = indicator = MockAppIndicator()
	world.sys = mock_sys = MockSys()
	if '$pid' in cmd:
		cmd = cmd.replace('$pid', str(world.external_process.pid))
	class Run(threading.Thread):
		daemon = True
		def run(self):
			args = cmd.split()
			indicate_task.appindicator.Indicator = indicator
			indicate_task.sys = mock_sys
			indicate_task.subprocess.Popen = popen
			real_main = indicate_task.gtk.main
			def _stub_main(*a):
				running.set()
				real_main()
			indicate_task.gtk.main = _stub_main
			returncode_queue.put(indicate_task.main(map(str, args)))
	world.run = Run()
	world.run.start()
	running.wait()

@after.each_feature
def after_feature(feature):
	try:
		world.external_process.kill()
	except AttributeError:
		pass

@step(u'When I run ([^ ]*)$')
def when_i_run(step, cmd):
	proc = subprocess.Popen(cmd.split(), stdin=subprocess.PIPE, stdout=subprocess.PIPE)
	world.external_process = proc

@step(u'And I wait for the task to complete')
def and_i_wait_for_the_task_to_complete(step):
	world.run.join()
	world.stdout = world.sys.stdout.value.rstrip()
	world.stderr = world.sys.stderr.value.rstrip()
	world.returncode = world.returncode_queue.get()

@step(u'Then there should be a "(.*)" indicator')
def then_there_should_be_a_group1_indicator(step, group1):
	print repr(world.indicator)
	assert world.indicator.label == group1, world.indicator.label

@step(u'And it should notify the user of the task\'s completion')
def and_it_should_notify_the_user_of_the_task_s_completion(step):
	assert world.popen['notify-send']

@step(u'it should not notify the user of the task\'s completion')
def and_it_should_not_notify_the_user_of_the_task_s_completion(step):
	assert 'notify-send' not in world.popen

@step(u'And the return code should not be 0')
def and_the_return_code_should_not_be_0(step):
	assert world.returncode != 0

@step(u'And the return code should be 0')
def and_the_return_code_should_be_0(step):
	assert world.returncode == 0

@step(u'And it should have no icon')
def and_it_should_have_no_icon(step):
	assert world.indicator.icon is None

@step(u'And it should have a menu description of "(.*)"')
def and_it_should_have_a_menu_description_of_group1(step, group1):
	assert world.indicator.menu_description == group1

@step(u'Then I kill \$pid')
def then_i_kill_pid(step):
	print "killing: %s" % (world.external_process.pid)
	world.external_process.kill()
	world.external_process.wait()
	print "done"
	del world.external_process
