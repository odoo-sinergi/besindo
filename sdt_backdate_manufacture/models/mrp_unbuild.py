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
                                old_sequence = self.env['ir.sequence.date_range'].search([('date_from', '=', name[1]), ('sequence_id', '=', seq.id)])
                                query = """update account_move set name = %s , date = %s where id = %s"""
                                seq = self.env['ir.sequence'].search([('name', '=', 'STJ Sequence')])
                                new_sequence = seq.next_by_id(user_date)
                                self.env.cr.execute(query, (new_sequence, str(user_date), account.id))
                                old_sequence.number_next_actual = old_sequence.number_next_actual - 1
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
                                old_sequence = self.env['ir.sequence.date_range'].search([('date_from', '=', name[1]), ('sequence_id', '=', seq.id)])
                                query = """update account_move set name = %s , date = %s where id = %s"""
                                seq = self.env['ir.sequence'].search([('name', '=', 'STJ Sequence')])
                                new_sequence = seq.next_by_id(user_date)
                                self.env.cr.execute(query, (new_sequence, str(user_date), account.id))
                                old_sequence.number_next_actual = old_sequence.number_next_actual - 1
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
                if account:
                    name = account.name.split('/')
                    if name[0] == 'STJ' and name[1] != str(user_date.year):
                        old_sequence = self.env['ir.sequence.date_range'].search([('date_from', '=', name[1]), ('sequence_id', '=', seq.id)])
                        query = """update account_move set name = %s , date = %s where id = %s"""
                        seq = self.env['ir.sequence'].search([('name', '=', 'STJ Sequence')])
                        new_sequence = seq.next_by_id(user_date)
                        self.env.cr.execute(query, (new_sequence, str(user_date), account.id))
                        old_sequence.number_next_actual = old_sequence.number_next_actual - 1
                        for account_line in account.invoice_line_ids:
                            account_line.write({'date': user_date})
                    else:
                        account.write({'date': user_date})
                        for account_line in account.invoice_line_ids:
                            account_line.write({'date': user_date})
        
        for move in self.unbuild_id.consume_line_ids:
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
                if account:
                    name = account.name.split('/')
                    if name[0] == 'STJ' and name[1] != str(user_date.year):
                        old_sequence = self.env['ir.sequence.date_range'].search([('date_from', '=', name[1]), ('sequence_id', '=', seq.id)])
                        query = """update account_move set name = %s , date = %s where id = %s"""
                        seq = self.env['ir.sequence'].search([('name', '=', 'STJ Sequence')])
                        new_sequence = seq.next_by_id(user_date)
                        self.env.cr.execute(query, (new_sequence, str(user_date), account.id))
                        old_sequence.number_next_actual = old_sequence.number_next_actual - 1
                        for account_line in account.invoice_line_ids:
                            account_line.write({'date': user_date})
                    else:
                        account.write({'date': user_date})
                        for account_line in account.invoice_line_ids:
                            account_line.write({'date': user_date})