from odoo import fields, models, api, _
from odoo.tools.float_utils import float_compare
from odoo.tools import float_is_zero, float_compare
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)


class SaleAdvancePayment(models.TransientModel):
    _inherit = 'sale.advance.payment.inv'

    def create_invoices(self):
        if self.advance_payment_method=='delivered':
            raise UserError('Anda tidak diperbolehkan membuat invoice dari menu Sales Order..')
        res = super(SaleAdvancePayment, self).create_invoices()
        return res
    
