from pea import *
from base_test import BaseTest

class CustomisingBehaviour(BaseTest):
	"""
	I want to be able to customise the appearance and
	behaviour of an indicator
	"""

	def test_suppressing_notification(self):
		When.I_run_indicate_task('--no-notify', '--', 'cat')
		And.I_press_ctrl_d()
		And.I_wait_for_the_task_to_complete()
		Then.it_should_not_notify_the_user_of_the_tasks_completion()

	def test_suppressing_errors(self):
		When.I_run_indicate_task('--ignore-errors', '--', 'cat')
		And.I_press_ctrl_c()
		And.I_wait_for_the_task_to_complete()
		And.it_should_not_display_the_tasks_output_to_the_user()

	def test_setting_a_label(self):
		When.I_run_indicate_task('-d', 'catty', '--', 'cat')
		And.I_press_ctrl_d()
		And.I_wait_for_the_task_to_complete()
		Then.there_should_be_an_indicator_named('catty')

	def test_no_icon(self):
		When.I_run_indicate_task('--no-icon', '--', 'cat')
		And.I_press_ctrl_d()
		And.I_wait_for_the_task_to_complete()
		Then.there_should_be_an_indicator_named('cat')
		And.it_should_have_no_icon()

	def test_long_description(self):
		When.I_run_indicate_task('--long-description=cat is ace', '--', 'cat')
		And.I_press_ctrl_d()
		And.I_wait_for_the_task_to_complete()
		Then.there_should_be_an_indicator_named('cat')
		And.it_should_have_a_description_of("cat is ace")
