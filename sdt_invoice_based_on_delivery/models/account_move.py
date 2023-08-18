from odoo import api, fields, models, _ , SUPERUSER_ID
#from odoo.addons.product.models import decimal_precision as dp
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
from datetime import datetime
from datetime import timedelta
from lxml import etree
class AccountMove(models.Model):
    _inherit='account.move'

    # SO
    sale_id = fields.Many2one(comodel_name='sale.order',string='Sales Order',store=True)
    sale_procurement_group_id = fields.Many2one(comodel_name='procurement.group',string='Sale Procurement Group', related='sale_id.procurement_group_id',readonly=True, store=True)
    stock_picking_tt_ids = fields.Many2many(string='DO',comodel_name='stock.picking', relation='account_picking_tt_rel',column1='move_id',column2='picking_id',)
    invoice_include_id = fields.Many2one(comodel_name='account.move',string='Include DP')
    invoice_dp_ids = fields.Many2many(comodel_name='account.move',string='Invoice DP', compute="_compute_invoice_dp_ids")
    # PO
    po_id = fields.Many2one(comodel_name='purchase.order',string='Purchase Order',store=True)
    purchase_procurement_group_id = fields.Many2one(comodel_name='procurement.group',string='Purchase Procurement Group', related='po_id.group_id',readonly=True, store=True)
    stock_picking_po_ids = fields.Many2many(string='RO',comodel_name='stock.picking', relation='account_picking_po_rel',column1='move_id',column2='picking_id',)
    is_generate = fields.Selection(string='is_generate', selection=[('y', 'Y'), ('n', 'N')], default='n')
    

    def generate_move_line (self):
        self.invoice_line_ids.unlink()
        self.create_invoice_line()

    @api.depends('sale_id')
    def _compute_invoice_dp_ids(self):
        for data in self:
            invoice_dp_ids = []
            for inv in data.sale_id.invoice_ids.filtered(lambda x:x.state=='posted'):
                is_dp = all(l.product_id.default_code=='SALES DOWN PAYMENT' for l in inv.invoice_line_ids)
                if is_dp:
                    invoice_dp_ids.append(inv.id)
            data.invoice_dp_ids = invoice_dp_ids
    
    def unlink_invoice_number_picking (self):
        if self.sale_id :
            for stock_picking_tt_id in self.stock_picking_tt_ids :
                if stock_picking_tt_id :
                    stock_picking_tt_id.invoice_id = False
            self.invoice_line_ids.sudo().unlink()
            self.stock_picking_tt_ids = False

        if self.po_id :
            for stock_picking_po_id in self.stock_picking_po_ids :
                if stock_picking_po_id :
                    stock_picking_po_id.invoice_id = False
            self.invoice_line_ids.sudo().unlink()
            self.stock_picking_po_ids = False
        self.is_generate = 'n'
        
    
    def action_post(self):
        res = super().action_post()
        for data in self:
            if self.sale_id :
                for stock_picking_tt_id in data.stock_picking_tt_ids :
                    if stock_picking_tt_id :
                        stock_picking_tt_id.invoice_id = data.id
            if self.po_id :
                for stock_picking_po_id in data.stock_picking_po_ids :
                    if stock_picking_po_id :
                        stock_picking_po_id.invoice_id = data.id
        return res

    
    def create_invoice_line (self):
        product_id = self.env['ir.config_parameter'].sudo().get_param('sale.default_deposit_product_id')
        product_dp_sale = self.env['product.product'].browse(int(product_id)).exists()
        if self.sale_id :
            aml_obj = self.env["account.move.line"]
            move_id = []
            semua_data_invoice = []
            sale_line_dp = self.sale_id.order_line.filtered(lambda x:x.product_id.id==product_dp_sale.id)
            for stock_picking_tt_id in self.stock_picking_tt_ids :
                for stock_move in stock_picking_tt_id.move_ids_without_package :
                    move_id.append(stock_move.id )
                    if stock_move.product_id.categ_id.property_valuation == 'real_time':
                        account = stock_move.product_id.categ_id.property_account_income_categ_id.id
                    else:
                        account = account = stock_move.product_id.property_account_income_id.id or stock_move.product_id.categ_id.property_account_income_categ_id.id
                    so_line = stock_move.sale_line_id
                    semua_data_invoice.append((0,0,{
                        "name": so_line.name,
                        "move_id": self.id,
                        "account_id": account,
                        "price_unit": so_line.price_unit,
                        "quantity": stock_move.quantity_done,
                        "currency_id": so_line.currency_id.id,
                        "product_uom_id": so_line.product_uom.id,
                        "product_id": so_line.product_id.id,
                        "sale_line_ids": [(6, 0, so_line.ids)],
                        "tax_ids": [(6, 0, so_line.tax_id.ids)],
                    }))

            if move_id:
                stock_move_2 = self.env['stock.move'].search([('origin_returned_move_id', 'in', tuple(move_id))])
                if stock_move_2 :
                    for sm2 in stock_move_2 :
                        account_2 = sm2.product_id.property_account_income_id.id or sm2.product_id.categ_id.property_account_income_categ_id.id
                        so_line_2 = sm2.sale_line_id
                        semua_data_invoice.append((0,0,{
                            "name": so_line_2.name,
                            "move_id": self.id,
                            "account_id": account_2,
                            "price_unit": so_line_2.price_unit,
                            "quantity": sm2.quantity_done * -1,
                            "currency_id": so_line_2.currency_id.id,
                            "product_uom_id": so_line_2.product_uom.id,
                            "product_id": so_line_2.product_id.id,
                            "sale_line_ids": [(6, 0, so_line_2.ids)],
                            "tax_ids": [(6, 0, so_line_2.tax_id.ids)],
                        }))
            # if sale_line_dp:
            #     for dp_line in sale_line_dp:
            #         account_dp = dp_line.product_id.property_account_income_id or dp_line.product_id.categ_id.property_account_income_categ_id
            #         tax_ids = self.sale_id.order_line.filtered(lambda x:x.product_id.id != product_dp_sale.id).mapped('tax_id').ids
            #         semua_data_invoice.append((0,0,{
            #             "name": dp_line.name,
            #             "move_id": self.id,
            #             "account_id": account_dp.id,
            #             "price_unit": dp_line.price_unit,
            #             "quantity": -1,
            #             "currency_id": dp_line.currency_id.id,
            #             "product_uom_id": dp_line.product_uom.id,
            #             "product_id": dp_line.product_id.id,
            #             "sale_line_ids": [(6, 0, dp_line.ids)],
            #             "tax_ids": [(6, 0, tax_ids)],
            #         }))
            if self.invoice_include_id:
                for dp_line in self.invoice_include_id.invoice_line_ids:
                    account_dp = dp_line.product_id.property_account_income_id or dp_line.product_id.categ_id.property_account_income_categ_id
                    tax_ids = self.sale_id.order_line.filtered(lambda x:x.product_id.id != product_dp_sale.id).mapped('tax_id').ids
                    semua_data_invoice.append((0,0,{
                        "name": dp_line.name,
                        "move_id": self.id,
                        "account_id": account_dp.id,
                        "price_unit": dp_line.price_unit,
                        "quantity": -1,
                        "currency_id": dp_line.currency_id.id,
                        "product_uom_id": dp_line.product_uom_id.id,
                        "product_id": dp_line.product_id.id,
                        "sale_line_ids": [(6, 0, dp_line.sale_line_ids.ids)],
                        "tax_ids": [(6, 0, tax_ids)],
                    }))
            pack= []
            for record in semua_data_invoice:
                if not pack :
                    total_qty = record[2]['quantity']
                    pack.append((0,0,{
                        "name": record[2]['name'],
                        "move_id": record[2]['move_id'],
                        "account_id": record[2]['account_id'],
                        "price_unit": record[2]['price_unit'],
                        "quantity": record[2]['quantity'],
                        "currency_id": record[2]['currency_id'],
                        "product_uom_id": record[2]['product_uom_id'],
                        "product_id": record[2]['product_id'],
                        "sale_line_ids": record[2]['sale_line_ids'],
                        "tax_ids": record[2]['tax_ids'],
                    }))
                else :
                    check_data = [d for d in pack if d[2]['product_id'] == record[2]['product_id'] and d[2]['price_unit'] == record[2]['price_unit'] and d[2]['name'] == record[2]['name']]
                    if not check_data :
                        pack.append((0,0,{
                            "name": record[2]['name'],
                            "move_id": record[2]['move_id'],
                            "account_id": record[2]['account_id'],
                            "price_unit": record[2]['price_unit'],
                            "quantity": record[2]['quantity'],
                            "currency_id": record[2]['currency_id'],
                            "product_uom_id": record[2]['product_uom_id'],
                            "product_id": record[2]['product_id'],
                            "sale_line_ids": record[2]['sale_line_ids'],
                            "tax_ids": record[2]['tax_ids'],
                        }))
                    else :
                        qty_var = check_data[0][2]['quantity'] + record[2]['quantity']
                        for pk in pack :
                            if pk[2]['product_id'] == record[2]['product_id'] and pk[2]['price_unit'] == record[2]['price_unit'] and pk[2]['name'] == record[2]['name'] :
                                pk[2]['quantity'] = qty_var
                
                                
            self.invoice_line_ids = pack
            # SO
            for stock_picking_tt_id in self.stock_picking_tt_ids :
                if stock_picking_tt_id :
                    stock_picking_tt_id.invoice_id = self.id
            x = 1
        # PO
        if self.po_id :
            aml_obj = self.env["account.move.line"]
            move_id = []
            semua_data_invoice = []
            for stock_picking_tt_id in self.stock_picking_po_ids :
                for stock_move in stock_picking_tt_id.move_ids_without_package :
                    move_id.append(stock_move.id )

                    # account = stock_move.product_id.property_account_income_id.id or stock_move.product_id.categ_id.property_account_income_categ_id.id
                    if stock_move.product_id.categ_id.property_valuation == 'real_time':
                        account = stock_move.product_id.categ_id.property_stock_account_input_categ_id.id
                    else:
                        account = stock_move.product_id.categ_id.property_account_expense_categ_id.id
                    po_line = stock_move.purchase_line_id
                    semua_data_invoice.append((0,0,{
                        "name": po_line.name,
                        "move_id": self.id,
                        "account_id": account,
                        "price_unit": po_line.price_unit,
                        "quantity": stock_move.quantity_done,
                        "currency_id": po_line.currency_id.id,
                        "product_uom_id": po_line.product_uom.id,
                        "product_id": po_line.product_id.id,
                        # "purchase_line_id": [(6, 0, po_line.ids)],
                        "purchase_line_id": po_line.id,
                        "tax_ids": [(6, 0, po_line.taxes_id.ids)],
                    }))

            if move_id:
                stock_move_2 = self.env['stock.move'].search([('origin_returned_move_id', 'in', tuple(move_id))])
                if stock_move_2 :
                    for sm2 in stock_move_2 :
                        if sm2.product_id.categ_id.property_valuation == 'real_time':
                            account_2 = sm2.product_id.categ_id.property_stock_account_input_categ_id.id
                        else:
                            account_2 = sm2.product_id.categ_id.property_account_expense_categ_id.id
                        po_line_2 = sm2.purchase_line_id
                        semua_data_invoice.append((0,0,{
                            "name": po_line_2.name,
                            "move_id": self.id,
                            "account_id": account_2,
                            "price_unit": po_line_2.price_unit,
                            "quantity": sm2.quantity_done * -1,
                            "currency_id": po_line_2.currency_id.id,
                            "product_uom_id": po_line_2.product_uom.id,
                            "product_id": po_line_2.product_id.id,
                            "purchase_line_id": po_line_2.id,
                            "tax_ids": [(6, 0, po_line_2.taxes_id.ids)],
                        }))
            pack= []
            for record in semua_data_invoice:
                if not pack :
                    total_qty = record[2]['quantity']
                    pack.append((0,0,{
                        "name": record[2]['name'],
                        "move_id": record[2]['move_id'],
                        "account_id": record[2]['account_id'],
                        "price_unit": record[2]['price_unit'],
                        "quantity": record[2]['quantity'],
                        "currency_id": record[2]['currency_id'],
                        "product_uom_id": record[2]['product_uom_id'],
                        "product_id": record[2]['product_id'],
                        "purchase_line_id": record[2]['purchase_line_id'],
                        "tax_ids": record[2]['tax_ids'],
                    }))
                else :
                    check_data = [d for d in pack if d[2]['product_id'] == record[2]['product_id'] and d[2]['price_unit'] == record[2]['price_unit'] and d[2]['name'] == record[2]['name']]
                    if not check_data :
                        pack.append((0,0,{
                            "name": record[2]['name'],
                            "move_id": record[2]['move_id'],
                            "account_id": record[2]['account_id'],
                            "price_unit": record[2]['price_unit'],
                            "quantity": record[2]['quantity'],
                            "currency_id": record[2]['currency_id'],
                            "product_uom_id": record[2]['product_uom_id'],
                            "product_id": record[2]['product_id'],
                            "purchase_line_id": record[2]['purchase_line_id'],
                            "tax_ids": record[2]['tax_ids'],
                        }))
                    else :
                        qty_var = check_data[0][2]['quantity'] + record[2]['quantity']
                        for pk in pack :
                            if pk[2]['product_id'] == record[2]['product_id'] and pk[2]['price_unit'] == record[2]['price_unit'] and pk[2]['name'] == record[2]['name'] :
                                pk[2]['quantity'] = qty_var
                                
            self.invoice_line_ids = pack
            self.invoice_date = datetime.today().strftime('%Y-%m-%d')
            # PO
            for stock_picking_po_id in self.stock_picking_po_ids :
                if stock_picking_po_id :
                    stock_picking_po_id.invoice_id = self.id
            x = 1
        self.is_generate = 'y'
