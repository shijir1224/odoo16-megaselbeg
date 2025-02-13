# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields

class DynamicFLow(models.Model):
	_inherit = 'dynamic.flow'

	is_cash = fields.Boolean(string='Бэлэн мөнгөний урсгал эсэх')
	is_between_account = fields.Boolean(string='Данс хоорондын урсгал эсэх')
	is_between_company = fields.Boolean(string='Компани хоорондын урсгал эсэх')
	is_butsaalt = fields.Boolean(string='Урьдчилгаа буцаалт эсэх')
	is_info = fields.Boolean(string='Мэдэгдэл харуулах эсэх')
