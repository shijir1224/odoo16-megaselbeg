# -*- coding: utf-8 -*-
# Powered by Kanak Infosystems LLP.
# © 2020 Kanak Infosystems LLP. (<https://www.kanakinfosystems.com>).

{
    "name": "Many2many Attachment Preview",
    'version': '16.0.1.1',
    'author': 'Kanak Infosystems LLP.',
    'license': 'OPL-1',
    "summary": 'This module can be used to show attachment preview of Many2many field in back-end across all the models in odoo.',
    "description": """
This is extension for Many2many field preview in back-end.
""",
    'website': 'https://www.kanakinfosystems.com',
    'category': 'Tools',
    "depends": ['web', 'mail'],
    'images': ['static/description/banner.jpg'],
    'data': [],
    'assets': {
        'web.assets_backend': [
            'web_many2many_attachment_preview_knk/static/src/models/models.js',
            'web_many2many_attachment_preview_knk/static/src/views/fields/many2many_binary/Many2manyBinaryField.js',
            'web_many2many_attachment_preview_knk/static/src/views/fields/many2many_binary/Many2manyBinaryField.xml',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'price': 30,
    'currency': 'EUR',
    'live_test_url': 'https://www.youtube.com/watch?v=V6B7hej9Cm4'
}
