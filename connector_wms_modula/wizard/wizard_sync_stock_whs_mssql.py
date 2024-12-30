
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_compare


class WizardSyncStockWhsMssql(models.TransientModel):
    _inherit = "wizard.sync.stock.whs.mssql"

    @staticmethod
    def _prepare_giacenze_query(i):
        # overridable method
        # respect order of fields retrieved!
        query = (
            "SELECT * FROM (SELECT row_number() OVER (ORDER BY GIA_ARTICOLO) "
            "AS rownum, GIA_ARTICOLO, GIA_GIAC, GIA_DATAORAS1 FROM EXP_GIACENZE) as A "
            "WHERE A.rownum BETWEEN %s AND %s AND LEFT(A.GIA_DATAORAS1, 10) = "
            "(SELECT LEFT(MAX(GIA_DATAORAS1), 10) FROM EXP_GIACENZE)" % (i, i + 2000)
        )
        return query

    @api.multi
    def apply(self):
        for wizard in self:
            dbsource_obj = self.env['base.external.dbsource']
            dbsource = dbsource_obj.browse(self._context['active_ids'])
            hyddemo_mssql_log_obj = self.env['hyddemo.mssql.log']
            connection = dbsource.connection_open_mssql()
            if not connection:
                raise UserError(_('Failed to open connection!'))
            new_last_update = fields.Datetime.now()
            inventory_obj = self.env['stock.inventory']
            inventory_line_obj = self.env['stock.inventory.line']
            if wizard.do_sync:
                inventory = inventory_obj.create([{
                    'name': 'WMS sync inventory ' + new_last_update.strftime(
                        "%Y-%m-%d"),
                    'location_id': dbsource.location_id.id,
                    'filter': 'products',
                }])
            product_obj = self.env['product.product']
            i = 0
            whs_log_lines = []
            stock_product_dict = dict()
            # get and aggregate stock data from WMS
            while True:
                giacenze_query = self._prepare_giacenze_query(i)
                i += 2000
                esiti_liste = dbsource.execute_mssql(
                    sqlquery=giacenze_query, sqlparams=None, metadata=None)
                # esiti_liste[0] contain result
                if not esiti_liste[0]:
                    break
                for esito_lista in esiti_liste[0]:
                    articolo = esito_lista[1]
                    try:
                        qty = float(esito_lista[2])
                    except ValueError:
                        qty = False
                        pass
                    except TypeError:
                        qty = False
                        pass
                    if articolo not in stock_product_dict:
                        stock_product_dict.update({articolo: qty})
                    else:
                        stock_product_dict[articolo] += qty

            # compare data with db and re-align values
            for stock_product in stock_product_dict:
                whs_log_line = {
                    'name': stock_product,
                }
                product = product_obj.search([
                    ('default_code', '=', stock_product),
                    ('type', '=', 'product'),
                    ('exclude_from_whs', '!=', True)])
                # if it is a service, only log but do not create inventory line
                if not product:
                    product = product_obj.search([
                        ('default_code', '=', stock_product),
                        ('type', '=', 'service'),
                        ('exclude_from_whs', '!=', True)])
                    if not product:
                        whs_log_line.update({
                            'type': 'not_found',
                        })
                        continue
                    else:
                        whs_log_line.update({
                            'type': 'service',
                        })
                        continue
                # it is a product or consumable, create log and align only if qty is
                # different and do_sync is True
                else:
                    product_qty = stock_product_dict[stock_product]
                    # it product is traceable, inventory cannot be done without lot info
                    if product.tracking != "none":
                        whs_log_line.update({
                            'type': 'tracking',
                        })
                        continue
                    if float_compare(
                        product_qty,
                        product.qty_available,
                        precision_rounding=product.uom_id.rounding
                    ):
                        whs_log_line.update({
                            'product_id': product.id,
                            'qty_wrong': product.qty_available,
                            'qty': product_qty,
                            'type': 'mismatch',
                        })
                        if wizard.do_sync:
                            line_data = {
                                'inventory_id': inventory.id,
                                'product_qty': product_qty,
                                'location_id': dbsource.location_id.id,
                                'product_id': product.id,
                                'product_uom_id': product.uom_id.id,
                                'reason': 'WMS synchronize',
                                }
                            inventory_line_obj.create(line_data)
                    else:
                        whs_log_line.update({
                            'product_id': product.id,
                            'qty': product_qty,
                            'type': 'ok',
                        })
                if whs_log_line.get('type'):
                    whs_log_lines.append(whs_log_line)

            if wizard.do_sync:
                inventory.action_validate()

            hyddemo_mssql_log = hyddemo_mssql_log_obj.create([{
                'errori': 'Stock inventory %s' % (
                    'sync' if wizard.do_sync else 'check'),
                'ultimo_invio': new_last_update,
                'dbsource_id': dbsource.id,
                'inventory_id': inventory.id if wizard.do_sync else False,
                'hyddemo_mssql_log_line_ids': [
                    (0, 0, x) for x in whs_log_lines]
            }])

            return {
                'type': 'ir.actions.act_window',
                'res_model': 'hyddemo.mssql.log',
                'view_mode': 'form',
                'view_type': 'form',
                'res_id': hyddemo_mssql_log.id,
                'views': [(False, 'form')],
                'target': 'current',
            }
