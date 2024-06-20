from odoo import api, fields, models, _ , SUPERUSER_ID
from odoo.exceptions import UserError


class ApprovalCategory(models.Model):
    _inherit = "approval.category"

    approval_so = fields.Boolean(string='Approval SO',)
    overdue_so = fields.Boolean(string="Overdue")
    approval_po = fields.Boolean(string='Approval PO',)
    min_approve_lvl_2_po = fields.Float(string='Amount Min Lvl 2',)
    currency_id = fields.Many2one('res.currency', 'Currency',)
