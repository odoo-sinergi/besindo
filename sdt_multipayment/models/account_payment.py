from odoo import fields, models, api, _
from datetime import datetime
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import formatLang, format_date, get_lang

class AccountMoveLine(models.Model):
    _inherit='account.move.line'

    @api.model
    def _get_default_line_name(self, document, amount, currency, date, partner=None):
        ''' Helper to construct a default label to set on journal items.

        E.g. Vendor Reimbursement $ 1,555.00 - INV001.

        :param document:    A string representing the type of the document.
        :param amount:      The document's amount.
        :param currency:    The document's currency.
        :param date:        The document's date.
        :param partner:     The optional partner.
        :return:            A string.
        '''
        # values = ['%s %s' % (document, formatLang(self.env, amount, currency_obj=currency))]
        values = ['%s ' % (document)]
        if partner:
            values.append(partner.display_name)
        return ' - '.join(values)

class AccountPayment(models.Model):
    _inherit='account.payment'

    multi_payment = fields.Boolean(string="Multi Payment",default=False)
    payment_wizard_id = fields.Integer(string="Payment Wizard ID")
    faktur = fields.Char(string='Faktur')
    

    def _prepare_move_line_default_vals(self, write_off_line_vals=None):
        res = super(AccountPayment, self)._prepare_move_line_default_vals(write_off_line_vals=None)
        for recs in self:
            if recs.multi_payment != True:
                return super(AccountPayment, self)._prepare_move_line_default_vals(write_off_line_vals=write_off_line_vals)

            if recs.currency_id.name != 'IDR':
                try:
                    # sql_query = """select rate from res_currency_rate where company_id=%s and currency_id=%s and name<=%s order by NAME desc limit 1
                    #         """
                    sql_query = """select inverse_rate from res_currency_rate where company_id=%s and currency_id=%s and name<=%s order by NAME desc limit 1
                            """
                    self.env.cr.execute(sql_query,
                                        (recs.company_id.id, recs.currency_id.id, recs.date,))
                    rate = self.env.cr.fetchone()[0] or 0.0
                except:
                    raise ValidationError(_('Rate for %s is not yet set..') % (self.currency_id.name))

            pay_wiz_obj=self.env['account.payment.register'].search([('id','=',recs.payment_wizard_id)], limit=1)
            amount_tot = pay_wiz_obj.amount_tot
            total_inv = pay_wiz_obj.source_amount
            opay_ids = []
            if pay_wiz_obj.opay_ids:
                for opay in pay_wiz_obj.opay_ids:
                    pay = {
                        'account_id': opay.mpacc_id.id,
                        'amount': opay.amount,
                        'label': opay.label,
                    }
                    opay_ids.append(pay)

            for line in opay_ids:
                # payment_display_name = {
                #     'outbound-customer': _("Customer Reimbursement"),
                #     'inbound-customer': _("Customer Payment"),
                #     'outbound-supplier': _("Vendor Payment"),
                #     'inbound-supplier': _("Vendor Reimbursement"),
                # }

                # default_line_name = self.env['account.move.line']._get_default_line_name(
                #     payment_display_name['%s-%s' % (recs.payment_type, recs.partner_type)],
                #     abs(line['amount']),
                #     recs.currency_id,
                #     recs.date,
                #     partner=recs.partner_id,
                # )
                if pay_wiz_obj.payment_type == 'inbound':
                    if line['amount'] < 0 :
                        if recs.currency_id.name != 'IDR':
                            amount = line['amount']*rate
                            rec_item = {'name': line['label'],
                                    'date_maturity': res[0]['date_maturity'],
                                    'amount_currency': line['amount'],
                                    'currency_id': res[0]['currency_id'],
                                    'debit': 0,
                                    'credit': -amount,
                                    'partner_id': res[0]['partner_id'],
                                    'account_id': line['account_id'],
                                    }
                        else:
                            rec_item = {'name': line['label'],
                                        'date_maturity': res[0]['date_maturity'],
                                        'amount_currency': line['amount'],
                                        'currency_id': res[0]['currency_id'],
                                        'debit': 0,
                                        'credit': -line['amount'],
                                        'partner_id': res[0]['partner_id'],
                                        'account_id': line['account_id'],
                                        }
                    else:
                        if recs.currency_id.name != 'IDR':
                            amount = line['amount']*rate
                            rec_item = {'name': line['label'],
                                    'date_maturity': res[0]['date_maturity'],
                                    'amount_currency': line['amount'],
                                    'currency_id': res[0]['currency_id'],
                                    'debit': amount,
                                    'credit': 0,
                                    'partner_id': res[0]['partner_id'],
                                    'account_id': line['account_id'],
                                    }
                        else:
                            rec_item = {'name': line['label'],
                                        'date_maturity': res[0]['date_maturity'],
                                        'amount_currency': line['amount'],
                                        'currency_id': res[0]['currency_id'],
                                        'debit': line['amount'],
                                        'credit': 0,
                                        'partner_id': res[0]['partner_id'],
                                        'account_id': line['account_id'],
                                        }
                    res.append(rec_item)
                elif pay_wiz_obj.payment_type == 'outbound':
                    if line['amount'] < 0 :
                        if recs.currency_id.name != 'IDR':
                            amount = line['amount']*rate
                            rec_item = {'name': line['label'],
                                    'date_maturity': res[0]['date_maturity'],
                                    'amount_currency': -line['amount'],
                                    'currency_id': res[0]['currency_id'],
                                    'debit': -amount,
                                    'credit': 0,
                                    'partner_id': res[0]['partner_id'],
                                    'account_id': line['account_id'],
                                    }
                        else:
                            rec_item = {'name': line['label'],
                                    'date_maturity': res[0]['date_maturity'],
                                    'amount_currency': -line['amount'],
                                    'currency_id': res[0]['currency_id'],
                                    'debit': -line['amount'],
                                    'credit': 0,
                                    'partner_id': res[0]['partner_id'],
                                    'account_id': line['account_id'],
                                    }
                    else:
                        if recs.currency_id.name != 'IDR':
                            amount = line['amount']*rate
                            rec_item = {'name': line['label'],
                                        'date_maturity': res[0]['date_maturity'],
                                        'amount_currency': -line['amount'],
                                        'currency_id': res[0]['currency_id'],
                                        'debit': 0,
                                        'credit': amount,
                                        'partner_id': res[0]['partner_id'],
                                        'account_id': line['account_id'],
                                        }
                        else:
                            rec_item = {'name': line['label'],
                                    'date_maturity': res[0]['date_maturity'],
                                    'amount_currency': -line['amount'],
                                    'currency_id': res[0]['currency_id'],
                                    'debit': 0,
                                    'credit': line['amount'],
                                    'partner_id': res[0]['partner_id'],
                                    'account_id': line['account_id'],
                                    }
                    res.append(rec_item)
            
            for rec in res:
                if pay_wiz_obj.payment_type == 'inbound':
                    if rec['credit'] > 0 and rec['account_id'] in pay_wiz_obj.line_ids.account_id.ids:
                        if recs.currency_id.name != 'IDR':
                            amount = amount_tot*rate
                        else:
                            amount = amount_tot
                        rec['credit'] = amount
                        rec['amount_currency'] = -amount_tot
                        payment_display_name = {
                            'outbound-customer': _("Customer Reimbursement"),
                            'inbound-customer': _("Customer Payment"),
                            'outbound-supplier': _("Vendor Payment"),
                            'inbound-supplier': _("Vendor Reimbursement"),
                        }

                        default_line_name = self.env['account.move.line']._get_default_line_name(
                            payment_display_name['%s-%s' % (recs.payment_type, recs.partner_type)],
                            abs(rec['amount_currency']),
                            recs.currency_id,
                            recs.date,
                            partner=recs.partner_id,
                        )
                        rec['name'] = default_line_name
                elif pay_wiz_obj.payment_type == 'outbound':
                    if rec['debit'] > 0 and rec['account_id'] in pay_wiz_obj.line_ids.account_id.ids:
                        if recs.currency_id.name != 'IDR':
                            amount = amount_tot*rate
                        else:
                            amount = amount_tot
                        rec['debit'] = amount
                        rec['amount_currency'] = amount_tot
                        payment_display_name = {
                            'outbound-customer': _("Customer Reimbursement"),
                            'inbound-customer': _("Customer Payment"),
                            'outbound-supplier': _("Vendor Payment"),
                            'inbound-supplier': _("Vendor Reimbursement"),
                        }

                        default_line_name = self.env['account.move.line']._get_default_line_name(
                            payment_display_name['%s-%s' % (recs.payment_type, recs.partner_type)],
                            abs(rec['amount_currency']),
                            recs.currency_id,
                            recs.date,
                            partner=recs.partner_id,
                        )
                        rec['name'] = default_line_name
            
            total_pay = 0.0
            for rec in res:
                total_pay += rec['credit']
            if recs.currency_id.name != 'IDR':
                recs.amount = total_pay/rate
            else:
                recs.amount = total_pay
            return res

    def _synchronize_to_moves(self, changed_fields):
        if self._context.get('skip_account_move_synchronization'):
            return

        for rec in self.with_context(skip_account_move_synchronization=True):
            if rec.multi_payment != True:
                return super(AccountPayment, self)._synchronize_to_moves(changed_fields)
    
    def _synchronize_from_moves(self, changed_fields):
        if self._context.get('skip_account_move_synchronization'):
            return

        multipayment = False
        for rec in self.with_context(skip_account_move_synchronization=True):
            if rec.multi_payment == True:
                multipayment = True
                break

        if multipayment != True:
            return super(AccountPayment, self)._synchronize_from_moves(changed_fields)
        
    def action_post(self):
        res = super(AccountPayment, self).action_post()
        for rec in self:
            if rec.faktur:
            # if rec.faktur and not rec.deposit_due:
                move_line_obj=self.env['account.move.line'].search([('payment_id','=',rec.id),('account_id','in',[rec.destination_account_id.id,rec.journal_id.default_account_id.id])])
                if move_line_obj:
                    faktur = rec.faktur.split(', ')
                    new_faktur = ""
                    faktur_obj=self.env['account.move'].search([('name','in',faktur),('move_type','=',"out_invoice")], order="id asc")
                    if faktur_obj and len(faktur_obj.ids) > 1:
                        tot_payment = rec.amount
                        for recs in faktur_obj:
                            tot_payment -= recs.amount_residual
                            if tot_payment < 0:
                                amount = f"{recs.amount_residual + tot_payment:,}"
                            else:
                                amount = f"{recs.amount_residual:,}"
                            new_faktur += recs.name + ':' + amount + ', '
                    for line in move_line_obj:
                        if faktur_obj:
                            if len(faktur_obj.ids) > 1:
                                name = line.name.split('-')[0]+ '- ' + faktur_obj.partner_id.name + ' - ' + new_faktur
                            else:
                                name = line.name.split('-')[0]+ '- ' + faktur_obj.partner_id.name + ' - ' + rec.faktur
                            line.write({'name':name})
                        else:
                            line.write({'name':line.name + ' - ' + rec.faktur})
        return res