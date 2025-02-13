{
    "name": "No Quick Edit / Create",
    "version": "16.0.0",
    "category": "Web",
    'description': """This Module allow quick create and edit depend on user group""",
    "author": "ComposerCodes",
    "website": "",
    "support": "maged.ibrahem1@gmail.com",
    "license": "AGPL-3",
    "depends": ["web"],
    'data': [
        'security/security.xml',
    ],
    "assets": {
        "web.assets_backend": [
            "no_quick_create/static/src/components/relational_utils.esm.js",
        ]
    },
    "installable": True,
}
