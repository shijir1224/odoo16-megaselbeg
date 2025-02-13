# -*- coding: utf-8 -*-
{
    'name': "Odoo GPT by JUMO",
    'summary': """Odoo GPT by JUMO Technologies""",
    'description': """
        Odoo GPT by JUMO Technologies is an AI based odoobot
    """,
    'author': 'JUMO Technologies, S.L.',
    'maintainer': 'JUMO Technologies, S.L.',
    'website': 'https://www.jumotech.com',
    'category': 'Sales, Accounting & Finance',
    'version': '16.0.1.0.0',
    "license": "OPL-1",
    'depends': ['base'],
    'data': [
        #security
        "security/ir.model.access.csv",
        "mail_templates.xml",
        "wizard/ask_emails_view.xml",
    ],
    'demo': [],
    'images': ['images/image.png'],
    'css': [],
    'js': [],
    'qweb': [],
    'price': 300.00,
    'currency': 'EUR',
    'live_test_url': 'https://www.jumotech.com',
    'post_init_hook': '_post_init_odoo_chatgpt',
}
