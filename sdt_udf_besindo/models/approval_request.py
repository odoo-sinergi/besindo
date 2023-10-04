from odoo import api, fields, models, _ , SUPERUSER_ID
from odoo.exceptions import UserError


class ApprovalRequest(models.Model):
    _inherit = "approval.request"

    sale_order_id = fields.Many2one('sale.order',string='Sale Order',)
    purchase_order_id = fields.Many2one('purchase.order',string='Purchase Order',)
    lvl_approver = fields.Integer(string='Lvl Approver',)
    
    def action_confirm(self):
        # make sure that the manager is present in the list if he is required
        self.ensure_one()
        # if self.category_id.manager_approval == 'required':
            # employee = self.env['hr.employee'].search([('user_id', '=', self.request_owner_id.id)], limit=1)
            # if not employee.parent_id:
            #     raise UserError(_('This request needs to be approved by your manager. There is no manager linked to your employee profile.'))
            # if not employee.parent_id.user_id:
            #     raise UserError(_('This request needs to be approved by your manager. There is no user linked to your manager.'))
            # if not self.approver_ids.filtered(lambda a: a.user_id.id == employee.parent_id.user_id.id):
            #     raise UserError(_('This request needs to be approved by your manager. Your manager is not in the approvers list.'))
        # if len(self.approver_ids) < self.approval_minimum:
        #     raise UserError(_("You have to add at least %s approvers to confirm your request.", self.approval_minimum))
        if self.requirer_document == 'required' and not self.attachment_number:
            raise UserError(_("You have to attach at lease one document."))

        approvers = self.approver_ids
        if self.approver_sequence:
            approvers = approvers.filtered(lambda a: a.status in ['new', 'pending', 'waiting'])

            # approvers[1:].status = 'waiting'
            # approvers = approvers[0] if approvers and approvers[0].status != 'pending' else self.env['approval.approver']
            approvers.status = 'pending'
        else:
            approvers = approvers.filtered(lambda a: a.status == 'new')

        approvers.write({'status': 'pending'})
        approvers._create_activity()
        self.write({'date_confirmed': fields.Datetime.now()})

        approvers.write({'status': 'pending'})
        approvers._create_activity()
        self.write({'date_confirmed': fields.Datetime.now()})

    def action_approve(self, approver=None):
        # Approval SO
        if self.sale_order_id :
            approval_request_obj = self.env['approval.request'].search([('sale_order_id','=',self.sale_order_id.id)])
            for approval_request in approval_request_obj :
                if approval_request.request_status == 'pending':
                        approval_request.sale_order_id.status_approval = 'approved'
            approver = self.mapped('approver_ids').filtered(lambda approver: approver.user_id == self.env.user)
            approver.write({'status': 'approved'})
            self.sudo()._get_user_approval_activities(user=self.env.user).action_feedback()
        
        if self.purchase_order_id :
            sql_query="""
                select * from approval_request where lvl_approver < %s and purchase_order_id = %s and request_status = 'pending'
            """
            self.env.cr.execute(sql_query, (self.lvl_approver,self.purchase_order_id.id,))
            result = self.env.cr.dictfetchall()
            if result :
                for res in result :
                    if res['request_status'] == 'pending':
                        raise UserError(_("Waiting Approval From Level %s", (self.lvl_approver-1)))
                    else :
                        pass
            else :
                self.purchase_order_id.info_status = 'Approved By Level ' + str(self.lvl_approver),
                approver = self.mapped('approver_ids').filtered(lambda approver: approver.user_id == self.env.user)
                approver.write({'status': 'approved'})
                self.sudo()._get_user_approval_activities(user=self.env.user).action_feedback()
                # check Request Approval and auto confirm PR
                sql_query="""
                    select * from approval_request where request_status = 'pending' and purchase_order_id = %s
                """
                self.env.cr.execute(sql_query, (self.purchase_order_id.id,))
                final_result = self.env.cr.dictfetchall()
                if final_result :
                    pass
                else :
                    self.purchase_order_id.info_status = 'APPROVED'
                    self.purchase_order_id.button_confirm()

        return super(ApprovalRequest, self).action_approve()

    def sdt_action_refuse (self):
        if self.sale_order_id :
            approval_request_obj = self.env['approval.request'].search([('sale_order_id','=',self.sale_order_id.id)])
            for approval_request in approval_request_obj :
                # SO
                approval_request.sale_order_id.status_approval = 'refused'
                approval_request.sale_order_id.req_approval = False
                approval_request.sale_order_id = False
                # PO
                approval_request.purchase_order_id.req_approval = False
                approval_request.purchase_order_id = False
                approval_request.action_refuse()
        
        if self.purchase_order_id :
            sql_query="""
                select * from approval_request where lvl_approver < %s and purchase_order_id = %s and request_status = 'pending'
            """
            self.env.cr.execute(sql_query, (self.lvl_approver,self.purchase_order_id.id,))
            result = self.env.cr.dictfetchall()
            if result :
                for res in result :
                    if res['request_status'] == 'pending':
                        raise UserError(_("Waiting Approval From Level %s", (self.lvl_approver-1)))
                    else :
                        pass
            else :
                purchase_order_obj = self.env['purchase.order'].search([('id','=',self.purchase_order_id.id)])
                for purchase_order in purchase_order_obj :
                    purchase_order.info_status = 'REFUSED'
                    purchase_order.button_cancel()

                approval_request_obj = self.env['approval.request'].search([('purchase_order_id','=',self.purchase_order_id.id)])
                for approval_request in approval_request_obj :
                    approval_request.purchase_order_id = False
                    approval_request.sudo().action_refuse()

                    approval_request.approver_ids.status = 'refused'
                    approval_request.action_refuse()
            x=1