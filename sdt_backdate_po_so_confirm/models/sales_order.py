from odoo import fields, models, api, _
from odoo.exceptions import UserError


class SalesOrder(models.Model):
    _inherit = "sale.order"

    def _prepare_confirmation_values(self):
        date_draft = self.date_order
        draft_year = date_draft.strftime("%Y")
        draft_month = date_draft.strftime("%m")
        draft_day = date_draft.strftime("%d")
        date_now = fields.Datetime.now()
        now_year = date_now.strftime("%Y")
        now_month = date_now.strftime("%m")
        now_day = date_now.strftime("%d")
        if draft_year == now_year and draft_month == now_month and draft_day == now_day :
            return {
                'state': 'sale',
                'date_order': fields.Datetime.now()
            }
        else :
            return {
            'state': 'sale',
            'date_order': date_draft
            }
    
    def action_confirm(self):
        # do actual processing
        res = super(SalesOrder, self).action_confirm()
        # overwrite date field where applicable
        for data in self:
            if data.date_order:
                data.write({'effective_date': data.date_order})
                for pick in data.picking_ids:
                    if pick.state not in ('done', 'cancel'):
                        pick.write(
                            {
                                'scheduled_date': data.date_order,
                                'date_deadline': data.date_order,
                            }
                        )
        return res
