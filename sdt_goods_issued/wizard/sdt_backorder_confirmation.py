# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class sdt_backorder_confirmation(models.TransientModel):
    _inherit = 'stock.backorder.confirmation'

    def process_cancel_backorder(self):
        if self.pick_ids.request_id:
            for line in self.pick_ids.move_ids_without_package:
                request_obj = self.env['consignment.request.line'].search(
                    [('request_id', '=', self.pick_ids.request_id.id), ('product_id', '=', line.product_id.id)])
                request_obj.write({'qty_receipt': request_obj.qty_receipt + line.quantity_done, 'state': 'done'})
            req_obj = self.env['consignment.request'].search([('id', '=', self.pick_ids.request_id.id)])
            req_obj.write({'state': 'done'})
        res=super(sdt_backorder_confirmation, self).process_cancel_backorder()
        pick_obj=self.env['stock.picking'].search([('backorder_id','=',self.pick_ids.id)])
        pick_obj.action_cancel()
        return res

    def _process(self, cancel_backorder=False):
        res = super(sdt_backorder_confirmation, self)._process()
        if cancel_backorder==False:
            if self.pick_ids.request_id:
                for line in self.pick_ids.move_ids_without_package:
                    request_obj = self.env['consignment.request.line'].search(
                        [('request_id.numb_request_consgn', '=', line.numb_req_cons), ('product_id', '=', line.product_id.id)])
                    if request_obj:
                        if request_obj.state!='done':
                            if request_obj.qty_receipt + line.quantity_done >= request_obj.qty_request:
                                request_obj.write({'qty_receipt': request_obj.qty_receipt + line.quantity_done, 'state': 'done'})
                            else:
                                request_obj.write({'qty_receipt': request_obj.qty_receipt + line.quantity_done, 'state': 'partial'})
                source = self.pick_ids.origin
                cons_request = source.split(', ')
                partial = ''
                open = ''
                done = ''
                for pbk in cons_request:
                    req_obj = self.env['consignment.request'].search([('numb_request_consgn', '=', pbk)])
                    for request in req_obj.line_ids:
                        if request.state == 'partial':
                            partial = 'Y'
                        elif request.state == 'open':
                            open = 'Y'
                        elif request.state == 'done':
                            done = 'Y'

                    if partial == 'Y':
                        req_obj.write({'state': 'partial'})
                    if open == 'Y' and done == '':
                        req_obj.write({'state': 'partial'})
                    if done == 'Y' and partial == '' and open == '':
                        req_obj.write({'state': 'done'})
        return res


