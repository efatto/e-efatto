Duplicating a product copies its sales price (``list_price``), so the new
product starts with the price of the original one.

This module sets ``copy=False`` on the ``list_price`` field of
``product.template``: when a product is duplicated the price is not copied and
the new product gets the field default, while the price of the original
product is left untouched.
