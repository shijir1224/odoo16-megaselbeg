# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'MW Sale Limit',
    'version': '1.0.0',
    'license': 'LGPL-3',
    'category': 'Sales',
    'sequence': 23,
    'summary': 'Борлуулалт хийх үед хязгаарлалт хийх',
    'author': 'Managewall LLC',
    'website': 'http://managewall.mn',
    'description': "Заасан бараан дээр борлуулалт хийх үед хязгаарлалт хийх боломжтой болно",
    'depends': ['sale_stock'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/sale_order_limit_setting_view.xml'
    ],
    'qweb': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
