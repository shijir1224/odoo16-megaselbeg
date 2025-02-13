{
    'name': 'Soyolon Contract',
    'version': '1.0',
    'sequence': 10,
    'category': 'HR Management',
    'author': 'Managewall LLC',
    'description': """
        Соёолон гэрээ модуль
        """,
    'depends': ['mw_contract'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/syl_contract_view.xml',
    ],
    'installable': True,
    'application': False,
    'qweb': [],
}
