{
    "name": "No Auto Save",
    "summary": """
        Web module extention to give proper msg and do not auto save
    """,
    "sequence": 95,
    "author": "BizzAppDev",
    "website": "http://www.bizzappdev.com",
    "category": "web",
    "version": "16.0.0.0.1",
    "depends": ["base", "web"],
    "data": [],
    "assets": {
        "web.assets_backend": [
            "web_no_auto_save/static/src/js/web_no_auto_save.js",
        ],
    },
    "images": ["images/SaveChangesEE.png"],
    "license": "LGPL-3",
    "installable": True,
}
