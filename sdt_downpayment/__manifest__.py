# -*- coding: utf-8 -*-
{
    'name': "SDT Down Payment",

    'summary': """
        Handle Down Payment""",

    'description': """
        Handle Down Payment
    """,

    'author': "Sinergi Data Totalindo, PT",
    'website': "http://www.sinergidata.co.id",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Accounting',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base',
                'account',
                # 'account_voucher',
                ],

    # always loaded
    'data': [
        'security/group.xml',
		'security/ir.model.access.csv',
        'views/udf_account_payment_view.xml',
        'views/sdt_downpayment_account.xml',
        'views/udf_account_journal_view.xml',
        'views/udf_account_view.xml',
        'report/sdt_down_payment_report.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}