
from odoo import models, fields

class StockLocation(models.Model):
    _inherit = 'stock.location'

    is_recalculate = fields.Boolean(string="Recalculate")