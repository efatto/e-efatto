This module enable changes to consume quantity of components in done productions ensuring price are computed in stock moves.

It does it by:

#. ensuring added components have the unit price from the product standard price, as they were added at production creation
#. adding an invisible field with the unit price to the mrp form view
#. giving ability to add components if the production is unlocked (to the users with the required access)
#. giving ability to add/change/remove timesheets in the production workorders
