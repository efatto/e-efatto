# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

_logger = logging.getLogger(__name__)


def pre_init_hook(cr):
    _logger.info(
        "Store field maintenance_plan_horizon on maintenance.plan in "
        "maintenance_plan_horizon_max"
    )
    cr.execute(
        """
        ALTER TABLE maintenance_plan
        ADD COLUMN IF NOT EXISTS maintenance_plan_horizon_max INTEGER;
        UPDATE maintenance_plan
        SET maintenance_plan_horizon_max = maintenance_plan_horizon;
        """
    )

    _logger.info(
        "Store field maintenance_plan on maintenance.plan in " "planning_step_max"
    )
    cr.execute(
        """
        ALTER TABLE maintenance_plan
        ADD COLUMN IF NOT EXISTS planning_step_max VARCHAR(255);
        UPDATE maintenance_plan
        SET planning_step_max = planning_step;
        """
    )
