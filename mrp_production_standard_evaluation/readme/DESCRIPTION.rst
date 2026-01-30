This module add ability to consume quantity of components in done productions.

It does it by:

#. ensuring added components have the price, as they were added at production creation
#. giving ability to add components if the production is unlocked (to the users with the required access)
#. giving ability to add/change/remove timesheets in the production workorders

This module change the cost generation method to apply this changes to the finished products.
Moreover, it change the cost computation method to set cost on the finished products even if it is not set an evaluation method in product categories, using a "default" logic to standard price.
