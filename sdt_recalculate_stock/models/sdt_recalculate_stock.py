# -*- coding: utf-8 -*-

from odoo import api, models, fields
# from datetime import datetime

class RecalculateStock(models.TransientModel):
    _name = 'sdt.recalculate.stock'

    def recalculate_stock_reserved(self):
        # today= datetime.today().strftime('%Y-%m-%d')
        loc_obj = self.env['stock.location'].search([('is_recalculate', '=', True)])
        for loc in loc_obj:
            sql_query = """UPDATE
                                stock_quant as q
                            SET
                                reserved_quantity = x.move_line
                            FROM
                                (SELECT
                                    sq.id, sml.product_id, sml.reference, sq.location_id,
                                    sml.qty_done as move_line, sq.reserved_quantity as quant
                                FROM
                                    stock_move_line sml
                                JOIN
                                    stock_quant sq
                                ON              
                                    sml.product_id = sq.product_id
                                    AND sml.location_id = sq.location_id
                                    AND (sml.qty_done = sq.reserved_quantity + 0.01
                                    OR sml.qty_done = sq.reserved_quantity + 0.02)
                                WHERE
                                    sml.location_id = %s
                                    AND sml.state in ('assigned')
                                    AND (sq.reserved_quantity + 0.01 <= sq.quantity OR sq.reserved_quantity + 0.02 <= sq.quantity)) x
                            WHERE 
                                q.id = x.id;
                            """%(loc.id)
            test = self.env.cr.execute(sql_query)
            return test
