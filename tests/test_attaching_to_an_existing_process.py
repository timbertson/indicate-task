from pea import *
from base_test import BaseTest

class AttachingToAnExistingProcess(BaseTest):
	"""
	I want to make an indicator for an already-running process
	"""

	def test_attaching_to_an_existing_process(self):
		When.I_run('cat')
		And.I_run_indicate_task('-d', 'cat', '--pid', world.external_process.pid)
		Then.there_should_be_an_indicator_named('cat')
		Then.I_kill_the_external_process()
		And.I_wait_for_the_task_to_complete()
