# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'MW Pos Ebarimt auto send data',
    'version': '1.0.1',
    'category': 'Point Of Sale',
    'sequence': 20,
    'author': 'Bayasaa Managewall LLC',
    'summary': 'Changed by Mongolian Point of sale',
    'description': "",
    'depends': ['mw_pos'],
    'data': [
        'views/widget_path.xml',
        'views/ebar_view.xml',
    ],
  	'assets': {
        'web.assets_frontend': [
            # "/mw_motors/static/src/css/base.css",
            # "/mw_motors/static/src/css/odometer-theme-car.css",
        ],
        'web.assets_backend': [
            "/mw_pos_ebarimit_senddata/static/src/js/mw_ebar.js",
        ],
        'web.assets_qweb': [
        ],
    },
    'website': 'http://managewall.mn',
    'installable': True,
}
