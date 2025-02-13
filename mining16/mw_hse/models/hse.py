# -*- coding: utf-8 -*-
##############################################################################
from odoo import  api, fields, models, _
from datetime import datetime, timedelta
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"

	
class HseSafetyPlan(models.Model):
	_name ='hse.safety.plan'
	_description = 'Safety plan'
	_inherit = ["mail.thread", "mail.activity.mixin"]
	_order = 'year asc, indicator_id desc, frequency asc'
   
	def _set_name(self):
		for item in self:
			item.name = item.year
 
	@api.depends('actual','count','is_count')
	def _set_percent(self):
		for item in self:
			obj = item
			per = 0
			if int(obj.actual):
				if obj.is_count:
					per = (100*int(obj.actual))/obj.count
					if per>100:
						per = 100
				elif int(obj.actual)>100:
					per=100
				else:
					per=obj.actual
			item.actual_percent = per
		
	name = fields.Char(compute='_set_name', string='Нэр', readonly=True)
	year = fields.Selection([('2012', '2012'),('2013', '2013'),('2014', '2014'),('2015', '2015'),('2016', '2016'),('2017', '2017'),('2018', '2018'),('2019', '2019'),('2020', '2020'),('2021', '2021'),('2022', '2022'),('', ''),('', '')], 'Жил', required=True)
	indicator_id = fields.Many2one('hse.safety.indicator','Үзүүлэлт', required=True)
	indicator_type = fields.Selection(related='indicator_id.type', readonly=True, store=True)
	frequency = fields.Selection([('season_1','1-р улирал'),('season_2','2-р улирал'),('season_3','3-р улирал'),('season_4','4-р улирал')], 'Давтамж', required=True)
	is_count = fields.Boolean('Тоогоор', default=True)
	count = fields.Integer('Тоо')
	percent = fields.Integer('Хувь %', group_operator='avg')
	actual = fields.Char('Гүйцэтгэл', default=0)
	actual_percent = fields.Integer(compute='_set_percent', string='Гүйцэтгэлийн хувь %', readonly=True, group_operator='avg', store=True)
	
	def write(self, vals):
		if 'is_count' in vals:
			if vals['is_count']:
				vals['percent']=0
			else:
				vals['count']=0
		return super(HseSafetyPlan, self).write(vals)

	
	# _sql_constraints = [
	#     ('name_uniq', 'UNIQUE(year, indicator_id, frequency)', 'Year and Indicator and Frequency must be unique!')
	# ]

class HseSafetyIndicator(models.Model):
	_name ='hse.safety.indicator'
	_description = 'Safety indicator'
   
	name = fields.Char('Name', required=True)
	type = fields.Selection([('leading','Leading indicators'),('lagging','Lagging indicators'),('training','Training'),('env','Env')], 'Type', required=True)
	value = fields.Char('Value', required=True)
	

