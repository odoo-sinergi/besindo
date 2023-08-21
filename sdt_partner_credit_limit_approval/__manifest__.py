# See LICENSE file for full copyright and licensing details.

{
    'name': 'SDT Partner Credit Limit Approval',
    'version': '16.1.0.0.0',
    'category': 'Partner',
    'license': 'AGPL-3',
    'author': 'Sinergi Data Totalindo, PT',
    'website': 'https://www.sinergidata.id',
    'maintainer': 'Sinergi Data Totalindo, PT',
    'summary': 'Request Approval when Credit Limit',
    'depends': [
        'sale',
        'approvals',
    ],
    'data': [
        'data/approval_category_data.xml',
        'views/sale_order.xml',
    ],
    'installable': True,
    'auto_install': False,
}
