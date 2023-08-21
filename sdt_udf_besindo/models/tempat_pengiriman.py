from odoo import api, fields, models, _ , SUPERUSER_ID
#from odoo.addons.product.models import decimal_precision as dp
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
from datetime import datetime
from datetime import timedelta
from lxml import etree
from odoo import fields, models, api, _

class TempatPengiriman(models.Model):
    _name='tempat.pengiriman'
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(string='Name', required=True)
    street = fields.Char(string='Street', required=True)
    city = fields.Char(string='City', required=True)
    state_id = fields.Many2one('res.country.state',string='State', required=True)
    zip = fields.Char(string='Zip', required=True)
    country_id = fields.Many2one('res.country',string="Country", required=True)
    
    

    @api.constrains('name')
    def _check_unique_name(self):
        existing_record = self.search([('name', '=', self.name)])
        if len(existing_record) > 1:
            raise UserError('Nama harus unik!')

    
    
    
    