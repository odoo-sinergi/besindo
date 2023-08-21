# -*- encoding: utf-8 -*-

{
    'name': 'SDT Goods Issued',
    'version': '1.0',
    'category': 'Inventory',
    'author':'Sinergi Data Totalindo, PT',
    'description': """A Good Issued is an instruction to Issued a certain quantity of materials,
                so that they are available at a certain point in time.
    """,
    'summary': 'Create good issued inventory',
    'website': 'http://sinergidata.co.id',
    'data': [
        'security/goods_issued_security.xml',
        'security/ir.model.access.csv',
        'data/goods_issued_sequence_data.xml',
        'data/return_goods_issued_sequence_data.xml',
        'views/goods_issued_view.xml',
        'views/return_goods_issued_view.xml',
        'views/stock.xml',
        'views/account_move.xml',
    ],
    'depends': ['base','stock','account','account_accountant',],
    'installable': True,
    'auto_install': False,
    'application': False,
    'sequence': 105,
    'license': 'AGPL-3',
}
