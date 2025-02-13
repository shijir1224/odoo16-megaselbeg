{
    "name": "Priority on Sales, Customer Invoices and Vendor Bills",
    "summary": """
            Priority on Sales, Customer Invoices and Vendor Bills
    """,
    "description": """
        This module can be used to set priority on sale orders, customer invoices and vendor bills.
    """,
    "author": "Sanesquare Technologies",
    "website": "https://www.sanesquare.com/",
    "support": "odoo@sanesquare.com",
    "license": "AGPL-3",
    "category": "Uncategorized",
    "images": ["static/description/app_image.png"],
    "version": "16.0.1.0.1",
    "depends": ["base", "sale_management", "purchase", "account"],
    "data": [
        "views/sale_views.xml",
        "views/account_move_views.xml",
    ],
}
