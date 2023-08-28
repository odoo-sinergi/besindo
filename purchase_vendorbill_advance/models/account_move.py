# -*- coding: utf-8 -*-

from re import search

from odoo import _, api, fields, models
from odoo.exceptions import UserError

class AccountMove(models.Model):
    _inherit = 'account.move'

    # @api.onchange('purchase_vendor_bill_id', 'purchase_id')
    # def _onchange_purchase_auto_complete(self):
    #     res = super(AccountMove, self)._onchange_purchase_auto_complete()
        
    #     po = self.env['purchase.order'].search([('name', '=', self.invoice_origin)])
    #     for rec in po:
    #         line_po = self.env['purchase.order.line'].search([('order_id', '=', rec.id)])
    #         for line in self.invoice_line_ids:
    #             if line.product_id.id != 150:
    #                 id = str(line.id)
    #                 string = 'NewId_'
    #                 if not search(string, id):
    #                     for data in line_po:
    #                         if line.purchase_line_id and line.purchase_line_id.id == data.id:
    #                             if line.product_id.id == data.product_id.id and line.sequence == data.sequence:
    #                                 line.write({'discount': data.discount, 'price_unit': data.price_befdisc})
            
    #     return res
    
    def button_cancel(self):
        res = super(AccountMove, self).button_cancel()
        dp_po_product_id = int(self.env['ir.config_parameter'].sudo().get_param('purchase.default_deposit_product_id'))
        for rec in self:
            if rec.move_type == 'in_invoice':
                if len(rec.invoice_line_ids) == 1:
                    for line in rec.invoice_line_ids:
                        if line.product_id.id == dp_po_product_id:
                            if line.purchase_line_id:
                                sql_query="""delete from purchase_order_line where id=%s 
                                    """
                                self.env.cr.execute(sql_query,(line.purchase_line_id.id,))

class AccountTax(models.Model):
    _inherit = 'account.tax'

    is_vat = fields.Boolean(string="Is a VAT",)