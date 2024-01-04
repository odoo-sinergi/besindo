from odoo import api, models, fields,_
from odoo.exceptions import UserError
import pytz
from datetime import datetime
from odoo.tools import float_compare, float_round

from collections import defaultdict

class SdtMrpUnbuild(models.Model):
    _inherit = "mrp.unbuild"

    unbuild_date = fields.Datetime('Date')

    @api.onchange('mo_id')
    def onchange_mo_id(self):
        if not self.mo_id:
            return
        
        else:
            self.location_id = self.mo_id.location_src_id.id
            self.location_dest_id = self.mo_id.location_dest_id.id
            if self.mo_id.lot_producing_id:
                self.lot_id = self.mo_id.lot_producing_id.id
    
    # def action_done(self):
    #     self.ensure_one()
    #     self._check_company()
    #     if self.product_id.tracking != 'none' and not self.lot_id.id:
    #         raise UserError(_('You should provide a lot number for the final product.'))

    #     if self.mo_id:
    #         if self.mo_id.state != 'done':
    #             raise UserError(_('You cannot unbuild a undone manufacturing order.'))

    #     consume_moves = self._generate_consume_moves()
    #     consume_moves._action_confirm()
    #     produce_moves = self._generate_produce_moves()
    #     produce_moves._action_confirm()

    #     finished_moves = consume_moves.filtered(lambda m: m.product_id == self.product_id)
    #     consume_moves -= finished_moves

    #     if any(produce_move.has_tracking != 'none' and not self.mo_id for produce_move in produce_moves):
    #         raise UserError(_('Some of your components are tracked, you have to specify a manufacturing order in order to retrieve the correct components.'))

    #     if any(consume_move.has_tracking != 'none' and not self.mo_id for consume_move in consume_moves):
    #         raise UserError(_('Some of your byproducts are tracked, you have to specify a manufacturing order in order to retrieve the correct byproducts.'))

    #     for finished_move in finished_moves:
    #         if finished_move.has_tracking != 'none':
    #             self.env['stock.move.line'].create({
    #                 'move_id': finished_move.id,
    #                 'lot_id': self.lot_id.id,
    #                 'qty_done': finished_move.product_uom_qty,
    #                 'product_id': finished_move.product_id.id,
    #                 'product_uom_id': finished_move.product_uom.id,
    #                 'location_id': finished_move.location_id.id,
    #                 'location_dest_id': finished_move.location_dest_id.id,
    #             })
    #         else:
    #             finished_move.quantity_done = finished_move.product_uom_qty

    #     # TODO: Will fail if user do more than one unbuild with lot on the same MO. Need to check what other unbuild has aready took
    #     qty_already_used = defaultdict(float)
    #     for move in produce_moves | consume_moves:
    #         if move.has_tracking != 'none':
    #             original_move = move in produce_moves and self.mo_id.move_raw_ids or self.mo_id.move_finished_ids
    #             original_move = original_move.filtered(lambda m: m.product_id == move.product_id)
    #             needed_quantity = move.product_uom_qty
    #             moves_lines = original_move.mapped('move_line_ids')
    #             if move in produce_moves and self.lot_id:
    #                 moves_lines = moves_lines.filtered(lambda ml: self.lot_id in ml.produce_line_ids.lot_id)  # FIXME sle: double check with arm
    #             for move_line in moves_lines:
    #                 # Iterate over all move_lines until we unbuilded the correct quantity.
    #                 taken_quantity = min(needed_quantity, move_line.qty_done - qty_already_used[move_line])
    #                 if taken_quantity:
    #                     self.env['stock.move.line'].create({
    #                         'move_id': move.id,
    #                         'lot_id': move_line.lot_id.id,
    #                         'qty_done': taken_quantity,
    #                         'product_id': move.product_id.id,
    #                         'product_uom_id': move_line.product_uom_id.id,
    #                         'location_id': move.location_id.id,
    #                         'location_dest_id': move.location_dest_id.id,
    #                     })
    #                     needed_quantity -= taken_quantity
    #                     qty_already_used[move_line] += taken_quantity
    #         else:
    #             move.quantity_done = float_round(move.product_uom_qty, precision_rounding=move.product_uom.rounding)

    #     finished_moves._action_done()
    #     consume_moves._action_done()
    #     produce_moves._action_done()
    #     produced_move_line_ids = produce_moves.mapped('move_line_ids').filtered(lambda ml: ml.qty_done > 0)
    #     consume_moves.mapped('move_line_ids').write({'produce_line_ids': [(6, 0, produced_move_line_ids.ids)]})
    #     if self.mo_id:
    #         unbuild_msg = _(
    #             "%(qty)s %(measure)s unbuilt in %(order)s",
    #             qty=self.product_qty,
    #             measure=self.product_uom_id.name,
    #             order=self._get_html_link(),
    #         )
    #         self.mo_id.message_post(
    #             body=unbuild_msg,
    #             subtype_id=self.env.ref('mail.mt_note').id)
    #     return self.write({'state': 'done'})

    def action_validate(self):

        if not self.unbuild_date:
            raise UserError("Isi field 'Date' terlebih dahulu")
        
        if self.produce_line_ids or self.consume_line_ids:
            if isinstance(self.unbuild_date, str) == True:
                self.unbuild_date = datetime.strptime(self.unbuild_date, "%Y-%m-%d %H:%M:%S")
            user_tz = self.env.user.tz or pytz.utc
            local = pytz.timezone(user_tz)
            local_date = pytz.utc.localize(self.unbuild_date).astimezone(local)
            user_date = local_date.replace(tzinfo=None)
            if self.produce_line_ids:
                for move in self.produce_line_ids:
                    move.write({'date': self.unbuild_date})
                    for line in move.move_line_ids:
                        line.write({'date': self.unbuild_date})

                    for rec in move.stock_valuation_layer_ids:
                        sql_query="""Update stock_valuation_layer set create_date=%s where stock_move_id=%s
                                """
                        self.env.cr.execute(sql_query,(self.unbuild_date,move.id))
                    
                    for account in move.account_move_ids:
                        if account:
                            name = account.name.split('/')
                            if name[0] == 'STJ' and name[1] != str(user_date.year):
                                query = """update account_move set name = %s , date = %s where id = %s"""
                                seq = self.env['ir.sequence'].search([('name', '=', 'STJ Sequence')])
                                new_sequence = seq.next_by_id(user_date)
                                self.env.cr.execute(query, (new_sequence, str(user_date), account.id))
                                for account_line in account.invoice_line_ids:
                                    account_line.write({'date': user_date})
                            else:
                                account.write({'date': user_date})
                                for account_line in account.invoice_line_ids:
                                    account_line.write({'date': user_date})

            if self.consume_line_ids:
                for move in self.consume_line_ids:
                    move.write({'date': self.unbuild_date})
                    for line in move.move_line_ids:
                        line.write({'date': self.unbuild_date})

                    for rec in move.stock_valuation_layer_ids:
                        sql_query="""Update stock_valuation_layer set create_date=%s where stock_move_id=%s
                                """
                        self.env.cr.execute(sql_query,(self.unbuild_date,move.id))
                    
                    for account in move.account_move_ids:
                        if account:
                            name = account.name.split('/')
                            if name[0] == 'STJ' and name[1] != str(user_date.year):
                                query = """update account_move set name = %s , date = %s where id = %s"""
                                seq = self.env['ir.sequence'].search([('name', '=', 'STJ Sequence')])
                                new_sequence = seq.next_by_id(user_date)
                                self.env.cr.execute(query, (new_sequence, str(user_date), account.id))
                                for account_line in account.invoice_line_ids:
                                    account_line.write({'date': user_date})
                            else:
                                account.write({'date': user_date})
                                for account_line in account.invoice_line_ids:
                                    account_line.write({'date': user_date})
        res = super(SdtMrpUnbuild, self).action_validate()
        return res
        

    
