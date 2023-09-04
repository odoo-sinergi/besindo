from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

# -*- coding: utf-8 -*-

class ResUsers(models.Model):
    _inherit = 'res.users'

    show_inventory_cost = fields.Boolean('Show Inventory Cost', default=False)
    show_inventory_price = fields.Boolean('Show Inventory Price', default=False)

class ProductTemplate(models.Model):
    _inherit = "product.template"

    is_show_inventory_cost = fields.Boolean(string='Is Show Inventory Cost', readonly=True, compute='_get_auth_user_cost')
    is_show_inventory_price = fields.Boolean(string='Is Show Inventory Cost', readonly=True, compute='_get_auth_user_price')

    def _get_auth_user(self, called_from):
        for line in self:
            user_obj = self.env['res.users'].search([('id', '=', line._uid)])
            if called_from == 'cost':
                if user_obj.show_inventory_cost == True:
                    line.is_show_inventory_cost=True
                else:
                    line.is_show_inventory_cost=False
            else:
                if user_obj.show_inventory_price == True:
                    line.is_show_inventory_price=True
                else:
                    line.is_show_inventory_price=False

    @api.depends()
    def _get_auth_user_cost(self):
        self._get_auth_user('cost')

    @api.depends()
    def _get_auth_user_price(self):
        self._get_auth_user('price')