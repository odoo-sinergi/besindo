# -*- coding: utf-8 -*-

from odoo import api, fields, models, _ , SUPERUSER_ID
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
from datetime import datetime


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def button_validate(self):
        # do actual processing
        res = super(StockPicking, self).button_validate()
        # overwrite date field where applicable
        for data in self:
            if data.force_date:
                data.write({'date_done': data.force_date})
        return res

