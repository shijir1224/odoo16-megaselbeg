# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Attache preview',
    'version': '1.0.1',
    'category': 'Base',
    'sequence': 20,
    'author': 'Daramaa Managewall LLC',
    'summary': 'Changed by Mongolian insurance',
    'description': "",
    'depends': ['mail','base'],
    'data': [       
        ],
    # 'demo': [
    # ],

    'website': 'http://managewall.mn',
    'installable': True,
    # 'auto_install': False,
    
    'assets' : {
        'web.assets_backend': [
            'mw_attach/static/src/js/chatter.js',
        ],
        'web.assets_qweb': [
        ],
    },
}
