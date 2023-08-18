from odoo import fields, models, api

class AccountConfigSettings(models.Model):
    _name='sdt.downpayment.account'

    user_id = fields.Many2one('res.users', 'User', required=True)
    account_id=fields.Many2many(comodel_name='account.account', string='Down Payment Account')
    payment_type=fields.Selection([('inbound', 'Receipt Money'),('outbound','Send Money')])

