from odoo import models, fields, api, exceptions, _
from . import terbilang

class SaleOrder(models.Model):
    _inherit = "sale.order"
    _template = 'form_standard_odoo.standard_sales_order_report_document'

    def terbilang_idr(self):
        return terbilang.terbilang(self.amount_total, 'idr', 'id')
    
    def terbilang_usd(self):
        return terbilang.terbilang(self.amount_total, 'usd', 'en')

    def render_html(self, data=None):
        report_obj = self.env['report']
        report = report_obj._get_report_from_name(self._template)
        docargs = {
            'terbilang_idr': self.terbilang_idr,
            'doc_ids': self._ids,
            'doc_model': report.model,
            'docs': self,
        }
        return report_obj.render(self._template, docargs)