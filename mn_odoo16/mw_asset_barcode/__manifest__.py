# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name' : 'MW ASSET BARCODE',
    'version' : '1.1',
    'license': 'LGPL-3',
    'summary': 'ASSET BARCODE',
    'sequence': 15,
    'description': """
MN asset
====================
    """,
    'category': 'Accounting/Accounting asset',
    'website': 'https://www.managewall.mn',
    'depends' : ['mw_asset', 'account_asset'],
    'data': [
#         'security/account_security.xml',
        'security/ir.model.access.csv',
#         'views/account_asset_views.xml',
        'wizard/account_asset_print_barcode_wizard_view.xml',
    ],
    'demo': [
    ],
    'mw_asset_barcode.assets': [
            'mw_asset_barcode/static/src/lib/JsBarcode',
             ],
    'qweb': [
    ],
    'auto_install': False,
}
