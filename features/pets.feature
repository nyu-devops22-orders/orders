Feature: The order store service back-end
    As a Order Store Owner
    I need a RESTful API service
    So that I can keep track of all my orders

Background:
    Given the following orders
        | customer   | total    | status    | date       |
        | fido       | 100      | Cancelled | 2019-11-18 |
        | kitty      | 10       | Refunded  | 2020-08-13 |
        | leo        | 1000     | Closed    | 2019-01-02 |
        | sammy      | 100      | Open      | 2018-06-04 |

Scenario: The server is running
    When I visit the "Home Page"
    Then I should see "Order Demo RESTful Service" in the title
    Then I should not see "404 Not Found"

Scenario: Create a Order
    When I visit the "Home Page"
    And I set the "customer" to "Happy"
    And I set the "total" to "100"
    And I select "Open" in the "status" dropdown
    And I set the "date" to "10-12-2020"
    And I press the "Create" button
    Then I should see the message "Success"
    When I copy the "Id" field
    And I press the "Clear" button
    Then the "Id" field should be empty
    And the "customer" field should be empty
    And the "total" field should be empty
    And the "date" field should be empty
    When I paste the "Id" field
    And I press the "Retrieve" button
    Then I should see "Happy" in the "customer" field
    And I should see "100" in the "total" field
    And I should see "Open" in the "status" dropdown
    And I should see "2020-12-10" in the "date" field

Scenario: List all orders
    When I visit the "Home Page"
    And I press the "Search" button
    Then I should see "fido" in the results
    And I should see "kitty" in the results
    And I should see "leo" in the results
    And I should not see "Happy" in the results

Scenario: Search for status when I visit the "Home Page"
    And I select "Open" in the "status" dropdown
    And I press the "Search" button
    Then I should see "fido" in the results
    And I should not see "sammy" in the results
    And I should not see "kitty" in the results
    And I should not see "leo" in the results
    And I should not see "Happy" in the results

Scenario: Update a Order
    When I visit the "Home Page"
    And I set the "customer" to "fido"
    And I press the "Search" button
    Then I should see "fido" in the "customer" field
    And I should see "100" in the "total" field
    And I should see "2019-11-18" in the "date" field
    And I should see "Cancelled" in the "status" dropdown
    When I change "customer" to "Boxer"
    And I press the "Update" button
    Then I should see the message "Success"
    When I copy the "Id" field
    And I press the "Clear" button
    And I paste the "Id" field
    And I press the "Retrieve" button
    Then I should see "Boxer" in the "customer" field
    When I press the "Clear" button
    And I press the "Search" button
    Then I should see "Boxer" in the results
    Then I should not see "fido" in the results

Scenario: Delete a Order
    When I visit the "Home Page"
    And I set the "customer" to  "kitty"
    And I press the "Search" button
    Then I should see "kitty" in the "customer" field
    And I should see "10" in the "total" field
    When I press the "Delete" button
    Then I should see the message "Order has been Deleted!"
    When I press the "Search" button
    Then I should not see "kitty" in the results


