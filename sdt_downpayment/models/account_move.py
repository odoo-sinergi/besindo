# -*- coding: utf-8 -*-

from collections import defaultdict
from contextlib import ExitStack, contextmanager
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from hashlib import sha256
from json import dumps
import re
from textwrap import shorten
from unittest.mock import patch

from odoo import api, fields, models, _, Command
from odoo.addons.base.models.decimal_precision import DecimalPrecision
from odoo.addons.account.tools import format_rf_reference
from odoo.exceptions import UserError, ValidationError, AccessError, RedirectWarning
from odoo.tools import (
    date_utils,
    email_re,
    email_split,
    float_compare,
    float_is_zero,
    format_amount,
    format_date,
    formatLang,
    frozendict,
    get_lang,
    is_html_empty,
    sql
)


#forbidden fields
INTEGRITY_HASH_MOVE_FIELDS = ('date', 'journal_id', 'company_id')
INTEGRITY_HASH_LINE_FIELDS = ('debit', 'credit', 'account_id', 'partner_id')

TYPE_REVERSE_MAP = {
    'entry': 'entry',
    'out_invoice': 'out_refund',
    'out_refund': 'entry',
    'in_invoice': 'in_refund',
    'in_refund': 'entry',
    'out_receipt': 'entry',
    'in_receipt': 'entry',
}

EMPTY = object()


