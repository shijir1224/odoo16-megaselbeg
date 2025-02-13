# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models, fields
from odoo.exceptions import UserError, ValidationError
import logging
_logger = logging.getLogger(__name__)

class ResUserLocation(models.Model):
	_name = 'res.user.location'
	_description = "res user location"

	user_id = fields.Many2one('res.users', 'User')
	lng = fields.Float('Longitude')
	lat = fields.Float('Latitude')
