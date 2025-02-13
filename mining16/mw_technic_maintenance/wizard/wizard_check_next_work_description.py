# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo import _, tools
from odoo.exceptions import UserError, ValidationError
from datetime import datetime

import time

class WizardCheckNextWorkDescription(models.TransientModel):
	_name = "wizard.check.next.work.description"
	_description = "wizard.check.next.work.description"  

	date_start = fields.Date(required=True, string=u'Эхлэх огноо', default=time.strftime('%Y-%m-01'))
	date_end = fields.Date(required=True, string=u'Дуусах огноо',default=fields.Date.context_today)
	technic_id = fields.Many2one('technic.equipment',string=u'Техник', 
		domain=[('state','!=','draft'),('owner_type','=','own_asset')])
	description = fields.Html(string=u'Desc...', readonly=True, default=u"Мэдээлэл олдсонгүй")

	
	def check_description(self):
		wos = []
		if self.technic_id:
			wos = self.env['maintenance.workorder'].search([
					('state','in',['closed','done']),
					('date_required','>=',self.date_start),
					('date_required','<=',self.date_end),
					('next_work_description','!=',False),
					('technic_id','=',self.technic_id.id),
					('next_work_state','=','pending'),
				])
		else:
			wos = self.env['maintenance.workorder'].search([
					('state','in',['closed','done']),
					('date_required','>=',self.date_start),
					('date_required','<=',self.date_end),
					('next_work_description','!=',False),
					('next_work_state','=','pending'),
				])
		number = 1
		message = ''

		base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
		action_id = self.env['ir.model.data']._xmlid_lookup('mw_technic_maintenance.action_maintenance_workorder')[2]

		for wo in wos:
			link = u"""<b><a target="_blank" href=%s/web#id=%s&view_type=form&model=maintenance.workorder&action=%s>%s</a></b>"""% (base_url,wo.id,action_id,wo.name)

			message += u'%d. %s-н "<font color="red">%s</font>" ажил <b>%s</b> техник дээр хийгдэхээр байна.<br/>' % (number, link, wo.next_work_description, wo.technic_id.name or 'x')
			number += 1
		self.description = message

		return {
		   'name': 'Хойшид хийгдэх ажлын мэдээ',
		   'view_type': 'form',
		   'view_mode': 'form',
		   'res_model': 'wizard.check.next.work.description',
		   'res_id': self.id,
		   'views': [(False, 'form')],
		   'type': 'ir.actions.act_window',
		   'target': 'new',
		   'nodestroy': True,
	   }
			
