# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo import _, tools
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, time, timedelta
import collections

class TechnicComponentConfig(models.Model):
	_inherit = 'technic.component.config'

	parent_id2 = fields.Many2one('factory.equipment.setting', string=u'Модел тохиргоо', ondelete='cascade', tracking=True)

class TechnicComponentPart(models.Model):
	_inherit = 'technic.component.part'

	current_equipment_id = fields.Many2one('factory.equipment', string=u'Одоогийн техник', tracking=True)
	main_attribute_ids = fields.One2many('equipment.main.attribute','component_id', string="Үндсэн үзүүлэлтүүд")
