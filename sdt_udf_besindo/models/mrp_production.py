from odoo import api, fields, models, _ , SUPERUSER_ID
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_round, format_datetime


class MRPProduction(models.Model):
    _inherit = "mrp.production"

    contact = fields.Many2one("res.partner", string="Contact", domain=[('category_id.name','=','Customer')], required=True)
    label_qty = fields.Integer(string='Label Print Quantity')
    label_qty_per_pack = fields.Integer(string='Quantity per Pack')
    label_part_num = fields.Char(string='Part Number')

    @api.onchange('workorder_ids','workorder_ids.workcenter_id')
    def _onchange_workcenter_id(self):
        for workorder_id in self.workorder_ids :
            if workorder_id.workcenter_id :
                mrp_routing_workcenter_obj = self.env['mrp.routing.workcenter'].search([('workcenter_id', '=', workorder_id.workcenter_id.id)], limit=1)
                if mrp_routing_workcenter_obj :
                    for mrp_routing_workcenter in mrp_routing_workcenter_obj :
                        workorder_id.name = mrp_routing_workcenter.name
                else :
                    pass
            else :
                workorder_id.name = ""

    @api.onchange('contact')
    def _onchange_contact(self):
        if self.picking_ids:
            for pick in self.picking_ids:
                test1 = '%s - %s'%(pick.id, pick.partner_id.name)
                test2 = '%s - %s'%(self.id, self.contact.name)
                print(test1)
                print(test2)
                pick._mrp_update_partner_id(pick.name, self.contact)
                test1 = '%s - %s'%(pick.id, pick.partner_id.name)
                print(test1)

    def action_confirm(self):
        self._check_company()
        for production in self:
            if production.bom_id:
                production.consumption = production.bom_id.consumption
            # In case of Serial number tracking, force the UoM to the UoM of product
            if production.product_tracking == 'serial' and production.product_uom_id != production.product_id.uom_id:
                production.write({
                    'product_qty': production.product_uom_id._compute_quantity(production.product_qty, production.product_id.uom_id),
                    'product_uom_id': production.product_id.uom_id
                })
                for move_finish in production.move_finished_ids.filtered(lambda m: m.product_id == production.product_id):
                    move_finish.write({
                        'product_uom_qty': move_finish.product_uom._compute_quantity(move_finish.product_uom_qty, move_finish.product_id.uom_id),
                        'product_uom': move_finish.product_id.uom_id
                    })
            production.move_raw_ids._adjust_procure_method()
            (production.move_raw_ids | production.move_finished_ids)._action_confirm(merge=False)
            production.workorder_ids._action_confirm()
        # run scheduler for moves forecasted to not have enough in stock
        self.move_raw_ids._trigger_scheduler()
        self.picking_ids.filtered(
            lambda p: p.state not in ['cancel', 'done']).action_confirm()
        # Force confirm state only for draft production not for more advanced state like
        # 'progress' (in case of backorders with some qty_producing)
        self.filtered(lambda mo: mo.state == 'draft').state = 'confirmed'
        
        for pick in self.picking_ids:
            pick.partner_id = self.contact
        return True

class MRPWorkOrder(models.Model):
    _inherit = "mrp.workorder"


    operator_factory_ids = fields.Many2many('sdt.operator.factory', string='Operator Factory')
    qty_remaining2 = fields.Float('Quantity to Produced', compute='_compute_qty_remaining2', digits='Product Unit of Measure', store=True)
    shift = fields.Selection([('shift_1', 'Shift 1'), ('shift_2', 'Shift 2'), ('shift_3', 'Shift 3')], string="Shift", required=True, default='shift_1')


    @api.depends('qty_production', 'qty_reported_from_previous_wo', 'qty_produced', 'production_id.product_uom_id')
    def _compute_qty_remaining2(self):
        for wo in self:
            if wo.production_id.product_uom_id:
                wo.qty_remaining2 = max(float_round(wo.qty_production - wo.qty_reported_from_previous_wo - wo.qty_produced, precision_rounding=wo.production_id.product_uom_id.rounding), 0)
            else:
                wo.qty_remaining2 = 0

    
    
    
    