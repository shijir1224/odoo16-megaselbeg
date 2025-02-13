# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo import _, tools
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, time, timedelta
import collections
import time

import logging
_logger = logging.getLogger(__name__)

class TirePlanGenerator(models.Model):
	_inherit = 'tire.plan.generator'

	company_id = fields.Many2one('res.company', string=u'Компани', required=True,
		default=lambda self: self.env.user.company_id,)
