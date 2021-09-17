# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


def pre_init_product_code(cr):
    # remove product template default code spaces or white spaces excluding duplicates
    cr.execute("""UPDATE product_template
        SET default_code = regexp_replace(default_code, '\s', '', 'g')
        WHERE default_code ~ '\s+' 
        AND id NOT IN (
            SELECT DISTINCT(pt.id)
            FROM product_template pt
            WHERE default_code = regexp_replace(default_code, '\s', '', 'g')
        )""")
    # update residual codes with _id
    cr.execute("""UPDATE product_template
        SET default_code = CONCAT(
            regexp_replace(
                default_code, '\s', '', 'g'), '_', nextval('ir_default_id_seq'))
        WHERE default_code ~ '\s+' 
        """)
    return True