class HseNopeLti(models.Model):
	_name ='hse.nope.lti'
	_description = 'Man/Hour without LTI'
	_inherit = ["mail.thread", "mail.activity.mixin"]
	_order = 'date desc'

	def _set_name(self):
		for item in self:
			item.name = item.branch_id.name+' '+item.date

	@api.depends('line_ids','line_ids.man_hour')
	def _sum_man_hour(self):
		for item in self:
			item.man_hour = str(sum(item.line_ids.mapped('man_hour')))
	
	@api.depends('line_ids','line_ids.man_hour')
	def _total_man_hour(self):
		hour = 0
		self.env.cr.execute("select max(h1.date),min(h1.date) from hse_nope_lti h1 where h1.date>=(select max(h2.date) from hse_nope_lti h2 where h2.man_hour='0' and h2.branch_id=h1.branch_id)");
		str_cr = self.env.cr.fetchone()
		day = (datetime.strptime(str_cr[0], '%Y-%m-%d') - datetime.strptime(str_cr[1], '%Y-%m-%d')).days

		self.env.cr.execute("select sum(man_hour::integer) from hse_nope_lti h1 where h1.date>=(select max(h2.date) from hse_nope_lti h2 where h2.man_hour='0' and h2.branch_id=h1.branch_id)");
		hour = int(self.env.cr.fetchone()[0])

		for item in self:
			item.total_man_hour = hour
			item.total_day = day
	
	@api.depends('branch_id','date')
	def _inc_man_hour(self):
		
		for obj_this in self.search([]):
			lti_date = False
			for item in self.search([('branch_id','=',obj_this.branch_id.id), ('man_hour','=','0'), ('date','<=',obj_this.date)]):
				if not lti_date:
					lti_date = item.date
				else:
					if lti_date < item.date:
						lti_date = item.date
			if lti_date:
				hour = 0
				day = 0
				max_date = lti_date
				for item in self.browse(self.search( [('branch_id','=',obj_this.branch_id.id),('date','>=',lti_date),('date','<=',obj_this.date)])):
					hour += int(item.man_hour)

				day = (datetime.strptime(obj_this.date, '%Y-%m-%d') - datetime.strptime(lti_date, '%Y-%m-%d')).days
				obj_this.inc_man_hour = str(hour)
				obj_this.inc_total_day = str(day)
				

	# by Bayasaa Өдөрөөр салгах

	@api.depends('date')
	def _set_date(self):
		for item in self:
			date_object = datetime.strptime(obj.date, '%Y-%m-%d')
			item.year = date_object.year
			item.month = date_object.month
			item.day =  date_object.day
		
	date = fields.Date('Date', required=True, default=fields.Date.context_today)
	name = fields.Char(compute='_set_name', string='Name', readonly=True)
	branch_id = fields.Many2one('res.branch','Салбар', required=True)
	year = fields.Integer(compute='_set_date', string='Year', readonly=True, store=True)
	month = fields.Integer(compute='_set_date',string='Month', readonly=True, store=True)
	day = fields.Integer(compute='_set_date',string='Day', readonly=True, store=True)
	line_ids = fields.One2many('hse.nope.lti.line', 'nope_lti_id', 'Nope lti line')
	man_hour = fields.Char(compute='_sum_man_hour',string='Man hour' , store=True)
	total_man_hour = fields.Integer(compute='_total_man_hour', string='Total man hour', store=True)
	total_day = fields.Integer(compute='_total_man_hour', string='Since the date registered lost time injury', store=True)
	inc_total_day = fields.Char(compute='_inc_man_hour', string='Increase since the date registered lost time injury', store=True)
	inc_man_hour = fields.Char(compute='_inc_man_hour', string='Increase man hour', store=True)
	
	# _sql_constraints = [
	#     ('name_uniq', 'UNIQUE(branch_id, date)', 'Project and Date must be unique!')
	# ]
	
# end yvaa
class HseHopeLtiLine(models.Model):
	_name ='hse.nope.lti.line'
	_description = 'Nope lti line'

	@api.depends('man','nope_lti_id')
	def _man_hour(self):
		res = {}
		m_hour = 0
		obj = self.browse(cr,uid,ids)[0]
		pr_hr = self.env['hse.branch.man.hour'].search([('branch_id','=',obj.nope_lti_id.branch_id.id)])
		pr = self.env['hse.branch.man.hour'].browse(pr_hr)[0]
		obj = self.browse(ids)[0]
		
		for item in self:
			pr_hr = self.env['hse.branch.man.hour'].search([('branch_id','=',obj.nope_lti_id.branch_id.id)], limit=1)
			pr = pr_hr
			item.man_hour = obj.man*pr.man_hour

		return res
   
	nope_lti_id = fields.Many2one('hse.nope.lti','Nope lti ID', required=True)
	location_id = fields.Many2one('hse.location','Location')
	man = fields.Integer('Man', required=True)
	man_hour = fields.Integer(compute='_man_hour', string='Man hour', store=True)
	
class HseBranchManHour(models.Model):
	_name ='hse.branch.man.hour'
	_description = 'Branch man hour'
   
	branch_id = fields.Many2one('res.branch','Салбар', required=True)
	man_hour = fields.Integer('Man hour')
	

