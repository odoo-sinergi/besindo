# -*- coding: utf-8 -*-
{
    'name': "SDT UDF BESINDO",

    'summary': """
        SDT UDF BESINDO """,

    'description': """
        SDT UDF by PT. Sinergi Data Totalindo
    """,

    'author': "Sinergi Data Totalindo, PT",
    'website': "http://www.sinergidata.co.id",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Customizations',
    'version': '16.0.1',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'stock',
        'product',
        'sale',
        'account',
        'mrp',
        'mrp_workorder',
        'approvals',
    ],

    # always loaded
    'data': [
        'security/user_groups.xml',
        'security/ir.model.access.csv',
        'views/product_template.xml',
        'views/jenis_product.xml',
        'views/res_partner.xml',
        'views/stock_picking.xml',
        'views/sale_report.xml',
        'views/account_invoice_report.xml',
        'views/sdt_operator_factory.xml',
        'views/mrp_production.xml',
        'views/tempat_pengiriman.xml',
        'views/purchase_order.xml',
        'views/account_move.xml',
        'views/stock_picking_type.xml',
        'views/sale_order.xml',
        'views/approval_category.xml',
        'views/approval_request.xml',
    ],
    # only loaded in demonstration mode
    # 'demo': [
    #     'demo/demo.xml',
    # ],
}