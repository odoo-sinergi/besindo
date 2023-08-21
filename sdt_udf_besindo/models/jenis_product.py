from odoo import api, fields, models, _ , SUPERUSER_ID
#from odoo.addons.product.models import decimal_precision as dp
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
from datetime import datetime
from datetime import timedelta
from lxml import etree
from odoo import fields, models, api, _

class ProductJenis(models.Model):
    _name='product.jenis'
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(string='Jenis', required=True)

    @api.constrains('name')
    def _check_unique_name(self):
        existing_record = self.search([('name', '=', self.name)])
        if len(existing_record) > 1:
            raise UserError('Jenis harus unik!')

    
    
    
    