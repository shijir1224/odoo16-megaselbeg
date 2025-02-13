    # -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': "Monglolian Consume Order",
    'version': '1.0',
    'license': 'LGPL-3',
    'depends': ['stock_account','branch','mw_stock_moves','mw_account','report_xlsx','branch','mw_stock','mw_asset'],
    'author': "ManageWall LLC",
    'category': 'Mongolian Account Modules',
    'description': """
         Бага үнэтэй түргэн элэгдэх зүйлс бүртгэх.
    """,
    'website' : 'www.managewall.mn',
    'data': [
        'security/security_view.xml',
        'security/ir.model.access.csv',
        'data/consume_order_data.xml',
        'data/data_account_standard_report.xml',
        'wizard/consumable_material_wizard_view.xml',
        'views/product_template_view.xml',
        'views/consumable_material_expense_view.xml',
        'views/consume_material_in_use_view.xml',
        'views/consumable_sell_view.xml',
        'wizard/consumable_material_wizard_view.xml',
        'wizard/consumable_report_view.xml',
        'wizard/asset_move_view.xml',
        'wizard/account_consume_validate.xml',
        'wizard/consum_depreciation_confirmation_wizard_views.xml',
        'views/consumable_inventory_adjustment_views.xml',
        # 'report/report_account_standard_report.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}