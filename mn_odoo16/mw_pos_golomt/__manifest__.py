# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'MW Golomt IPPOS',
    'version': '1.0.1',
    'category': 'Point Of Sale',
    'sequence': 20,
    'author': 'Badmaarag Managewall LLC',
    'summary': 'Changed by Mongolian Point of sale',
    'description': "",
    'depends': ['point_of_sale'],
    'data': [
        # 'views/widget_path.xml',
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/golomt_view.xml',
    ],
    'assets': {
        'point_of_sale.assets':
            [
            'mw_pos_golomt/static/src/js/mw_models_xb.js',
            'mw_pos_golomt/static/src/js/mw_golomt.js',
            "mw_pos_golomt/static/src/js/models.js",
            "mw_pos_golomt/static/src/js/PaymentgolomtPay.js",
            'mw_pos_golomt/static/src/js/base64.min.js',
            "mw_pos_golomt/static/src/xml/mw_golomt.xml",
            ],
        'web.assets_qweb': [
            # "mw_pos_ebarimt3/static/src/xml/PaymentScreen.xml",
        ],
    },
    'website': 'http://managewall.mn',
    'installable': True,
}
