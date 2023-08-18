from odoo import fields, models, api


class MultipaymentAccount(models.Model):
    _name = "sdt.multipayment.account"

    user_id = fields.Many2one('res.users', 'User', required=True)
    account_id = fields.Many2many(comodel_name='account.account', string='Account', required=True, )


