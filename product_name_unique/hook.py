def pre_init_product_name(env):
    langs = env["res.lang"].search([])
    for lang in langs:
        lang_code = lang.code
        env.cr.execute(
            """UPDATE product_template
            SET name = jsonb_set(
                name, %s, to_jsonb(
                    COALESCE(name->>%s, name->>'it_IT', name->>'en_US', '')
                     || '_' || nextval('ir_default_id_seq')))
            WHERE id in (SELECT distinct(pt.id)
                         FROM product_template pt
                         INNER JOIN (
                            SELECT COALESCE(name->>%s, '') as name_lang, COUNT(*)
                            FROM product_template
                            GROUP BY COALESCE(name->>%s, '')
                            HAVING COUNT(*)>1
                         ) pt1 on COALESCE(pt.name->>%s, '') = pt1.name_lang)
            """,
            (
                f"{{{lang_code}}}",
                lang_code,
                lang_code,
                lang_code,
                lang_code,
            ),
        )
    return True
