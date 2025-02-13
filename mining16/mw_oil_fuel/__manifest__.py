# -*- coding: utf-8 -*-

{
	'name': 'mw oil fuel',
	'version': '1.0',
	'sequence': 31,
	'category': 'Mining',
	'license': 'LGPL-3',
	'website': 'http://manangewall.mn',
	'author': 'Managewall LLC Bayasa',
	'description': """
		Түлшний зарцуулалтын модуль """,
	'depends': ['base','account','mw_technic_equipment','stock','purchase','mw_mining','mw_stock','mw_technic_maintenance'],
	'summary': '',
	'data': [
		'security/security.xml',
		'security/ir.model.access.csv',
		'views/oil_fuel_view.xml',
		'views/oil_fuel_config_view.xml',
		'views/oil_fuel_wizard_view.xml',
		'report/oil_fuel_report_view.xml',
		# 'views/widget_path.xml',
		'views/dashboard_view.xml',
		'views/technic_equipment_inherit.xml',
	],
	'installable': True,
	'application': True,
	# 'qweb': ['static/xml/*.xml'],

	'assets' : {
		'web.assets_backend': [
				# '/mining15/mw_oil_fuel/static/js/oil_fuel_dashboard.js',
				# '/mw_oil_fuel/static/libs/drilldown.js',
				# '/mw_oil_fuel/static/libs/export-data.js',
				# '/mw_oil_fuel/static/libs/exporting.js',
				# '/mw_oil_fuel/static/libs/highcharts.js',
				],

		# 'web.assets_qweb': [
		#     '/mw_oil_fuel/static/xml/custom_templates.xml',
		# ],
	},
}
