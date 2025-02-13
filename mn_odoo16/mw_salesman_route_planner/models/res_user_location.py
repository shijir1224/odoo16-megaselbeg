# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models, fields
import logging
_logger = logging.getLogger(__name__)

class ResUserLocation(models.Model):
	_name = 'res.user.gps.location'
	_description = "User GPS location"

	user_id = fields.Many2one('res.users', 'User')
	lng = fields.Float('Longitude', digits=(16, 5))
	lat = fields.Float('Latitude', digits=(16, 5))
