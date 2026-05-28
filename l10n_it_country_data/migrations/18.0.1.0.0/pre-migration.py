import logging

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)


@openupgrade.migrate()
def migrate(env, version):
    _logger.info("Running l10n_it_country_data pre-migration")
    l10n_it_module = env["ir.module.module"].search([("name", "=", "l10n_it")])
    if l10n_it_module.state == "uninstalled":
        _logger.info("l10n_it module is uninstalled, searching and installing "
                     "l10n_it_account_xmlid_fix")
        module_fix = env["ir.module.module"].search(
            [("name", "=", "l10n_it_account_xmlid_fix")]
        )
        if module_fix.state == "uninstalled":
            _logger.info("l10n_it_account_xmlid_fix module is uninstalled, "
                         "attempting to install")
            module_fix.button_immediate_install()
            _logger.info("l10n_it_account_xmlid_fix module installed")
        elif module_fix.state == "installed":
            _logger.info("l10n_it_account_xmlid_fix module already installed")
        else:
            _logger.info(
                "l10n_it_account_xmlid_fix not present or in unexpected state: %s",
                module_fix.state)
