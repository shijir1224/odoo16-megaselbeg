{
    'name': 'Soyolon Orientation',
    'version': '1.0',
    'sequence': 10,
    'category': 'HR Management',
    'author': 'Managewall LLC',
    'description': """
        Соёолон ДЗХ
        """,
    'depends': ['employee_orientation','mw_hr','syl_hr'],
    'data': [
        'security/ir.model.access.csv',
        'views/syl_orientation_view.xml',
    ],
    'installable': True,
    'application': False,
    'qweb': [],
}
