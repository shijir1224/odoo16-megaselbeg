# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Stock partner SO PO',
    'version': '1.0',
    'category': 'Stock',
    'sequence': 22,
    'author': 'Managewall LLC',
    'summary': 'Худалдан авалт болон Борлуулалтын харилцагч Stock Move болон Stock move line дээр нэмэв.',
    'description': "",
    'depends': ['sale_stock','purchase_stock'],
    'data': [
        'security/security.xml',
        'views/inherit_view.xml',
    ],
    'website': 'http://managewall.mn',
    'installable': True,
    'auto_install': False,
    'license': 'OEEL-1',
}
