
from odoo import fields, api, models, _
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    is_credit_limit = fields.Boolean(string='Is Credit Limit', compute='_compute_is_credit_limit', store=True)
    hide_button_confirm = fields.Boolean(string='Hide Button Confirm', compute='_compute_hide_button_confirm')
    is_approve_limit = fields.Boolean(string='Is Approve Limit')
    approval_id = fields.Many2one('approval.request', string='Approval Request')


    @api.depends('amount_total','currency_id','company_id','date_order')
    def _compute_is_credit_limit(self):
        for data in self:
            is_credit_limit = False
            if data.partner_id.credit_limit:
                amount_total_currency = data.currency_id._convert(data.tax_totals['amount_total'], data.company_id.currency_id, data.company_id, data.date_order)
                if amount_total_currency > (data.partner_id.credit_limit-data.partner_id.credit):
                    is_credit_limit = True
            data.is_credit_limit = is_credit_limit


    @api.depends('is_credit_limit','is_approve_limit')
    def _compute_hide_button_confirm(self):
        for data in self:
            hide_button_confirm = False
            if data.is_credit_limit == False:
                hide_button_confirm = False
            elif data.is_credit_limit == True and data.is_approve_limit == False:
                hide_button_confirm = True
            data.hide_button_confirm = hide_button_confirm


    def action_approval_limit(self):
        for data in self:
            approval_req_obj = self.env['approval.request']
            approval_category = self.env.ref('sdt_partner_credit_limit_approval.approval_category_data_partner_credit_limit')
            amount_total_currency = data.currency_id._convert(data.tax_totals['amount_total'], data.company_id.currency_id, data.company_id, data.date_order)
            new_approval_request = approval_req_obj.sudo().create({
                'date' : fields.Datetime.now(),
                'reference':data.name,
                'category_id' : approval_category.id,
                'partner_id' : data.partner_id.id,
                'request_owner_id' : data.env.uid,
                'request_status' : 'pending',
                'amount' : amount_total_currency,
            })
            new_approval_request.action_confirm()
            data.approval_id = new_approval_request.id

    def action_request_approval(self):
        for rec in self :
            if not rec.req_approval and rec.approval_disc:
                approval_so_obj = self.env['approval.category'].search([('approval_so','=',True),('overdue_so','=',False),('active','=',True)], limit=1)
                if approval_so_obj.approval_minimum == 1 :
                    approvals_id = self.env['approval.request'].sudo().create({
                    'name':'Approval/SO/-'+self.name,
                    'date' : fields.Datetime.now(),
                    'reference':rec.name,
                    'category_id' : approval_so_obj.id,
                    'sale_order_id' : rec.id,
                    'request_owner_id' : self.env.uid,
                    'request_status' : 'pending',
                    'amount' : rec.amount_total,
                    })
                    for line_id in self.order_line:
                        vals ={
                            'approval_request_id': approvals_id.id,
                            'product_id': line_id.product_id.id,
                            'description': line_id.name,
                            'quantity': line_id.product_uom_qty,
                            'product_uom_id': line_id.product_uom.id,
                        }
                        self.env['approval.product.line'].create(vals)
                    approvals_id.action_confirm()
                elif approval_so_obj.approval_minimum == len(approval_so_obj.approver_ids.ids) :
                    for user_id in approval_so_obj.user_ids:
                        approvals_id = self.env['approval.request'].sudo().create({
                        'name':'Approval/SO/-'+self.name,
                        'date' : fields.Datetime.now(),
                        'reference':rec.name,
                        'category_id' : approval_so_obj.id,
                        'sale_order_id' : rec.id,
                        'request_owner_id' : self.env.uid,
                        'request_status' : 'pending',
                        'amount' : rec.amount_total,
                        })
                        for line_id in rec.order_line:
                            vals ={
                                'approval_request_id': approvals_id.id,
                                'product_id': line_id.product_id.id,
                                'description': line_id.name,
                                'quantity': line_id.product_uom_qty,
                                'product_uom_id': line_id.product_uom.id,
                            }
                            self.env['approval.product.line'].create(vals)
                        for approver_id1 in approvals_id.approver_ids :
                            approver_id1.unlink()
                        
                        approvals_id.approver_ids += self.env['approval.approver'].new({
                            'request_id': approvals_id.id,
                            'user_id': user_id.id,
                        })
                        approvals_id.action_confirm()
                elif approval_so_obj.approval_minimum > len(approval_so_obj.approver_ids.ids) :
                    raise UserError('Jumlah Approver Tidak Boleh Lebih Besar Dari Approver')
                else :
                    raise UserError('Jumlah Approver Tidak Boleh Nol')
                rec.req_approval = True
                rec.status_approval = 'waiting'

            if rec.show_req_approval:
                approval_so_obj = self.env['approval.category'].search([('approval_so','=',True),('overdue_so','=',True),('active','=',True)])
                if not approval_so_obj :
                    raise UserError('Settingan Approval Tidak Ditemukan')
                for approval_so in approval_so_obj :
                    for user_id in approval_so.approver_ids:
                        sql_query="""
                            select count(1) from approval_request where sale_order_id= %s and lvl_approver = %s
                        """
                        self.env.cr.execute(sql_query, (rec.id, user_id.lvl_approver,))
                        check_po = self.env.cr.dictfetchall()
                        check_po = check_po[0]['count']
                        if check_po == 0 :
                            approvals_id = self.env['approval.request'].sudo().create({
                            'name':'Approval/SO/-'+self.name,
                            'date' : fields.Datetime.now(),
                            'reference':rec.name,
                            'category_id' : approval_so.id,
                            'sale_order_id' : rec.id,
                            'lvl_approver' : user_id.lvl_approver,
                            'request_owner_id' : self.env.uid,
                            'request_status' : 'pending',
                            'amount' : rec.amount_total,
                            })
                            for approver_id in approvals_id.approver_ids :
                                approver_id.unlink()
                            if user_id :
                                approvals_id.approver_ids += self.env['approval.approver'].create({
                                    'user_id': user_id.user_id.id,
                                    'request_id': approvals_id.id,
                                    'status': 'new',
                                    'company_id': rec.company_id.id,
                                })
                            approvals_id.action_confirm()
                        else :
                            sql_query="""
                                select id from approval_request where sale_order_id= %s and lvl_approver = %s
                            """
                            self.env.cr.execute(sql_query, (rec.id, user_id.lvl_approver,))
                            id_aq = self.env.cr.dictfetchall()
                            id_aq = id_aq[0]['id']
                            approvals_id.approver_ids += self.env['approval.approver'].create({
                                'user_id': user_id.user_id.id,
                                'request_id': id_aq,
                                'status': 'pending',
                                'company_id': rec.company_id.id,
                            })
                    rec.show_req_approval = False
                    rec.approval_bod_state = 'waiting'