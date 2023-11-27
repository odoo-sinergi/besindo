# -*- coding: utf-8 -*-

from odoo import api, models, fields
# from datetime import datetime

class RecalculateStock(models.TransientModel):
    _name = 'sdt.recalculate.stock'

    def recalculate_stock_reserved(self):
        # today= datetime.today().strftime('%Y-%m-%d')
        loc_obj = self.env['stock.location'].search([('is_recalculate', '=', True)])
        for loc in loc_obj:
            sql_query = """UPDATE stock_quant SET reserved_quantity=0 WHERE location_id=%s;
                UPDATE stock_quant AS b SET reserved_quantity=a.product_qty
                FROM (SELECT product_id, location_id, sum(qty_done) AS product_qty
                    FROM stock_move_line
                    WHERE state in ('confirmed','assigned','partially_available')
                    GROUP BY product_id,location_id,result_package_id) a
                WHERE b.product_id=a.product_id AND b.location_id=a.location_id
                AND a.product_qty<>b.reserved_quantity and a.location_id=%s;
                """
            self.env.cr.execute(sql_query, (loc.id, loc.id))
