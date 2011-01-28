from pea import *
from base_test import BaseTest

class TestDisplayingOutput(BaseTest):
	"""
	I want to see command output when a task is running
	"""

	def test_displaying_output_of_a_still_running_command(self):
		When.I_run_indicate_task('--', 'cat')
		And.I_enter("input")
		And.I_show_the_output_of_the_task()
		Then.the_output_is_shown_with("input")

		When.I_enter("second_line")
		Then.the_output_is_shown_with("input\nsecond line")

		Then.I_press_ctrl_d()
		And.I_wait_for_the_task_to_complete()

		And.it_should_have_shown_the_output_once()

	def test_not_capturing_output(self):
		When.I_run_indicate_task('--no-capture', '--', 'cat')
		And.I_enter("input")
		Then.it_should_not_capture_any_output()
		And.I_press_ctrl_d()

