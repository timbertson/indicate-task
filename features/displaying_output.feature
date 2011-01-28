Feature: displaying output
	I want to see command output when a task is running

Scenario: displaying output of a still-running command
	When I run indicate-task -- cat
	And I enter "input"
	And I show the output of the task
	Then the output is shown with 1 line

	When I enter "second line"
	Then the output is shown with 2 lines

	Then I press ctrl-d
	And I wait for the task to complete

	And it should have shown the output once

Scenario: not capturing output
	When I run indicate-task --no-capture -- cat
	And I enter "input"
	Then it should not capture any output
	And I press ctrl-d

