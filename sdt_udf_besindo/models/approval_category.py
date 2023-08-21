from odoo import api, fields, models, _ , SUPERUSER_ID
from odoo.exceptions import UserError


class ApprovalCategory(models.Model):
    _inherit = "approval.category"

    approval_so = fields.Boolean(string='Approval SO',)
    approval_po = fields.Boolean(string='Approval PO',)
