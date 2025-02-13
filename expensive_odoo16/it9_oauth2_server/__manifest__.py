{
    'name': "Standard OAuth2 Server",
    'description': "Standard OAuth2 Server",
    'summary': "Authentication, Authorization, Security",
    'author': "IT9",
    'website': "https://github.com/superpkson",
    "license": "OPL-1",
    'category': 'App/Security',
    'version': '1.1',
    "depends": ["base"],
    "data": [
        'data/oauth2.scope.csv',
        'data/oauth2.grant_type.csv',
        'data/oauth2.response_type.csv',
        'data/ir_rule.xml',

        'security/ir.model.access.csv',

        'views/oauth2_dialog.xml',
        'views/oauth2_client.xml',
        'views/oauth2_code.xml',
        'views/menu.xml',
    ],
    'images': [
        'static/description/main_screenshot.png',
        'static/description/main_3.png',
        'static/description/main_0.png'
    ],
    "installable": True,
    "auto_install": False,
    "application": True,
    "currency": "USD",
    "price": "20",
}
