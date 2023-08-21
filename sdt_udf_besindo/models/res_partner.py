from odoo import api, fields, models, _ , SUPERUSER_ID
from odoo.exceptions import UserError


class ResPartner(models.Model):
    _inherit = "res.partner"

    sales_type = fields.Selection([('domestic','DOMESTIC'),('export','EXPORT')], string='Sales Type')

    
    
    
    