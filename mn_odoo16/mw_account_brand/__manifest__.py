# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    'name': 'MN Accounting brand',
    'version': '16.1',
    'license': 'LGPL-3',
    'category': 'Brand and Accounting',
    'sequence': 20,
    'author': 'Daramaa Managewall LLC',
    'summary': 'Changed by Mongolian Accounting',
        'description': """Brand модуль
                - ажил гүйлгээнд брэнд сонгох
                - Зардал хуваарилахад бранд ээр сонгох хуваарилах
                - Гүйлгээ шинжилгээн брэнд харах
                    """,
    "depends": ["mw_account","product_brand","mw_stock","mw_account_expense_allocation"],
    "data": [
        "security/ir.model.access.csv",
        "views/account_view.xml",
        "reports/account_transaction_balance_pivot_view.xml",
    ],
    "installable": True,
    "auto_install": False,
}
