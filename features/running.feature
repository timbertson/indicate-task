Feature: running indicate-task
	Running a basic, blocking process that consumes
	and produces output.

Scenario: running and cancelling a program
	When I run indicate-task -- cat
	And I enter "input"
	And I press ctrl-c
	And I wait for the task to complete

	Then there should be a "cat" indicator
	And it should have a menu description of "cat: running..."
	And the output should be: input
	And the error output should be empty
	And the return code should not be 0
	And it should display the task's output to the user
	And it should notify the user of the task's completion

Scenario: running a program that successfully completes
	When I run indicate-task -- cat
	And I enter "input"
	And I press ctrl-d
	And I wait for the task to complete

	Then there should be a "cat" indicator
	And the output should be: input
	And the error output should be empty
	And the return code should be 0
	And it should not display the task's output to the user
	And it should notify the user of the task's completion



