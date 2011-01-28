#!/usr/bin/env python
#
# Copyright 2009 Canonical Ltd, 2011 Tim Cuthbertson
#
# Authors: Tim Cuthbertson <tim@gfxmonk.net>
#          Neil Jagdish Patel <neil.patel@canonical.com>
#          Jono Bacon <jono@ubuntu.com>
#
# This program is free software: you can redistribute it and/or modify it 
# under the terms of either or both of the following licenses:
#
# 1) the GNU Lesser General Public License version 3, as published by the 
# Free Software Foundation; and/or
# 2) the GNU Lesser General Public License version 2.1, as published by 
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but 
# WITHOUT ANY WARRANTY; without even the implied warranties of 
# MERCHANTABILITY, SATISFACTORY QUALITY or FITNESS FOR A PARTICULAR 
# PURPOSE.	See the applicable version of the GNU Lesser General Public 
# License for more details.
#
# You should have received a copy of both the GNU Lesser General Public 
# License version 3 and version 2.1 along with this program.	If not, see 
# <http://www.gnu.org/licenses/>
#

import gobject
gobject.threads_init()

import gtk
import appindicator
import optparse
import threading
from StringIO import StringIO
import sys
import os
import subprocess
import logging

def init_globals():
	global QUIT, ALREADY_QUITTING, CANCELLED, CHILD, OPTS, OUTPUT
	QUIT = threading.Event()
	ALREADY_QUITTING = threading.Event()
	CANCELLED = threading.Event()
	CHILD = None
	OPTS = None
	OUTPUT = None
	logging.basicConfig(level=logging.INFO)

class ExistingProcess(object):
	def __init__(self, pid):
		self.pid = pid
		self.returncode = 0 # can't get return code of another process
	
	def wait(self):
		import signal
		from time import sleep
		while True:
			try:
				os.kill(self.pid, signal.SIG_DFL)
			except OSError:
				break
			sleep(1)

	def kill(self):
		import signal
		os.kill(self.pid, signal.SIGINT)
	
def cancel(*a):
	print >> sys.stderr, "killing: %s" % (CHILD.pid,)
	CANCELLED.set()
	CHILD.kill()

def display_text(s):
	p = subprocess.Popen(['zenity', '--text-info', '--width=600', '--height=400'], stdin=subprocess.PIPE)
	p.stdin.write(s)
	return p

class Output(object):
	def __init__(self, child):
		self.combined = StringIO()
		self.lock = threading.RLock()
		self.display = None

		StreamReader(child.stdout, sys.stdout, self).start()
		StreamReader(child.stderr, sys.stderr, self).start()
	
	def add(self, line):
		with self.lock:
			self.combined.write(line)
			if self.display_running:
				self.display.stdin.write(line)
	
	@property
	def display_running(self):
		with self.lock:
			if self.display:
				self.display.poll()
				return self.display.returncode is None
			return False

	def show(self, *a):
		with self.lock:
			s = self.combined.getvalue()
			logging.debug("showing output: %s" % (s,))
			s = "Output from %s (%s)\n____\n%s" % (OPTS.description or 'command', ' '.join(map(repr, CMD)),s)
			self.display = display_text(s)

class Cancel(RuntimeError): pass

def launch(args):
	global CHILD, OUTPUT
	if OPTS.pid:
		CHILD = ExistingProcess(OPTS.pid)
	else:
		try:
			CHILD = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		except OSError, e:
			msg = "Couldn't launch task: %s\ndoes %r exist?\n  -- %s" % (" ".join(map(repr, args)), args[0], e)
			logging.debug(msg)
			display_text(msg)
			raise Cancel
		if OPTS.capture_output:
			OUTPUT = Output(CHILD)

	WatchForEnd(CHILD).start()

class StreamReader(threading.Thread):
	daemon = True
	def __init__(self, instream, outstream, output, *a, **kw):
		self.instream = instream
		self.outstream = outstream
		self.output = output
		super(StreamReader, self).__init__(*a, **kw)

	def run(self):
		for line in self.instream:
			print >> self.outstream, line,
			self.output.add(line)

