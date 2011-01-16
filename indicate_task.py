#!/usr/bin/env python
#
# Copyright 2009 Canonical Ltd.
#
# Authors: Neil Jagdish Patel <neil.patel@canonical.com>
#          Jono Bacon <jono@ubuntu.com>
#          Tim Cuthbertson <tim@gfxmonk.net>
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
import StringIO
import sys
import subprocess

lock = threading.RLock()
output = StringIO.StringIO()
quit = threading.Event()
already_quitting = threading.Event()
child = None
cmd = None
opts = None

def cancel(*a):
	print >> sys.stderr, "killing: %s" % (child.pid,)
	child.kill()

def show_log(*a, **kw):
	with lock:
		s = output.getvalue()
	s = "Output from %s (%s)\n____\n%s" % (opts.description or 'command', ' '.join(map(repr, cmd)),s)
	display = subprocess.Popen(['zenity', '--text-info', '--width=600', '--height=400'], stdin=subprocess.PIPE)
	display.stdin.write(s)
	display.stdin.close()

def launch(args):
	global child
	child = subprocess.Popen(args, stdout=subprocess.PIPE)
	StdinReader(child.stdout).start()

class StdinReader(threading.Thread):
	daemon = True
	def __init__(self, file, *a, **kw):
		self.file = file
		super(StdinReader, self).__init__(*a, **kw)

	def run(self):
		try:
			while True:
				line = self.file.readline()
				if line == '':
					raise EOFError()
				print line,
				with lock:
					output.write(line)
		except EOFError:
			quit.set()

class WaitForQuit(threading.Thread):
	daemon = True
	def run(*a):
		quit.wait()
		def _quit(*a):
			if already_quitting.is_set():
				return
			already_quitting.set()
			gtk.main_quit()
		gobject.idle_add(_quit)

def notify(opts):
	if child.returncode != 0:
		show_log()
	if not opts.notify:
		return
	subprocess.Popen([
		'notify-send',
		opts.long_description or opts.description or 'task',
		"Finished %s" % ('successfully' if child.returncode == 0 else ('with error code %s' % (child.returncode,))),
	])

def main():
	global cmd, opts
	p = optparse.OptionParser(
		"usage: indicate-task [options] -- command-and-arguments",
		epilog="eg: indicate-task -d download -- curl 'http://example.com/bigfile'")
	p.add_option('--style', default='network-transmit-receive')
	p.add_option('--long-description', default=None, help='set long description (visible in popup menu)')
	p.add_option('-d', '--description', default=None, help='set description (visible in tray)')
	p.add_option('--id', default=None, help='set application ID (defaults to description or a random string if no description given)')
	p.add_option('--no-icon', dest='style', action='store_const', const='', help="don't use an icon")
	p.add_option('--no-notify', dest='notify', action='store_false', default=True, help="suppress completion notification")
	p.add_option('--ignore-errors', action='store_false', dest='show_errors', default=True, help="Suppress automatic output display when process returns nonzero error code")
	opts, cmd = p.parse_args()

	assert len(cmd) > 0
	if not opts.id:
		if opts.description:
			opts.id = opts.description
		else:
			# assign a random ID
			import random
			random.seed()
			opts.id = "indicate-task__%s" % (random.randrange(10,99),)

	if not opts.long_description and opts.description:
		opts.long_description = opts.description + ": running..."

	ind = appindicator.Indicator(opts.id,
		opts.style,
		appindicator.CATEGORY_APPLICATION_STATUS)

	ind.set_status(appindicator.STATUS_ACTIVE)
	if opts.description:
		ind.set_label(opts.description)

	items = []
	show_log_menu = gtk.MenuItem("Show output...")
	show_log_menu.connect("activate", show_log, None)
	items.append(show_log_menu)
	items.append(gtk.MenuItem())

	cancel_menu = gtk.MenuItem("Cancel")
	cancel_menu.connect("activate", cancel, None)
	items.append(cancel_menu)

	# show all items
	menu = gtk.Menu()

	if opts.long_description:
		label = gtk.MenuItem(opts.long_description)
		label.set_sensitive(False)
		items.insert(0, label)

	for item in items:
		menu.append(item)
		item.show()
	ind.set_menu(menu)

	launch(cmd)
	WaitForQuit().start()
	try:
		gtk.main()
	except KeyboardInterrupt:
		print >> sys.stderr, "ending..."
		cancel()
	except Exception:
		quit.set()
		if opts.verbose:
			raise

	child.wait()
	notify(opts)
	return child.returncode

if __name__ == "__main__":
	sys.exit(main())
