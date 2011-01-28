Feature: attaching to an existing process
	I want to make an indicator for an already-running process

Scenario: attaching to an existing process
	When I run cat
	And I run indicate-task -d cat --pid $pid
	Then there should be a "cat" indicator
	Then I kill $pid
	And I wait for the task to complete
