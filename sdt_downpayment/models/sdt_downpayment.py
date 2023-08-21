from odoo import fields, models, api, _

SESSION_STATES =[('open','Open'),('close','Close')]
DP_STATES =[('assigned','Assigned'),('canceled','Canceled')]

class Down_Payment(models.Model):
    _name = "sdt.downpayment"

    payment_type = fields.Selection([('inbound', 'Receipt Money'), ('outbound', 'Send Money')])
    partner_type = fields.Selection([('customer', 'Customer'), ('supplier', 'Vendor')])
    partner_id = fields.Many2one('res.partner', string='Partner')
    account_dp = fields.Many2one('account.account', 'Down Payment Account')
    control_account = fields.Many2one('account.account', 'Control Account')
    amount = fields.Monetary(string='DP Amount', required=True)
    currency_id = fields.Many2one('res.currency', string='Currency', required=True,
                                  default=lambda self: self.env.user.company_id.currency_id)
    date = fields.Date(string='Payment Date', default=fields.Date.context_today, required=True, copy=False)
    ref = fields.Char(string='Memo')
    journal_id = fields.Many2one('account.journal', string='Payment Journal', required=True,
                                 domain=[('type', 'in', ('bank', 'cash'))])
    company_id = fields.Many2one('res.company', related='journal_id.company_id', string='Company', readonly=True)
    dp_no = fields.Char(string="Down Payment No.", length=50)
    state = fields.Selection(string="State", selection=SESSION_STATES, required=False, readonly=True,
                             default=SESSION_STATES[0][0])
    payment_id = fields.Many2one('account.payment', string="Originator Payment", help="Payment that created this entry")
    open_move_id = fields.Many2one('account.move', 'Accounting Entry', copy=False)
    close_amount = fields.Monetary(string='Payment Amount')
    balance_amount = fields.Monetary(string='Balance Amount')
    rate = fields.Monetary(string='Rate')
    amount_currency = fields.Monetary(string='Amount Currency')
    detail_ids = fields.One2many(comodel_name="sdt.downpayment.lines", inverse_name="dp_id",string="Detail Down Payment", required=False)

class Down_Payment_Lines(models.Model):
    _name = "sdt.downpayment.lines"

    inv_id = fields.Many2one(comodel_name="account.move", string="Invoice", required=False)
    dp_id = fields.Many2one(comodel_name="sdt.downpayment", string="DP Details", required=False)
    date = fields.Date(string='Date', copy=False)
    currency_id = fields.Many2one('res.currency', string='Currency', required=True,
                                  default=lambda self: self.env.user.company_id.currency_id)
    account_dp = fields.Many2one('account.account', 'Down Payment Account')
    dp_no = fields.Char(string="Down Payment No.", length=50)
    close_amount = fields.Monetary(string='Payment Amount')
    balance_amount = fields.Monetary(string='Balance Amount')
    close_move_id = fields.Many2one('account.move', 'Accounting Entry', copy=False)
    state = fields.Char(string="State", required=False,default=DP_STATES[0][0])
    
