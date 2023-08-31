# -*- coding: utf-8 -*-
{
    'name': "SDT Standard Form",

    'summary': """
        Form Standard""",

    'description': """
        Form Standard
    """,

    'author': "Sinergi Data Totalindo, PT",
    'website': "http://www.sinergidata.co.id",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Report',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base',
                'account',
                'sale',
                'purchase',
                'mrp',
                'stock',
                ],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',

        # 'report/sdt_quotation_date_number.xml',
        'report/template.xml',
        # 'report/sdt_standard_delivery_order.xml',
        'report/sdt_standard_good_receipt.xml',
        'report/sdt_standard_inventory_transfer.xml',
        'report/sdt_standard_payment_receipt.xml',
        'report/sdt_standard_payment.xml',
        'report/sdt_standard_preparation_do_it.xml',
        'report/sdt_standard_purchase_order.xml',
        'report/sdt_standard_purchase_request_quotation.xml',
        'report/sdt_standard_sales_invoice.xml',
        'report/sdt_standard_sales_order.xml',
        'report/sdt_standard_sales_quotation.xml',
        'report/sdt_standard_surat_jalan.xml',
        'report/sdt_standard_vendor_bill.xml',
        'report/sdt_standard_journal_entries.xml',
        'report/menu.xml',
        'report/sdt_standard_label_qc_post_prod.xml',
        'views/stock_picking_views.xml',
    ],
    # only loaded in demonstration mode
}