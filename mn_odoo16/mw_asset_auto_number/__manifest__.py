# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name' : 'MW Asset Code',
    'version' : '1.0.1',
    'license': 'LGPL-3',
    'summary': 'Asset Code',
    'author': 'Altanduulga Managewall LLC',
    'sequence': 15,
    'description': """
        Үндсэн хөрөнгийг автоматаар кодлох
    """,
    'category': 'Accounting/Accounting',
    'website': 'https://www.managewall.mn',
    'depends' : ['account_asset','mw_asset','base'],
    'data': [
        'views/account_asset_views.xml',
    ],
    'demo': [
    ],
    'qweb': [
    ],
    'auto_install': False,
    'installable': True,
    'icon': '/mw_base/static/src/img/managewall.png',
}
