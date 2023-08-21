from odoo import api, models
from datetime import datetime
from odoo.exceptions import UserError


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def button_confirm(self):
        # do actual processing
        res = super(PurchaseOrder, self).button_confirm()
        # overwrite date field where applicable
        for data in self:
            if data.date_order:
                data.write(
                    {
                        'date_approve': data.date_order,
                        'effective_date': data.date_order,
                        }
                    )
                # data.picking_ids.write({'force_date': data.date_order})
        return res
