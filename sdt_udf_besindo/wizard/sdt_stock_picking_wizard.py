from odoo import api, fields, models, _
from odoo.exceptions import UserError

class StockMoveAlasanSelisih(models.TransientModel):
    _name="stock.move.alasan.selisih"

    move_id = fields.Many2one('stock.move', readonly=True)
    product_id = fields.Many2one('product.product', 'Product', related='move_id.product_id', readonly=True)
    product_uom_qty = fields.Float('Demand', related='move_id.product_uom_qty', readonly=True)
    quantity_done = fields.Float('Done', related='move_id.quantity_done', readonly=True)
    product_uom_id = fields.Many2one('uom.uom', related='move_id.product_uom', readonly=True)
    alasan_selisih=fields.Char('Alasan Selisih', related='move_id.alasan_selisih', readonly=False)

    def action_save_button(self):
        test = self