from pea import TestCase, world
import all_steps
class BaseTest(TestCase):
	def setUp(self):
		import sys
	def tearDown(self):
		super(BaseTest, self).tearDown()
		try:
			world.external_process.kill()
		except AttributeError:
			pass

