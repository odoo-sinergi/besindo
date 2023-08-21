from odoo import api, Command, fields, models, _
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = "stock.picking"

    actual_date = fields.Datetime(string='Actual Delivery Date')
    workcenter_name = fields.Char(string='Workcenter Name', compute='_get_workcenter')
    is_qc_production = fields.Boolean(string='Is QC Production',related='picking_type_id.is_qc_production',readonly=True, store=True)
    different_delivery_date = fields.Boolean(string='Different Delivery Date',related='picking_type_id.different_delivery_date',readonly=True, store=True)

    @api.depends('location_id','location_dest_id','date_done','move_ids_without_package','scheduled_date')
    def _get_workcenter(self):
        # self.name = self.name
        for rec in self :
            if rec.is_qc_production == True :
                mrp_obj = self.env['mrp.production'].search([('name', '=', rec.group_id.name)])
                for workorder_id in mrp_obj.workorder_ids :
                    if not rec.workcenter_name :
                        rec.workcenter_name = workorder_id.workcenter_id.name
                    else :
                        rec.workcenter_name = rec.workcenter_name + '  ' +'||' + '  ' + workorder_id.workcenter_id.name
            elif rec.is_qc_production == False :
                rec.workcenter_name = '-'
    
class StockMove(models.Model):
    _inherit = "stock.move"

    alasan_selisih = fields.Char(string='Alasan Selisih',)
        