class HseSafetyMeeting(models.Model):
	_name ='hse.safety.meeting'
	_description = 'Safety meeting'
	_inherit = ["mail.thread", "mail.activity.mixin"]
	_order = 'date desc'

	@api.depends('branch_id','date')
	def _set_name(self):
		for item in self:
			if not item.name:
				my_id = self.env['ir.model'].search([('model','=','hse.safety.meeting')] , limit=1)
				conf_ids = self.env['hse.code.config'].search([('branch_id','=',item.branch_id.id),('model_id','=',my_id.id)], limit=1)
				if conf_ids:
					num_name = conf_ids.name
					max_count = 0
					self.env.cr.execute('SELECT id FROM hse_safety_meeting where branch_id = %s and EXTRACT(YEAR FROM date) = %s ',(item.branch_id.id, datetime.strptime(item.date, '%Y-%m-%d').year))
					obj_ids = map(lambda x: x[0],self.env.cr.fetchall())
					for item_sub in self.env['hse.safety.meeting'].browse(obj_ids):
						s = item_sub.name
						if s and int(s[len(num_name): len(s)]) > max_count:
							max_count = int(s[len(num_name): len(s)])

					item.name = num_name+str(max_count+1).zfill(4)
	  
	@api.depends('meeting_line')
	def _sum_count(self):
		for item in self:
			item.participants_count = len(item.meeting_line)

	
	date = fields.Date('Огноо', required=True, states={'done':[('readonly',True)]}, default=fields.Date.context_today)
	state = fields.Selection([('draft', 'Draft'),('done', 'Done')], 'Төлөв', readonly=True, tracking=True, default='draft')
	part = fields.Selection([('a', 'A'),('b', 'B'),('c', 'C')], 'Part', required=True, states={'done':[('readonly',True)]})
	name = fields.Char(compute='_set_name', string='Number', readonly=True, store=True)
	branch_id = fields.Many2one('res.branch', 'Салбар', required=True, states={'done':[('readonly',True)]})

	monitoring_user_id = fields.Many2one('res.users','Хянасан ажилтан', required=True, states={'done':[('readonly',True)]}, default=lambda self: self.env.user)
	department_id = fields.Many2one('hr.department','Хэлтэс', required=True, states={'done':[('readonly',True)]})
	participants_count = fields.Integer(compute='_sum_count', string='Оролцогчидын тоо')
	subject = fields.Char('ААСХ-ын сэдэв', required=True, states={'done':[('readonly',True)]})
	managing_employee_ids = fields.Many2many('hr.employee', 'hse_safety_meeting_employee_rel', 'safety_meeting_id', 'employee_id', string='Удирдсан ажилтан', states={'done':[('readonly',True)]})
	safety_meeting_1 = fields.Text('safety_meeting_1', states={'done':[('readonly',True)]})
	safety_meeting_2 = fields.Text('safety_meeting_2', states={'done':[('readonly',True)]})
	comment = fields.Text('Санал', states={'done':[('readonly',True)]})
	attachment_ids = fields.Many2many('ir.attachment', 'hse_safety_meeting_ir_attachments_rel','safety_meeting_id', 'attachment_id', 'Хавсралт', states={'done':[('readonly',True)]})
	meeting_line = fields.One2many('hse.safety.meeting.line', 'safety_meeting_id', 'Safety meeting line')
	
	def action_to_done(self):
		self.write({'state': 'done'})
		
	def action_to_draft(self):
		self.write({'state': 'draft'})
	   
	def import_participants(self):
		obj = self
		if obj.meeting_line:
			obj.meeting_line.unlink()

		line_ids = []
		# Oroltsogch importlohiig tur haav
		# hr_branch = self.env['hr.department'].search( [('branch_id','=',obj.branch_id.id)])
		# relay_id = self.env['work.schedule.relay'].search( [('relay','=',obj.part.upper()),('branch_id','in',hr_branch.ids)])

		# hr_table_ids = self.env['time.table.details'].search(cr ,uid, [('employee_state','in',['work_at_night','work_at_day']),('branch_id','in',hr_branch),('relay','in',relay_id),('department_id','=',obj.department_id.id),('date','=',(datetime.strptime(obj.date, '%Y-%m-%d') - timedelta(days=1)).strftime('%Y-%m-%d')),('date','<=',(datetime.strptime(obj.date, '%Y-%m-%d') + timedelta(days=1)).strftime('%Y-%m-%d'))])
		# hr_empolyees = []
		
		# for item in self.env['time.table.details'].browse( hr_table_ids):
		#     if item.employee_id.id not in hr_empolyees:
		#         hr_empolyees.append(item.employee_id.id)
		#         data = { 'safety_meeting_id': obj.id,
		#              'participant_id': item.employee_id.id,
		#              }
		#         line_id = self.env['hse.safety.meeting.line').create( data, context=context)

		# line_ids = self.env['hse.safety.meeting.line'].search( [('safety_meeting_id','=',obj.id)])
		
		# return {
		#         'value': {
		#         'meeting_line':line_ids
		#     }
		# }


