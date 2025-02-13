# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
	'name': 'MW Stock in out product convert',
	'version': '1.0.1',
	'license': 'LGPL-3',
	'category': 'Stock',
	'sequence': 20,
	'author': 'Managewall LLC',
	'summary': 'Changed by stock',
	'description': "",
	'depends': ['stock','mw_stock'],
	'data': [
		'security/security.xml',
		'security/ir.model.access.csv',
		'views/stock_move_view.xml',
		'views/stock_picking_view.xml',
	],
	'qweb': [],
	'website': 'http://managewall.mn',
	'installable': True,
	'auto_install': False,
}
