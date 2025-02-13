# -*- coding: utf-8 -*-

{
    'name': 'Sale contract & Promotion',
    'version': '2.0',
    'license': 'LGPL-3',
    'sequence': 31,
    'category': 'Sales Management',
    'author': 'Managewall Amaraa',
    'description': """
        Sale's contract and Promotion """,
    'depends': ['base','contacts','sale','sales_team','mw_sales_master_plan',
        'sale_management','mw_base','mw_product','product_brand'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/sales_contract_view.xml',
        'views/sales_promotion_view.xml',
        'views/sale_inherit_view.xml',
        'views/planned_sales_compute_view.xml',
        'views/sales_payment_info_view.xml',
        'views/sales_gift_cart_view.xml',
        'views/product_view.xml',
        'views/res_partner.xml',
        'wizard/wizard_pricelist_import_view.xml', 
        'wizard/wizard_edit_partner_tags_view.xml',

        'views/menu_view.xml',
    ],
    'installable': True,
    'application': True,
}
