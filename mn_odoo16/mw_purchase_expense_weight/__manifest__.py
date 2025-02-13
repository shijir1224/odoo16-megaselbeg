# -*- coding: utf-8 -*-
{
	'name': 'MW Purchase Order expense by weight',
	'version': '1.0.1',
	'category': 'Inventory/Purchase',
	'sequence': 20,
	'author': 'Managewall LLC',
	'summary': 'Changed to meet requirements of Mongolian Purchase order added weight',
	'website': 'http://managewall.mn',
	'description': "",
	'installable': True,
	'auto_install': False,
	'license': 'LGPL-3',
	'depends': [
		'mw_purchase_expense',
	],
	'data': [
		'views/purchase_order_add_cost_weight.xml',
	],
	'qweb': [],
}
