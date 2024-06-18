# -*- coding: utf-8 -*-
{
    'name': "SDT SALES ANALYSIS PPIC",

    'summary': """
        SDT SALES ANALYSIS PPIC """,

    'description': """
        Adding menu Sales Analysis without showing any cost or price for PPIC by PT. Sinergi Data Totalindo
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
        'sale',
        'stock',
    ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        # 'report/account_invoice_report_views.xml',
        # 'report/ir_actions_report_templates.xml',
        # 'report/ir_actions_report.xml',
        'report/sale_report_views.xml'
    ],
    # only loaded in demonstration mode
    # 'demo': [
    #     'demo/demo.xml',
    # ],
}