# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': "Managewall POS ebarimt 3.0",
    'version': '16.1',
    'category': 'Point of sale',
    'sequence': 40,
    'summary': 'Manage Point of sale ebarimt',
    'description': """ПОС ибаримт модуль
                - 
                    """,
    'depends': ['point_of_sale','mw_base_ebarimt'],
    'data': [
        'views/pos_config_view.xml',
        # 'views/account_tax_views.xml',
        'views/point_of_sale.xml',
        # 'data/tax_data.xml'
    ],
    'assets': {
        'point_of_sale.assets':
            [
             # 'mw_pos_qpay/static/src/js/PaymentQpay.js',
            'mw_pos_ebarimt3/static/src/js/ebarimt.js',
            'mw_pos_ebarimt3/static/src/js/PaymentScreen.js',
             # 'mw_pos_qpay/static/src/js/QrPopup.js',
             # 'mw_pos_qpay/static/src/css/qpay.css'
            "mw_pos_ebarimt3/static/src/xml/PaymentScreen.xml",
            "mw_pos_ebarimt3/static/src/xml/OrderReceipt.xml",
            ],
        'web.assets_qweb': [
            # "mw_pos_ebarimt3/static/src/xml/PaymentScreen.xml",
        ],
    },
    'qweb': [],
    'website': '',
    'installable': True,
    'auto_install': False,
}