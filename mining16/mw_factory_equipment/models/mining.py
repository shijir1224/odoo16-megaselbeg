# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero, float_compare
import logging
_logger = logging.getLogger(__name__)


class miningMotohourEntryLine(models.Model):
	_inherit = "mining.motohour.entry.line"

	equipment_id = fields.Many2one('factory.equipment', string='Тоног төхөөрөмж', readonly=True, index=True)
	facility_id = fields.Many2one('factory.facility', string='Тоног төхөөрөмж байгууламж', readonly=True, index=True)
	technic_id = fields.Many2one('technic.equipment','Technic', required=False,readonly=True, index=True)