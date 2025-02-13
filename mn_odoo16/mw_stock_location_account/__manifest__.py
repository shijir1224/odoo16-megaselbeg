# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
	'name': 'Stock Location Account',
	'version': '1.0.0',
	'license': 'LGPL-3',
	'category': 'Stock',
	'sequence': 20,
	'author': 'Managewall LLC',
	'summary': 'Changed by Mongolian Stock Location Account',
	'description': "Add account for stock location",
	'depends': ['stock_account'],
	'data': [
		'views/stock_location_views.xml',
	],
	'qweb': [],
	'website': 'http://managewall.mn',
	'installable': True,
	'auto_install': False,
}
