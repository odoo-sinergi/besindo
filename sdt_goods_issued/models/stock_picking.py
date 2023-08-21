# -*- coding: utf-8 -*-

from odoo import api, fields, models, _ , SUPERUSER_ID
#from odoo.addons.product.models import decimal_precision as dp
from odoo.addons import decimal_precision as dp
from  odoo.exceptions import UserError
from datetime import datetime
from datetime import timedelta
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class StockPickingLine(models.Model):
    _inherit = 'stock.move'

    issued_line_id = fields.Many2one('goods.issued.line', string='Issued Line ID', track_visibility='onchange')
    return_line_id = fields.Many2one('return.goods.issued.line', string='Return Line ID', track_visibility='onchange')
    analytic_product_id = fields.Many2one('account.analytic.account', string='Analytic Product', domain="[('plan_id.name','=','Product')]")
    analytic_project_id = fields.Many2one('account.analytic.account', string='Analytic Project', domain="[('plan_id.name','=','Project')]")
    analytic_section_id = fields.Many2one('account.analytic.account', string='Analytic Section', domain="[('plan_id.name','=','Section')]")
    analytic_departement_id = fields.Many2one('account.analytic.account', string='Analytic Departement', domain="[('plan_id.name','=','Departement')]")