class HseSafetyMeetingline(models.Model):
	_name ='hse.safety.meeting.line'
	_description = 'Safety meeting line'
   
	safety_meeting_id = fields.Many2one('hse.safety.meeting', 'Safety meeting ID', required=True, ondelete='cascade')
	participant_id = fields.Many2one('hr.employee','Оролцогчид', required=True)
	

class HseHazardType(models.Model):
	_name ='hse.hazard.type'
	_description = 'Types of hazard'
	_inherit = ["mail.thread", "mail.activity.mixin"]
   
	name = fields.Char('Нэр', required=True)
	
	_sql_constraints = [
		('name_uniq', 'UNIQUE(name)', 'Нэр давтагдахгүй!')
	]
	_order = 'name asc'

class HseRiskRating(models.Model):
	_name ='hse.risk.rating'
	_description = 'Risk Rating'
	_inherit = ["mail.thread", "mail.activity.mixin"]

	@api.depends('rating','likelihood_id','consequence_id')
	def _set_name(self):
		for item in self:
			item.name = str(item.rating) +'.  /'+item.likelihood_id.name+'/  /'+item.consequence_id.name+'/'

	name = fields.Char(compute='_set_name', string='Нэр', readonly=True, store=True)
	rating = fields.Integer('Зэрэг')
	likelihood_id = fields.Many2one('hse.likelihood', 'Магадлал', required=True)
	consequence_id = fields.Many2one('hse.consequence', 'Үр дагавар', required=True)
	assessment_type = fields.Selection([('low_risky','Бага эрсдэлтэй'),('risky','Эрсдэлтэй'),('high_risky','Өндөр эрдэлтэй')],'Үнэлгээ төрөл', required=True)
	assessment_description = fields.Char('Үнэлгээ тайлбар')
	
	_order = 'rating asc'

class HseConsequence(models.Model):
	_name ='hse.consequence'
	_description = 'Consequence'
	_inherit = ["mail.thread", "mail.activity.mixin"]
   
	consequence_rating = fields.Integer('Үр дагаварын зэрэг')
	name = fields.Char('Нэр', required=True)
	man_healthy = fields.Char('Хүний эрүүл мэнд', required=True)
	env_healthy = fields.Char('Байгаль орчинд учруулж болзошгүй хохирол', required=True)
	lost_time = fields.Char('Цаг алдалт', required=True)
	asset_damage = fields.Char('Хөрөнгийн хохирол', required=True)
	
	_order = 'consequence_rating asc'

class HseLikelihood(models.Model):
	_name ='hse.likelihood'
	_description = 'Likelihood'
	_inherit = ["mail.thread", "mail.activity.mixin"]
   
	name = fields.Char('Магадлал', required=True)
	assessment = fields.Char('Үнэлгээ', required=True)
	description = fields.Char('Тайлбар', required=True)
	
	_order = 'assessment asc'


class HseAccidentCategory(models.Model):
	_name ='hse.accident.category'
	_description = 'Categories of accidents'
	_order = 'name asc'
	_inherit = ["mail.thread", "mail.activity.mixin"]
   
	name = fields.Char('Ослын төрөл', required=True)
	accident_id = fields.Many2one('hse.accident.type', 'Ослын ангилал', required=True)

