# -*- coding: utf-8 -*-

{
	'name': 'MW Purchase Workflow',
	'version': '1.0',
	'sequence': 31,
	'category': 'Inventory/Purchase',
	'website': 'http://managewall.mn',
	'author': 'Managewall LLC',
	'description': """Mongolian purchase module integrated with dynamic workflow""",
	'depends': ['mw_purchase','mw_dynamic_flow'],
	'installable': True,
	'auto_install': True,
	'application': True,
	'summary': 'Main managewall purchase with workflow',
	'data': [
		"security/ir.model.access.csv",
		"views/purchase_order_view.xml",
	],
	'license': 'LGPL-3',
}
