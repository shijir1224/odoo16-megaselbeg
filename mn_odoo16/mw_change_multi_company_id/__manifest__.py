# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'MW multi company change',
    'version': '1.0.1',
    'license': 'LGPL-3',
    'category': 'Base',
    'sequence': 20,
    'author': 'Daramaa Managewall LLC',
    'summary': 'Changed by Mongolian web',
    'description': "",
    'depends': ['web'],
    'data': [
        'security/security.xml',
        # 'views/webclient_templates.xml',
    ],
    'website': 'http://managewall.mn',
    'installable': True,
    'assets': {
        'web.assets_backend': [
            "/mw_change_multi_company_id/static/js/session.js",
        ]
    }
}
