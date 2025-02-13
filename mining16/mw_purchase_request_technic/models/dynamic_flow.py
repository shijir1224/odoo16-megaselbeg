# -*- coding: utf-8 -*-
from odoo import fields, models, tools, api
from odoo.exceptions import UserError, Warning


class DynamicFlowInherit(models.Model):
	_inherit = 'dynamic.flow'

	is_technic = fields.Boolean(string=u"Техник дээр захиалдаг", default=False)
