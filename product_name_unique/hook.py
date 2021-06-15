# Copyright (C) 2019 - 2021, Open Source Integrators
# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


def pre_init_product_name(cr):
    cr.execute("""UPDATE product_template
        SET name = CONCAT(name, '_', nextval('ir_default_id_seq'))
        WHERE id in (SELECT distinct(pt.id)
                     FROM product_template pt
                     INNER JOIN (SELECT name, COUNT(*)
                                 FROM product_template
                                 GROUP BY name
                                 HAVING COUNT(*)>1
                                 )pt1 on pt.name=pt1.name
                                  or pt.name is NULL
                                  or LENGTH(pt.name) = 0)""")
    return True
