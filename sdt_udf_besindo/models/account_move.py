from odoo import api, fields, models, _ , SUPERUSER_ID
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = "account.move"

    amount_ppn = fields.Monetary(
        string='PPN',
        compute='_compute_tax_totals', store=True, readonly=True,
        inverse='_inverse_amount_total',
    )
    amount_pph = fields.Monetary(
        string='PPH',
        compute='_compute_tax_totals', store=True, readonly=True,
        inverse='_inverse_amount_total',
    )

    sdt_partner_bank_ids = fields.Many2many(
        string='Detail Payment',
        comodel_name='res.partner.bank',
        relation='account_move_res_partner_bank_rel',
        column1='res_partner_bank_id',
        column2='account_move_id',
    )

    do_number = fields.Char(string='Do Number',)
    hs_code = fields.Char(string='HS Code',)
    no_faktur_pajak = fields.Char(string='Tax Invoice Number',)
    date_payment = fields.Date(string='Paid Date', store=True, )
    

    def _compute_date_payment(self):
        for record in self:
            if record.payment_state == 'paid' :
                payment_obj = self.env['account.payment'].search([('ref', '=', record.name)], order='date desc', limit=1)
                if payment_obj :
                    for payment in payment_obj :
                        if not record.date_payment :
                            record.date_payment = payment.date
                        else :
                            # pass
                            record.date_payment = payment.date
                else :
                    pass
            else :
                    pass
            
    # @api.depends('order_line.taxes_id', 'order_line.price_subtotal', 'amount_total', 'amount_untaxed')
    @api.depends(
        'invoice_line_ids.currency_rate',
        'invoice_line_ids.tax_base_amount',
        'invoice_line_ids.tax_line_id',
        'invoice_line_ids.price_total',
        'invoice_line_ids.price_subtotal',
        'invoice_payment_term_id',
        'partner_id',
        'currency_id',
    )
    def  _compute_tax_totals(self):
        """ Computed field used for custom widget's rendering.
            Only set on invoices.
        """
        res = super(AccountMove, self)._compute_tax_totals()
        for move in self:
            if move.tax_totals != False:
                if len(move.tax_totals['groups_by_subtotal']['Untaxed Amount']) > 1 :
                    for tax in move.tax_totals['groups_by_subtotal']['Untaxed Amount']:
                        if tax['tax_group_name'] == 'VAT':
                            move.amount_ppn = tax['tax_group_amount']
                        elif tax['tax_group_name'] == 'PPh':
                            move.amount_pph = tax['tax_group_amount']
                elif len(move.tax_totals['groups_by_subtotal']['Untaxed Amount']) == 1 :
                    for tax in move.tax_totals['groups_by_subtotal']['Untaxed Amount']:
                        if tax['tax_group_name'] == 'VAT':
                            move.amount_ppn = tax['tax_group_amount']
                            move.amount_pph = 0
                        elif tax['tax_group_name'] == 'PPh':
                            move.amount_pph = tax['tax_group_amount']
                            move.amount_ppn = 0
                else:
                    move.amount_ppn = 0
                    move.amount_pph = 0
            else:
                move.amount_ppn = 0
                move.amount_pph = 0
        self._compute_date_payment()
        return res