from odoo import api, models, fields,_
from odoo.exceptions import UserError
import pytz
from datetime import datetime


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
        
        res = super(SdtMrpUnbuild, self).action_validate()

        if self.produce_line_ids:
            if isinstance(self.unbuild_date, str) == True:
                self.unbuild_date = datetime.strptime(self.unbuild_date, "%Y-%m-%d %H:%M:%S")
            user_tz = self.env.user.tz or pytz.utc
            local = pytz.timezone(user_tz)
            local_date = pytz.utc.localize(self.unbuild_date).astimezone(local)
            user_date = local_date.replace(tzinfo=None)

            for move in self.produce_line_ids:
                move.write({'date': self.unbuild_date})
                for line in move.move_line_ids:
                    line.write({'date': self.unbuild_date})

                for rec in move.stock_valuation_layer_ids:
                    sql_query="""Update stock_valuation_layer set create_date=%s where stock_move_id=%s
                            """
                    self.env.cr.execute(sql_query,(self.unbuild_date,move.id))
                
                for account in move.account_move_ids:
                    account.write({'date': user_date})
                    for account_line in account.invoice_line_ids:
                        account_line.write({'date': user_date})
        else:
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

        


