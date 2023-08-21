from odoo import fields, models, api, _
from odoo.exceptions import UserError

class StockPicking(models.Model):
    _inherit='stock.picking'

    invoice_id = fields.Many2one('account.move',string='No. Invoice',)
