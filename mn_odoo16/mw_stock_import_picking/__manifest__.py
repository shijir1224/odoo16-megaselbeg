# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
	'name': 'MW Stock import product',
	'version': '1.0.1',
	'category': 'Stock',
	'sequence': 20,
	'author': 'Managewall LLC',
	'summary': 'Changed by Mongolian Stock',
	'description': "",
	'depends': ['stock'],
	'data': [
		'security/ir.model.access.csv',
		'views/stock_picking_view.xml',
	],
	'qweb': [],
	'website': 'http://managewall.mn',
	'installable': True,
	'auto_install': False,
	'license': 'LGPL-3',
}
