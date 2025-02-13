# -*- coding: utf-8 -*-
{
    "name" : "MW Paymant request",
    "version" : "1.0",
    'license': 'LGPL-3',
    "author" : "Managewall",
    "category" : "Generic Modules/Account",
    "description": """
        The mongolian financial module.
        * Depending account.
        * Functionals:
        Payment request module
        """,
    "depends" : [
        "account",
        "mw_account",
        "mw_dynamic_flow",
        "base",
    ],
    "demo_xml" : [],
    "data" : [
        "security/security.xml",
        "security/ir.model.access.csv",
        "wizard/account_make_expense_view.xml",
        # "wizard/account_assign_account_view.xml",
        "wizard/print_payment_orders_view.xml",
        "views/request_template_view.xml",
        "views/account_payment_report.xml",
        "views/account_payment_request_view.xml",
        "views/account_payment_request_sequence.xml",
        "views/dynamic_view.xml",
        "views/request_onboarding_views.xml",
        "views/template.xml",
        'views/account_move_views.xml',
        "wizard/create_payment_request_view.xml",
        'data/ir_cron.xml',
    ],
    "assets": {
        "web.assets_backend": [
            "mw_account_payment_request/static/src/css/style.css",
        ],
    },
    "auto_install": False,
    "installable": True,
    'icon': '/mw_base/static/src/img/managewall.png',
}
