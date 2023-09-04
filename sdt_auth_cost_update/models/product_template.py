from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

# -*- coding: utf-8 -*-

class ResUsers(models.Model):
    _inherit = 'res.users'

    show_inventory_cost = fields.Boolean('Show Inventory Cost',default=False)


class ProductTemplate(models.Model):
    _inherit = "product.template"

    is_show_inventory_cost = fields.Boolean(string='Is Show Inventory Cost', readonly=False, compute='_get_auth_user')

    @api.depends()
    def _get_auth_user(self):
        for line in self:
            user_obj = self.env['res.users'].search([('id', '=', line._uid)])
            if user_obj.show_inventory_cost == True:
                line.is_show_inventory_cost=True
            else:
                line.is_show_inventory_cost=False

