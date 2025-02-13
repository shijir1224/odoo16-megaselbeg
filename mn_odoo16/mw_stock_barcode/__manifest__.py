# -*- coding: utf-8 -*-

# Copyright 2017-2018 Devendra kavthekar <https://twitter.com/kdevendr>
# Website: <https://dek-odoo.github.io>

{
    "name": "MW stock barcode",
    "summary": "Select lot when selling product",
    "category": "Point of Sale",
    "version": "13.0.1.2",

    "description": """
        Агуулах баркод
    """,
    "application": False,
    "sequence": 7,
    "author": "by Bayasaa",
    "website": "http://managewall.mn",
    "license": "LGPL-3",
    "depends": ["stock_barcode"],
    "data": [
        "views/stock.xml",
    ],
    # "installable": True,
    "auto_install": False,
    'license': 'OEEL-1',
    'assets': {
        'web.assets_backend': [
            'mw_stock_barcode/static/src/**/*.js',
        ],
    }
}
