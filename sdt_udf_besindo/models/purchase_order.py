from odoo import api, fields, models, _ , SUPERUSER_ID
from odoo.exceptions import UserError


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    tempat_pengiriman_id = fields.Many2one('tempat.pengiriman',string='Tempat Pengiriman',)
    pembayaran = fields.Char(string='Pembayaran',)

    amount_ppn = fields.Monetary(
        string='PPN',
        compute='_compute_tax_totals', store=True, readonly=True,
        inverse='_inverse_amount_total',
    )
    amount_pph = fields.Monetary(
        string='PPH',
        compute='_compute_tax_totals', store=True, readonly=True,
        inverse='_inverse_amount_total',
    )
    info_status = fields.Char(string='Status Approval', copy=False)

    @api.depends('order_line.taxes_id', 'order_line.price_subtotal', 'amount_total', 'amount_untaxed')
    def  _compute_tax_totals(self):
        """ Computed field used for custom widget's rendering.
            Only set on invoices.
        """
        res = super(PurchaseOrder, self)._compute_tax_totals()
        for move in self:
            if move.tax_totals != False:
                if len(move.tax_totals['groups_by_subtotal']['Untaxed Amount']) > 1 :
                    for tax in move.tax_totals['groups_by_subtotal']['Untaxed Amount']:
                        if tax['tax_group_name'] == 'VAT':
                            move.amount_ppn = tax['tax_group_amount']
                        elif tax['tax_group_name'] == 'PPh':
                            move.amount_pph = tax['tax_group_amount']
                elif len(move.tax_totals['groups_by_subtotal']['Untaxed Amount']) == 1 :
                    for tax in move.tax_totals['groups_by_subtotal']['Untaxed Amount']:
                        if tax['tax_group_name'] == 'VAT':
                            move.amount_ppn = tax['tax_group_amount']
                            move.amount_pph = 0
                        elif tax['tax_group_name'] == 'PPh':
                            move.amount_pph = tax['tax_group_amount']
                            move.amount_ppn = 0
                else:
                    move.amount_ppn = 0
                    move.amount_pph = 0
            else:
                move.amount_ppn = 0
                move.amount_pph = 0
        
        return res
    

    req_approval = fields.Boolean(string='Req Approval', copy=False)
    # approval_disc = fields.Boolean(string='Approval Disc', copy=False)

    # @api.onchange('order_line')
    # def _onchange_approval_disc(self):
    #     for record in self:
    #         for order in record.order_line :
    #             if order.discount > 0:
    #                 record.approval_disc = True
    #             else :
    #                 record.approval_disc = False

    def button_confirm(self):
        res = super(PurchaseOrder, self).button_confirm()
        for record in self:
            approval_category_obj = self.env['approval.category'].search([('approval_po','=',True)], limit=1)
            if approval_category_obj :
                if record.req_approval == False :
                    raise UserError('Silahkan Meminta Approval Terlebih Dahulu')
                else :
                    approval_request_obj = self.env['approval.request'].search([('purchase_order_id','=',record.id)])
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
            approval_po_obj = self.env['approval.category'].search([('approval_po','=',True)])
            if not approval_po_obj :
                raise UserError('Settingan Tidak Ditemukan')
            for approval_po in approval_po_obj :
                if rec.currency_id.id == approval_po.currency_id.id :
                    if approval_po.currency_id.display_name == 'IDR' :
                        if rec.amount_total >= approval_po.min_approve_lvl_2_po:
                            for user_id in approval_po.approver_ids:
                                approvals_id = self.env['approval.request'].sudo().create({
                                'name':'Approval/PO/-'+self.name,
                                'date' : fields.Datetime.now(),
                                'reference':rec.name,
                                'category_id' : approval_po.id,
                                'purchase_order_id' : self.id,
                                'lvl_approver' : user_id.lvl_approver,
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
                            for user_id in approval_po.approver_ids:
                                if user_id.lvl_approver == 1 :
                                    approvals_id = self.env['approval.request'].sudo().create({
                                    'name':'Approval/PO/-'+self.name,
                                    'date' : fields.Datetime.now(),
                                    'reference':rec.name,
                                    'category_id' : approval_po.id,
                                    'purchase_order_id' : self.id,
                                    'lvl_approver' : user_id.lvl_approver,
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
                                    for approver_id in approvals_id.approver_ids :
                                        approver_id.unlink()
                                    if user_id :
                                        if user_id.lvl_approver == 1 :
                                            approvals_id.approver_ids += self.env['approval.approver'].create({
                                                'user_id': user_id.user_id.id,
                                                'request_id': approvals_id.id,
                                                'status': 'new',
                                                'company_id': rec.company_id.id,
                                            })
                                    approvals_id.action_confirm()
                    if approval_po.currency_id.display_name != 'IDR' :
                        for user_id in approval_po.approver_ids:
                            approvals_id = self.env['approval.request'].sudo().create({
                            'name':'Approval/PO/-'+self.name,
                            'date' : fields.Datetime.now(),
                            'reference':rec.name,
                            'category_id' : approval_po.id,
                            'purchase_order_id' : self.id,
                            'lvl_approver' : user_id.lvl_approver,
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
                rec.req_approval = True


            rec.req_approval = True
class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    price_per_kg = fields.Float(string='Price per KG', default=0)
    req_approval = fields.Boolean(string='Req Approval', related='order_id.req_approval', readonly=True,store=True)
