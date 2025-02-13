# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _, tools
from datetime import datetime, timedelta
from dateutil.relativedelta import *
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError,Warning
from odoo.osv import expression
from odoo.http import request


class Http(models.AbstractModel):
	_inherit = 'ir.http'

	def session_info(self):
		user = request.env.user
		session_info = super(Http, self).session_info()
		session_info['user_companies']['current_company'] = (user.company_id.id, user.company_id.name, user.company_id.short_name)
		session_info['user_companies']['allowed_companies'] = {comp.id: {'id':comp.id, 'name': comp.name or '', 'sequence': comp.sequence, 'short_name': comp.short_name} for comp in user.company_ids}
		return session_info

class resCompany(models.Model):
	_inherit = 'res.company'
	_description = 'Company short name'

	short_name = fields.Char(string=u'Товч Нэр')

class resBranch(models.Model):
	_inherit = 'res.branch'

	def name_get(self):
		res = []
		for item in self:
			res_name = super(resBranch, item).name_get()
			if item.company_id and item.name and item.company_id.short_name:
				res_name = qty_str = '{0} {1}'.format(item.name, '[' + item.company_id.short_name + ']' or '')
				res.append((item.id, res_name))
			else:
				res.append(res_name[0])
		return res

class hrEmployee(models.Model):
	_inherit = 'hr.employee'

	def name_get(self):
		res = []
		for item in self:
			res_name = super(hrEmployee, item).name_get()
			if item.company_id and item.display_name and item.company_id.short_name:
				res_name = qty_str = '{0} {1}'.format(item.display_name, '[' + item.company_id.short_name + ']' or '')
				res.append((item.id, res_name))
			else:
				res.append(res_name[0])
		return res

class hrDepartment(models.Model):
	_inherit = 'hr.department'

	def name_get(self):
		res = []
		for item in self:
			res_name = super(hrDepartment, item).name_get()
			if item.company_id and item.display_name and item.company_id.short_name and not item.company_id.short_name in item.display_name:
				res_name = qty_str = '{0} {1}'.format(item.display_name, '[' + item.company_id.short_name + ']' or '')
				res.append((item.id, res_name))
			else:
				res.append(res_name[0])
		return res

	@api.depends('name', 'parent_id.complete_name', 'company_id', 'company_id.short_name')
	def _compute_complete_name(self):
		for department in self:
			if department.parent_id:
				department.complete_name = '%s / %s' % (department.parent_id.complete_name, department.name)
			else:
				department.complete_name = department.name
			if department.company_id.short_name and department.company_id:
				if not department.company_id.short_name in department.complete_name:
					department.complete_name = '%s [%s]' % (department.complete_name, department.company_id.short_name)

class productTemplate(models.Model):
	_inherit = 'product.template'

	def name_get(self):
		res = []
		for item in self:
			res_name = super(productTemplate, item).name_get()
			if item.company_id and item.display_name and item.company_id.short_name:
				res_name = qty_str = '{0} {1}'.format(item.display_name, '[' + item.company_id.short_name + ']' or '')
				res.append((item.id, res_name))
			else:
				res.append(res_name[0])
		return res

class productProduct(models.Model):
	_inherit = 'product.product'

	def name_get(self):
		res = []
		for item in self:
			res_name = super(productProduct, item).name_get()
			if item.company_id and item.display_name and item.company_id.short_name:
				res_name = qty_str = '{0} {1}'.format(item.display_name, '[' + item.company_id.short_name + ']' or '')
				res.append((item.id, res_name))
			else:
				res.append(res_name[0])
		return res

class dynamicFlow(models.Model):
	_inherit = 'dynamic.flow'

	def name_get(self):
		res = []
		for item in self:
			res_name = super(dynamicFlow, item).name_get()
			if item.company_id and item.name and item.company_id.short_name:
				res_name = qty_str = '{0} {1}'.format(item.name, '[' + item.company_id.short_name + ']' or '')
				res.append((item.id, res_name))
			else:
				res.append(res_name[0])
		return res
	
class AccountAccount(models.Model):
	_inherit = 'account.account'

	def name_get(self):
		res = []
		for item in self:
			res_name = super(AccountAccount, item).name_get()
			if item.company_id and item.name and item.company_id.short_name:
				res_name = qty_str = '{0} {1} {2}'.format(item.code, item.name, '[' + item.company_id.short_name + ']' or '')
				res.append((item.id, res_name))
			else:
				res.append(res_name[0])
		return res

class stockWarehouse(models.Model):
	_inherit = 'stock.warehouse'

	def name_get(self):
		res = []
		for item in self:
			res_name = super(stockWarehouse, item).name_get()
			if item.company_id and item.name and item.company_id.short_name:
				res_name = qty_str = '{0} {1} {2}'.format(item.code, item.name, '[' + item.company_id.short_name + ']' or '')
				res.append((item.id, res_name))
			else:
				res.append(res_name[0])
		return res
