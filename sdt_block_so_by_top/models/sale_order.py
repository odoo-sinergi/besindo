# -*- coding: utf-8 -*-

from email.policy import default
from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError, ValidationError
from datetime import timedelta, date

class Message(models.Model):
    _inherit = "mail.message"

    sale_id = fields.Many2one('sale.order',string='Sale Order', copy=False)
    picking_id = fields.Many2one('stock.picking',string='Stock Picking', copy=False)
    invoice_ids = fields.Many2many('account.move',string='Invoice', copy=False)

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    over_due_date = fields.Boolean('Over Due Date?', dafault=False, copy=False)
    
    def check_blocking_top(self,inv_obj):
        self.ensure_one()
        if self.over_due_date == True and self.approval_bod_state != 'approved':
            inv_name = ', '.join(inv for inv in inv_obj.mapped('name'))
            raise ValidationError(
                    _(
                        "Tidak dapat confirm Sale Order.\n"
                        "Karena invoice ('%s') overdue.\n"
                        "Ajukan approval terlebih dahulu.\n"
                    )
                    % (inv_name)
                )
    
    def check_top(self,picking_obj):
        date_now = date.today()
        partner_id = self.partner_invoice_id
        company_id = self.company_id
        invoice_obj = self.env['account.move'].search([('partner_id','=',partner_id.id),('company_id','=',company_id.id),('state','=','posted'),('move_type','=','out_invoice'),('invoice_date_due','<',date_now),('payment_state','not in',['paid', 'reversed'])], order = 'invoice_date_due asc, id asc')
        if invoice_obj:
            inv_ids = invoice_obj.ids
            for inv in invoice_obj:
                tolerance_day = inv.tolerance_terms
                invoice_date_due = inv.invoice_date_due + timedelta(days=tolerance_day) if tolerance_day > 0 else inv.invoice_date_due
                if invoice_date_due > date_now:
                    inv_ids.remove(inv.id)
                
            inv_obj = invoice_obj.filtered(lambda p: p.id in inv_ids)
            if len(inv_ids) > 0:
                if picking_obj:
                    picking_obj.over_due_date = True
                    message_body = _("Can not confirm Delivery Order.<br/>"
                                        "<table>"
                                        "<tr>"
                                            "<td>Invoice</td>"
                                            "<td>Date Due</td>"
                                        "</tr>"
                                    )
                    for inv in inv_obj:
                        tolerance_day = inv.tolerance_terms
                        invoice_date_due = inv.invoice_date_due + timedelta(days=tolerance_day) if tolerance_day > 0 else inv.invoice_date_due
                        message_body += _("<tr>"
                                            "<td>%(invoice)s</td>"
                                            "<td>(%(date_due)s)</td>"
                                        "</tr>",invoice=inv.name,date_due=invoice_date_due,
                                        )
                    message_body += _("</table>")
                    message_obj = picking_obj.env['mail.message'].search([('description','=',message_body),('picking_id','=',picking_obj.id)])
                    if not message_obj and picking_obj.state in ('confirmed','assigned'):
                        message_obj = picking_obj.message_post(body=message_body, message_type='notification')
                        message_obj.write({'picking_id': picking_obj.id,'invoice_ids': [(6, 0, inv_ids)]})
                else:
                    self.over_due_date = True
                    message_body = _("Can not confirm Sale Order.<br/>"
                                        "<table>"
                                        "<tr>"
                                            "<td>Invoice</td>"
                                            "<td>Date Due</td>"
                                        "</tr>"
                                    )
                    for inv in inv_obj:
                        tolerance_day = inv.tolerance_terms
                        invoice_date_due = inv.invoice_date_due + timedelta(days=tolerance_day) if tolerance_day > 0 else inv.invoice_date_due
                        message_body += _("<tr>"
                                            "<td>%(invoice)s</td>"
                                            "<td>(%(date_due)s)</td>"
                                        "</tr>",invoice=inv.name,date_due=invoice_date_due,
                                        )
                    message_body += _("</table>")
                    message_obj = self.env['mail.message'].search([('description','=',message_body),('sale_id','=',self.id)])
                    if not message_obj and self.state == 'draft':
                        message_obj = self.message_post(body=message_body, message_type='notification')
                        message_obj.write({'sale_id': self.id,'invoice_ids': [(6, 0, inv_ids)]})
            else:
                if picking_obj:
                    picking_obj.write({'over_due_date': False})
                else:
                    self.write({'over_due_date': False})
            return inv_obj
        else:
            self.write({'over_due_date': False})
    
    # @api.onchange('amount_total','date_order')
    # def check_amount(self):
    #     for order in self:
    #         order.check_limit()
    #         order.check_top(False)
    
    def action_confirm(self):
        for order in self:
            inv_obj = order.check_top(False)
            order.check_blocking_top(inv_obj)
        res = super(SaleOrder, self).action_confirm()
        return res
    
    @api.model
    def create(self, vals):
        res = super(SaleOrder, self).create(vals)
        res.check_top(False)
        return res


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    over_due_date = fields.Boolean('Over Due Date?', dafault=False, copy=False)
    # approval
    approval_bod = fields.Many2one('res.users',string='Approved by BOD', copy=False,
        domain=lambda self: [
            (
                "groups_id",
                "in",
                self.env.ref("sdt_block_so_by_top.delivery_order_approval").id,
            )
        ])
    approval_bod_time = fields.Datetime(string='Approved (Time)', copy=False)
    approval_bod_state = fields.Selection(
        string='State',
        selection=[
            ('draft', 'Draft'),
            ('waiting', 'Waiting'),
            ('approved', 'Approved'),
            ('refuse', 'Refused'),
            ], default='draft',copy=False, readonly=True)
    has_approve = fields.Boolean(string="Has Access To Approve", compute="_compute_has_approve")

    def _compute_has_approve(self):
        for request in self:
            sale_order = request.sale_id
            if sale_order:
                sale_order.check_top(request)
            if request.approval_bod == self.env.user:
                request.has_approve = True
            else:
                request.has_approve = False
            
    def _get_user_approval_activities(self, user):
        domain = [
            ('res_model', '=', 'stock.picking'),
            ('res_id', 'in', self.ids),
            ('activity_type_id', '=', 4),
            ('user_id', '=', user.id)
        ]
        activities = self.env['mail.activity'].search(domain)
        return activities
    
    def action_request_approval(self):
        for data in self:
            if not data.approval_bod:
                raise ValidationError(_('Please select a User for Approval.'))
            data.write({'approval_bod_state': 'waiting',})
            data.activity_schedule(
                'mail.mail_activity_todo',
                user_id=data.approval_bod.id,
                summary='Delivery Order: To Approve')
    
    def action_approve(self):
        for data in self:
            data.write({'approval_bod_time': fields.Datetime.now(),
                        'approval_bod_state': 'approved',})
            data.sudo()._get_user_approval_activities(user=data.env.user).action_feedback()
    
    def action_refuse(self):
        for order in self:
            order.write({'approval_bod_time': fields.Datetime.now(),
                        'approval_bod_state': 'refuse',})
            order.sudo()._get_user_approval_activities(user=order.env.user).action_feedback()
    
    def action_reset_approval(self):
        for rec in self:
            sale_order = rec.sale_id
            if sale_order:
                inv_obj = sale_order.check_top(rec)
            rec.write({'approval_bod_time': False,
                        'approval_bod_state': 'draft',})

    def button_validate(self):
        for rec in self:
            sale_order = rec.sale_id
            if sale_order:
                inv_obj = sale_order.check_top(rec)
            if rec.over_due_date == True and rec.approval_bod_state != 'approved':
                if inv_obj:
                    inv_name = ', '.join(inv for inv in inv_obj.mapped('name'))
                    raise ValidationError(
                            _(
                                "Tidak dapat confirm Delivery Order.\n"
                                "Karena invoice ('%s') overdue."
                            )
                            % (inv_name)
                        )
                else:
                    rec.write({'over_due_date': False})
                    return super(StockPicking, rec).button_validate()
        return super(StockPicking, rec).button_validate()
            


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    @api.onchange("qty_done")
    def onchange_qty_done_top(self):
        sale_order = self.move_id.picking_id.sale_id
        if sale_order:
            sale_order.check_top(self.move_id.picking_id)