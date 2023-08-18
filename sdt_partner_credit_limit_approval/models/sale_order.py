
from odoo import fields, api, models, _
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    is_credit_limit = fields.Boolean(string='Is Credit Limit', compute='_compute_is_credit_limit', store=True)
    hide_button_confirm = fields.Boolean(string='Hide Button Confirm', compute='_compute_hide_button_confirm')
    is_approve_limit = fields.Boolean(string='Is Approve Limit')
    approval_id = fields.Many2one('approval.request', string='Approval Request')


    @api.depends('amount_total','currency_id','company_id','date_order')
    def _compute_is_credit_limit(self):
        for data in self:
            is_credit_limit = False
            if data.partner_id.credit_limit:
                amount_total_currency = data.currency_id._convert(data.tax_totals['amount_total'], data.company_id.currency_id, data.company_id, data.date_order)
                if amount_total_currency > (data.partner_id.credit_limit-data.partner_id.credit):
                    is_credit_limit = True
            data.is_credit_limit = is_credit_limit


    @api.depends('is_credit_limit','is_approve_limit')
    def _compute_hide_button_confirm(self):
        for data in self:
            hide_button_confirm = False
            if data.is_credit_limit == False:
                hide_button_confirm = False
            elif data.is_credit_limit == True and data.is_approve_limit == False:
                hide_button_confirm = True
            data.hide_button_confirm = hide_button_confirm


    def action_approval_limit(self):
        for data in self:
            approval_req_obj = self.env['approval.request']
            approval_category = self.env.ref('sdt_partner_credit_limit_approval.approval_category_data_partner_credit_limit')
            amount_total_currency = data.currency_id._convert(data.tax_totals['amount_total'], data.company_id.currency_id, data.company_id, data.date_order)
            new_approval_request = approval_req_obj.sudo().create({
                'date' : fields.Datetime.now(),
                'reference':data.name,
                'category_id' : approval_category.id,
                'partner_id' : data.partner_id.id,
                'request_owner_id' : data.env.uid,
                'request_status' : 'pending',
                'amount' : amount_total_currency,
            })
            new_approval_request.action_confirm()
            data.approval_id = new_approval_request.id
