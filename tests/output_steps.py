from pea import step, world
from indicate_task import main as indicate_task_main

@step
def I_show_the_output_of_the_task():
	indicate_task_main.OUTPUT.show()

class Object(object): pass
@step
def the_output_is_shown_with(expected_lines):
	lines = world.popen['zenity'].stdin.getvalue().rstrip()
	print repr(lines)
	# ignore the two-line header
	lines = "\n".join(lines.splitlines()[2:])
	world.assertEquals(lines, expected_lines)

@step
def it_should_have_shown_the_output_once():
	assert len(world.popen.zenities) == 1, world.popen.zenities

@step
def it_should_not_capture_any_output():
	assert indicate_task_main.OUTPUT is None

@step
def the_output_should_be(match):
	world.assertEquals(world.stdout, match)

@step
def the_error_output_should_be(match):
	world.assertEquals(world.stderr, match)

@step
def the_error_output_should_be_empty():
	the_error_output_should_be('')

@step
def it_should_display_the_tasks_output_to_the_user():
	assert "Output from " in world.popen['zenity'].stdin.getvalue()

@step
def it_should_not_display_the_tasks_output_to_the_user():
	assert 'zenity' not in world.popen

