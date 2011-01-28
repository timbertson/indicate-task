from lettuce import step, world
import indicate_task
from feature_helper import *
from time import sleep

@step(u'And I show the output of the task')
def and_i_show_the_output_of_the_task(step):
	indicate_task.OUTPUT.show()

@step(u'Then the output is shown with (\d+) lines?')
def then_the_output_is_shown_with_n_lines(step, n):
	n = int(n)
	lines = world.popen['zenity'].stdin.getvalue().splitlines()
	print repr(lines)
	# ignore the two-line header
	lines = lines[2:]
	assertEquals(len(lines), n)

@step(u'And it should have shown the output once')
def and_it_should_have_shown_the_output_once(step):
	assert len(world.popen.zenities) == 1, world.popen.zenities

@step(u'Then it should not capture any output')
def then_it_should_not_capture_any_output(step):
	assert indicate_task.OUTPUT is None

@step(u'And the output should be: (.*)')
def and_the_output_should_be(step, match):
	assertEquals(world.stdout, match)

@step(u'And the error output should be: (.*)')
def and_the_error_output_should_be(step, match):
	assertEquals(world.stderr, match)

@step(u'And the error output should be empty')
def and_the_error_output_should_be_empty(step):
	step.behave_as('And the error output should be: ')

@step(u'And it should display the task\'s output to the user')
def and_it_should_display_the_task_s_output_to_the_user(step):
	assert "Output from " in world.popen['zenity'].stdin.getvalue()

@step(u'And it should not display the task\'s output to the user')
def and_it_should_not_display_the_task_s_output_to_the_user(step):
	assert 'zenity' not in world.popen

