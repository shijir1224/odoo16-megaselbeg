# -*- coding: utf-8 -*-

{
    'name': 'Highchart libs Module',
    'version': '1.0',
    'license': 'LGPL-3',
    'sequence': 31,
    'category': 'Tools',
    'website': 'http://managewall.mn',
    'author': 'Amaraa',
    'description': """ Highchart's library install """,
    'depends': ['base'],
    'summary': '',
    'data': [],
    'installable': True,
    'application': False,
    'assets': {
        'web.assets_backend': [
            "/highchart_libs_module/static/css/highcharts.css",
            "/highchart_libs_module/static/libs/highcharts.js",
            "/highchart_libs_module/static/libs/numeral.js",
        ],
    }
}
