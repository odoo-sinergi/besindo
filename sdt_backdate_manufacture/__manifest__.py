# -*- encoding: utf-8 -*-

{
    'name': 'SDT Backdate Manufacture',
    'version': '1.0',
    'category': 'Manufacture',
    'author':'Sinergi Data Totalindo, PT',
    'description': """
        Use BackDate for Manufacture.
    """,
    'summary': 'Backdate Manufacture',
    'website': 'http://sinergidata.co.id',
    'data': [
        'views/mrp_production.xml',
        'views/mrp_unbuild.xml',
    ],
    'depends': ['mrp',],
    'installable': True,
    'auto_install': False,
    'application': True,
    'sequence': 105,
    'license': 'AGPL-3',
}
