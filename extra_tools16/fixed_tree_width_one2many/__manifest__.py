# -*- coding: utf-8 -*-
{
    'name': "Fixed column width in one2many tree",

    'summary': """
        Fixed column width in one2many tree
        """,

    'description': """
        Fixed column width in one2many tree
    """,

    'author': "loilv",
    'website': "loilv.295@gmail.com",
    "license": "AGPL-3",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/16.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'App/',
    'sequence': 1,
    "version": "16.0.1.0.1",

    # any module necessary for this one to work correctly
    'depends': ['base'],

    # always loaded
    'data': [

    ],
    'images': [
        'static/description/icon.png',
    ],
    'assets': {
        'web.assets_backend': [
            'fixed_tree_width_one2many/static/src/js/custom_width_tree.js',
        ],
    },
    # only loaded in demonstration mode
    'demo': [
        # 'demo/demo.xml',
    ],
    "installable": True,
    "application": True,
    "auto_install": False,
}
