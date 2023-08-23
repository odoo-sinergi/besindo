from odoo import api, Command, fields, models, _
from odoo.exceptions import UserError
from lxml import etree


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
    
    @api.model
    def get_view(self, view_id=None, view_type='form', **options):
        res = super(StockPicking, self).get_view(view_id=view_id, view_type=view_type, **options)
        if view_type == 'form':
            doc = etree.XML(res['arch'])
            validate_button = doc.xpath("//button[@name='button_validate']")
            context = self.env['stock.picking.type'].search([('name','=','RECEIPTS')]).id

            if not self.env.user.has_group('sdt_udf_besindo.group_picking_validate_qc'):
                validate_button[0].set('modifiers','{"invisible": ["|", ["picking_type_id", "=", '+str(context)+'], "|", ["state", "in", ["waiting", "confirmed"]], ["show_validate", "=", false]]}')
                validate_button[1].set('modifiers','{"invisible": ["|", ["picking_type_id", "=", '+str(context)+'], "|", ["state", "not in", ["waiting", "confirmed"]], ["show_validate", "=", false]]}')

            res['arch'] = etree.tostring(doc)
        return res
    
class StockMove(models.Model):
    _inherit = "stock.move"

    alasan_selisih = fields.Char(string='Alasan Selisih',)
        