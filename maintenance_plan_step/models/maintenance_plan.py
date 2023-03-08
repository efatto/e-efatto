# Copyright 2021 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields, api
from dateutil.relativedelta import relativedelta


def get_relativedelta(interval, step):
    if step == 'day':
        return relativedelta(days=interval)
    elif step == 'week':
        return relativedelta(weeks=interval)
    elif step == 'month':
        return relativedelta(months=interval)
    elif step == 'year':
        return relativedelta(years=interval)


class MaintenancePlan(models.Model):
    _inherit = 'maintenance.plan'

    maintenance_plan_horizon = fields.Integer(
        string='Planning Horizon real period',
        compute='_get_maintenance_plan_horizon',
        readonly=True,
        help='Maintenance planning horizon. Only the maintenance requests '
             'inside the horizon will be created.')
    planning_step = fields.Selection([
        ('day', 'Day(s)'),
        ('week', 'Week(s)'),
        ('month', 'Month(s)'),
        ('year', 'Year(s)')],
        string='Planning Horizon real step',
        readonly=True,
        compute='_get_maintenance_plan_horizon',
        help="Let the event automatically repeat at that interval")
    maintenance_plan_horizon_max = fields.Integer(
        string='Planning Horizon period',
        default=1,
        help='Maintenance planning horizon. Only the maintenance requests '
             'inside the horizon will be created.')
    planning_step_max = fields.Selection([
        ('day', 'Day(s)'),
        ('week', 'Week(s)'),
        ('month', 'Month(s)'),
        ('year', 'Year(s)')],
        string='Planning Horizon step',
        default='year',
        help="Let the event automatically repeat at that interval")

    @api.depends('equipment_id.maintenance_plan_horizon',
                 'equipment_id.maintenance_plan_step',
                 'maintenance_plan_horizon_max',
                 'planning_step_max')
    def _get_maintenance_plan_horizon(self):
        # get minimum horizon plan
        for plan in self:
            equipment = plan.equipment_id
            if equipment.maintenance_plan_horizon and equipment.maintenance_plan_step:
                if plan.maintenance_plan_horizon_max and plan.planning_step_max:
                    plan_horizon_date = fields.Date.from_string(
                        fields.Date.today()) + get_relativedelta(
                        plan.maintenance_plan_horizon_max,
                        plan.planning_step_max)
                    equipment_horizon_date = fields.Date.from_string(
                        fields.Date.today()) + get_relativedelta(
                        equipment.maintenance_plan_horizon,
                        equipment.maintenance_plan_step)
                    if plan_horizon_date <= equipment_horizon_date:
                        plan.maintenance_plan_horizon = \
                            plan.maintenance_plan_horizon_max
                        plan.planning_step = plan.planning_step_max
                    else:
                        plan.maintenance_plan_horizon = \
                            equipment.maintenance_plan_horizon
                        plan.planning_step = equipment.maintenance_plan_step
            else:
                plan.maintenance_plan_horizon = plan.maintenance_plan_horizon_max
                plan.planning_step = plan.planning_step_max
