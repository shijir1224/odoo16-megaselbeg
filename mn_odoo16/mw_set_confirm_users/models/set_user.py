
# -*- coding: utf-8 -*-
from odoo.exceptions import UserError
from odoo import fields, models, _
from odoo.exceptions import UserError

class SetConfirmUser(models.Model):
	_name = "set.confirm.user"

	employee_ids = fields.Many2many('hr.employee', string = 'Ажилчид')
	user_ids = fields.Many2many('res.users', string='Хэрэглэгчид')
	confirm_user_ids = fields.Many2many('res.users','res_rset_confirm_users',id1='conf_user_id',id2='user_id',string='Батлах хэрэглэгчид')

	def action_to_set(self):
		users =[]
		temp_users = []
		for item in self.employee_ids:
			for res in self.confirm_user_ids:
				users.append((res.id))
				if item.user_id:
					if item.user_id.manager_user_ids:
						for user in item.user_id.manager_user_ids:
							temp_users = item.user_id.manager_user_ids.ids
							if res.id != user.id:
								temp_users+=users
					else:
						temp_users = users
				else:
					raise UserError(_("%s- Ажилтны хэрэглэгч хоосон байна"%(item.name)))
				item.user_id.manager_user_ids = temp_users

	def action_to_set_all(self):
		users =[]
		temp_users = []
		for item in self.employee_ids:
			for res in self.confirm_user_ids:
				users.append((res.id))
				if item.user_id:
					temp_users = users
				else:
					raise UserError(_("%s- Ажилтны хэрэглэгч хоосон байна"%(item.name)))
				item.user_id.manager_user_ids = temp_users