class WatchForEnd(threading.Thread):
	def __init__(self, child, *a, **kw):
		self.child = child
		super(WatchForEnd, self).__init__(*a, **kw)
	
	def run(self):
		try:
			self.child.wait()
		finally:
			QUIT.set()

class WaitForQuit(threading.Thread):
	daemon = True
	def run(self):
		QUIT.wait()
		def _quit(*a):
			if ALREADY_QUITTING.is_set():
				return
			ALREADY_QUITTING.set()
			gtk.main_quit()
		gobject.idle_add(_quit)

def notify(opts):
	if CANCELLED.is_set():
		return
	if CHILD.returncode != 0 and OPTS.show_errors:
		OUTPUT.show()
	if not OPTS.notify:
		return
	subprocess.Popen([
		'notify-send',
		OPTS.description or 'task',
		"Finished %s" % ('successfully' if CHILD.returncode == 0 else ('with error code %s' % (CHILD.returncode,))),
	])

def main(args=None):
	init_globals()
	global CMD, OPTS
	if args is None:
		args = sys.argv[1:]
	p = optparse.OptionParser(
		"usage: indicate-task [options] -- command-and-arguments",
		epilog="eg: indicate-task -d download -- curl 'http://example.com/bigfile'")
	p.add_option('--style', default='network-transmit-receive')
	p.add_option('--long-description', default=None, help='set long description (visible in popup menu)')
	p.add_option('-d', '--description', default=None, help='set description (visible in tray, defaults to command executable)')
	p.add_option('-p', '--pid', default=None, type='int', help='attach to an already-running PID')
	p.add_option('--id', default=None, help='set application ID (defaults to description)')
	p.add_option('--no-icon', dest='style', action='store_const', const='', help="don't use an icon")
	p.add_option('--no-notify', dest='notify', action='store_false', default=True, help="suppress completion notification")
	p.add_option('--no-capture', dest='capture_output', action='store_false', default=True, help="suppress output capture")
	p.add_option('--ignore-errors', action='store_false', dest='show_errors', default=True, help="Suppress automatic output display when process returns nonzero error code")
	OPTS, CMD = p.parse_args(args)

	if OPTS.pid:
		OPTS.capture_output = False
	else:
		assert len(CMD) > 0
		if OPTS.description is None:
			OPTS.description = os.path.basename(CMD[0])

	if not OPTS.id:
		OPTS.id = str(OPTS.description)

	if not OPTS.long_description and OPTS.description:
		OPTS.long_description = OPTS.description + ": running..."

	ind = appindicator.Indicator(OPTS.id,
		OPTS.style,
		appindicator.CATEGORY_APPLICATION_STATUS)

	ind.set_status(appindicator.STATUS_ACTIVE)
	if OPTS.description:
		try:
			ind.set_label(OPTS.description)
		except (AttributeError, RuntimeError):
			print >> sys.stderr, "Unable to set label - your libindicator version may be too old. use -d'' to disable this message"

	launch(CMD)

	items = []
	if OPTS.capture_output:
		show_log_menu = gtk.MenuItem("Show output...")
		show_log_menu.connect("activate", OUTPUT.show, None)
		items.append(show_log_menu)
		items.append(gtk.MenuItem())

	cancel_menu = gtk.MenuItem("Cancel")
	cancel_menu.connect("activate", cancel, None)
	items.append(cancel_menu)

	# show all items
	menu = gtk.Menu()

	if OPTS.long_description:
		label = gtk.MenuItem(OPTS.long_description)
		label.set_sensitive(False)
		items.insert(0, label)

	for item in items:
		menu.append(item)
		item.show()
	ind.set_menu(menu)

	WaitForQuit().start()
	try:
		gtk.main()
	except KeyboardInterrupt:
		if OPTS.pid is None:
			print >> sys.stderr, "ending..."
			cancel()
	except Exception:
		QUIT.set()
		if OPTS.verbose:
			raise

	CHILD.wait()
	notify(OPTS)
	return CHILD.returncode

if __name__ == "__main__":
	try:
		sys.exit(main())
	except (KeyboardInterrupt, EOFError, Cancel), e:
		sys.exit(1)
	except Exception, e:
		import traceback
		trace = traceback.format_exc()
		display_text(trace)
