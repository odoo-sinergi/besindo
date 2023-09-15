# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    mrp_id = fields.Many2one('mrp.production', string = 'MO Origin')
    customer_reference = fields.Char(string = 'Customer PO Num.', compute='_compute_customer_reference')
    # label_qty = fields.Float(string='Label Print Quantity')

    @api.depends('origin')
    @api.onchange('origin')
    def partner_origin(self):
        self.partner_id = self.env['mrp.production'].search([('name', '=', self.origin)]).contact

    @api.depends('origin')
    @api.onchange('origin')
    def onchange_mrp_id(self):
        self.mrp_id = self.env['mrp.production'].search([('name', '=', self.origin)])
        self.partner_id = self.mrp_id.contact

    @api.depends('origin')
    @api.onchange('origin')
    def _compute_customer_reference(self):
        for pick in self:
        #     so = self.env['sale.order'].search([('name', '=', pick.origin)])
        #     if so:
        #         for order in so:
        #             if order.client_order_ref:
        #                 pick.customer_reference = order.client_order_ref
        #             else:
        #                 pick.customer_reference = False
            pick.customer_reference = False