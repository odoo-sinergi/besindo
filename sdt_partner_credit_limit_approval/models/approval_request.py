
from odoo import fields, api, models, _
from odoo.exceptions import UserError


class ApprovalRequest(models.Model):
    _inherit = "approval.request"


    def action_approve(self, approver=None):
        res = super().action_approve(approver=None)
        for data in self:
            status_lst = data.mapped('approver_ids.status')
            if status_lst.count('approved') >= data.approval_minimum:
                sale_order = self.env['sale.order'].search([('approval_id','=',data.id)])
                if sale_order:
                    sale_order.update({'is_approve_limit':True})
        return res

    