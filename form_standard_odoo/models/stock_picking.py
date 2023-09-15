# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    mrp_id = fields.Many2one('mrp.production', string = 'MO Origin')
    customer_reference = fields.Char(string = 'Customer PO Num.', compute='_compute_customer_reference')
    label_qty = fields.Float(string='Label Print Quantity')

    @api.depends('origin')
    @api.onchange('origin')
    def partner_origin(self):
        # self.partner_id = self.env['mrp.production'].search([('name', '=', self.origin)]).contact
        mrp_production_obj = self.env['mrp.production'].search([('name', '=', self.origin)])
        for mrp_production in mrp_production_obj :
            self.partner_id = mrp_production.contact

    @api.depends('origin')
    @api.onchange('origin')
    def onchange_mrp_id(self):
        # self.mrp_id = self.env['mrp.production'].search([('name', '=', self.origin)])
        # self.partner_id = self.mrp_id.contact
        mrp_production_obj = self.env['mrp.production'].search([('name', '=', self.origin)])
        for mrp_production in mrp_production_obj :
            self.mrp_id = mrp_production.id
            self.partner_id = mrp_production.contact

    @api.depends('origin')
    @api.onchange('origin')
    def _compute_customer_reference(self):
        for i in self :
            sale_order_obj = self.env['sale.order'].search([('name', '=', self.origin)])
            if sale_order_obj :
                for sale_order in sale_order_obj :
                    i.customer_reference = sale_order.client_order_ref
            else :
                pass
        # self.customer_reference = self.env['sale.order'].search([('name', '=', self.origin)]).client_order_ref