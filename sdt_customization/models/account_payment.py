# -*- coding: utf-8 -*-

from odoo import api, fields, models, _ , SUPERUSER_ID
#from odoo.addons.product.models import decimal_precision as dp
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
from datetime import datetime
from datetime import timedelta
from lxml import etree

from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    @api.onchange('partner_type')
    def _onchange_partnertype(self):
        if self.partner_type=='customer':
            partner_obj = self.env['res.partner'].search([('category_id.name', '=', 'Customer')]).ids
            domain = {'partner_id': [('id', 'in', partner_obj)]}
            return {'domain': domain} 
        elif self.partner_type=='supplier':
            partner_obj = self.env['res.partner'].search([('category_id.name', '=', 'Vendor')]).ids
            domain = {'partner_id': [('id', 'in', partner_obj)]}
            return {'domain': domain} 



    