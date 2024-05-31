# -*- coding: utf-8 -*-
# Copyright 2016-TODAY Serpent Consulting Services Pvt. Ltd.
# See LICENSE file for full copyright and licensing details.

from datetime import datetime

from odoo import fields, api, models, _
from odoo.exceptions import UserError

from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF


WARNING_MESSAGE = [
                   ('no-message','No Message'),
                   ('warning','Warning'),
                   ('block','Blocking Message')
                   ]

WARNING_HELP = _('Selecting the "Warning" option will notify user with the message, Selecting "Blocking Message" will throw an exception with the message and block the flow. The Message has to be written in the next field.')

class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    def check_limit(self):
        self.ensure_one()
        partner = self.partner_id

        commercial_id=self.env['res.partner'].search([('id','=',partner.id)]).commercial_partner_id
        # commercial_date=self.env['account.invoice'].search([('id','=',partner.id)]).commercial_partner_id
        # commercial_date_invoice=self.env['account.invoice'].search([('id','=',partner.id)]).date_invoice
        # commercial_date_due=self.env['account.invoice'].search([('id','=',partner.id)]).date_due
        
        if self.type in ('out_invoice'):
        
            # Blocking faktur
            sql_query = """select count(1) from account_invoice where type='out_invoice' and state='open' and commercial_partner_id=%s
                                    """
            self.env.cr.execute(sql_query, (commercial_id.id,))
            faktur = self.env.cr.fetchone()[0] or 0.0

            allow_faktur=self.env['res.partner'].search([('id','=',commercial_id.id)]).faktur_blocking

            if commercial_id.faktur_blocking != 0 :
                if faktur>=(allow_faktur):
                    msg = 'Can not confirm Invoice, Total Faktur more than allowed, Total Faktur = %s Total Allow = %s' % (faktur,allow_faktur)
                    raise UserError(_('Faktur Blocking !\n' + msg))

            #Blocking overdue (due date)
            day_overdue=self.env['res.partner'].search([('id','=',commercial_id.id)]).overdue_blocking

            if day_overdue > 0:
                sql_query = """select count(1) from account_invoice a where 
                    a.state='open' and a.type='out_invoice' and a.commercial_partner_id=%s
                    and (select now()::date) - a.date_due >= %s
                    """
                self.env.cr.execute(sql_query, (commercial_id.id,day_overdue,))
                overdue = self.env.cr.fetchone()[0] or 0.0

                if overdue>0:
                    msg = 'Can not confirm Sales Order, Total OverDue Invoice ' \
                        'is %s Document..!' % (overdue)
                    raise UserError(_('OverDue Invoice !\n' + msg))                            

            #Blocking Credit Limit
            debit, credit = 0.0, 0.0
            today_dt = datetime.strftime(datetime.now().date(), DF)
            warning = {}
            title = False
            message = False

            # moveline_obj = self.env['account.move.line']
            # movelines = moveline_obj.search(
            #     [('partner_id', '=', commercial_id.id),
            #      ('account_id.user_type_id.name', 'in', ['Receivable', 'Payable']),
            #      ('full_reconcile_id', '=', False)]
            # )

            sql_query="""select a.credit,a.debit,a.date_maturity,a.full_reconcile_id from account_move_line a inner join res_partner b
                on a.partner_id=b.id inner join account_account_type c on a.user_type_id=c.id where b.commercial_partner_id=%s
                and c.name in ('Receivable', 'Payable') and a.full_reconcile_id is null;
                """
            self.env.cr.execute(sql_query, (commercial_id.id,))
            movelines = self.env.cr.dictfetchall()

            for line in movelines:
                # if line['date_maturity'] < today_dt:
                debit += line['debit']
                credit += line['credit']

            total_used=debit - credit
            if commercial_id.credit_limit != 0 :
                if (total_used) > commercial_id.credit_limit:
                    if not commercial_id.over_credit:
                        msg = 'Can not validate Invoice, Credit Limit exceeded, ' \
                            'Over Limit %s !\nCheck Partner Credit ' \
                            'Limits !' % (commercial_id.credit_limit - debit)
                        raise UserError(_('Credit Over Limits !\n' + msg))
                    else:
                        if total_used > commercial_id.credit_limit + commercial_id.parameter_amount:
                            msg = 'Can not validate Invoice, Credit Limit exceeded, ' \
                            'Over Limit %s !\nCheck Partner Credit ' \
                            'Limits !' % (commercial_id.credit_limit + commercial_id.parameter_amount - debit)
                            raise UserError(_('Credit Over Limits !\n' + msg))

                        #raise UserWarning(_('Credit Over Limits !\n' + msg1))
                        #partner.write({'credit_limit': credit - debit + self.amount_total})

            return True

    def action_invoice_open(self):
        res = super(AccountInvoice, self).action_invoice_open()
        for order in self:
            order.check_limit()
        return res

