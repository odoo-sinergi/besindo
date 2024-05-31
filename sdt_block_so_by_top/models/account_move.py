# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError

class AccountMove(models.Model):
    _inherit='account.move'

    tolerance_terms = fields.Integer('Tolerance Terms', related="partner_id.tolerance_terms", readonly=True)

