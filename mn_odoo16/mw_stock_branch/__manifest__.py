# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'MW Stock with Branch',
    'version': '1.0.1',
    'category': 'Stock',
    'sequence': 20,
    'author': 'Managewall LLC',
    'summary': 'Changed by Mongolian Stock Branch',
    'description': "Uur dr tohiruulsan aguulah dr ",
    'depends': ['mw_stock','branch','mw_stock_product_report','mw_stock_inv_add'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/stock_branch_view.xml',
    ],
    'qweb': [],
    'website': 'http://managewall.mn',
    'installable': True,
    'auto_install': False,
    'license': 'OEEL-1',
}
