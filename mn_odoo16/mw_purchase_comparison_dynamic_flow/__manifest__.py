# -*- coding: utf-8 -*-
{
	'name': 'MW Purchase Comparison Dynamic Flow',
	'version': '1.0',
	'sequence': 31,
	'category': 'Inventory/Purchase',
	'website': 'http://managewall.mn',
	'author': 'Managewall LLC',
	'description': """
		Purchase comparison to purchase order with dynamic workflow""",
	'depends': ['mw_purchase_comparison', 'mw_dynamic_flow'],
	'summary': '',
	'data': [
		"views/purchase_comparison_view.xml",
	],
	'installable': True,
	'auto_install': True,
	'application': False,
	'license': 'LGPL-3',
}
