# -*- coding: utf-8 -*-

from odoo import api, fields, models, _ , SUPERUSER_ID
#from odoo.addons.product.models import decimal_precision as dp
from odoo.addons import decimal_precision as dp
from  odoo.exceptions import UserError
from datetime import datetime
from datetime import timedelta
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

_STATES = [
    ('open', 'Draft'),
    ('to_approved', 'To Be Approved'),
    ('approved', 'Approved'),
    ('rejected', 'Rejected'),
    ('valid', 'Done'),
    ('canceled', 'Canceled')
]


class SDTGoodsIssued(models.Model):
    _name = 'sdt.goods.issued'
    _description = 'Goods Issued'
    _order = 'name desc, id desc'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'sequence.mixin']

    @api.model
    def _get_default_requested_by(self):
        return self.env['res.users'].browse(self.env.uid)

    @api.model
    def _get_default_name(self):
        return self.env['ir.sequence'].next_by_code('sdt.goods.issued')

    name = fields.Char('Name', size=32, required=True, default=_get_default_name, track_visibility='onchange',copy=True,index=True)
    date = fields.Date('Date', default=fields.Date.context_today, track_visibility='onchange')
    partner_id = fields.Many2one('res.partner', string='Vendor', track_visibility='onchange')
    # date_issued = fields.Date('Issued Date', default=fields.Date.context_today, track_visibility='onchange')
    force_date = fields.Date('Force Date', default=fields.Date.context_today, track_visibility='onchange')
    picking_type_id = fields.Many2one('stock.picking.type', string='Operation Type', domain="[('code', '=', 'internal'),('default_location_dest_id.usage', '=', 'inventory')]")
    location_from = fields.Many2one('stock.location', string='Location From', domain="[('usage', '=', 'internal')]")
    location_to = fields.Many2one('stock.location', string='Location To', track_visibility='onchange')
    picking_id = fields.Many2one('stock.picking', 'Picking', track_visibility='onchange')
    description = fields.Text('Description')
    line_ids = fields.One2many('sdt.goods.issued.line', 'issued_id', string='Products to Issued', states={'open': [('readonly', False)]}, copy=True, readonly=True,)
    state = fields.Selection(selection=_STATES,string='Status',index=True,track_visibility='onchange',required=True,copy=False,default='open')
    company_id = fields.Many2one('res.company', required=True, readonly=True, default=lambda self: self.env.company)
    
    # @api.model
    # def create(self, vals):
    #     if not vals['line_ids']:
    #         raise UserError(('Line Detail is not found..'))
    #     for line in vals.get("line_ids"):
    #         product_id = line[2]["product_id"]
    #         cek_lot=self.env['product.product'].search([('id','=',product_id)])
    #         if cek_lot.product_tmpl_id.tracking!='none':
    #             if line[2]["lot_id"]==False:
    #                 raise UserError('Product %s need a lot number, not allow empty' % (cek_lot.product_tmpl_id.name))
        
    #     res = super(SDTGoodsIssued, self).create(vals)
    #     return res

    #@api.multi
    # def write(self, vals):
    #     # if vals.get('line_ids', False):
    #     #     for line in vals['line_ids']:
    #     #         product_id = line[2]["product_id"]
    #     #         cek_lot=self.env['product.product'].search([('id','=',product_id)])
    #     #         if cek_lot.product_tmpl_id.tracking!='none':
    #     #             if line[2]["lot_id"]==False:
    #     #                 raise UserError('Product %s need a lot number, not allow empty' % (cek_lot.product_tmpl_id.name))

    #     if vals.get('name', False):
    #         docnum=vals['name']
    #     else:
    #         docnum = self.name
    #     sql_query="""select count(1) from goods_issued where name=%s"""
    #     self.env.cr.execute(sql_query, (docnum,))
    #     cek = self.env.cr.fetchone()[0]
    #     if cek>1 :
    #         vals['name']=self.env['ir.sequence'].next_by_code('sdt.goods.issued')
    #     res = super(SDTGoodsIssued, self).write(vals)
    #     return res

    # @api.onchange('picking_type_id')
    # def onchange_picking_type(self):
    #     self.location_from=self.picking_type_id.default_location_src_id.id
    #     self.location_to=self.picking_type_id.default_location_dest_id.id

    def approve(self):
        self.state='approved'

    def to_approve(self):
        self.state='to_approved'

    def reject(self):
        self.state='rejected'

    def draft(self):
        self.state='open'

    def canceled(self):
        if self.state != 'open':
            raise UserError("Cancel not allowed")
        #1. Update Stock Quant - Location Source
        self.ensure_one()
        sql_query="""select count(1) from stock_move_line a left join stock_quant b on a.product_id=b.product_id and a.location_id=b.location_id and a.lot_id=b.lot_id
            where a.picking_id=%s and b.product_id is null
            """
        self.env.cr.execute(sql_query, (self.picking_id.id,))
        cek = self.env.cr.fetchone()[0]
        if cek:
            sql_query="""insert into stock_quant (product_id,company_id,location_id,lot_id,quantity,reserved_quantity,in_date,create_uid,create_date,write_uid,write_date)
                select a.product_id,a.company_id,a.location_id,a.lot_id,a.qty_done,0,(now() AT TIME ZONE 'UTC'),%s,(now() AT TIME ZONE 'UTC'),%s 
                from stock_move_line a left join stock_quant b on a.product_id=b.product_id and a.location_id=b.location_id 
                where a.picking_id=%s and b.product_id is null;
                """
            self.env.cr.execute(sql_query, (self._uid,self._uid,self.picking_id.id))
        else:
            sql_query="""Update stock_quant a set quantity=quantity+b.qty_done,write_uid=%s,write_date=(now() AT TIME ZONE 'UTC') from stock_move_line b 
                where a.product_id=b.product_id and a.location_id=b.location_id and a.lot_id=b.lot_id and b.picking_id=%s;
                """
            self.env.cr.execute(sql_query, (self._uid,self.picking_id.id))

        #2. Update Stock Quant - Location Destination
        sql_query="""select count(1) from stock_move_line a left join stock_quant b on a.product_id=b.product_id and a.location_dest_id=b.location_id and a.lot_id=b.lot_id
            where a.picking_id=%s and b.product_id is null
            """
        self.env.cr.execute(sql_query, (self.picking_id.id,))
        cek2 = self.env.cr.fetchone()[0]
        if cek2:
            sql_query="""insert into stock_quant (product_id,company_id,location_id,lot_id,quantity,reserved_quantity,in_date,create_uid,create_date,write_uid,write_date)
                select a.product_id,a.company_id,a.location_id,a.lot_id,a.qty_done*-1,0,(now() AT TIME ZONE 'UTC'),%s,(now() AT TIME ZONE 'UTC'),%s 
                from stock_move_line a left join stock_quant b on a.product_id=b.product_id and a.location_id=b.location_dest_id 
                where a.picking_id=%s and b.product_id is null;
                """
            self.env.cr.execute(sql_query, (self._uid,self._uid,self.picking_id.id))
        else:
            sql_query="""Update stock_quant a set quantity=quantity-b.qty_done from stock_move_line b where a.product_id=b.product_id and a.location_id=b.location_dest_id
            and a.lot_id=b.lot_id and b.picking_id=%s;
            """
            self.env.cr.execute(sql_query, (self.picking_id.id,))
        
        #3. Update Fifo stock.valuation.layer
        # sql_query="""Update stock_valuation_layer a set remaining_qty=remaining_qty+b.qty,remaining_value=remaining_value+b.total_cost from goods_issued_line_fifo b 
        #     where a.id=b.valuation_id and b.issued_id=%s;
        #     DELETE FROM stock_valuation_layer AS a USING stock_move AS b
        #     WHERE a.stock_move_id = b.id and b.picking_id=%s;
        #     """
        # self.env.cr.execute(sql_query, (self.id,self.picking_id.id,))
        
        #4. Delete Account Journal - Account Journal Line
        sql_query="""DELETE FROM account_move_line AS a USING account_move AS b,stock_move AS c
            WHERE a.move_id = b.id AND b.stock_move_id = c.id and c.picking_id=%s;
            DELETE FROM account_move AS a USING stock_move AS b
            WHERE a.stock_move_id = b.id and b.picking_id=%s;
            """
        self.env.cr.execute(sql_query, (self.picking_id.id,self.picking_id.id,))
        
        #5. Delete Stock Picking - Stock Move - Stock Move Line
        sql_query="""DELETE FROM stock_move_line WHERE picking_id=%s;
            DELETE FROM stock_move WHERE picking_id=%s;
            DELETE FROM stock_picking WHERE id=%s;
            """
        self.env.cr.execute(sql_query, (self.picking_id.id,self.picking_id.id,self.picking_id.id,))
        
        #6. Delete Good Issued Line Fifo
        # sql_query="""DELETE FROM goods_issued_line_fifo WHERE issued_id=%s;
        #     """
        # self.env.cr.execute(sql_query,(self.id,))
        
        self.state='canceled'

    def validate(self):
        self.ensure_one()
        header_trans = {}
        pick_id = self.picking_type_id.id
        header_trans = {'name': self.name,
                        'company_id': self.company_id.id,
                        # 'scheduled_date': self.date_issued,
                        'scheduled_date': self.date,
                        # 'force_date': self.force_date,
                        'location_id': self.location_from.id,
                        'location_dest_id': self.location_to.id,
                        'picking_type_id': self.picking_type_id.id,
                        'origin': self.name,
                        'state': 'assigned'}
        trans_dict = {}
        kirim = self.env['stock.picking'].create(header_trans)
        picking_id = kirim.id
        for line in self.line_ids:
            trans_dict = {'name': self.name,
                        'product_id': line.product_id.id,
                        'product_uom_qty': line.qty,
                        'product_uom': line.product_uom_id.id,
                        'analytic_product_id': line.analytic_product_id.id,
                        'analytic_project_id': line.analytic_project_id.id,
                        'analytic_section_id': line.analytic_section_id.id,
                        'analytic_departement_id': line.analytic_departement_id.id,
                        'state': 'assigned',
                        'picking_id': picking_id,
                        'location_id': self.location_from.id,
                        'location_dest_id': self.location_to.id,
                        'picking_type_id': self.picking_type_id.id,
                        'issued_line_id': line.id,
                        'move_line_ids': [(0, 0, {'product_id': line.product_id.id,
                                                    'picking_id': picking_id,
                                                    'lot_id': line.lot_id.id,
                                                    'qty_done': line.qty,
                                                    'product_uom_id': line.product_uom_id.id,
                                                    'package_id': False,
                                                    'result_package_id': False,
                                                    'location_id': self.location_from.id,
                                                    'location_dest_id': self.location_to.id, })],
                        'origin': self.name}

            move = self.env['stock.move'].create(trans_dict)
            move_id=move.id
            line.move_id=move_id

        kirim.button_validate()
        self.picking_id = picking_id
        self.state = 'valid'
        for line in self.line_ids:
            move_id=self.env['stock.move'].search([('picking_id','=',picking_id),('issued_line_id','=',line.id)]).id
            account_move=self.env['account.move'].search([('stock_move_id','=',move_id)])
            account_move_line=self.env['account.move.line'].search([('move_id','=',account_move.id),('product_id','=',line.product_id.id),('debit','>',0)])
            if account_move_line:
                all_analytic = {}
                for dep in line.analytic_product_id:
                    all_analytic.update({str(line.analytic_product_id.id) : 100})
                for dep in line.analytic_project_id:
                    all_analytic.update({str(line.analytic_project_id.id) : 100})
                for dep in line.analytic_section_id:
                    all_analytic.update({str(line.analytic_section_id.id) : 100})
                for dep in line.analytic_departement_id:
                    all_analytic.update({str(line.analytic_departement_id.id) : 100})
                account_move_line.write({
                    'account_id':line.account_id.id,
                    'analytic_product_id':line.analytic_product_id.id,
                    'analytic_project_id':line.analytic_project_id.id,
                    'analytic_section_id':line.analytic_section_id.id,
                    'analytic_departement_id':line.analytic_departement_id.id,
                    'analytic_distribution':all_analytic
                })
        
        # sql_query = """SELECT name FROM goods_issued_line_fifo INNER JOIN purchase_order ON goods_issued_line_fifo.po_id = purchase_order.id
        #             WHERE issued_id = %s """
        # self.env.cr.execute(sql_query, (self.id,))
        # result = self.env.cr.dictfetchall()
        # po = ""
        # for res in result:
        #     if po == "":
        #         po = res['name']
        #     else:
        #         po = po+', '+ res['name']

        # po_number = self.env['sdt.goods.issued.line'].search([('issued_id','=', self.id)])
        # if po_number:
        #     for line in po_number:
        #         line.write({
        #         'po_numbers' : po
        #         })
        return      
        

    @api.onchange('picking_type_id')
    def _onchange_picking_type_id(self):
        if not self.picking_type_id:
            return
        self.location_from = self.picking_type_id.default_location_src_id.id
        self.location_to = self.picking_type_id.default_location_dest_id.id
        
         


