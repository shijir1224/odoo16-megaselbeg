# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
	'name': 'MW Mining Cost',
	'version': '1.0.1',
	'category': 'Mining',
	'license': 'LGPL-3',
	'sequence': 20,
	'author': 'Managewall LLC',
	'summary': 'Mining Cost BCM',
	'description': "",
	'depends': ['branch','mw_mining', 'mw_technic_equipment', 'mrp'
				# 'mw_product_warehouse_account'
				],
	'data': [
		'security/mw_mining_security.xml',
		'security/ir.model.access.csv',
		'views/mining_cost_config_view.xml',
		'views/mining_cost_view.xml',
		'views/mining_cost_dollar_view.xml',
		'views/mining_cost_indirect_view.xml',
		'views/mining_cost_overhead_view.xml',
		'views/mining_cost_ancillary_view.xml',
		'report/mining_mrp_analyze_view.xml',
		'report/report_wizard.xml'
	],
	'qweb': [],
	'website': 'http://managewall.mn',
	'installable': True,
	'auto_install': False,
}
