# -*- coding: utf-8 -*-

{
    'name': 'Тоног төхөөрөмж модуль',
    'version': '2.0',
    'sequence': 31,
    'category': 'Repair',
	'license': 'LGPL-3',
    'website': 'http://manangewall.mn',
    'author': 'Managewall LLC badaam',
    'description': """
        Тоног төхөөрөмжийн модуль """,
    'depends': ['mw_technic_equipment','mw_technic_maintenance','mw_product_warehouse_account','mw_mining','mw_analytic_account'],
    'summary': '',
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/equipment_model_brand_view.xml',
        'views/factory_settings_view.xml',
        'views/factory_equipment_view.xml',
        'views/equipment_component_part_view.xml',
        'views/maintenance_workorder_view.xml',
        'views/maintenance_plan_generator_view.xml',
        'views/stock_picking_inherit_view.xml',
        'views/account_analytic_line_views.xml',
        'views/account_move_view.xml',
        'views/product_account_view.xml',
        # 'views/factory_electric_view.xml',
        'views/factory_call_view.xml',
        'views/parts_waiting_view.xml',
        'views/parts_move_view.xml',
		
        'wizard/wizard_equipment_expense_view.xml',
        'wizard/equipment_expense_report_view.xml',
        'wizard/equipment_worktime_reason_report_view.xml',
        'views/menu_view.xml',
	],
	'installable': True,
	'application': True,
	'assets': {}
}
