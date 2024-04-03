from odoo import api, fields, models, _ , SUPERUSER_ID
from odoo.exceptions import UserError


class SaleReport(models.Model):
    _inherit = "sale.report"

    def fields_get(self, allfields=None, attributes=None):
        res = super(SaleReport, self).fields_get(allfields, attributes=attributes)
        # if res['margin']:
        #     is_margin = self.env['res.users'].search([('id', '=', self._uid)]).show_inventory_cost
        #     if not is_margin:
        #         res['margin']=False
        return res