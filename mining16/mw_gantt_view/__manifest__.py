# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Web Gantt MW inherit for enterprise ',
    'category': 'Hidden',
    'description': """Odoo Web Gantt chart view.""",
    'version': '2.0',
    'depends': ['web_gantt'],
    'assets': {
        'web.assets_qweb': [
            'mw_gantt_view/static/src/xml/**/*',
        ],
        'web.assets_backend': [
            'mw_gantt_view/static/src/**/*',
        ],
        'web.qunit_suite_tests': [
            'mw_gantt_view/static/tests/**/*',
        ],
    },
    'auto_install': True,
    'license': 'OEEL-1',
}
