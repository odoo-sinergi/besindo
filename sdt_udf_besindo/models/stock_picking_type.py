from odoo import api, Command, fields, models, _
from odoo.exceptions import UserError


class StockPickingType(models.Model):
    _inherit = "stock.picking.type"

    
    is_qc_production = fields.Boolean(string='Is QC Production',)
    