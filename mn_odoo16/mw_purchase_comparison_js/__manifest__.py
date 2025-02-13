# -*- coding: utf-8 -*-
{
	'name': 'MW Purchase Comparison JS',
	'version': '1.0',
	'sequence': 31,
	'category': 'Purchase',
	'website': 'http://managewall.mn',
	'author': 'Managewall LLC',
	'description': """
		Purchase comparison js to purchase order""",
	'depends': ['mw_purchase', 'mw_purchase_comparison', 'mw_purchase_comparison_dynamic_flow', 'mw_purchase_request', 'mw_purchase_dynamic_flow'],
	'summary': '',
	'data': [
		"security/comparison_security.xml",
		"security/ir.model.access.csv",
		"views/purchase_comparison_view.xml"
	],
	'assets': {
		'web.assets_backend': [
			'mw_purchase_comparison_js/static/src/js/purchase_comparison.js',
			'mw_purchase_comparison_js/static/src/js/purchase_comparison_widget.js',
			'mw_purchase_comparison_js/static/src/xml/purchase_comparison.xml',
		],
		'web.assets_common': [
			'mw_purchase_comparison_js/static/src/css/purchase_comparison.css',
		],
	},
	'installable': True,
	'auto_install': False,
	'application': False,
	'license': 'LGPL-3',
}
