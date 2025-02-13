# -*- coding: utf-8 -*-
{
	'name': 'MW Purchase Order expense by custom',
	'version': '1.0.1',
	'category': 'Inventory/Purchase',
	'sequence': 20,
	'author': 'Managewall LLC',
	'summary': 'Changed to meet requirements of Mongolian Purchase order added custom',
	'website': 'http://managewall.mn',
	'description': "",
	'installable': True,
	'auto_install': False,
	'license': 'LGPL-3',
	'depends': [
		'mw_purchase',
		'mw_purchase_expense',
		'mw_purchase_expense_weight',
		'mw_purchase_am_view',
	],
	'data': [
		'security/security.xml',
		'security/ir.model.access.csv',
		'views/add_cost_view.xml',
		'report/add_cost_report_view.xml',
		'views/menu_view.xml',
	],
}
