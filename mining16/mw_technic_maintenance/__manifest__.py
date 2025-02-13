# -*- coding: utf-8 -*-

{
	'name': 'Засварын модуль',
	'version': '2.0',
	'sequence': 31,
	'category': 'Stock',
	'license': 'LGPL-3',
	'website': 'http://manangewall.mn',
	'author': 'Managewall LLC by amaraa',
	'description': """
		Техникийн засварын модуль """,
	'depends': ['stock','product','mw_technic_equipment',
			 'mw_purchase_request',
			 'web','mw_stock','hr',
				'base','web_widget_colorpicker',
				'mw_product',
				'mw_dynamic_flow','mw_stock_moves','web_gantt'
				# 'mw_quotation'
				],
	'summary': '',
	'data': [
		# Access rights
		'security/security.xml',
		'security/ir.model.access.csv',
		# Data
		# 'data/maintenance_damaged_type.xml',
		# 'data/maintenance_setting_datas.xml',
		# 'data/technic_data.xml',
		# UI
		'views/maintenance_settings_view.xml',
		'views/maintenance_workorder_view.xml',
		'views/technic_inherit_view.xml',
		'views/maintenance_plan_view.xml',
		'views/maintenance_plan_generator_view.xml',
		'views/stock_picking_inherit_view.xml',
		'views/maintenance_call_view.xml',
		'views/maintenance_oil_sample_view.xml',
		'views/maintenance_dems_info_view.xml',
		'views/maintenance_long_term_view.xml',
		'views/maintenance_pm_material_generator_view.xml',
		'views/maintenance_parts_move_view.xml',
		'views/maintenance_parts_waiting_view.xml',
		'views/maintenance_year_other_expense.xml',
		'views/hr_inherit_view.xml',

		'reports/maintenance_expense_report_view.xml',
		'reports/maintenance_wo_report_view.xml',
		'reports/worktime_reason_report_view.xml',
		'reports/oil_sample_pivot_report_view.xml',
		'reports/repairman_pivot_report_view.xml',

		'wizard/wizard_maintenance_expense_view.xml',
		'wizard/wizard_repairman_report_view.xml',
		'wizard/wizard_check_parts_qty_view.xml',
		'wizard/wizard_check_next_work_description_view.xml',
		'wizard/wizard_maintenance_monthly_report_view.xml',
		'wizard/wizard_maintenance_weekly_report_view.xml',
		'wizard/wizard_maintenance_daily_report_view.xml',
		'wizard/wizard_oil_sample_report_view.xml',
		'wizard/wizard_set_last_pm_view.xml',
		'wizard/wizard_create_stopped_technic_plan_view.xml',
		'wizard/wizard_maintenance_pr_line_view.xml',
		'wizard/wizard_smr_report_view.xml',
		'wizard/wizard_part_waiting_move_view.xml',
		'wizard/wizard_expense_repeat_report_view.xml',
		'wizard/wizard_maintenance_year_tbbk_view.xml',
		'wizard/wizard_daily_report_view.xml',

		# 'data/maintenance_damaged_type.xml',
		# 'data/maintenance_setting_datas.xml',

		'views/dashboard_view.xml',

		# 'views/widget_path.xml',
		'views/menu_view.xml',
	],
	'installable': True,
	'application': True,
	# 'qweb': ['static/xml/*.xml'],
	'assets': {
		'web.assets_frontend': [
			"/mw_technic_maintenance/static/css/base.css",
			# "/mw_technic_equipment/static/src/css/odometer-theme-car.css",
		],
		'web.assets_backend': [
			"/mw_technic_maintenance/static/css/base.css",
			"/mw_technic_maintenance/static/js/widget.js",
			"/mw_technic_maintenance/static/libs/jspdf.js",
			# "/mw_technic_equipment/static/src/libs/treemap.js",
			# "/mw_technic_equipment/static/src/css/bootstrap-year-calendar.css",
			# "/mw_technic_equipment/static/src/libs/bootstrap-year-calendar.js",
			# "/mw_technic_equipment/static/src/js/widget.js",
		],
		'web.assets_qweb': [
			'/mw_technic_maintenance/static/xml/custom_templates.xml',
		]
	}
}
