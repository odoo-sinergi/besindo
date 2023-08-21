from odoo import api, fields,models
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError

class AccountPaymentRegister(models.TransientModel):
    _inherit='account.payment.register'

    def action_create_payments(self):
        planner = super(AccountPaymentRegister, self).action_create_payments()
        for i in self :
            account_payment_obj = self.env['account.payment'].search([('ref', '=', i.communication)])
            for account_payment in account_payment_obj :
                if i.line_ids.move_id.invoice_line_ids.analytic_account_id.ids[0] :
                    account_payment.account_analytic_id = i.line_ids.move_id.invoice_line_ids.analytic_account_id.ids[0]
                else :
                    pass
        return planner
        