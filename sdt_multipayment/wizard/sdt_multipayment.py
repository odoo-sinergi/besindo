from odoo import api, fields,models
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError

class AccountPaymentRegister(models.TransientModel):
    _inherit='account.payment.register'

    opay_ids = fields.One2many('sdt.other.payment', 'mpay_id', string='Detail', copy=True, auto_join=True)
    amount_tot = fields.Monetary('Total Payment')
    balance_pay = fields.Float('Amount Due')
    journal_acc = fields.Char(string='Journal Account')
    faktur = fields.Char(string='Faktur')

    @api.onchange('opay_ids','amount','journal_id')
    def balance(self):
        amount_payment = 0
        all_account = 0
        for all in self.opay_ids:
            amount_payment += all.amount

            if all_account != 0:
                all_account = all_account + ', ' + all.mpacc_id.name
            else:
                all_account = all.mpacc_id.name

        self.amount_tot = self.amount + amount_payment

        self.balance_pay = self.payment_difference - amount_payment
        if self.opay_ids:
            self.journal_acc = all_account

    @api.depends('line_ids')
    def _compute_from_lines(self):
        res = super(AccountPaymentRegister, self)._compute_from_lines()
        ''' Load initial values from the account.moves passed through the context. '''
        for wizard in self:
            if not wizard.faktur:
                batches = wizard._get_batches()

                if len(batches) == 1:
                    faktur = ', '.join(label for label in wizard.line_ids.mapped('move_name') if label)
                    wizard.faktur = faktur
                else:
                    wizard.faktur = False
            
            return res
    
    # def _create_payment_vals_from_wizard(self):
    #     if not self.opay_ids:
    #         res = super(AccountPaymentRegister, self)._create_payment_vals_from_wizard()
    #         res['faktur'] = self.faktur
    #         return res
    def _create_payment_vals_from_wizard(self, batch_result):
        if not self.opay_ids:
            vals = super()._create_payment_vals_from_wizard(batch_result)
            return vals

        # if self.check_deposit==True:
        #     if self.communication:
        #         self.communication=self.deposit_no + ' - ' + self.communication
        #     else:
        #         self.communication=self.deposit_no
            
        payment_vals = {
            'multi_payment': True,
            'payment_wizard_id': self.id,
            'date': self.payment_date,
            'amount': self.amount,
            'payment_type': self.payment_type,
            'partner_type': self.partner_type,
            'ref': self.communication,
            'journal_id': self.journal_id.id,
            'currency_id': self.currency_id.id,
            'partner_id': self.partner_id.id,
            'partner_bank_id': self.partner_bank_id.id,
            # 'payment_method_id': self.payment_method_id.id,
            'destination_account_id': self.line_ids[0].account_id.id,
            # 'check_deposit': self.check_deposit,
            # 'deposit_due': self.deposit_due,
            # 'deposit_no': self.deposit_no,
            'faktur': self.faktur
        }

        return payment_vals
        


class sdtOtherPayment(models.TransientModel):
    _name = "sdt.other.payment"

    mpay_id = fields.Many2one('account.payment.register', string='MPay Id', index=True, copy=False)
    mpacc_id = fields.Many2one('account.account', 'Account', required=True)
    amount = fields.Float('Amount', required=True)
    label = fields.Char(string='Label', required=True)

    @api.onchange('mpacc_id')
    def onchange_mpacc_id(self):
        sql_query = """select distinct a.account_account_id 
                    from account_account_sdt_multipayment_account_rel a
                    join sdt_multipayment_account b on b.user_id=%s
                        """
        self._cr.execute(sql_query, (self._uid,))
        res_id = self._cr.dictfetchall()
        account_list = []
        if res_id != False:
            for field in res_id:
                account_list.append(field['account_account_id'])
            domain = {'mpacc_id': [('id', 'in', (account_list))]}
            return {'domain': domain}

