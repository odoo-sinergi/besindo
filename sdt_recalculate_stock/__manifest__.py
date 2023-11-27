# See LICENSE file for full copyright and licensing details.

{
    'name': 'SDT Recalculate Stock',
    'version': '16.1.0.0.0',
    'category': 'Inventory',
    'license': 'AGPL-3',
    'author': 'Sinergi Data Totalindo, PT',
    'website': 'https://www.sinergidata.id',
    'maintainer': 'Sinergi Data Totalindo, PT',
    'summary': 'Recalculate reserved stock based on stock move lines',
    'depends': [
        'stock',
    ],
    'data': [
        'views/stock_location_views.xml',
        'data/scheduler.xml'
    ],
    'installable': True,
    'auto_install': False,
}
