# See LICENSE file for full copyright and licensing details.


from odoo import _, api, models, fields
from odoo.exceptions import UserError,ValidationError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    over_credit = fields.Boolean('Over Credit?', dafault=False, copy=False)
    # approval
    approval_bod = fields.Many2one('res.users',string='Approved by BOD', copy=False,
        domain=lambda self: [
            (
                "groups_id",
                "in",
                self.env.ref("partner_credit_limit.sale_order_approval").id,
            )
        ])
    approval_bod_time = fields.Datetime(string='Approved (Time)', copy=False)
    approval_bod_state = fields.Selection(
        string='State',
        selection=[
            ('draft', 'Draft'),
            ('waiting', 'Waiting'),
            ('approved', 'Approved'),
            ('refuse', 'Refused'),
            ], default='draft',copy=False, readonly=True)
    has_approve = fields.Boolean(string="Has Access To Approve", compute="_compute_has_approve")
    show_req_approval = fields.Boolean(string='Show Approval', compute='_get_show_req_approval')

    def _get_show_req_approval(self):
        for data in self:
            if not data.over_credit and not data.over_due_date:
                data.show_req_approval = False
            else:
                if data.approval_bod_state != 'draft':
                    data.show_req_approval = False
                else:
                    if data.over_credit or data.over_due_date:
                        data.show_req_approval = True
    
    def _compute_has_approve(self):
        for request in self:
            request.check_amount()
            if request.approval_bod == self.env.user:
                request.has_approve = True
            else:
                request.has_approve = False

    def _get_user_approval_activities(self, user):
        domain = [
            ('res_model', '=', 'sale.order'),
            ('res_id', 'in', self.ids),
            ('activity_type_id', '=', 4),
            ('user_id', '=', user.id)
        ]
        activities = self.env['mail.activity'].search(domain)
        return activities
    
    def action_request_approval(self):
        for data in self:
            if not data.approval_bod:
                raise ValidationError(_('Please select a User for Approval.'))
            data.write({'approval_bod_state': 'waiting',})
            data.activity_schedule(
                'mail.mail_activity_todo',
                user_id=data.approval_bod.id,
                summary='Sale Order: To Approve')
    
    def action_approve(self):
        for data in self:
            data.write({'approval_bod_time': fields.Datetime.now(),
                        'approval_bod_state': 'approved',})
            data.sudo()._get_user_approval_activities(user=data.env.user).action_feedback()
            data.action_confirm()
    
    def action_refuse(self):
        for order in self:
            order.check_limit()
            order.write({'approval_bod_time': fields.Datetime.now(),
                        'approval_bod_state': 'refuse',})
            order.sudo()._get_user_approval_activities(user=order.env.user).action_feedback()
            order.action_cancel()
    
    def action_reset_approval(self):
        for order in self:
            order.check_limit()
            order.write({'approval_bod_time': False,
                        'approval_bod_state': 'draft',})
    
    def check_blocking_limit(self, available_credit_limit):
        self.ensure_one()
        if self.over_credit == True and self.approval_bod_state != 'approved':
            amount = f"{available_credit_limit:,}"
            credit_limit = f"{self.partner_id.credit_limit:,}"
            msg = 'Your available credit limit' \
                ' Amount = %s \nCustomer "%s" Credit Limit = %s ' \
                'Limits.' % (amount,
                            self.partner_id.name,credit_limit)
            raise ValidationError(_("Can't confirm Sale Order.\n" + msg))
    
    def check_limit(self):
        self.ensure_one()
        partner = self.partner_id
        partner_inv = self.partner_invoice_id
        user_id = self.env['res.users'].search([
            ('partner_id', '=', partner.id)], limit=1)
        if user_id and not user_id.has_group('base.group_portal') or not \
                user_id:
            moveline_obj = self.env['account.move.line']
            movelines = moveline_obj.search(
                ['|',('partner_id', '=', partner_inv.id),('partner_id', '=', partner.id),
                ('account_id.user_type_id.name', 'in',
                    ['Receivable', 'Payable']),('company_id','=',self.company_id.id),('parent_state','=','posted')])
            confirm_sale_order = self.search(
                [('partner_id', '=', partner.id),('state', '=', 'sale'),('company_id','=',self.company_id.id),
                ('invoice_status', '!=', 'invoiced'),('state_order', '!=', 'close')])

            debit, credit = 0.0, 0.0
            amount_total = 0.0
            if self.id not in confirm_sale_order.ids and self.state == 'draft':
                amount_total += self.amount_total

            for status in confirm_sale_order:
                if status.invoice_ids:
                    invoiced = sum(status.invoice_ids.mapped("amount_total"))
                    not_invoiced = status.amount_total - invoiced
                    amount_total += not_invoiced
                else:
                    amount_total += status.amount_total

            for line in movelines:
                credit += line.credit
                debit += line.debit
            
            partner_credit_limit = (
                debit + amount_total) - credit
            available_credit_limit = round(
                partner.credit_limit - partner_credit_limit, 2)
            if partner_credit_limit > partner.credit_limit and partner.credit_limit > 0.0:
                # if not partner.over_credit:
                self.over_credit = True
            else:
                self.over_credit = False

            return available_credit_limit

    @api.constrains('amount_total')
    def check_amount(self):
        for order in self:
            order.check_limit()
            # order.check_top(False)

    @api.model
    def create(self, vals):
        res = super(SaleOrder, self).create(vals)
        if res.partner_id.credit_limit > 0.0 and \
                not res.partner_id.over_credit:
            res.check_limit()
        res.check_top(False)
        return res
    
    def action_draft(self):
        res = super(SaleOrder, self).action_draft()
        for order in self:
            order.check_limit()
            order.check_top(False)
            order.action_reset_approval()
        return res
    
    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        for order in self:
            available_credit_limit = order.check_limit()
            order.check_blocking_limit(available_credit_limit)
        return res
