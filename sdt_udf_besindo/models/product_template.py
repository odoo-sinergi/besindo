from odoo import api, fields, models, _ , SUPERUSER_ID
#from odoo.addons.product.models import decimal_precision as dp
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
from datetime import datetime
from datetime import timedelta
from lxml import etree
from odoo import fields, models, api, _

class ProductTemplate(models.Model):
    _inherit='product.template'

    panjang = fields.Float(string='Panjang',)
    lebar = fields.Float(string='Lebar',)
    tebal = fields.Float(string='Tebal',)
    nama_alias = fields.Char(string='Product Name Alias')
    panjang_uom_id = fields.Many2one('uom.uom',string='Panjang Uom',)
    lebar_uom_id = fields.Many2one('uom.uom',string='Lebar Uom',)
    tebal_uom_id = fields.Many2one('uom.uom',string='Tebal Uom',)
    part_number = fields.Char(string='Part Number',)
    jenis_product_id = fields.Many2one('product.jenis',string='Jenis Product',)
    