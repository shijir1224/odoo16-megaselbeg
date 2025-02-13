###################################################################################
#
#    Copyright (c) 2017-2019 MuK IT GmbH.
#
#    This file is part of MuK Backend Theme 
#    (see https://mukit.at).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>. 
#  
###################################################################################
{
	"name": "MW web wizard", 
	"summary": "Odoo Community Backend Theme",
	"version": "13.0.1.0.6", 
	'license': 'LGPL-3',
	"category": "Themes/Backend", 
	"license": "LGPL-3", 
	"author": "Managewall",
	"website": "http://managewall.mn",
	"depends": [
		"web",
	],
	"data": [
		"template/assets.xml",
	],
	'assets': {
		'web.assets_backend': [
			'mw_web_wizard_width/static/src/scss/wizard.scss',
		]
	},
	"application": False,
	"installable": True,
	"auto_install": False,
}
