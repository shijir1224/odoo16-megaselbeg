# -*- coding: utf-8 -*-
##############################################################################
from odoo import  api, fields, models, _
from odoo.exceptions import UserError


class HrMission(models.Model):
	_inherit = 'hr.mission'

	is_check = fields.Boolean(string='ХАБ Зааварчилгаатай танилцсан эсэх', default=False, readonly=True, copy=False)
	user_id = fields.Many2one('res.users', string='ХАБ Зааварчилгаатай танилцсан ажилтан', readonly=True, copy=False)
	check_date = fields.Date(string='ХАБ Зааварчилгаатай танилцсан огноо', readonly=True, copy=False)
	attachment_ids = fields.Many2many('ir.attachment', string='ХАБ Зааварчилгаа файл', readonly=True, copy=False)


	def action_next_stage(self):
		attachment_id = self.env['ir.attachment'].search([('name','=','ХАБ Зааварчилгаа')], limit=1)
		war_obj = self.env['hse.mission.wizard']
		if self.flow_line_next_id.state_type=='done' and not self.is_check and not self.env.context.get('Танилцсан',False):
			war_id = war_obj.create({
				'mission_id': self.id,
				'is_check': False,
				'user_id': self.employee_id.user_id.id if self.employee_id.user_id else self.env.user.id,
				'attachment_ids': attachment_id.ids
				})
			return {
				'name': 'ХАБ Зааварчилгаа',
				'type': 'ir.actions.act_window',
				'view_mode': 'form',
				'res_model': 'hse.mission.wizard',
				'view_id': self.env.ref('mw_hse.hse_mission_instructions_view').id,
				'res_id': war_id.id,
				'target': 'new',
			}
		return super(HrMission, self).action_next_stage()

	
class HseMissionWizard(models.TransientModel):
	_name = "hse.mission.wizard"  
	_description = "Hse Mission Wizard"

	mission_id = fields.Many2one('hr.mission', string="Томилолт ID", readonly=True)
	is_check = fields.Boolean(string='ХАБ Зааварчилгаатай танилцсан эсэх', default=False)
	user_id = fields.Many2one('res.users', string='ХАБ Зааварчилгаатай танилцсан ажилтан')
	attachment_ids = fields.Many2many('ir.attachment', string='ХАБ Зааварчилгаа файл', readonly=True)

	def hse_mission_instructions(self):
		if not self.is_check:
			raise UserError(u'Зааварчилгаатай танилцсан эсэх чек хийнэ үү!!!')
		else:
			self.mission_id.write({
				'id': self.mission_id.id,
				'is_check': self.is_check,
				'user_id': self.env.user.id,
				'check_date': fields.Date.context_today(self),
				'attachment_ids': self.attachment_ids
			})
			self.sent_mail()
			return self.mission_id.with_context(Танилцсан=True).action_next_stage()
	
	def sent_mail(self):
		base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
		action_id = self.env['ir.model.data'].check_object_reference('mw_hr', 'view_hr_mission_form')[1]
		html = u'<b>Томилолтын ХАБ Зааварчилгаа ирлээ, Хавсралт файлтай уншиж танилцана уу!!! Доорх линкээр орно уу.</b><br/>'
		html += u"""<b><a target="_blank" href=%s/web#id=%s&view_type=form&model=preliminary.notice&action=%s>%s</a></b>!!!"""% (base_url, self.mission_id.id, action_id, self.mission_id.name)
		for item in self.mission_id.mission_ids:
			for line in item.employee_id:
				if line.user_partner_id:
					self.env.user.send_chat(html,[line.user_partner_id], with_mail=True, attachment_ids=self.attachment_ids.ids)