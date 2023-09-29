# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    mrp_id = fields.Many2one('mrp.production', string = 'MO Origin')
    customer_reference = fields.Char(string = 'Customer PO Num.', compute='_compute_customer_reference', store=True)
    label_qty = fields.Float(string='Label Print Quantity')
    mrp_shift = fields.Char(string='Shift', compute='_compute_mrp_shift')

    @api.depends('origin')
    @api.onchange('origin')
    def partner_origin(self):
        # self.partner_id = self.env['mrp.production'].search([('name', '=', self.origin)]).contact
        mrp_production_obj = self.env['mrp.production'].search([('name', 'like', '%s%'%self.origin)])
        for mrp_production in mrp_production_obj :
            self.partner_id = mrp_production.contact

    @api.depends('origin')
    @api.onchange('origin')
    def onchange_mrp_id(self):
        # self.mrp_id = self.env['mrp.production'].search([('name', '=', self.origin)])
        # self.partner_id = self.mrp_id.contact
        mrp_production_obj = self.env['mrp.production'].search([('name', 'like', '%s%'%self.origin)])
        for mrp_production in mrp_production_obj :
            self.mrp_id = mrp_production.id
            self.partner_id = mrp_production.contact

    @api.depends('origin')
    @api.onchange('origin')
    def _compute_customer_reference(self):
        for pick in self:
            pick.customer_reference = False
            so_ref = self.env['sale.order'].search([('name', 'like', '%s%'%pick.origin)], limit=1).client_order_ref
            if so_ref:
                pick.customer_reference = so_ref

    @api.depends('origin')
    @api.onchange('origin')
    def _compute_mrp_shift(self):
        for pick in self:
            pick.mrp_shift = False
            mrp_production_obj = self.env['mrp.production'].search([('name', 'like', '%s%'%pick.origin)], limit=1)
            if mrp_production_obj.workorder_ids:
                for mrp in mrp_production_obj.workorder_ids:
                    shift = {
                        'shift_1':'Shift 1',
                        'shift_2':'Shift 2',
                    }
                    pick.mrp_shift = shift[mrp.shift]
                    