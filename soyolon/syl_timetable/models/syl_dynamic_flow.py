from odoo import api, fields, models, _
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError


DATETIME_FORMAT = "%Y-%m-%d"
DATE_FORMAT = "%Y-%m-%d"


class HrLeaveRequestMw(models.Model):
	_inherit = "hr.leave.mw"
	
	flow_desc = fields.Char('Урсгал таних',compute='_compute_flow_desc',store=True, default='other')

	@api.depends('is_work')
	def _compute_flow_desc(self):
		for i in self:
			if i.shift_plan_id.is_work == 'overtime_hour':
				i.flow_desc = 'overtime'
			elif i.shift_plan_id.is_work in('out_work','business_trip'):
				i.flow_desc = 'trip'
			else:
				i.flow_desc = 'other'
				
	flow_id = fields.Many2one('dynamic.flow', string='Урсгалын тохиргоо', tracking=True, copy=False, domain="[('model_id.model','=','hr.leave.mw'),('description','=',flow_desc)]", required=True, store=True)
	
    
	

	


	
	