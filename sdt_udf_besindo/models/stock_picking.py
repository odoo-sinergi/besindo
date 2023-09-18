from odoo import api, Command, fields, models, _
from odoo.exceptions import UserError
from lxml import etree


class StockPicking(models.Model):
    _inherit = "stock.picking"

    actual_date = fields.Datetime(string='Actual Delivery Date')
    workcenter_name = fields.Char(string='Workcenter Name', compute='_get_workcenter')
    is_qc_production = fields.Boolean(string='Is QC Production',related='picking_type_id.is_qc_production',readonly=True, store=True)
    different_delivery_date = fields.Boolean(string='Different Delivery Date',related='picking_type_id.different_delivery_date',readonly=True, store=True)
    is_alasan_selisih = fields.Boolean(string='Alasan Selisih Quantity',related='picking_type_id.is_alasan_selisih',readonly=True, store=True)
    mrp_date = fields.Datetime(string="Manufatured Date", compute='_compute_mrp_date')

    @api.depends('location_id','location_dest_id','date_done','move_ids_without_package','scheduled_date')
    def _get_workcenter(self):
        for rec in self :
            if rec.is_qc_production == True :
                if rec.group_id.name:
                    mrp_obj = self.env['mrp.production'].search([('name', '=', rec.group_id.name)])
                    if mrp_obj.workorder_ids :
                        for workorder_id in mrp_obj.workorder_ids :
                            if not rec.workcenter_name :
                                rec.workcenter_name = workorder_id.workcenter_id.name
                            else :
                                rec.workcenter_name = rec.workcenter_name + '  ' +'||' + '  ' + workorder_id.workcenter_id.name
                    else :
                        rec.workcenter_name = '-'
                else:
                    rec.workcenter_name = '-'
            elif rec.is_qc_production == False :
                rec.workcenter_name = '-'
    
    @api.onchange('origin')
    def fill_line_description(self):
        if self.origin:
            sales_order_id = self.env['sale.order'].search([('name', '=', self.origin)])
            order_line = sales_order_id.order_line
            if order_line and self.move_ids:
                for line in order_line:
                    for move in self.move_ids:
                        if move.product_id == line.product_id:
                            move.description_picking = line.name
                            break
        self._compute_move_without_package()
        
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
    
    @api.depends('mrp_id')
    def _compute_mrp_date(self):
        for rec in self:
            if rec.mrp_id:
                rec.mrp_date = rec.mrp_id.mrp_date
            else:
                rec.mrp_date = False
            rec.compute_line_description = False
            if rec.origin:
                order_line = rec.sale_id.order_line if rec.sale_id else False
                if order_line and rec.move_ids:
                    for line in order_line:
                        for move in rec.move_ids:
                            if move.product_id == line.product_id:
                                move.description_picking = line.name
                                rec.compute_line_description = True
                                break
            rec._compute_move_without_package()
    
class StockMove(models.Model):
    _inherit = "stock.move"

    alasan_selisih = fields.Char(string='Alasan Selisih')
    desctription_so = fields.Char(string='Description from SO', compute='_compute_description_so')
    
    def action_assign_alasan_selisih(self):
        self.ensure_one()
        params = {'move_id':self.id}
        view_id = self.env['stock.move.alasan.selisih']
        new = view_id.create(params)
        return {
            'name': _('Alasan Selisih'),
            'type': 'ir.actions.act_window',
            'res_model': 'stock.move.alasan.selisih',
            'res_id': new.id,
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('sdt_udf_besindo.alasan_selisih_wizard',False).id,
            'target': 'new',
        }
    
    @api.depends('picking_id.sale_id')
    def _compute_description_so(self):
        for move in self:
            move.description_so = False
            if move.picking_id.sale_id:
                if move.picking_id.sale_id.order_line:
                    for line in move.picking_id.sale_id.order_line:
                        if move.product_id == line.product_id:
                            move.description_so = line.name
                            move._description_picking = move.description_so
                            break