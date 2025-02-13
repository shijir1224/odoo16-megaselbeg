from urllib.parse import uses_fragment
from odoo import  api, fields, models, _
from datetime import datetime, timedelta



class HseHealthAnalysis(models.Model):
	_name ='hse.health.analysis'
	_description = 'Hse Health Analysis'
	_inherit = ["mail.thread", "mail.activity.mixin"]

	def name_get(self):
		result = []
		for obj in self:
			result.append((obj.id, obj.date.strftime('%Y-%m-%d') + ' (' + obj.employee_id.name + ')'))
		return result
   
	employee_id = fields.Many2one('hr.employee', string='Ажилтан', required=True)
	employee_vat = fields.Char(related='employee_id.passport_id', string='Регистр',)
	job_id = fields.Many2one(related='employee_id.job_id', string='Албан тушаал')
	user_company_id = fields.Many2one('res.company', string=u'Компани', readonly=True)
	company_id = fields.Many2one(related='employee_id.company_id', string='Компани')
	gender = fields.Selection(related='employee_id.gender', string='Хүйс')
	birth_year = fields.Date(related='employee_id.birthday', string='Төрсөн огноо')
	phone = fields.Char(related='employee_id.work_phone', string='Утасны дугаар', )
	create_work_date = fields.Date(related='employee_id.engagement_in_company', string='Ажилд орсон огноо')
	date = fields.Date(string='Шинжилгээ өгсөн огноо', required=True)
	attachment_ids = fields.Many2many('ir.attachment', string='Хавсралт')