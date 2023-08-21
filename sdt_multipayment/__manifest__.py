# -*- coding: utf-8 -*-
{
    'name': "SDT Multi Payment",

    'summary': """
        Modul Multi Payment""",

    'description': """
        
    """,

    'author': "Sinergi Data Totalindo, PT",
    'website': "http://www.sinergidata.co.id",
    'category': 'accounting',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base',
                'account'],

    # always loaded
    'data': [
        "security/group.xml",
		"security/ir.model.access.csv",
        'views/sdt_multipayment_account_view.xml',
        'wizard/sdt_multipayment_view.xml',
    ],

    'application': True,
    'installable': True,
    'auto_install': False,
}