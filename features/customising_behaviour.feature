Feature: customising behaviour
	I want to be able to customise the appearance and behaviour of an indicator

Scenario: suppressing notification
	When I run indicate-task --no-notify -- cat
	And I press ctrl-d
	And I wait for the task to complete
	Then it should not notify the user of the task's completion

Scenario: suppressing errors
	When I run indicate-task --ignore-errors -- cat
	And I press ctrl-c
	And I wait for the task to complete
	And it should not display the task's output to the user

Scenario: setting a label
	When I run indicate-task -d catty -- cat
	And I press ctrl-d
	And I wait for the task to complete
	Then there should be a "catty" indicator

Scenario: no icon
	When I run indicate-task --no-icon -- cat
	And I press ctrl-d
	And I wait for the task to complete
	Then there should be a "cat" indicator
	And it should have no icon

Scenario: long description
	When I run indicate-task --long-description=cat_is_ace -- cat
	And I press ctrl-d
	And I wait for the task to complete
	Then there should be a "cat" indicator
	And it should have a menu description of "cat_is_ace"
