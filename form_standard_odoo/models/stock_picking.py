# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    mrp_id = fields.Many2one('mrp.production', string = 'MO Origin')

    @api.depends('origin')
    def partner_origin(self):
        self.partner_id = self.env['mrp.production'].search([('name', '=', self.origin)]).contact

    @api.onchange('origin')
    def onchange_mrp_id(self):
        self.mrp_id = self.env['mrp.production'].search([('name', '=', self.origin)])
        self.partner_id = self.mrp_id.contact