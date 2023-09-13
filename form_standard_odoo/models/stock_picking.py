# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    mrp_id = fields.Many2one('mrp.production', string = 'MO Origin')
    customer_reference = fields.Char(string = 'Customer PO Num.', compute='_compute_customer_reference')

    @api.depends('origin')
    @api.onchange('origin')
    def onchange_mrp_id(self):
        self.mrp_id = self.env['mrp.production'].search([('name', '=', self.origin)])

    @api.depends('origin')
    @api.onchange('origin')
    def _compute_customer_reference(self):
        for rec in self:
            rec.customer_reference = rec.env['sale.order'].search([('name', '=', rec.origin)]).client_order_ref