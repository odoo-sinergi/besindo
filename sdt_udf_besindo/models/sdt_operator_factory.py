from odoo import api, fields, models, _ , SUPERUSER_ID
from odoo.exceptions import UserError


class SDTOperatorFactory(models.Model):
    _name = "sdt.operator.factory"


    name = fields.Char(string='Name')
    tag_ids = fields.Many2many('sdt.operator.factory.tag', string='Tags')

    
class SDTOperatorFactoryTag(models.Model):
    _name = "sdt.operator.factory.tag"


    name = fields.Char(string='Name')
    
    