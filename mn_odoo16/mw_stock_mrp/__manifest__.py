# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'MW Mrp create from internal transfer',
    'version': '1.0.1',
    'category': 'Mrp',
    'sequence': 21,
    'summary': 'Changed by Mongolian Custom stock',
    'author': 'Managewall LLC',
    'website': 'http://managewall.mn',
    'description': "",
    'depends': [
        'mrp',
        'stock'
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'wizard/stock_picking_create_production_wizard.xml',
        'views/stock_picking_views.xml'
    ],
    'qweb': [],
    'installable': True,
    'auto_install': False,
    'license': 'OPL-1',
}
