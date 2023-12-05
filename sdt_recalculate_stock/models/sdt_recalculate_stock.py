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
                                (
                                    SELECT
                                    sq.id, sml.product_id, sml.reference, sq.location_id,
                                    sml.reserved_qty as move_line, sq.reserved_quantity as quant
                                FROM
                                    stock_move_line sml
                                JOIN
                                    stock_quant sq
                                ON              
                                    sml.product_id = sq.product_id
                                    AND sml.location_id = sq.location_id
                                    AND (sml.reserved_qty = sq.reserved_quantity + 0.01
                                    OR sml.reserved_qty = sq.reserved_quantity + 0.02)
                                WHERE
                                    sml.location_id = %s
                                    AND sml.state in ('partially_available','assigned')
                                    AND (sq.reserved_quantity + 0.01 <= sq.quantity OR sq.reserved_quantity + 0.02 <= sq.quantity)
                            ) x
                            WHERE 
                                q.id = x.id;
                            """%(loc.id)
            # test = self.env.cr.execute(sql_query)
            sql_query = """
                        SELECT
                            q.id, x.product_id, x.location_id, x.rqty, q.reserved_quantity, q.quantity, x.rqty - q.reserved_quantity AS diff
                        FROM
                            stock_quant q
                        JOIN
                            (
                            SELECT
                                product_id, location_id, SUM(reserved_uom_qty) AS rqty
                            FROM
                                stock_move_line
                            WHERE
                                state in ('partially_available', 'assigned')
                            GROUP BY
                                product_id, location_id
                            ) x
                        ON
                            x.product_id = q.product_id
                            AND
                                x.location_id = q.location_id
                        WHERE
                            x.rqty > q.reserved_quantity
                            AND
                                x.location_id = %s
                        ORDER BY
                            x.rqty ASC
                        """%(loc.id)
            self.env.cr.execute(sql_query)
            query_result = self._cr.dictfetchall()
            for result in query_result:
                sql_query = f"""
                                UPDATE
                                    stock_move_line as sml
                                SET
                                    reserved_uom_qty = sml.reserved_uom_qty - %s,
                                    reserved_qty = sml.reserved_uom_qty - %s
                                FROM
                                (
                                    SELECT
                                        id, product_id, reserved_uom_qty, reference, location_id, state
                                    FROM
                                        stock_move_line
                                    WHERE
                                        product_id = %s
                                        AND
                                            location_id = %s
                                        AND
                                            state in ('assigned', 'partially_available')
                                        AND
                                            reserved_uom_qty <> 0
                                    LIMIT 1
                                ) ml
                                WHERE sml.id = ml.id
                            """%(result['diff'], result['diff'], result['product_id'], loc.id)
                self.env.cr.execute(sql_query)
            return
