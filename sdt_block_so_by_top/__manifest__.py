# -*- encoding: utf-8 -*-

{
    'name': 'SDT Block SO By TOP',
    'version': '1.0',
    'category': 'Accounting',
    'author':'Sinergi Data Totalindo, PT',
    'description': """
    Block SO By TOP
    """,
    'summary': 'Block SO By TOP',
    'website': 'http://sinergidata.co.id',
    'depends': ['base', 'sale', 'stock', 'account', 'partner_credit_limit', 'sdt_udf_besindo'],
    'data': [
        'security/group.xml',
        'views/account_move.xml',
        'views/res_partner.xml',
        'views/sale_order.xml',
        'views/stock_picking.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'sequence': 105,
    'license': 'AGPL-3',
}
