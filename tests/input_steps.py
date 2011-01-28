from pea import step, world
from time import sleep
input_wait_time = 0.2
import os, signal

@step
def I_enter(input):
	world.popen[0].stdin.write(input + '\n')
	sleep(input_wait_time)

@step
def I_press_ctrl_c():
	os.kill(world.popen[0].pid, signal.SIGINT)

@step
def I_press_ctrl_d():
	world.popen[0].stdin.close()


