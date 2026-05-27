from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    l10n_it_module = env["ir.module.module"].search([("name", "=", "l10n_it")])
    if l10n_it_module.state == "uninstalled":
        module_fix = env["ir.module.module"].search(
            [("name", "=", "l10n_it_account_xmlid_fix")]
        )
        if module_fix.state == "uninstalled":
            module_fix.button_immediate_install()
