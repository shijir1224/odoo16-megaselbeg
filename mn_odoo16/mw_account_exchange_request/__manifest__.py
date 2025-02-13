# -*- coding: utf-8 -*-
{
    "name" : "MW Paymant exchange",
    "version" : "1.0",
    'license': 'LGPL-3',
    "author" : "Managewall",
    "category" : "Generic Modules/Account",
    "description": """
        The mongolian financial module.
        * Depending account.
        * Functionals:
        exchange request module
        """,
    "depends" : [
        "account",
        "base",
        "branch",
        "mw_account_payment_request"
    ],
    "demo_xml" : [],
    "data" : [
        "security/security.xml",
        "security/ir.model.access.csv",
        # "wizard/account_make_expense_view.xml",
        # "wizard/print_exchange_orders_view.xml",
        "views/account_exchange_request_view.xml",
        "views/account_exchange_request_sequence.xml",
        # 'views/account_move_views.xml',
        # "wizard/create_exchange_request_view.xml",
    ],
    "assets": {
        "web.assets_backend": [
            # "mw_account_exchange_request/static/src/css/style.css",
        ],
    },
    "auto_install": False,
    "installable": True,
    'icon': '/mw_base/static/src/img/managewall.png',
}
