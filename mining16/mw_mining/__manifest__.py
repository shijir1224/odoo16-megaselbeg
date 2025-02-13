# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
	'name': 'MW Mining',
	'version': '1.0.1',
	'category': 'Mining',
	'license': 'LGPL-3',
	'sequence': 20,
	'author': 'Managewall LLC',
	'summary': 'Mining Blast and Drilling module for',
	'description': "",
	'depends': ['branch','hr', 'mw_technic_equipment','mw_technic_maintenance'], # web_grid, mw_web_gantt
	'data': [
		'security/mw_mining_security.xml',
		'security/ir.model.access.csv',
		'report/mining_coal_report_view.xml',
		'report/mining_motohour_view.xml',
		'report/mining_operator_analyze_view.xml',
		'report/mining_report_survey.xml',

		'views/mining_config_view.xml',
		'views/mining_blast_view.xml',
		'views/mining_drilling_view.xml',
		'views/mining_dashboard_view.xml',
		'views/mining_dispatcher_view.xml',
		'views/mining_concentrator_view.xml',
		'views/mining_engineer_view.xml',
		'views/mining_dpr_report.xml',
		'views/mining_plan_view.xml',
		# 'views/widget_path.xml',
		'report/mining_drilling_report_view.xml',
		'report/mining_blast_report_view.xml',
		'report/mining_production_report_view.xml',
		'report/mining_technic_analyze_view.xml',
		'report/report_wizard.xml',
		'views/mining_coal_view.xml',
		'views/mining_blast_drilling_menu_view.xml',
		'views/technic_equipment_views.xml',
		'wizards/operator_production_analyze_view.xml',
		'board/plan_view.xml',
		'views/mining_menu_view.xml',
		'views/technic_equipment_inherit.xml',
		'views/moto_hour_count.xml',

	],
	# 'qweb': ['static/xml/*.xml'],
	'website': 'http://managewall.mn',
	'installable': True,
	'auto_install': False,
	'assets': {
		'web.assets_frontend': [
			"/mw_mining/static/css/base.css",
			# "/mw_technic_equipment/static/src/css/odometer-theme-car.css",
		],
		'web.assets_backend': [
			"/mw_mining/static/css/base.css",
			"/mw_mining/static/libs/data.js",
			"/mw_mining/static/libs/drilldown.js",
			"/mw_mining/static/js/grid_mining.js",
			"/mw_mining/static/js/mining_blast.js",
			"/mw_mining/static/js/mining_dashboard.js",
			"/mw_mining/static/js/lib.js",
			"/mw_mining/static/js/plan_view.js",
		],
		'web.assets_qweb': [
			'/mw_mining/static/xml/custom_templates.xml',
			'/mw_mining/static/xml/lib.xml',
			'/mw_mining/static/xml/plan.xml',
		]
	}
}
