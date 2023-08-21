# -*- encoding: utf-8 -*-

{
    'name': 'SDT Customization',
    'version': '1.0',
    'category': 'Inventory',
    'author':'Sinergi Data Totalindo, PT',
    'description': """Customization
    """,
    'summary': 'Customization',
    'website': 'http://sinergidata.co.id',
    'data': [
        # 'views/account_move.xml',
        'views/sale_order.xml',
    ],
    'depends': ['mail','sale','account','purchase'],
    'installable': True,
    'auto_install': False,
    'application': False,
    'sequence': 105,
    'license': 'AGPL-3',
}
