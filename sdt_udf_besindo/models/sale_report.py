from odoo import api, fields, models, _ , SUPERUSER_ID
from odoo.exceptions import UserError


class SaleReport(models.Model):
    _inherit = "sale.report"

    sales_type = fields.Selection([('domestic','DOMESTIC'),('export','EXPORT')], string='Sales Type', readonly=True)

    def _select_additional_fields(self):
        res = super()._select_additional_fields()
        res['sales_type'] = "partner.sales_type"
        return res

    def _group_by_sale(self):
        res = super()._group_by_sale()
        res += """,
            partner.sales_type"""
        return res

    
    
    
    