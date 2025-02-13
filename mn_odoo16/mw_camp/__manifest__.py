# -*- coding: utf-8 -*-

# Copyright 2017-2018 Devendra kavthekar <https://twitter.com/kdevendr>
# Website: <https://dek-odoo.github.io>

{
    "name": "MW Camp",
    "summary": "Select lot when selling product",
    "category": "Camp Order",
    "version": "13.0.1.2",
    "description": """Camp zahialga tailan""",
    "application": False,
    "sequence": 7,
    "author": "by Muugii",
    "website": "http://managewall.mn",
    "license": "OPL-1",
    "depends": ['mw_account', 'mw_base'],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "views/camp_order.xml",
        "views/camp_room_block_view.xml",
        "views/respartner_view.xml",
        "reports/camp_order_report_view.xml",
        "views/menu_view.xml",
    ],
    "qweb": [],
    "auto_install": False,
}
