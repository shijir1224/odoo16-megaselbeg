
# -*- coding: utf-8 -*-

import time
import math

from odoo.osv import expression
from odoo.tools.float_utils import float_round as round
from odoo.exceptions import UserError, ValidationError
from odoo import api, fields, models, _
import dateutil.parser
from odoo.tools import float_compare, float_is_zero
from odoo.addons.auth_signup.models.res_partner import SignupError, now
import odoo.netsvc, decimal, os
import odoo.addons.decimal_precision as dp
from odoo.osv import osv


class DocumentInherit(models.Model):
	_inherit = 'documents.document'


	employee_ids = fields.Many2many('hr.employee',string='Ажилтнууд')

	def action_send_chat_employee(self):
		action_id = self.env['ir.model.data'].get_object_reference('documents', 'document_action')[1]
		base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')		
		html = u"""<b><a target="_blank" href=%s/web#id=%s&view_type=kanban&model=documents.document&action=%s>%s - бүлэгт %s - нэртэй баримт нэмэгдэж орлоо !! </a></b>"""% (base_url,str(self.id),str(action_id),str(self.folder_id.display_name),str(self.name))
		for item in self.employee_ids:
			self.env.user.send_chat(html,[item.partner_id],True,True)
