from odoo import models, fields, api, exceptions, _
from . import terbilang

class AccountMove(models.Model):
    _inherit = "account.move"
    _template = 'form_standard_odoo.standard_sales_invoice_document'

    
    # info_po = fields.Char(string='Info Po',)

    def terbilang_idr(self):
        return terbilang.terbilang(self.amount_total, 'idr', 'id')

    def terbilang_usd(self):
        return terbilang.terbilang(self.amount_total, 'usd', 'en')
    
    def render_html(self, data=None):
        report_obj = self.env['report']
        report = report_obj._get_report_from_name(self._template)
        docargs = {
            'terbilang_idr': self.terbilang_idr,
            'terbilang_usd': self.terbilang_usd,
            'doc_ids': self._ids,
            'doc_model': report.model,
            'docs': self,
        }
        return report_obj.render(self._template, docargs)
    
# class InfoPoAccountMove(models.AbstractModel):
    # _name = "report.form_standard_odoo.standard_vendor_bill_report"
    # _description = 'Info Po Account Move'

    # @api.model
    # def _get_report_values(self, docids, data=None):
    #     docs = self.env['account.move'].browse(docids)
    #     printed = ''
    #     for doc in docs:
    #         no_po = []
    #         no_po1 = []
    #         for record in doc.invoice_line_ids:
    #             if not no_po :
    #                 no_po.append(({
    #                     'purchase_order':record.purchase_order_id.name
    #                 }))
    #             else :
    #                 check_data = [d for d in no_po if d['purchase_order'] == record.purchase_order_id.name]
    #                 if not check_data :
    #                     no_po.append(({
    #                         'purchase_order':record.purchase_order_id.name
    #                     }))
    #                 else :
    #                     pass
    #         for nopo in no_po :
    #             if nopo :
    #                 no_po1.append(({
    #                         'purchase_order':nopo['purchase_order']
    #                     }))
    #             doc.write({
    #                 'info_po': no_po1
    #                 })
    #         x=1

    #     return {
    #         'doc_ids': docs.ids,
    #         'doc_model': 'account.move',
    #         'docs': docs,
    #         'printed': printed,
    #     }