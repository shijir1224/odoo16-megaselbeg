# -*- coding: utf-8 -*-
{
    'name': 'Sale Order barcode',
    'version': '1.0',
    'license': 'LGPL-3',
    'category': 'Sale',
    'sequence': 23,
    'author': 'Managewall LLC',
    'summary': 'Add product by barcode scanner',
    'description': "",
    'depends': ['web','sale','barcodes'],
    'data': [
        'views/sale_order_config_view.xml',
    ],
    'qweb': [],
    'website': 'http://managewall.mn',
    'installable': True,
    'auto_install': False,
}
