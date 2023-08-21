from odoo import models, fields, api, exceptions, _
from . import terbilang

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"
    _template = 'form_standard_odoo.purchase_order_report_document'

    def terbilang_idr(self):
        return terbilang.terbilang(self.amount_total, 'idr', 'id')

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