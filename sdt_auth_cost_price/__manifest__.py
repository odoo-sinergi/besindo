# -*- coding: utf-8 -*-
{
    'name': "SDT Authorization for Cost and Price",

    'summary': """
        SDT Authorization for Cost and Price""",

    'description': """
        SDT Authorization for Cost and Price
    """,

    'author': "Sinergi Data Totalindo, PT",
    'website': "http://www.sinergidata.co.id",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'accounting',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','product', 'stock','account','sale', 'sale_margin'],

    # always loaded
    'data': [
        'security/user_groups.xml',
        # 'security/ir.model.access.csv',
        'views/product_template.xml',
        'views/sale_order.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}