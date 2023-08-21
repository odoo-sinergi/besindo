from odoo import api, fields, models, _ , SUPERUSER_ID
from odoo.exceptions import UserError


class AccountInvoiceReport(models.Model):
    _inherit = "account.invoice.report"

    sales_type = fields.Selection([('domestic','DOMESTIC'),('export','EXPORT')], string='Sales Type', readonly=True)

    def _select(self):
        return super()._select() + ", partner.sales_type as sales_type"

    
    
    
    