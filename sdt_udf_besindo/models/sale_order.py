from odoo import api, Command, fields, models, _
from odoo.exceptions import UserError
from email.policy import default


class SaleOrder(models.Model):
    _inherit = "sale.order"

    req_approval = fields.Boolean(string='Req Approval', copy=False)
    approval_disc = fields.Boolean(string='Approval Disc', copy=False)

    status_approval = fields.Selection(
        string='Status Approval', default='draft', copy=False,
        selection=[('draft', 'Draft'),
                   ('nfa', 'Needs For Approval'),
                   ('waiting', 'Waiting For Approval'),
                   ('approved', 'Approved'),
                   ('noa', 'No Approval'),
                   ('refused', 'Refused'),
                   ]
    )

    @api.onchange('order_line')
    def _onchange_approval_disc(self):
        for record in self:
            for order in record.order_line :
                if order.discount > 0:
                    approval_so_obj = self.env['approval.category'].search([('approval_so','=',True)], limit=1)
                    if approval_so_obj :
                        record.approval_disc = True
                        record.status_approval = 'nfa'
                    else :
                        record.approval_disc = False
                else :
                    record.approval_disc = False
                    record.status_approval = 'noa'
    
    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        for record in self:
            if record.approval_disc == True:
                if record.req_approval == False :
                    raise UserError('Silahkan Meminta Approval Terlebih Dahulu')
                else :
                    approval_request_obj = self.env['approval.request'].search([('sale_order_id','=',record.id)])
                    for approval_request in approval_request_obj :
                        if approval_request.request_status == 'new':
                            raise UserError('Silahkan Menunggu Approval Terlebih Dahulu')
                        elif approval_request.request_status == 'pending' :
                            raise UserError('Silahkan Menunggu Approval Terlebih Dahulu')
                        else :
                            pass
            else :
                pass
        return res

    def action_req_approval (self):
        for rec in self :
            approval_so_obj = self.env['approval.category'].search([('approval_so','=',True)], limit=1)
            if approval_so_obj.approval_minimum == 1 :
                approvals_id = self.env['approval.request'].sudo().create({
                'name':'Approval/SO/-'+self.name,
                'date' : fields.Datetime.now(),
                'reference':rec.name,
                'category_id' : approval_so_obj.id,
                'sale_order_id' : self.id,
                'request_owner_id' : self.env.uid,
                'request_status' : 'pending',
                'amount' : self.amount_total,
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
                    'sale_order_id' : self.id,
                    'request_owner_id' : self.env.uid,
                    'request_status' : 'pending',
                    'amount' : self.amount_total,
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

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    # price_unit = fields.Float(digits='Product Price Sales',)
    sdt_price_unit = fields.Float(string='Sdt Price Unit', digits='Product Price Sales', store=True) 
    delivery_deadline = fields.Date(string="Deadline Delivery Date")
    
