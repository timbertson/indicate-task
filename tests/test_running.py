from pea import *
from base_test import BaseTest

class TestRunning(BaseTest):
	"""
	Feature: Running a basic, blocking process that
	consumes and produces output.
	"""

	def test_running_and_cancelling_a_program(self):
		When.I_run_indicate_task('--', 'cat')
		And.I_enter("input")
		And.I_press_ctrl_c()
		And.I_wait_for_the_task_to_complete()
		Then.there_should_be_an_indicator_named("cat")
		And.it_should_have_a_description_of("cat: running...")
		And.the_output_should_be('input')
		And.the_error_output_should_be_empty()
		And.the_return_code_should_not_be(0)
		And.it_should_display_the_tasks_output_to_the_user()
		And.it_should_notify_the_user_of_the_tasks_completion()

	def test_running_a_program_that_successfully_completes(self):
		When.I_run_indicate_task('--','cat')
		And.I_enter("input")
		And.I_press_ctrl_d()
		And.I_wait_for_the_task_to_complete()

		Then.there_should_be_an_indicator_named('cat')
		And.the_output_should_be("input")
		And.the_error_output_should_be_empty()
		And.the_return_code_should_be(0)
		And.it_should_not_display_the_tasks_output_to_the_user()
		And.it_should_notify_the_user_of_the_tasks_completion()



