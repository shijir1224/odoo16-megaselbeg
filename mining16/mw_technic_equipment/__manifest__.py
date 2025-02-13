# -*- coding: utf-8 -*-

{
    'name': 'Техникийн модуль',
    'version': '2.0',
    'sequence': 31,
    'category': 'Repair',
	'license': 'LGPL-3',
    'website': 'http://manangewall.mn',
    'author': 'Managewall LLC amaraa',
    'description': """
        Техник тоног төхөөрөмжийн модуль """,
    'depends': ['base','analytic','hr','stock','web_widget_colorpicker','branch',
    'mw_asset', 'mw_hr',
    'highchart_libs_module',],
    'summary': '',
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/technic_data.xml',
        'views/technic_inspection_view.xml',
        'views/technic_model_brand_view.xml',
        'views/technic_equipment_view.xml',
        'views/technic_equipment_log_status_view.xml',
        'views/technic_tire_view.xml',
        'views/tire_inspection_view.xml',
        'views/tire_install_view.xml',
        'views/technic_component_part_view.xml',
        'views/tire_plan_generator_view.xml',
        # 'views/technic_equipment_configuration_view.xml',
        # 'views/technic_equipment_id_view.xml',
        'views/water_well_view.xml',
        'views/well_water_record_view.xml',
		'views/electric_technical_view.xml',
		'views/electric_record_view.xml',
        # 'views/water_record_view.xml',

        # 'views/widget_path.xml',
        'views/technic_tire_import_view.xml',
		'views/account_asset_view.xml',

		'reports/technic_inspection_pivot_report_view.xml',
		'reports/technic_tire_pivot_report_view.xml',
		'reports/technic_log_status_pivot_report_view.xml',

		'wizard/wizard_detection_sheet_report_view.xml',
		'wizard/wizard_set_component_odometer_view.xml',
		'wizard/wizard_tire_report_view.xml',
		'wizard/wizard_component_report_view.xml',
		'wizard/wizard_equipment_master_sheet_report_view.xml',
		'wizard/wizard_equipment_warrenty_report_view.xml',
		'wizard/wizard_equipment_firesystem_report_view.xml',
		'wizard/wizard_set_tire_odometer_view.xml',
		'wizard/wizard_new_tire_report_view.xml',
		'wizard/wizard_retired_tire_report_view.xml',
		'wizard/wizard_location_tire_report_line_view.xml',

		'views/menu_view.xml',
	],
	'installable': True,
	'application': True,
	# 'qweb': ['static/src/xml/*.xml'],
	'assets': {
		# 'web.assets_common': [
		'web.assets_common': [
			"mw_technic_equipment/static/src/css/base.css",
			"mw_technic_equipment/static/src/css/odometer-theme-car.css",
		],
		'web.assets_backend': [
			# "mw_technic_equipment/static/src/css/base.css",
			# "mw_technic_equipment/static/src/css/odometer-theme-car.css",
			# "mw_technic_equipment/static/src/js/odometer.js",
			# "mw_technic_equipment/static/src/libs/networkgraph.js",
			# "mw_technic_equipment/static/src/libs/treemap.js",
			# "mw_technic_equipment/static/src/css/bootstrap-year-calendar.css",
			# "mw_technic_equipment/static/src/libs/bootstrap-year-calendar.js",
			# "mw_technic_equipment/static/src/js/custom_widget.js",
			'mw_technic_equipment/static/src/xml/custom_templates.xml',
			"mw_technic_equipment/static/src/js/custom.js",
			"mw_technic_equipment/static/src/js/custom_legacy.js",
		],
		'web.assets_qweb': [
			'mw_technic_equipment/static/src/xml/*.xml',
		]
	}
}
