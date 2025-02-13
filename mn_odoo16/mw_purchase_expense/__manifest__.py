# -*- coding: utf-8 -*-
{
	'name': 'MW Purchase Order expense',
	'version': '1.0.1',
	'category': 'Inventory/Purchase',
	'sequence': 20,
	'website': 'http://managewall.mn',
	'author': 'Managewall LLC',
	'summary': 'Changed to meet requirements of Mongolian Purchase order',
	'installable': True,
	'auto_install': False,
	'license': 'LGPL-3',
	'description': "",
	'depends': [
		'mw_purchase',
	],
	'data': [
		'security/mw_purchase_security.xml',
		'security/ir.model.access.csv',
		'views/purchase_order_view.xml',
		'views/purchase_order_expenses_views.xml',
		'views/product_views.xml',
		'report/po_expenses_report.xml',
	],
	'qweb': [],
}