class AccountMove(models.Model):
    _inherit = 'account.move'

    dp_line_ids = fields.One2many(comodel_name="sdt.downpayment.lines", inverse_name="inv_id",
                                  string="Down Payment Lines", required=False, states={'open': [('readonly', False)]}, )

    amount_payment = fields.Monetary(currency_field='currency_id')

    @api.depends('move_type', 'line_ids.amount_residual')
    def _compute_payments_widget_reconciled_info(self):
        for move in self:
            # reconciled_vals = move._get_reconciled_info_JSON_values()
            # reconciled_vals = move._compute_payments_widget_reconciled_info()
            if move.state == 'posted' and move.is_invoice(include_receipts=True):
                reconciled_vals = []
                reconciled_partials = move._get_all_reconciled_invoice_partials()
                for reconciled_partial in reconciled_partials:
                    counterpart_line = reconciled_partial['aml']
                    if counterpart_line.move_id.ref:
                        reconciliation_ref = '%s (%s)' % (counterpart_line.move_id.name, counterpart_line.move_id.ref)
                    else:
                        reconciliation_ref = counterpart_line.move_id.name
                    if counterpart_line.amount_currency and counterpart_line.currency_id != counterpart_line.company_id.currency_id:
                        foreign_currency = counterpart_line.currency_id
                    else:
                        foreign_currency = False

                    reconciled_vals.append({
                        'name': counterpart_line.name,
                        'journal_name': counterpart_line.journal_id.name,
                        'amount': reconciled_partial['amount'],
                        'currency_id': move.company_id.currency_id.id if reconciled_partial['is_exchange'] else reconciled_partial['currency'].id,
                        'date': counterpart_line.date,
                        'partial_id': reconciled_partial['partial_id'],
                        'account_payment_id': counterpart_line.payment_id.id,
                        'payment_method_name': counterpart_line.payment_id.payment_method_line_id.name,
                        'move_id': counterpart_line.move_id.id,
                        'ref': reconciliation_ref,
                        # these are necessary for the views to change depending on the values
                        'is_exchange': reconciled_partial['is_exchange'],
                        'amount_company_currency': formatLang(self.env, abs(counterpart_line.balance), currency_obj=counterpart_line.company_id.currency_id),
                        'amount_foreign_currency': foreign_currency and formatLang(self.env, abs(counterpart_line.amount_currency), currency_obj=foreign_currency)
                    })
                if reconciled_vals:
                    # Add downpayment
                    unrecon = 'N'
                    for recon in reconciled_vals:
                        payment_id = recon['account_payment_id']
                        payment_obj = self.env['account.payment'].search([('id', '=', payment_id)])
                        if payment_obj.down_payment == True:
                            dp_obj = self.env['sdt.downpayment'].search([('payment_id', '=', payment_id)])
                            if dp_obj:
                                if dp_obj.state != 'close':
                                    close_obj = self.env['sdt.downpayment.lines'].search(
                                        [('dp_id', '=', dp_obj.id), ('inv_id', '=', self.id), ('state', '=', 'assigned')])
                                    if not close_obj:
                                        self.update_downpayment(recon, dp_obj)
                                unrecon = 'Y'
                    if unrecon == 'Y':
                        dp_line_obj = self.env['sdt.downpayment.lines'].search([('inv_id', '=', self.id),('state', '=', 'assigned')])
                        if dp_line_obj:
                            for dp in dp_line_obj:
                                dp_unlink = 'Y'
                                # if dp.state=='canceled':
                                #     sql_query="""Delete from sdt_downpayment_lines where id=%s;"""
                                #     self.env.cr.execute(sql_query,(dp.id,))
                                # dp.unlink()
                                for rec in reconciled_vals:
                                    if dp.dp_id.payment_id.id == rec['account_payment_id']:
                                        dp_unlink = 'N'
                                if dp_unlink == 'Y':
                                    inv_id = dp.close_move_id.id
                                    if inv_id != False:
                                        dp_id = dp.dp_id.id
                                        amount = dp.close_amount
                                        po = move.invoice_origin
                                        sql_query = """Delete from account_move where id=%s;"""
                                        self.env.cr.execute(sql_query, (inv_id,))
                                        sql_query = """Delete from account_move_line where move_id=%s;"""
                                        self.env.cr.execute(sql_query, (inv_id,))
                                        sql_query="""Update sdt_downpayment_lines set state='canceled' where dp_id=%s;"""
                                        #sql_query="""Delete from sdt_downpayment_lines where id=%s;"""
                                        self.env.cr.execute(sql_query, (dp_id,))
                                        sql_query = """
                                            Update sdt_downpayment set state='open',close_amount=close_amount-%s,balance_amount=balance_amount+%s where id=%s;
                                            """
                                        self.env.cr.execute(sql_query, (amount, amount, dp_id,))
                    else:
                        # Release downpayment
                        if move.state == 'posted':
                            if move.dp_line_ids:
                                dp_line_ids = move.dp_line_ids.filtered(lambda x: x.close_move_id)
                                if dp_line_ids:
                                    for line in dp_line_ids:
                                        dp_unlink = 'Y'
                                        for rec in reconciled_vals:
                                            if line.dp_id.payment_id.id == rec['account_payment_id']:
                                                dp_unlink = 'N'
                                        if dp_unlink == 'Y':
                                            inv_id = line.close_move_id
                                            if inv_id != False:
                                                domain = [('account_type', 'in', ('asset_receivable', 'liability_payable'))]
                                                payment_lines = line.dp_id.payment_id.journal_dp.line_ids.filtered_domain(domain)
                                                lines = inv_id.line_ids.filtered_domain(domain)

                                                if payment_lines.account_type == 'asset_receivable':
                                                    if len(payment_lines.matched_credit_ids.ids) > 1:
                                                        (lines).remove_move_reconcile()
                                                    else:
                                                        (payment_lines + lines).remove_move_reconcile()
                                                else:
                                                    if len(payment_lines.matched_debit_ids.ids) > 1:
                                                        (lines).remove_move_reconcile()
                                                    else:
                                                        (payment_lines + lines).remove_move_reconcile()

                                                amount = line.close_amount
                                                sql_query = """Delete from account_move where id=%s;"""
                                                self.env.cr.execute(sql_query, (inv_id.id,))
                                                sql_query = """Delete from account_move_line where move_id=%s;"""
                                                self.env.cr.execute(sql_query, (inv_id.id,))
                                                sql_query="""Update sdt_downpayment_lines set state='canceled' where id=%s;"""
                                                self.env.cr.execute(sql_query, (line.id,))
                                                sql_query = """
                                                    Update sdt_downpayment set state='open',close_amount=close_amount-%s,balance_amount=balance_amount+%s where id=%s;
                                                    """
                                                self.env.cr.execute(sql_query, (amount, amount, line.dp_id.id,))
                else:
                    # Release downpayment
                    if move.state == 'posted':
                        if move.dp_line_ids:
                            dp_line_ids = move.dp_line_ids.filtered(lambda x: x.close_move_id)
                            if dp_line_ids:
                                for line in dp_line_ids:
                                    reconciled_vals = move._get_reconciled_info_JSON_values()
                                    inv_id = line.close_move_id
                                    dp_id = line.dp_id.id
                                    amount = line.close_amount
                                    if inv_id != False:
                                        domain = [('account_type', 'in', ('asset_receivable', 'liability_payable'))]
                                        payment_lines = line.dp_id.payment_id.journal_dp.line_ids.filtered_domain(domain)
                                        lines = inv_id.line_ids.filtered_domain(domain)

                                        if payment_lines.account_type == 'asset_receivable':
                                            if len(payment_lines.matched_credit_ids.ids) > 1:
                                                (lines).remove_move_reconcile()
                                            else:
                                                (payment_lines + lines).remove_move_reconcile()
                                        else:
                                            if len(payment_lines.matched_debit_ids.ids) > 1:
                                                (lines).remove_move_reconcile()
                                            else:
                                                (payment_lines + lines).remove_move_reconcile()

                                        sql_query = """Delete from account_move where id=%s;"""
                                        self.env.cr.execute(sql_query, (inv_id.id,))
                                        sql_query = """Delete from account_move_line where move_id=%s;"""
                                        self.env.cr.execute(sql_query, (inv_id.id,))
                                        sql_query="""Update sdt_downpayment_lines set state='canceled' where id=%s;"""
                                        self.env.cr.execute(sql_query, (line.id,))
                                        sql_query = """
                                            Update sdt_downpayment set state='open',close_amount=close_amount-%s,balance_amount=balance_amount+%s where id=%s;
                                            """
                                        self.env.cr.execute(sql_query, (amount, amount, dp_id,))

        return super(AccountMove, self)._compute_payments_widget_reconciled_info()

    def update_downpayment(self, res, dp_aml_id):
        # update dp_state

        dp_id = dp_aml_id.id
        ref = dp_aml_id.ref
        flagPay = ''
        if dp_aml_id.payment_type == 'outbound':
            flagPay = 'outbound'
        elif dp_aml_id.payment_type == 'inbound':
            flagPay = 'inbound'

        # dp_aml_id=self.env['sdt.downpayment'].browse(dp_id)
        balance_currency = 0
        # residual_currency = 0
        # residual = self.amount_residual
        if self.currency_id.name != 'IDR':
            if dp_aml_id.payment_id.is_payment_rate and dp_aml_id.payment_id.rate:
                rate = dp_aml_id.payment_id.rate
            else:
                rate = dp_aml_id.rate

            currency = self.currency_id.id
            # residual_currency = self.amount_residual+dp_aml_id.balance_amount
            # residual_currency = residual
            if dp_aml_id.currency_id.name != 'IDR':
                balance = dp_aml_id.balance_amount*rate
                balance_currency = dp_aml_id.balance_amount
                dp_assigned = res['amount']*rate
            else:
                balance = dp_aml_id.balance_amount
                balance_currency = dp_aml_id.balance_amount/rate
                dp_assigned = res['amount']*rate
            dp_assigned_currency = res['amount']
            # residual = residual_currency*rate
        else:
            dp_assigned = res['amount']
            balance = dp_aml_id.balance_amount
            balance_currency = dp_aml_id.balance_amount
            # residual = self.amount_residual+dp_aml_id.balance_amount
            currency = False
            # residual_currency = 0
            dp_assigned_currency = res['amount']
        if balance > 0:
            if balance >= dp_assigned:
                # tambah account_move_line : journal pembalik dp
                # hutang vendor pada dp
                journal = dp_aml_id.journal_id

                line_ids = []
                debit_sum = 0.0
                credit_sum = 0.0
                account_id = ''

                # -> account journal tidak ada
                account_journal = self.env['account.journal']
                move = {
                    'name': '/',
                    'partner_id': dp_aml_id.partner_id.id,
                    'journal_id': journal.id,
                    # 'type':'entry',move_type
                    'move_type': 'entry',
                    'date': self.date,
                    'ref': '',
                }
                if flagPay == 'outbound':
                    # account_id = self.partner_id.property_account_liability_payable_id.id
                    account_id = dp_aml_id.control_account.id
                    debit_line = [0, 0, {
                        'move_id': self.id,
                        'name': dp_aml_id.dp_no,
                        'partner_id': dp_aml_id.partner_id.id,
                        'account_id': account_id,
                        'journal_id': journal.id,
                        'ref': ref,
                        'date': self.date,
                        'amount_currency': dp_assigned_currency,
                        'currency_id': currency,
                        'debit': dp_assigned,
                        'credit': 0.0,
                        # 'reconciled':True,
                        # 'payment_id':dp_aml_id.payment_id.id,
                        'account_type': 'other',
                        'currency_id': self.currency_id.id,
                        # 'exclude_from_invoice_tab': True,
                        # 'analytic_account_id': line['analytic_account_id'],
                    }]
                    # self.env['account.move.line'].create(debit_line)
                    line_ids.append(debit_line)

                    credit_line = [0, 0, {
                        'move_id': self.id,
                        'name': dp_aml_id.dp_no,
                        'partner_id': dp_aml_id.partner_id.id,
                        'account_id': dp_aml_id.account_dp.id,
                        'journal_id': journal.id,
                        'ref': ref,
                        'date': self.date,
                        'amount_currency': dp_assigned_currency*-1,
                        'currency_id': currency,
                        'debit': 0.0,
                        'credit': dp_assigned,
                        # 'reconciled':True,
                        # 'payment_id':dp_aml_id.payment_id.id,
                        'account_type': 'other',
                        'currency_id': self.currency_id.id,
                        # 'exclude_from_invoice_tab': True,
                        # 'analytic_account_id': line['analytic_account_id'],
                    }]
                    # self.env['account.move.line'].create(credit_line)
                    line_ids.append(credit_line)
                elif flagPay == 'inbound':
                    # account_id = self.partner_id.property_account_asset_receivable_id.id
                    account_id = dp_aml_id.control_account.id
                    debit_line = [0, 0, {
                        'move_id': self.id,
                        'name': dp_aml_id.dp_no,
                        'partner_id': dp_aml_id.partner_id.id,
                        'account_id': account_id,
                        'journal_id': journal.id,
                        'ref': ref,
                        'date': self.date,
                        'amount_currency': dp_assigned_currency*-1,
                        'currency_id': currency,
                        'debit': 0.0,
                        'credit': dp_assigned,
                        # 'reconciled':True,
                        # 'payment_id':dp_aml_id.payment_id.id,
                        'account_type': 'other',
                        'currency_id': self.currency_id.id,
                        # 'exclude_from_invoice_tab': True,
                        # 'analytic_account_id': line['analytic_account_id'],
                    }]
                    # self.env['account.move.line'].create(debit_line)
                    line_ids.append(debit_line)

                    credit_line = [0, 0, {
                        'move_id': self.id,
                        'name': dp_aml_id.dp_no,
                        'partner_id': dp_aml_id.partner_id.id,
                        'account_id': dp_aml_id.account_dp.id,
                        'journal_id': journal.id,
                        'ref': ref,
                        'date': self.date,
                        'amount_currency': dp_assigned_currency,
                        'currency_id': currency,
                        'debit': dp_assigned,
                        'credit': 0.0,
                        # 'reconciled':True,
                        # 'payment_id':dp_aml_id.payment_id.id,
                        'account_type': 'other',
                        'currency_id': self.currency_id.id,
                        # 'exclude_from_invoice_tab': True,
                        # 'analytic_account_id': line['analytic_account_id'],
                    }]
                    # self.env['account.move.line'].create(credit_line)
                    line_ids.append(credit_line)

                # self.env['account.move.line'].create(line_ids)
                move['line_ids'] = line_ids
                move_obj = self.env['account.move'].create(move)
                move_obj.action_post()
                #move_line_obj = self.env['account.move.line'].search([('move_id', '=', self.id),('payment_id','=',dp_aml_id.payment_id.id)])
                # sql_query = """Update account_move_line set reconciled=true, payment_id=%s where move_id=%s
                #     """
                # self.env.cr.execute(
                #     sql_query, (dp_aml_id.payment_id.id, move_obj.id,))

                # move_line_obj = self.env['account.move.line'].search([('move_id', '=', move_id.id),('payment_id','=',dp_aml_id.payment_id.id)])
                # if move_line_obj:
                #     move_line_obj.write({'reconciled':True})
                domain = [('account_type', 'in', ('asset_receivable', 'liability_payable')), ('reconciled', '=', False)]
                payment_lines = dp_aml_id.payment_id.journal_dp.line_ids.filtered_domain(domain)
                lines = move_obj.line_ids.filtered_domain(domain)
                for account in payment_lines.account_id:
                    (payment_lines + lines)\
                        .filtered_domain([('account_id', '=', account.id), ('reconciled', '=', False)])\
                        .reconcile()

                # simpan ke table downpayment_lines
                if dp_aml_id.currency_id.name != 'IDR':
                    dp_obj = self.env['sdt.downpayment.lines']
                    new_dp = dp_obj.create({
                        'inv_id': self.id,
                        'dp_id': dp_aml_id.id,
                        'date': self.date,
                        'currency_id': dp_aml_id.currency_id.id,
                        'account_dp': dp_aml_id.account_dp.id,
                        'dp_no': dp_aml_id.dp_no,
                        'close_amount': dp_assigned_currency,
                        'balance_amount': balance_currency-dp_assigned_currency,
                        'close_move_id': move_obj.id,
                        'state': 'assigned',
                    })
                else:
                    dp_obj = self.env['sdt.downpayment.lines']
                    new_dp = dp_obj.create({
                        'inv_id': self.id,
                        'dp_id': dp_aml_id.id,
                        'date': self.date,
                        'currency_id': dp_aml_id.currency_id.id,
                        'account_dp': dp_aml_id.account_dp.id,
                        'dp_no': dp_aml_id.dp_no,
                        'close_amount': dp_assigned,
                        'balance_amount': balance-dp_assigned,
                        'close_move_id': move_obj.id,
                        'state': 'assigned',
                    })
                # update table downpayment
                if dp_aml_id.currency_id.name != 'IDR':
                    dp_aml_id.write({'close_amount': dp_aml_id.close_amount +
                                    dp_assigned_currency, 'balance_amount': dp_aml_id.balance_amount-dp_assigned_currency})
                    if balance_currency-dp_assigned_currency <= 0:
                        dp_aml_id.write({'state': 'close'})
                else:
                    dp_aml_id.write({'close_amount': dp_aml_id.close_amount +
                                    dp_assigned, 'balance_amount': dp_aml_id.balance_amount-dp_assigned})
                    if balance-dp_assigned <= 0:
                        dp_aml_id.write({'state': 'close'})
            else:
                # buat journal pembalik dp
                # hutang vendor pada dp
                #account_journal = self.env['account.journal']
                journal = dp_aml_id.journal_id

                line_ids = []
                debit_sum = 0.0
                credit_sum = 0.0

                move = {
                    'name': '/',
                    'partner_id': dp_aml_id.partner_id.id,
                    'journal_id': journal.id,
                    # 'type':'entry',
                    'move_type': 'entry',
                    'date': self.date,
                    'ref': '',
                }

                if flagPay == 'outbound':
                    # account_id = self.partner_id.property_account_liability_payable_id.id
                    account_id = dp_aml_id.control_account.id
                    debit_line = {
                        'move_id': self.id,
                        'name': dp_aml_id.dp_no,
                        'partner_id': dp_aml_id.partner_id.id,
                        'account_id': account_id,
                        'journal_id': journal.id,
                        'ref': ref,
                        'date': self.date,
                        'amount_currency': balance_currency,
                        'currency_id': currency,
                        'debit': balance,
                        'credit': 0.0,
                        # 'reconciled':True,
                        # 'payment_id':dp_aml_id.payment_id.id,
                        'account_type': 'other',
                        'currency_id': self.currency_id.id,
                        # 'exclude_from_invoice_tab': True,
                        # 'analytic_account_id': line['analytic_account_id'],
                    }
                    # self.env['account.move.line'].create(debit_line)
                    line_ids.append(debit_line)

                    credit_line = {
                        'move_id': self.id,
                        'name': dp_aml_id.dp_no,
                        'partner_id': dp_aml_id.partner_id.id,
                        'account_id': dp_aml_id.account_dp.id,
                        'journal_id': journal.id,
                        'ref': ref,
                        'date': self.date,
                        'amount_currency': balance_currency*-1,
                        'currency_id': currency,
                        'debit': 0.0,
                        'credit': balance,
                        # 'reconciled':True,
                        # 'payment_id':dp_aml_id.payment_id.id,
                        'account_type': 'other',
                        'currency_id': self.currency_id.id,
                        # 'exclude_from_invoice_tab': True,
                        # 'analytic_account_id': line['analytic_account_id'],
                    }
                    # self.env['account.move.line'].create(credit_line)
                    line_ids.append(credit_line)
                elif flagPay == 'inbound':
                    # account_id = self.partner_id.property_account_asset_receivable_id.id
                    account_id = dp_aml_id.control_account.id
                    debit_line = {
                        'move_id': self.id,
                        'name': dp_aml_id.dp_no,
                        'partner_id': dp_aml_id.partner_id.id,
                        'account_id': account_id,
                        'journal_id': journal.id,
                        'ref': ref,
                        'date': self.date,
                        'amount_currency': balance_currency*-1,
                        'currency_id': currency,
                        'debit': 0.0,
                        'credit': balance,
                        # 'reconciled':True,
                        # 'payment_id':dp_aml_id.payment_id.id,
                        'account_type': 'other',
                        'currency_id': self.currency_id.id,
                        # 'exclude_from_invoice_tab': True,
                        # 'analytic_account_id': line['analytic_account_id'],
                    }
                    # self.env['account.move.line'].create(debit_line)
                    line_ids.append(debit_line)

                    credit_line = {
                        'move_id': self.id,
                        'name': dp_aml_id.dp_no,
                        'partner_id': dp_aml_id.partner_id.id,
                        'account_id': dp_aml_id.account_dp.id,
                        'journal_id': journal.id,
                        'ref': ref,
                        'date': self.date,
                        'amount_currency': balance_currency,
                        'currency_id': currency,
                        'debit': balance,
                        'credit': 0.0,
                        # 'reconciled':True,
                        # 'payment_id':dp_aml_id.payment_id.id,
                        'account_type': 'other',
                        'currency_id': self.currency_id.id,
                        # 'exclude_from_invoice_tab': True,
                        # 'analytic_account_id': line['analytic_account_id'],
                    }
                    # self.env['account.move.line'].create(credit_line)
                    line_ids.append(credit_line)
                self.env['account.move.line'].create(line_ids)

                move['line_ids'] = [0, 0, line_ids]
                move_obj = self.env['account.move'].create(move)
                move_obj.action_post()
                # move_line_obj = self.env['account.move.line'].search([('move_id', '=', self.id),('payment_id','=',dp_aml_id.payment_id.id)])
                # sql_query = """Update account_move_line set reconciled=true, payment_id=%s where move_id=%s
                #     """
                # self.env.cr.execute(
                #     sql_query, (dp_aml_id.payment_id.id, move_obj.id,))

                domain = [('account_type', 'in', ('asset_receivable', 'liability_payable')), ('reconciled', '=', False)]
                payment_lines = dp_aml_id.payment_id.journal_dp.line_ids.filtered_domain(domain)
                lines = move_obj.line_ids.filtered_domain(domain)
                for account in payment_lines.account_id:
                    (payment_lines + lines)\
                        .filtered_domain([('account_id', '=', account.id), ('reconciled', '=', False)])\
                        .reconcile()

                # move_line_obj = self.env['account.move.line'].search([('move_id', '=', move_id.id),('payment_id','=',dp_aml_id.payment_id.id)])
                # if move_line_obj:
                #     move_line_obj.write({'reconciled':True})

                # simpan ke table downpayment_lines
                if dp_aml_id.currency_id.name != 'IDR':
                    dp_obj = self.env['sdt.downpayment.lines']
                    new_dp = dp_obj.create({
                        'inv_id': self.id,
                        'dp_id': dp_aml_id.id,
                        'date': self.date,
                        'currency_id': dp_aml_id.currency_id.id,
                        'account_dp': dp_aml_id.account_dp.id,
                        'dp_no': dp_aml_id.dp_no,
                        'close_amount': dp_assigned_currency,
                        'balance_amount': balance_currency-dp_assigned_currency,
                        'close_move_id': move_obj.id,
                        'state': 'assigned',
                    })
                else:
                    dp_obj = self.env['sdt.downpayment.lines']
                    new_dp = dp_obj.create({
                        'inv_id': self.id,
                        'dp_id': dp_aml_id.id,
                        'date': self.date,
                        'currency_id': dp_aml_id.currency_id.id,
                        'account_dp': dp_aml_id.account_dp.id,
                        'dp_no': dp_aml_id.dp_no,
                        'close_amount': dp_assigned,
                        'balance_amount': balance-dp_assigned,
                        'close_move_id': move_obj.id,
                        'state': 'assigned',
                    })
                # update table downpayment
                if dp_aml_id.currency_id.name != 'IDR':
                    dp_aml_id.write({'close_amount': dp_aml_id.close_amount + dp_assigned_currency, 'balance_amount': dp_aml_id.balance_amount-dp_assigned_currency, 'state': 'open'})
                else:
                    dp_aml_id.write({'close_amount': dp_aml_id.close_amount + dp_assigned, 'balance_amount': dp_aml_id.balance_amount-dp_assigned, 'state': 'open'})

        return
