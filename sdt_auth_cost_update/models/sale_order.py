# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    is_show_inventory_cost = fields.Boolean(string='Is Show Inventory Cost', readonly=True, compute='_get_auth_user_cost')
    is_show_inventory_price = fields.Boolean(string='Is Show Inventory Price', readonly=True, compute='_get_auth_user_price')

    def _get_auth_user(self, called_from):
        for record in self:
            user_obj = self.env['res.users'].search([('id', '=', record._uid)])
            if called_from == 'cost':
                if user_obj.show_inventory_cost == True:
                    record.is_show_inventory_cost=True
                else:
                    record.is_show_inventory_cost=False
            else:
                if user_obj.show_inventory_price == True:
                    record.is_show_inventory_price=True
                else:
                    record.is_show_inventory_price=False

    @api.depends()
    def _get_auth_user_cost(self):
        self._get_auth_user('cost')

    @api.depends()
    def _get_auth_user_price(self):
        self._get_auth_user('price')