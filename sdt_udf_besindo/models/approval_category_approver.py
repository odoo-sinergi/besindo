import base64
from pickle import FALSE

from odoo import api, fields, models, tools, _
from odoo.modules.module import get_module_resource
from odoo.exceptions import UserError

class ApprovalCategoryApprover(models.Model):
    _inherit = 'approval.category.approver'
    _description = 'Approval Category Approver'

    
    lvl_approver = fields.Integer(string='Lvl Approver',)
    