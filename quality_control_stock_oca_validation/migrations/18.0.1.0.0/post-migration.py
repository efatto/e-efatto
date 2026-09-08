from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    # Set timings in qc.trigger.line to 'before'
    models = [
        "qc.trigger.product_category_line",
        "qc.trigger.product_template_line",
        "qc.trigger.product_line",
    ]
    for model in models:
        trigger_lines = env[model].sudo().search([])
        trigger_lines.write({"timing": "before"})
