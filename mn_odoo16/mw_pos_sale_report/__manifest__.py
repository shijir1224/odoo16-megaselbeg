# -*- coding: utf-8 -*-

# Copyright 2017-2018 Devendra kavthekar <https://twitter.com/kdevendr>
# Website: <https://dek-odoo.github.io>

{
    "name": "MW POS Sale report",
    "summary": "Select lot when selling product",
    "category": "Point of Sale",
    "version": "13.0.1.2",
    "description": """Pos sale payment hamt haragddag tailan""",
    "application": False,
    "sequence": 7,
    "author": "by Bayasaa",
    "website": "http://managewall.mn",
    "license": "OPL-1",
    "depends": ["point_of_sale","sale"],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "views/pos_sale.xml",
    ],
    "qweb": [],
    "auto_install": False,
}
