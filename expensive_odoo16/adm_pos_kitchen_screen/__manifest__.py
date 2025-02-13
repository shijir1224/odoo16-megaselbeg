{
    'name': "Pos Kitchen Screen",
    'version': "16.0.3",
    'category': "Tools",
    'summary': """
        Point of sale Kitchen Screen | Pos Restaurant Screen | POS Bar Screen | POS Kitchen Screen
        | Point of sale bar screen | Odoo Kitchen Display | POS Kitchen display system | Point of sale restaurant screen 
        | vista de cocina en punto de venta | cocina en POS
    """,
    'author': "Javier Fernández",
    'website': "https://asdelmarketing.com",
    'license': 'OPL-1',
    'price': 28.99,
    'currency': 'EUR',
    'data': [
        'views/kitchen_menu_view.xml',
        'views/product_views.xml',
        'views/user_views.xml',
        'views/res_config_settings_views.xml',
        'views/pos_config_view.xml',
    ],
    'demo': [],
    'images': [
        'static/description/thumbnail.gif',
    ],
    'depends': [
        'web',
        'point_of_sale',
        'pos_restaurant'
    ],
    "assets": {
        "web.assets_backend": [
            "adm_pos_kitchen_screen/static/src/js/kitchen.js",
            "adm_pos_kitchen_screen/static/src/css/custom.css",
            "adm_pos_kitchen_screen/static/src/xml/kitchen.xml",
        ],
        'point_of_sale.assets': [
            'adm_pos_kitchen_screen/static/src/js/Screens/DraftPosOrderButton.js',
            'adm_pos_kitchen_screen/static/src/xml/DraftPosOrderButton.xml',
        ],
    },
   


    'installable': True,
}