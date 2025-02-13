# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'MW Point of sale',
    'version': '1.0.0',
    'license': 'LGPL-3',
    'category': 'Point of sale',
    'sequence': 20,
    'author': 'Managewall LLC',
    'summary': 'Changed by Mongolian Ebarimt integration and customization',
    'description': "",
    'depends': ['point_of_sale','branch','account', 'mw_sale_stock', 'mw_account'],#,'mw_sale_ebarimt'   FIXME: mw_sale_stock дундын модуль дээр байх ёстой байх
    'data': [
        'security/ir.model.access.csv',
        'data/ebarimt_aimag_district.xml',
        'data/tax_data.xml',
        'data/report_paperformat_data.xml',
        'views/res_config_settings_views.xml',
        'views/account_tax_views.xml',
        'views/pos_payment_views.xml',
        'views/pos_config_views.xml',
        'views/pos_order_views.xml',
        'views/report_receipt.xml',
        'views/product_views.xml',
        'views/report_saledetails.xml',
        'report/ebarimt_reports.xml'
    ],
    'assets': {
        'point_of_sale.assets':
            [
             'mw_pos/static/src/js/ebarimt.js',
             'mw_pos/static/src/js/ClientDetailsEdit.js',
             'mw_pos/static/src/js/OrderReceipt.js',
             'mw_pos/static/src/js/OrderReceiptCopy.js',
             'mw_pos/static/src/js/PaymentScreen.js',
             'mw_pos/static/src/js/PaymentScreenStatus.js',
             'mw_pos/static/src/css/mn_ebarimt.css'
            ],
        'web.assets_qweb': [
            "mw_pos/static/src/xml/ClientDetailsEdit.xml",
            "mw_pos/static/src/xml/OrderReceipt.xml",
            "mw_pos/static/src/xml/PaymentScreenPaymentLines.xml",
            "mw_pos/static/src/xml/PaymentScreen.xml",
            "mw_pos/static/src/xml/ProductItem.xml",
        ],
    },
    'qweb': [],
    'website': 'https://managewall.mn',
    'installable': True,
    'auto_install': False,
}
