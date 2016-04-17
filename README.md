indicate-task
=============

<img src="http://gfxmonk.net/dist/status/project/indicate-task.png">

A command line tool that displays an indicator / persistent
notification for the duration of a long-running process (a task).

It has been tested on Ubuntu 10.10 and Fedora 15, but other distros
may not yet have the required support in libnotify / appindicators.

It can also notify you when the task is complete, and allows you to
cancel the task or view its output while it is running.

indicate-task echoes stdin to stdout as well as capturing it, so you
can wrap a program in an indicator and still get the same output /
return code.

**Note**: indicate task requires the `python-appindicator` package
on Ubuntu. I can't add this to the feed's dependency list, as it
doesn't exist (and isn't needed) in any other distro.

------------------------------

## Usage:

