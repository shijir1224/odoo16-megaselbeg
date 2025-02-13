# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Point of sale - QPay integration',
    'version': '1.0.0',
    'license': 'OPL-1',
    'category': 'Point of sale',
    'sequence': 21,
    'author': 'Managewall LLC',
    'summary': 'QPay integration',
    'description': "",
    'depends': ['mw_pos',],
    'data': [
        'views/res_config_settings_views.xml',
    ],
    'assets': {
        'point_of_sale.assets':
            [
             'mw_pos_qpay/static/src/js/PaymentQpay.js',
             'mw_pos_qpay/static/src/js/models.js',
             'mw_pos_qpay/static/src/js/PaymentScreen.js',
             'mw_pos_qpay/static/src/js/QrPopup.js',
             'mw_pos_qpay/static/src/css/qpay.css'
            ],
        'web.assets_qweb': [
            "mw_pos_qpay/static/src/xml/QrPopup.xml",
        ],
    },
    'qweb': [],
    'website': '',
    'installable': True,
    'auto_install': False,
}