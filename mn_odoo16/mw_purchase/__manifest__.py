# -*- coding: utf-8 -*-

{
	'name': 'MW Purchase',
	'version': '1.0',
	'license': 'LGPL-3',
	'sequence': 31,
	'category': 'Inventory/Purchase',
	'website': 'http://managewall.mn',
	'author': 'Managewall LLC',
	'description': """
		Main managewall purchase stock""",
	'depends': ['branch', 'mw_base', 'purchase_stock', 'product_expiry'],
	'summary': 'Changed to meet requirements of Mongolian Purchase',
	'data': [
		"security/security.xml",
		"security/ir.model.access.csv",
		"views/res_config_settings_views.xml",
		"views/res_partner_views.xml",
		"views/purchase_order.xml",
		'wizard/wizard_price_import_view.xml',
	],
	'license': 'LGPL-3',
	'installable': True,
	'auto_install': False,
	'application': True,
}