class SDTGoodsIssuedLine(models.Model):
    _name = "sdt.goods.issued.line"
    _description = "Goods Issued Line"
    _order = "id desc, name desc"
    _rec_names_search = ['name', 'issued_id', 'product_id']

    issued_id = fields.Many2one(comodel_name='sdt.goods.issued', string='Goods Issued', ondelete='cascade', required=True, index=True, copy=False, auto_join=True, check_company=True)
    name = fields.Char('Description')
    sequence = fields.Integer(string='Sequence', default=10)
    display_type = fields.Selection([
        ('line_section', "Section"),
        ('line_note', "Note")], default=False, help="Technical field for UX purpose.")
    product_id = fields.Many2one('product.product', 'Material Name',domain=[('type', '=', 'product')])
    product_uom_id = fields.Many2one(comodel_name='uom.uom', string='UoM', store=True)
    lot_id = fields.Many2one(comodel_name='stock.lot', string='Lot', store=True)
    qty = fields.Float(string='Qty', digits=dp.get_precision('Product Unit of Measure'))
    account_id = fields.Many2one('account.account', string='Account', index=True,)
    # analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account', index=True,)
    # analytic_tag_id = fields.Many2one('account.analytic.tag', string='Analytic Tag',)
    move_id = fields.Many2one('stock.move', string='Move Id', index=True,)
    company_id = fields.Many2one('res.company', required=True, related='issued_id.company_id', store=True, default=lambda self: self.env.company)
    analytic_product_id = fields.Many2one('account.analytic.account', string='Analytic Product', domain="[('plan_id.name','=','Product')]")
    analytic_project_id = fields.Many2one('account.analytic.account', string='Analytic Project', domain="[('plan_id.name','=','Project')]")
    analytic_section_id = fields.Many2one('account.analytic.account', string='Analytic Section', domain="[('plan_id.name','=','Section')]")
    analytic_departement_id = fields.Many2one('account.analytic.account', string='Analytic Departement', domain="[('plan_id.name','=','Departement')]")


    @api.onchange('product_id')
    def onchange_product_id(self):
        if not self.product_id:
            return
        if self.issued_id.location_from.id==False:
            raise UserError('Location From is empty, not allowed')

        self.product_uom_id=self.product_id.uom_id.id
        domain = {}
        lot_list = []
        sql_query="""select distinct lot_id from stock_quant where quantity-reserved_quantity>0 and product_id=%s and location_id=%s
            """
        self.env.cr.execute(sql_query,(self.product_id.id,self.issued_id.location_from.id,))
        res_lot=self.env.cr.dictfetchall()
        for lot in res_lot:
            lot_list.append(lot['lot_id'])
        product_uom_ids = self.env['uom.uom'].search([('category_id','=',self.product_id.uom_id.category_id.id)]).ids
        domain = {'product_uom_id': [('id', 'in', product_uom_ids)]}
        domain.update({'lot_id': [('id', '=', lot_list)]})
        return {'domain': domain}
