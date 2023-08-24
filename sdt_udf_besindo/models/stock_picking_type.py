from odoo import api, Command, fields, models, _
from odoo.exceptions import UserError


class StockPickingType(models.Model):
    _inherit = "stock.picking.type"

    
    is_qc_production = fields.Boolean(string='Is QC Production',)
    different_delivery_date = fields.Boolean(string='Different Delivery Date')
    is_alasan_selisih = fields.Boolean(string='Alasan Selisih Quantity', default=False)