class SdtStockWarnInsufficientQtyUnbuild(models.TransientModel):
    _inherit = 'stock.warn.insufficient.qty.unbuild'

    def action_done(self):
        res = super(SdtStockWarnInsufficientQtyUnbuild, self).action_done()

        for move in self.unbuild_id.produce_line_ids:
            if isinstance(self.unbuild_id.unbuild_date, str) == True:
                self.unbuild_id.unbuild_date = datetime.strptime(self.unbuild_id.unbuild_date, "%Y-%m-%d %H:%M:%S")
            user_tz = self.env.user.tz or pytz.utc
            local = pytz.timezone(user_tz)
            local_date = pytz.utc.localize(self.unbuild_id.unbuild_date).astimezone(local)
            user_date = local_date.replace(tzinfo=None)

            move.write({'date': self.unbuild_id.unbuild_date})
            for line in move.move_line_ids:
                line.write({'date': self.unbuild_id.unbuild_date})
            
            for rec in move.stock_valuation_layer_ids:
                sql_query="""Update stock_valuation_layer set create_date=%s where stock_move_id=%s
                        """
                self.env.cr.execute(sql_query,(self.unbuild_id.unbuild_date,move.id))
            
            for account in move.account_move_ids:
                account.write({'date': user_date})
                for account_line in account.invoice_line_ids:
                    account_line.write({'date': user_date})

        


