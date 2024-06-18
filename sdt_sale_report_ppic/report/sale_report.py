# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools


class SaleReport(models.Model):
    _name = "sdt.sale.report"
    _description = "Sales Analysis Report"
    _auto = False
    _rec_name = 'date'
    _order = 'date desc'

    @api.model
    def _get_done_states(self):
        return ['sale', 'done']

    name = fields.Char('Order Reference', readonly=True)
    date = fields.Datetime('Order Date', readonly=True)
    delivery_date = fields.Datetime('Delivery Deadline Date', readonly=True)
    product_id = fields.Many2one('product.product', 'Product Variant', readonly=True)
    product_uom = fields.Many2one('uom.uom', 'Unit of Measure', readonly=True)
    product_uom_qty = fields.Float('Qty Ordered', readonly=True)
    qty_to_deliver = fields.Float('Qty To Deliver', readonly=True)
    qty_delivered = fields.Float('Qty Delivered', readonly=True)
    qty_to_invoice = fields.Float('Qty To Invoice', readonly=True)
    qty_invoiced = fields.Float('Qty Invoiced', readonly=True)
    partner_id = fields.Many2one('res.partner', 'Customer', readonly=True)
    company_id = fields.Many2one('res.company', 'Company', readonly=True)
    user_id = fields.Many2one('res.users', 'Salesperson', readonly=True)
    product_tmpl_id = fields.Many2one('product.template', 'Product', readonly=True)
    categ_id = fields.Many2one('product.category', 'Product Category', readonly=True)
    nbr = fields.Integer('# of Lines', readonly=True)
    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account', readonly=True)
    team_id = fields.Many2one('crm.team', 'Sales Team', readonly=True)
    country_id = fields.Many2one('res.country', 'Customer Country', readonly=True)
    industry_id = fields.Many2one('res.partner.industry', 'Customer Industry', readonly=True)
    commercial_partner_id = fields.Many2one('res.partner', 'Customer Entity', readonly=True)
    state = fields.Selection([
        ('draft', 'Draft Quotation'),
        ('sent', 'Quotation Sent'),
        ('sale', 'Sales Order'),
        ('done', 'Sales Done'),
        ('cancel', 'Cancelled'),
        ], string='Status', readonly=True)
    weight = fields.Float('Gross Weight', readonly=True)
    volume = fields.Float('Volume', readonly=True)

    campaign_id = fields.Many2one('utm.campaign', 'Campaign', readonly=True)
    medium_id = fields.Many2one('utm.medium', 'Medium', readonly=True)
    source_id = fields.Many2one('utm.source', 'Source', readonly=True)

    order_id = fields.Many2one('sale.order', 'Order #', readonly=True)

    def _with_sale(self):
        return ""

    def _select_sale(self):
        select_ = f"""
            MIN(l.id) AS id,
            l.product_id AS product_id,
            t.uom_id AS product_uom,
            CASE WHEN l.product_id IS NOT NULL THEN SUM(l.product_uom_qty / u.factor * u2.factor) ELSE 0 END AS product_uom_qty,
            CASE WHEN l.product_id IS NOT NULL THEN SUM(l.qty_delivered / u.factor * u2.factor) ELSE 0 END AS qty_delivered,
            CASE WHEN l.product_id IS NOT NULL THEN SUM((l.product_uom_qty - l.qty_delivered) / u.factor * u2.factor) ELSE 0 END AS qty_to_deliver,
            CASE WHEN l.product_id IS NOT NULL THEN SUM(l.qty_invoiced / u.factor * u2.factor) ELSE 0 END AS qty_invoiced,
            CASE WHEN l.product_id IS NOT NULL THEN SUM(l.qty_to_invoice / u.factor * u2.factor) ELSE 0 END AS qty_to_invoice,
            l.delivery_deadline AS delivery_date,
            COUNT(*) AS nbr,
            s.name AS name,
            s.date_order AS date,
            s.state AS state,
            s.partner_id AS partner_id,
            s.user_id AS user_id,
            s.company_id AS company_id,
            s.campaign_id AS campaign_id,
            s.medium_id AS medium_id,
            s.source_id AS source_id,
            t.categ_id AS categ_id,
            s.analytic_account_id AS analytic_account_id,
            s.team_id AS team_id,
            p.product_tmpl_id,
            partner.country_id AS country_id,
            partner.industry_id AS industry_id,
            partner.commercial_partner_id AS commercial_partner_id,
            CASE WHEN l.product_id IS NOT NULL THEN SUM(p.weight * l.product_uom_qty / u.factor * u2.factor) ELSE 0 END AS weight,
            CASE WHEN l.product_id IS NOT NULL THEN SUM(p.volume * l.product_uom_qty / u.factor * u2.factor) ELSE 0 END AS volume,
            s.id AS order_id"""

        additional_fields_info = self._select_additional_fields()
        template = """,
            %s AS %s"""
        for fname, query_info in additional_fields_info.items():
            select_ += template % (query_info, fname)

        return select_

    def _case_value_or_one(self, value):
        return f"""CASE COALESCE({value}, 0) WHEN 0 THEN 1.0 ELSE {value} END"""

    def _select_additional_fields(self):
        """Hook to return additional fields SQL specification for select part of the table query.

        :returns: mapping field -> SQL computation of field, will be converted to '_ AS _field' in the final table definition
        :rtype: dict
        """
        return {}

    def _from_sale(self):
        return """
            sale_order_line l
            LEFT JOIN sale_order s ON s.id=l.order_id
            JOIN res_partner partner ON s.partner_id = partner.id
            LEFT JOIN product_product p ON l.product_id=p.id
            LEFT JOIN product_template t ON p.product_tmpl_id=t.id
            LEFT JOIN uom_uom u ON u.id=l.product_uom
            LEFT JOIN uom_uom u2 ON u2.id=t.uom_id
            JOIN {currency_table} ON currency_table.company_id = s.company_id
            """.format(
            currency_table=self.env['res.currency']._get_query_currency_table(
                {
                    'multi_company': True,
                    'date': {'date_to': fields.Date.today()}
                }),
            )

    def _where_sale(self):
        return """
            l.display_type IS NULL"""

    def _group_by_sale(self):
        return """
            l.product_id,
            l.order_id,
            l.delivery_deadline,
            t.uom_id,
            t.categ_id,
            s.name,
            s.date_order,
            s.partner_id,
            s.user_id,
            s.state,
            s.company_id,
            s.campaign_id,
            s.medium_id,
            s.source_id,
            s.analytic_account_id,
            s.team_id,
            p.product_tmpl_id,
            partner.country_id,
            partner.industry_id,
            partner.commercial_partner_id,
            s.id,
            currency_table.rate"""

    def _query(self):
        with_ = self._with_sale()
        return f"""
            {"WITH" + with_ + "(" if with_ else ""}
            SELECT {self._select_sale()}
            FROM {self._from_sale()}
            WHERE {self._where_sale()}
            GROUP BY {self._group_by_sale()}
            {")" if with_ else ""}
        """

    @property
    def _table_query(self):
        return self._query()
