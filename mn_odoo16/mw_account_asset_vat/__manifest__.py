# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name' : 'MW Asset Vat',
    'version' : '1.0.1',
    'summary': 'Asset Vat Expense',
    'license': 'LGPL-3',
    'sequence': 15,
    'author': 'Duulga Managewall LLC',
    'description': """
            Хөрөнгийн НӨАТ-ын бууруулалт
    """,
    'category': 'Accounting/Accounting',
    'website': 'https://www.managewall.mn',
    'depends' : ['account', 'account_asset', 'mw_asset'],
    'data': [
        'security/account_security.xml',
        'security/ir.model.access.csv',
        'views/account_asset_vat_views.xml',
    ],
    'demo': [
    ],
    'qweb': [
    ],
    'auto_install': False,
}
