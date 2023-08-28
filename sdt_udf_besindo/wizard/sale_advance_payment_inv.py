from odoo import fields, models, api, _
from odoo.tools.float_utils import float_compare
from odoo.tools import float_is_zero, float_compare
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)


class SaleAdvancePayment(models.TransientModel):
    _inherit = 'sale.advance.payment.inv'

    def create_invoices(self):
        res = super(SaleAdvancePayment, self).create_invoices()
        for sale_order_id in self.sale_order_ids :
            for sale_order in sale_order_id.order_line :
                if sale_order :
                    account_move_obj = self.env['account.move'].search([('invoice_origin', '=',sale_order_id.name)])
                    if account_move_obj :
                        for account_move in account_move_obj :
                            for invoice_line_id in account_move.invoice_line_ids :
                                if invoice_line_id.product_id.id == sale_order.product_id.id :
                                    invoice_line_id.sdt_price_unit = self.sale_order_ids.order_line.sdt_price_unit
                                    x=1
                                else :
                                    pass
                    else :
                        pass
        return res
    
