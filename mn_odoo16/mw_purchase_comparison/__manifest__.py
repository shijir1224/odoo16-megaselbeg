# -*- coding: utf-8 -*-
{
	'name': 'MW Purchase Comparison',
	'version': '1.0',
	'sequence': 31,
	'category': 'Inventory/Purchase',
	'website': 'http://managewall.mn',
	'author': 'Managewall LLC',
	'description': """
		Purchase comparison to purchase order""",
	'depends': ['mw_purchase', 'branch', 'mw_purchase_expense'],
	'summary': '',
	'data': [
		"security/comparison_security.xml",
		"security/ir.model.access.csv",
		"data/ir_rule.xml",
		"data/ir_sequence.xml",
		"views/purchase_comparison_view.xml",
		"views/purchase_order_inherit.xml",
		"wizard/comparison_vote_wizard_views.xml",
		"views/menu_view.xml",
	],
	'installable': True,
	'auto_install': False,
	'application': False,
	'license': 'LGPL-3',
}
