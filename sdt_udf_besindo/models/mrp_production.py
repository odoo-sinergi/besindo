from odoo import api, fields, models, _ , SUPERUSER_ID
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_round, format_datetime


class MRPProduction(models.Model):
    _inherit = "mrp.production"

    

class MRPWorkOrder(models.Model):
    _inherit = "mrp.workorder"


    operator_factory_ids = fields.Many2many('sdt.operator.factory', string='Operator Factory')
    qty_remaining2 = fields.Float('Quantity to Produced', compute='_compute_qty_remaining2', digits='Product Unit of Measure', store=True)


    @api.depends('qty_production', 'qty_reported_from_previous_wo', 'qty_produced', 'production_id.product_uom_id')
    def _compute_qty_remaining2(self):
        for wo in self:
            if wo.production_id.product_uom_id:
                wo.qty_remaining2 = max(float_round(wo.qty_production - wo.qty_reported_from_previous_wo - wo.qty_produced, precision_rounding=wo.production_id.product_uom_id.rounding), 0)
            else:
                wo.qty_remaining2 = 0

    
    
    
    