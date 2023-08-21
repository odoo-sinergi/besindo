# -*- coding: utf-8 -*-
{
    'name': "SDT INVOICING BASED ON DELIVERY BESINDO",

    'summary': """
        SDT INVOICING BASED ON DELIVERY BESINDO """,

    'description': """
        SDT INVOICING BASED ON DELIVERY by PT. Sinergi Data Totalindo
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
        'account',
        'sale',
    ],

    # always loaded
    'data': [
        'views/stock.xml',
        'views/account_move.xml',
    ],
    # only loaded in demonstration mode
    # 'demo': [
    #     'demo/demo.xml',
    # ],
}