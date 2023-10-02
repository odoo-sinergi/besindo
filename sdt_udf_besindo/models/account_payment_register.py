from odoo import api, fields, models, _ , SUPERUSER_ID
from odoo.exceptions import UserError
from functools import lru_cache


class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"

    
    # @api.model
    # def _get_batch_communication(self, batch_result):
    #     ''' Helper to compute the communication based on the batch.
    #     :param batch_result:    A batch returned by '_get_batches'.
    #     :return:                A string representing a communication to be set on payment.
    #     '''
    #     labels = set(line.name+' ('+line.move_id.accounting_ref+')' if line.move_id.accounting_ref else line.name or line.move_id.ref+' ('+line.move_id.accounting_ref+')' if line.move_id.accounting_ref else line.move_id.ref or line.move_id.name+' ('+line.move_id.accounting_ref+')' if line.move_id.accounting_ref else line.move_id.name for line in batch_result['lines'])
    #     return ' '.join(sorted(labels))