# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name' : 'MW ASSET TAX DEPRECIATION',
    'license': 'LGPL-3',
    'version' : '1.1',
    'summary': 'ASSET TAX DEPRECIATION',
    'sequence': 15,
    'description': """
MN asset
====================
    """,
    'category': 'Accounting/Accounting asset tax',
    'website': 'https://www.managewall.mn',
    'depends' : ['mw_asset', 'account_asset'],
    'data': [
        'security/ir.model.access.csv',
        'views/account_asset_views.xml',
        'wizard/asset_depreciation_validate_tax_views.xml',
    ],
    'demo': [
    ],
    'qweb': [
    ],
    'auto_install': False,
    'icon': '/mw_base/static/src/img/managewall.png',
}
