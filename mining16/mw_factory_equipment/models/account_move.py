# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero, float_compare
import logging
_logger = logging.getLogger(__name__)


class AccountMoveLine(models.Model):
	_inherit = "account.move.line"
	
	equipment_id = fields.Many2one('factory.equipment', string=u'Холбоотой тоног төхөөрөмж')

	def _prepare_analytic_distribution_line(self, distribution, account_id, distribution_on_each_plan):
		""" equipment_id
		"""
		self.ensure_one()
		res = super(AccountMoveLine, self)._prepare_analytic_distribution_line(distribution=distribution, account_id=account_id, distribution_on_each_plan=distribution_on_each_plan)
		res.update({
			'equipment_id':self.equipment_id and self.equipment_id.id or False
		})
		return res

class AccountAnalyticLine(models.Model):
	_inherit = "account.analytic.line"
	
	equipment_id = fields.Many2one('factory.equipment', string=u'Холбоотой тоног төхөөрөмж')
