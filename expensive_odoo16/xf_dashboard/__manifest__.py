# -*- coding: utf-8 -*-
{
    'name': 'XF Home Landing Page (Dashboard)',
    'version': '1.3.3',
    'summary': """
    Intranet Dashboard and Landing Page with Customizable Widgets
    
    , Intranet Portal Page
    , Corporate Portal
    , Home Page Dashboard
    , Employee Dashboard
    , Employee Portal
    , Employee Intranet
    , Employee Quick Links
    , Most Visited Modules
    , Most Visited Apps
    , Home Dashboard Widgets
    """,
    'category': 'Extra Tools, Dashboard, Design, Productivity',
    'author': 'XFanis',
    'support': 'odoo@xfanis.dev',
    'website': 'https://xfanis.dev/odoo.html',
    'license': 'OPL-1',
    'price': 30,
    'currency': 'EUR',
    'description':
        """
XF Home Dashboard
=================
This module allows to create intranet home/landing page with several built-in widgets. 
Also module supports adding custom widgets. 
The procedure for adding new sub-modules with widgets is easy even for inexperienced developers.

Built-in widgets:
* Hello Widget
* Logo Widget
* Bookmarks (list + tiles)
* Popular Links (separate for each user and based on their activity)


----------------------

You can create custom widgets through administration panel using existing built-in widgets code as example. 
Each widget has many setting options to be able to customize it without writing code.
But if there are any complications, do not hesitate to contact me and I will try to help you.
If you have an idea or suggestion for a widget for this dashboard, you can share it with me. 
If I like the idea, I will implement this widget and publish it in the Odoo app store for free.

        """,
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/menu.xml',
        'data/rows.xml',
        'views/adm_panel/dashboard.xml',
        'views/adm_panel/bookmarks.xml',
        'views/widgets/default_templates.xml',
        'views/widgets/bookmarks.xml',
        'views/widgets/tiles.xml',
        'views/widgets/hello.xml',
        'views/widgets/logo.xml',
        'views/widgets/popular_links.xml',
        'wizard/xf_dashboard_widget_template.xml',
        'data/icons.xml',
    ],
    'demo': [
        'data/demo.xml'
    ],
    'depends': ['web'],
    'assets': {
        'web.assets_backend': [
            'xf_dashboard/static/src/xml/**/*',
            'xf_dashboard/static/src/scss/xf_dashboard.scss',
            'xf_dashboard/static/src/js/xf_dashboard.js',
            'xf_dashboard/static/src/js/xf_dashboard_widget.js',
            'xf_dashboard/static/src/js/popular_menu.js',
        ],
    },
    'images': [
        'static/description/xf_dashboard.png',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
