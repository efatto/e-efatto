# Copyright (C) 2019 - 2021, Open Source Integrators
# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


def pre_init_product_name(env):
    env.cr.execute(
        "SELECT 1 FROM pg_class WHERE relkind = 'S' AND relname = 'ir_default_id_seq'"
    )
    if not env.cr.fetchone():
        env.cr.execute("CREATE SEQUENCE ir_default_id_seq INCREMENT BY 1 START WITH 1")
    env.cr.execute(
        """UPDATE product_template
        SET name = jsonb_set(
            name, '{en_US}', to_jsonb(
                COALESCE(name->>'en_US', '') || '_' || nextval('ir_default_id_seq')))
        WHERE id in (SELECT distinct(pt.id)
                     FROM product_template pt
                     INNER JOIN (
                        SELECT COALESCE(name->>'en_US', '') as name_en, COUNT(*)
                        FROM product_template
                        GROUP BY COALESCE(name->>'en_US', '')
                        HAVING COUNT(*)>1
                     ) pt1 on COALESCE(pt.name->>'en_US', '') = pt1.name_en)
        """
    )
    return True
