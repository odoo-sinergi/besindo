# -*- coding: utf-8 -*-

from email.policy import default
from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError

class ResPartner(models.Model):
    _inherit = 'res.partner'

    tolerance_terms = fields.Integer(string="Tolerance Terms",)

