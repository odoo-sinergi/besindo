# -*- encoding: utf-8 -*-

{
    'name': 'SDT Backdate PO SO Confirm',
    'version': '1.0',
    'category': 'Purchase',
    'author':'Sinergi Data Totalindo, PT',
    'description': """
        Addon for back date on purchase, sales and stock picking module
    """,
    'summary': 'Backdate Purchase Sales Confirm',
    'website': 'http://sinergidata.id',
    'data': [
        # 'security/consignment_security.xml',
        # 'security/ir.model.access.csv',
        'views/sale_order.xml',
    ],
    'depends': ['purchase','sale','stock','stock_force_date_app'],
    'installable': True,
    'auto_install': False,
    'application': True,
    'sequence': 105,
    'license': 'AGPL-3',
}
