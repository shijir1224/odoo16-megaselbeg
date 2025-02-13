# -*- coding: utf-8 -*-

from odoo import tools
from odoo import api, fields, models
import time
from datetime import datetime, timedelta
from odoo.exceptions import UserError
from tempfile import NamedTemporaryFile
import base64
import xlrd

import logging
_logger = logging.getLogger(__name__)

class WizardEditPartnerTags(models.TransientModel):
	_name = 'wizard.edit.partner.tags'
	_description = "wizard edit partner tags"
	# Columns
	partner_ids = fields.Many2many('res.partner', string=u'Харилцагчид', required=True,)
	partner_category_ids = fields.Many2many('res.partner.category', string=u'Пайз/Ангилал', required=True,)

	edit_type = fields.Selection([
			('add', 'Нэмэх'),
			('remove', 'Хасах'),
		], default='add', required=True, string='Засах төрөл',)

	def action_edit_tags(self):
		for partner in self.partner_ids:
			for tag in self.partner_category_ids:
				if self.edit_type == 'add':
					partner.category_id += tag
				else:
					partner.category_id -= tag
		return True	
		