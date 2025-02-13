# -*- coding: utf-8 -*-

from odoo.osv import osv
from odoo import api, fields, models
from datetime import date, datetime, timedelta
from odoo.tools.translate import _
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"



class ActionBackDescription(models.TransientModel):
	_name = 'action.back.description'
	_description = 'Action Draft'

	description = fields.Text('Буцаах тайлбар')

	def action_to_back(self):
		context=self._context
		if not self.description:
			raise UserError(_(u'Анхааруулга! Буцаах шалтгаан бичнэ үү.'))
		info_id = self.env['hr.leave.mw'].search([('id', '=', context['active_id'])])
		info_id.action_back_stage()
		info_id.return_description = self.description
		return True


class HrTimetableLineConfWizard(models.TransientModel):
	_name = 'hr.timetable.line.conf.wizard'
	_description = 'Configure wizard'

	shift_id = fields.Many2one('hr.shift.time','Хуваарь')
	date_start = fields.Date('Эхлэх огноо',required=True)
	date_to = fields.Date('Дуусах огноо',required=True)

	def action_to_done(self):
		context=self._context
		from_dt = datetime.strptime(
			str(self.date_start), DATE_FORMAT).date()
		to_dt = datetime.strptime(
			str(self.date_to), DATE_FORMAT).date()
		step = timedelta(days=1)
		while from_dt <= to_dt:
			if self.shift_id:
				line_id = self.env['hr.timetable.line.line'].search([('parent_id', '=', context['active_id']),('date','=',from_dt)])
			line_id.update({
				'shift_attribute_id':self.shift_id.id,
				'shift_plan_id':self.shift_id.id})
			from_dt += step
		return True