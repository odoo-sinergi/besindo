from odoo import fields, models, api, _
from datetime import datetime
from odoo.exceptions import UserError, ValidationError

class AccountVoucher(models.Model):
    _inherit='account.payment'

    down_payment = fields.Boolean(string="Down Payment",default=False)
    reset_draft = fields.Boolean(string="Reset Draft",default=False)
    account_dp = fields.Many2one('account.account', 'Down Payment Account')
    journal_dp = fields.Many2one('account.move', 'Journal DP')
    ji_count = fields.Integer(string='Journal Items', compute='_compute_ji_count')

    def action_cancel(self):
        if not self.down_payment:
            return super(AccountVoucher, self).action_cancel()
        if self.name!='/':
            move_obj = self.env['account.move'].search([('name', '=', self.name)])
            move_obj.button_cancel()

        return super(AccountVoucher, self).action_cancel()
    
    def action_draft(self):
        if not self.down_payment:
            return super(AccountVoucher, self).action_draft()
        dp_id = self.env['sdt.downpayment'].search([('payment_id', '=', self.id)]).id
        sql_query = """
                select count(1) from sdt_downpayment_lines where dp_id=%s and state='assigned'
                """
        self.env.cr.execute(sql_query,(dp_id,) )
        check_dp = self.env.cr.fetchone()[0] or 0.0
        if check_dp != 0:
            raise ValidationError(_('Payment tidak bisa dicancel karena sudah diassignkan ke Bill/Invoice'))

        downpayment_obj = self.env['sdt.downpayment'].search([('payment_id', '=', self.id)])
        downpayment_obj.unlink()
        move_obj = self.env['account.move'].search([('name', '=', self.name)])
        move_obj.state = 'draft'
        move_obj.posted_before = False
        self.reset_draft = True

        return super(AccountVoucher, self).action_draft()

    @api.onchange('down_payment')
    def dp_domain(self):
        if not self.down_payment:
            return {'domain': {'down_payment': []}}

        if self.down_payment==True:
            sql_query = """
                select account_account_id from sdt_downpayment_account a, account_account_sdt_downpayment_account_rel b
            where a.id = b.sdt_downpayment_account_id and a.payment_type = %s and a.user_id = %s
                """

            self.env.cr.execute(sql_query,(self.payment_type, self._uid,))
            res_dp = self.env.cr.dictfetchall()
            dp_list = []
            if res_dp:
                for field in res_dp:
                    dp_list.append(field['account_account_id'])
            else:
                raise ValidationError(_('Down Payment Account belum di setting'))

            return {'domain': {'account_dp': [('id', 'in', (dp_list))]}}
        else:
            self.account_dp=""

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        if not self.partner_id :
            partner_id = self.partner_id
    
    def action_post(self):
        res = super(AccountVoucher, self).action_post()
        for rec in self:
            if rec.down_payment==True:
                if rec.reset_draft == True:
                    raise ValidationError(_('Payment DP tidak bisa diconfirm, karena sudah di Reset To Draft'))

                label=rec.name
                memo=rec.ref
                move_obj=self.env['account.move'].search([('name','=',rec.move_id.name)], limit=1)
                move_line_obj=self.env['account.move.line'].search([('move_id','=',move_obj.id)])
                move_line_obj.write({'name':rec.partner_id.name + ' - ' + rec.name,'ref':memo})
                flagPay=''
                # prepare numbering
                # check payment_receipt
                if rec.payment_type=='outbound':
                    flagBank='K'
                    flagPay='outbound'
                elif rec.payment_type=='inbound':
                    flagBank='M'
                    flagPay = 'inbound'

                #add to downpayment model
                    #buat journal pembalik
                    #dp pada hutang vendor

                account_journal = self.env['account.journal']
                journal = rec.journal_id
                dp_no=rec.name
                line_ids = []
                debit_sum = 0.0
                credit_sum = 0.0
                amount_currency=0
                
                journal_dp_obj=self.env['account.journal'].search([('down_payment','=',True)])
                move = {
                    'name': label,
                    # 'journal_id': journal.id,
                    'journal_id': journal_dp_obj.id,
                    'date': rec.date,
                    'ref': memo,
                }

                if flagPay =='outbound':
                    account_debit=rec.account_dp.id
                    account_credit=rec.destination_account_id.id
                    # account_credit=self.partner_id.property_account_payable_id.id
                elif flagPay =='inbound':
                    account_credit = rec.account_dp.id
                    account_debit = rec.destination_account_id.id
                    # account_debit = self.partner_id.property_account_receivable_id.id
                
                rate=0
                if rec.currency_id.name != 'IDR':
                    currency = rec.currency_id.id
                    amount_currency = rec.amount
                    try:
                        # sql_query = """select rate from res_currency_rate where company_id=%s and currency_id=%s and name<=%s order by NAME desc limit 1
                        #         """
                        sql_query = """select inverse_rate from res_currency_rate where company_id=%s and currency_id=%s and name<=%s order by NAME desc limit 1
                                """
                        self.env.cr.execute(sql_query,
                                            (rec.company_id.id, rec.currency_id.id, rec.date,))
                        rate = self.env.cr.fetchone()[0] or 0.0
                    except:
                        raise ValidationError(_('Rate for %s is not yet set..') % (rec.currency_id.name))
                    # amount = self.amount/rate
                    amount = rec.amount*rate
                else:
                    amount = rec.amount
                    currency = rec.currency_id.id
                    amount_currency = 0

                debit_line = (0, 0, {
                    'name': rec.partner_id.name + ' - ' + rec.name,
                    'partner_id': rec.partner_id.id,
                    'account_id': account_debit,
                    'journal_id': journal.id,
                    'ref': memo,
                    'date': rec.date,
                    'currency_id': currency,
                    'debit': amount,
                    'credit': 0.0,
                    # 'amount_currency': amount_currency,
                    'amount_currency': amount,
                    'balance': amount,
                    'amount_residual': amount,
                    'amount_residual_currency': amount,
                    # 'analytic_account_id': line['analytic_account_id'],
                })
                line_ids.append(debit_line)

                credit_line = (0, 0, {
                    'name': rec.partner_id.name + ' - ' + rec.name,
                    'partner_id': rec.partner_id.id,
                    'account_id': account_credit,
                    'journal_id': journal.id,
                    'ref': memo,
                    'date': rec.date,
                    # 'amount_currency': amount_currency*-1,
                    'currency_id': currency,
                    'debit': 0.0,
                    'credit': amount,

                    'amount_currency': amount *-1,
                    'balance': amount*-1,
                    'amount_residual': amount*-1,
                    'amount_residual_currency': amount*-1,
                    # 'analytic_account_id': line['analytic_account_id'],
                })
                line_ids.append(credit_line)

                move['line_ids'] = line_ids
                move_id = self.env['account.move'].create(move)
                move_id.action_post()
                rec.journal_dp = move_id
                move_id.amount_payment = amount
                move_line_obj=self.env['account.move.line'].search([('move_id','=',move_id.id)])
                if move_line_obj:
                    move_line_obj.write({'payment_id':rec.id})
                
                # for move_line in move_line_obj :
                #     if move_line.account_id.id ==  rec.account_dp.id:
                #         move_line.debit = rec.amount
                #         move_line.balance = rec.amount
                #         move_line.amount_currency = rec.amount
                #         move_line.amount_residual = rec.amount
                #         move_line.amount_residual_currency = rec.amount
                #     x= 1
                #simpan ke table downpayment
                downpayment_obj = self.env['sdt.downpayment']
                new_dp = downpayment_obj.create({
                    'payment_type': flagPay,
                    'partner_type': rec.partner_type,
                    'partner_id': rec.partner_id.id,
                    'account_dp': rec.account_dp.id,
                    'control_account': rec.destination_account_id.id,
                    'amount': rec.amount,
                    'currency_id': rec.currency_id.id,
                    'date': rec.date,
                    'ref': rec.ref,
                    'journal_id': rec.journal_id.id,
                    'company_id': rec.company_id.id,
                    'dp_no': dp_no,
                    'state': 'open',
                    'close_amount' : 0,
                    'balance_amount' : rec.amount,
                    'payment_id': rec.id,
                    'open_move_id': move_id.id,
                    'rate': rate,
                    'amount_currency': amount_currency,
                })

        # move_line_debit_obj=self.env['account.move.line'].search([('move_id','=',move_id.id),('account_id','=',move_line_obj.account_id.ids[0])])
        # move_line_credit_obj=self.env['account.move.line'].search([('move_id','=',move_id.id),('account_id','=',move_line_obj.account_id.ids[1])])
        
        # for move_line_debit in move_line_debit_obj:
        #     if move_line_debit :
        #         move_line_debit.write({'debit':amount})

        # for move_line_credit in move_line_credit_obj:
        #     if move_line_credit :
        #         move_line_credit.write({'debit':amount})
        return res

    @api.depends('ji_count')
    def _compute_ji_count(self):
        for order in self:
            ji_obj = self.env['account.move.line'].search([('name', '=', self.name)])
            order.ji_count = len(ji_obj)
    
    def button_open_journal(self):
        ''' Redirect the user to the invoice(s) paid by this payment.
        :return:    An action on account.move.
        '''
        self.ensure_one()

        action = {
            'name': _("Journal Item"),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move.line',
            'context': {'create': False},
        }
        ji_obj = self.env['account.move.line'].search([('name', '=', self.name)])
        if len(ji_obj.ids) == 1:
            action.update({
                'view_mode': 'form',
                'res_id': ji_obj.ids,
            })
        else:
            action.update({
                'view_mode': 'list,form',
                'domain': [('id', 'in', ji_obj.ids)],
            })
        return action
