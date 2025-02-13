# -*- coding: utf-8 -*-

{
	'name': 'MW Sale Workflow',
	'version': '1.0',
	'sequence': 31,
    'license': 'LGPL-3',
	'category': 'Sale',
	'website': 'http://managewall.mn',
	'author': 'Managewall LLC',
	'description': """Mongolian sale module integrated with dynamic workflow""",
	'depends': ['mw_sale','mw_dynamic_flow'],
	'installable': True,
	'auto_install': True,
	'application': True,
	'summary': 'Main managewall sale with workflow',
	'data': [
		"security/ir.model.access.csv",
		"views/sale_order_view.xml",
	],
}