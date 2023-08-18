# -*- coding: utf-8 -*-

from odoo import api, fields, models, _ , SUPERUSER_ID
#from odoo.addons.product.models import decimal_precision as dp
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
from datetime import datetime
from datetime import timedelta
from lxml import etree

from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        if self.invoice_status=='no':
            partner_obj = self.env['res.partner'].search([('category_id.name', '=', 'Customer')]).ids
            domain = {'partner_id': [('id', 'in', partner_obj)]}
            return {'domain': domain} 



    