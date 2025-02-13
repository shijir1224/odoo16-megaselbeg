# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'MW Xac Bank',
    'version': '1.0.1',
    'category': 'Point Of Sale',
    'sequence': 20,
    'author': 'Bayasaa Managewall LLC',
    'summary': 'Changed by Mongolian Point of sale',
    'description': "",
    'depends': ['point_of_sale'],
    'data': [
        # 'views/widget_path.xml',
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/xacbank_view.xml',
    ],
    'assets': {
        'point_of_sale.assets':
            [
            'mw_pos_xac/static/src/js/mw_models_xb.js',
            'mw_pos_xac/static/src/js/mw_xac.js',
            "mw_pos_xac/static/src/js/models.js",
            "mw_pos_xac/static/src/js/PaymentXacPay.js",
            'mw_pos_xac/static/src/js/base64.min.js',
            "mw_pos_xac/static/src/xml/mw_xac.xml",
            ],
        'web.assets_qweb': [
            # "mw_pos_ebarimt3/static/src/xml/PaymentScreen.xml",
        ],
    },
    'website': 'http://managewall.mn',
    'installable': True,
}
