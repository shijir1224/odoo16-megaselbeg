from odoo import fields, models, _, api
from odoo.exceptions import UserError
from datetime import date

class Orientation(models.Model):
	_inherit = 'employee.orientation'

	@api.model
	def _line_rate_item(self):
		cons = self.env['rate.question'].search([('type_n','=','type1')])
		w = []
		for cc in cons:
			vals = {
				'question_id': cc.id,
				'score':cc.score
			}
			w.append(vals)
		return w

	@api.model
	def _line_item360(self):
		cons360 = self.env['rate.question'].search([('type_n','=','type2')])
		w = []
		for cc in cons360:
			vals = {
				'question_id': cc.id,
			}
			w.append(vals)
		return w
	
	@api.model
	def _line_item_report(self):
		cons_report = self.env['rate.question'].search([('type_n','=','type3')])
		w = []
		for cc in cons_report:
			vals = {
				'question_id': cc.id,
				'score':cc.score
			}
			w.append(vals)
		return w

	@api.model
	def _line_item_all(self):
		cons_report = self.env['rate.question'].search([('type_n','=','type4')])
		w = []
		for cc in cons_report:
			vals = {
				'question_id': cc.id,
				'score':cc.score,
				'type':cc.type
			}
			w.append(vals)
		return w

	@api.model
	def _line_item_hr(self):
		cons_report = self.env['rate.question'].search([('type_n','=','type5')])
		w = []
		for cc in cons_report:
			vals = {
				'question_id': cc.id,
			}
			w.append(vals)
		return w
	
	@api.model
	def _line_rule(self):
		cons_report = self.env['orientation.rule'].search([])
		w = []
		for cc in cons_report:
			vals = {
				'rule_id': cc.id,
			}
			w.append(vals)
		return w
	
	@api.model
	def _line_training_item(self):
		cons_report = self.env['employee.training'].search([])
		w = []
		for cc in cons_report:
			vals = {
				'training_id': cc.id,
				'period': cc.period,
				'idea': cc.idea,
				'type_n': cc.type_n,
				'user_id': cc.program_convener_id.id,
				'date_from': cc.date_from,
				'date_to': cc.date_to,
			}
			w.append(vals)
		return w

	@api.model
	def _line_item_meet(self):
		cons_report = self.env['rate.question'].search([('type_n','=','type6')])
		w = []
		for cc in cons_report:
			vals = {
				'question_id': cc.id,
				'type':cc.type
			}
			w.append(vals)
		return w
	

	def write(self, values):
		res = super(Orientation,self).write(values)
		no1 = 0
		no2 = 0
		no3 = 0
		no4 = 0
		no5 = 0
		no6=0
		no7=0
		no8=0
		no9=0
		no10=0
		no11=0
		for line in self.orientation_request_ids:
			no1 +=1
			line.sequence = no1
		for line in self.rate_ids:
			no2 +=1
			line.sequence = no2
		for line in self.rate_ids_360:
			no3 +=1
			line.sequence = no3
		for line in self.rate_report_ids:
			no4 +=1
			line.sequence = no4
		for line in self.rate_all_ids:
			no5 +=1
			line.sequence = no5
		for line in self.rule_ids:
			no6 +=1
			line.sequence = no6
		for line in self.report_ids:
			no7 +=1
			line.sequence = no7
		for line in self.training_ids:
			no8 +=1
			line.sequence = no8
		for line in self.hour_ids:
			no9 +=1
			line.sequence = no9
		for line in self.meet_ids:
			no10 +=1
			line.sequence = no10
		for line in self.rate_hr_ids:
			no11 +=1
			line.sequence = no11
		return res
	
	orientation_id = fields.Many2one('orientation.checklist', string='ДЗХ тохиргоо',domain=False, required=True)
	rate_ids_360 = fields.One2many('orientation.rate.line360', 'rate_id', string='Rate question',default=_line_item360)
	rate_report_ids = fields.One2many('orientation.rate.line.report', 'rate_id', string='Rate question',default=_line_item_report)
	rate_all_ids = fields.One2many('orientation.rate.line.all', 'rate_id', string='Rate question',default=_line_item_all)
	rate_hr_ids = fields.One2many('orientation.rate.line.hr', 'rate_id', string='Rate question',default=_line_item_hr)
	rule_ids = fields.One2many('orientation.rule.line', 'rate_id', string='Rate question',default=_line_rule)
	rate_ids = fields.One2many('orientation.rate.line', 'rate_id', string='Rate question',default=_line_rate_item)
	report_ids = fields.One2many('orientation.report.line', 'rate_id', string='Rate question')
	training_ids = fields.One2many('orientation.training.line', 'rate_id', string='Rate question',default=_line_training_item)
	meet_ids = fields.One2many('orientation.meet.line', 'rate_id', string='Rate question',default=_line_item_meet)
	shu_purpose = fields.Char('Сайжруулах шаардлагатай мэргэжлийн болон хувь хүний ур чадвар')
	hr_purpose1 = fields.Char('Хөтөлбөрийг цаашид сайжруулах таны санал, зөвлөмж')
	hr_purpose2 = fields.Char('Хөтөлбөрийн үе шатнаас ямар үйлчилгээг авч чадаагүй вэ?')
	hour_ids = fields.One2many('orientation.hour.line', 'rate_id', string='Цаг')
	
	rate_score1 = fields.Float('Нийт авсан удирдлангын үнэлгээ',compute='_compute_total_score',store=True)
	rate_score2 = fields.Float('Нийт авсан үнэлгээ нэгтгэл',compute='_compute_total_score',store=True)
	rate_score3 = fields.Float('Нийт авсан үнэлгээ тайлан',compute='_compute_total_score',store=True)
	rate_score4 = fields.Float('Нийт авсан үнэлгээ цаг ',compute='_compute_total_score',store=True)
	rate_score5 = fields.Float('Нийт авсан үнэлгээ 360 ',compute='_compute_total_score',store=True)
	rate_score6 = fields.Float('Нийт авсан үнэлгээ ХН ',compute='_compute_total_score',store=True)
	worked_hour = fields.Float('Нийт ажилласан цаг ',compute='_compute_total_score',store=True)
	ht_worked = fields.Float('Нийт АЗЦ ',compute='_compute_total_score',store=True)
	desc_360 = fields.Text(default='Бүрэн дүүрэн сэтгэл ханамжтай(1),  Сэтгэл ханамжтай(0.5),Хариулахад хүндрэлтэй(0),  Сэтгэл ханамжгүй(-0.5),  Ямарч сэтгэл ханамжгүй(-1)',string='Үнэлгээний тайлбар')
	desc_hr = fields.Text(default='Муу(1),  Дунд(2),  Дундаас дээгүүр(3),  Сайн(4),   Маш сайн(5)',string='Дасан зохицох хөтөлбөрийн үнэлгээ')

	percent = fields.Selection([
		('1','Муу(1)'),
		('2','Дунд(2)'),
		('3','Дундаас дээгүүр(3)'),
		('4','Сайн(4)'),
		('5','Маш сайн(5)'),
	], string='Үнэлгээ', tracking=True
	)
	
	def action_draft(self):
		self.write({'state': 'draft'})


	def create_hour_data(self):
		for item in self.hour_ids:
			hb_lin_id = self.env['hour.balance.dynamic.line'].search([('month','=',item.month),('year','=',str(self.date.year)),('employee_id','=',self.employee_id.id),('state','=','done')],limit=1,order='date_to desc')
			item.update({
				'hour_to_work':hb_lin_id.hour_to_work_month,
				'worked_hour': hb_lin_id.total_worked_hour,
			})


	def create_emp_data(self):
		trainee_line_id = self.env['trainee.emp.line']
		for item in self.rate_all_ids:
			trainee_id = self.env['trainee.emp.line'].search([('question_id','=',item.question_id.id),('employee_id','=',self.employee_id.id)])
			emp_id = self.env['hr.employee'].search([('id','=',self.employee_id.id)],limit=1)
			if not  trainee_id:
				trainee_line_id.create({
					'employee_id':emp_id.id,
					'question_id':item.question_id.id,
					'score': item.score,
					'get_score':item.get_score,
				})
			else:
				raise UserError('%s Үүссэн давхардаж байна' % item.question_id.name)

	def compute_all_score(self):
		for item in self.rate_all_ids:
			if item.type=='type1':
				item.update({
					'get_score':self.rate_score1,
				})
			if item.type=='type2':
				item.update({
					'get_score':self.rate_score5,
				})
			if item.type=='type3':
				item.update({
					'get_score':self.rate_score4,
				})
			if item.type=='type4':
				item.update({
					'get_score':self.rate_score3,
				})

	@api.depends('rate_ids','rate_report_ids','rate_all_ids.score','rate_all_ids.get_score','hour_ids','hour_ids.get_score','rate_ids_360')
	def _compute_total_score(self):
		for item in self:
			rate_score1=0
			rate_score2=0
			rate_score3=0
			rate_score4=0
			rate_score5=0
			rate_score6=0
			worked_hour=0
			hour_to_work=0
			if item.rate_ids:
				rate_score1 = sum(item.rate_ids.mapped('get_score'))
			if item.rate_all_ids:
				score = sum(item.rate_all_ids.mapped('score'))
				if score>0:
					rate_score2 = (sum(item.rate_all_ids.mapped('get_score')) * 100)/score
			if item.rate_report_ids:
				rate_score3 = sum(item.rate_report_ids.mapped('get_score'))
			if item.hour_ids:
				lens =  len(item.hour_ids)
				rate_score4 = sum(item.hour_ids.mapped('get_score'))/lens
				worked_hour = sum(item.hour_ids.mapped('worked_hour'))
				hour_to_work = sum(item.hour_ids.mapped('hour_to_work'))
			if item.rate_ids_360:
				rate_score5 = sum(item.rate_ids_360.mapped('sum_get_score'))
			if item.rate_hr_ids:
				lens =  len(item.rate_hr_ids)
				rate_score6 = sum(item.rate_hr_ids.mapped('get_score'))/lens
			item.rate_score1=rate_score1
			item.rate_score2=rate_score2
			item.rate_score3=rate_score3
			item.rate_score4=rate_score4
			item.rate_score5=rate_score5
			item.rate_score6=rate_score6
			item.ht_worked= hour_to_work
			item.worked_hour= worked_hour


class OrientationChecklistRequest(models.Model):
	_inherit = 'orientation.request'
	

	sequence = fields.Integer('Дугаарлалт')
	
class OrientationRate(models.Model):
	_inherit = 'orientation.rate.line'
	
	sequence = fields.Integer('Дугаарлалт')
	score = fields.Integer('Авбал зохих оноо')
	get_score = fields.Float('Авсан оноо')
	
class OrientationRate360(models.Model):
	_name = 'orientation.rate.line360'
	_description = "Orientation Rate360"
	
	question_id = fields.Many2one('rate.question',string='Үнэлгээ')
	rate_id = fields.Many2one('employee.orientation',string='Rate')
	sequence = fields.Integer('Дугаарлалт')
	get_score1 = fields.Float('Үнэлгээ 1')
	get_score2 = fields.Float('Үнэлгээ 2')
	get_score3 = fields.Float('Үнэлгээ 3')
	get_score4 = fields.Float('Үнэлгээ 4')
	sum_get_score = fields.Float('Нийт',compute='_compute_get_score',store=True)
	percent = fields.Selection([
		('1','Бүрэн дүүрэн сэтгэл ханамжтай(1)'),
		('0.5','Сэтгэл ханамжтай(0.5)'),
		('0','Хариулахад хүндрэлтэй(0)'),
		('-0.5','Сэтгэл ханамжгүй(-0.5)'),
		('-1','Ямарч сэтгэл ханамжгүй(-1)'),
	], string='Үнэлгээ', tracking=True
	)

	@api.depends('get_score1','get_score2','get_score3','get_score4')
	def _compute_get_score(self):
		for item in self:
			sum_get_score=0
			if item.get_score1:
				sum_get_score+=item.get_score1
			if item.get_score2:
				sum_get_score+=item.get_score2
			if item.get_score3:
				sum_get_score+=item.get_score3
			if item.get_score4:
				sum_get_score+=item.get_score4
			item.sum_get_score = sum_get_score
	
class OrientationRateReport(models.Model):
	_name = 'orientation.rate.line.report'
	_description = "Orientation Rate Report"
	
	question_id = fields.Many2one('rate.question',string='Үнэлгээ')
	rate_id = fields.Many2one('employee.orientation',string='Rate')
	sequence = fields.Integer('Дугаарлалт')
	score = fields.Integer('Авбал зохих оноо')
	get_score = fields.Float('Авсан оноо')
	desc = fields.Char('Тайлбар')
	
class OrientationRateAll(models.Model):
	_name = 'orientation.rate.line.all'
	_description = "Orientation Rate All"
	
	question_id = fields.Many2one('rate.question',string='Асуулга')
	rate_id = fields.Many2one('employee.orientation',string='Rate')
	sequence = fields.Integer('Дугаарлалт')
	score = fields.Integer('Авбал зохих оноо')
	get_score = fields.Float('Авсан оноо')
	desc = fields.Char('Тайлбар')
	type = fields.Selection([
		('type1','Шууд удирдлагын үнэлгээ'),
		('type2','360 градусын үнэлгээ'),
		('type3','Ирц бүртгэл'),
		('type4','Ажлын тайлангийн үнэлгээ')
	], string='Төрөл', tracking=True
	)
	
class OrientationRateHR(models.Model):
	_name = 'orientation.rate.line.hr'
	_description = "Orientation Rate All"
	
	question_id = fields.Many2one('rate.question',string='Асуулга')
	rate_id = fields.Many2one('employee.orientation',string='Rate')
	sequence = fields.Integer('Дугаарлалт')
	get_score = fields.Float('Авсан оноо')
	percent = fields.Selection([
		('1','Муу(1)'),
		('2','Дунд(2)'),
		('3','Дундаас дээгүүр(3)'),
		('4','Сайн(4)'),
		('5','Маш сайн(5)'),
	], string='Үнэлгээ', tracking=True
	)

class OrientationRuleLine(models.Model):
	_name = 'orientation.rule.line'
	_description = "Orientation Rule line"
	
	rate_id = fields.Many2one('employee.orientation',string='Rate')
	rule_id = fields.Many2one('orientation.rule',string='Дүрэм')
	sequence = fields.Integer('Дугаарлалт')
	is_check = fields.Selection([('Тийм','Тийм'),('Үгүй','Үгүй')],'Танилцсан эсэх')
	
class OrientationReportLine(models.Model):
	_name = 'orientation.report.line'
	_description = "Orientation Rule line"
	
	rate_id = fields.Many2one('employee.orientation',string='Rate')
	task = fields.Char('Туршилтын хугацаанд хийх ажлууд')
	period = fields.Char('Хугацаа')
	evaluation = fields.Char('Гүйцэтгэлийн шалгуур үзүүлэлт')
	score = fields.Float('Өөрийн үнэлгээ')
	get_score = fields.Float('Удирдлагын үнэлгээ')
	sequence = fields.Integer('Дугаарлалт')
	
class OrientationMeetLine(models.Model):
	_name = 'orientation.meet.line'
	_description = "Orientation Meet line"
	
	rate_id = fields.Many2one('employee.orientation',string='Rate')
	question_id = fields.Many2one('rate.question',string='Асуулт')
	evaluation = fields.Char('Тэмдэглэл')
	sequence = fields.Integer('Дугаарлалт')
	type = fields.Selection([
		('type1','Шууд удирдлагын үнэлгээ'),
		('type2','360 градусын үнэлгээ'),
		('type3','Ирц бүртгэл'),
		('type4','Ажлын тайлангийн үнэлгээ'),
		('type5','Уулзалтын тэмдэглэл')
	], string='Нэгдсэн үнэлгээний төрөл', tracking=True
	)
	
class RateQuestion(models.Model):
	_inherit = 'rate.question'
	
	score = fields.Integer('Авбал зохих оноо')
	type_n = fields.Selection([('type1','Удирдлагын үнэлгээ'),('type2','360 үнэлгээ'),('type3','Ажлын тайлан'),('type4','Нэгдсэн үнэлгээ'),('type5','ХН-ийг үнэлэх'),('type6','Уулзалтын тэмдэглэл')],'Төрөл')
	type = fields.Selection([
		('type1','Шууд удирдлагын үнэлгээ'),
		('type2','360 градусын үнэлгээ'),
		('type3','Ирц бүртгэл'),
		('type4','Ажлын тайлангийн үнэлгээ'),
		
	], string='Нэгдсэн үнэлгээний төрөл', tracking=True
	)
	

class OrientationRule(models.Model):
	_name = 'orientation.rule'
	_description = "Orientation Rule"
	_inherit = 'mail.thread'

	name = fields.Char(string='Нэр',required=True)
	type_n = fields.Selection([('type1','Уншиж танилцсан байх дүрэм журмууд '),('type2','Тухайн нэгжийн чиг үүргийн дагуу уншиж судлах дүрэм, журам, зааврууд')],'Төрөл')
	

class OrientationTrainingLine(models.Model):
	_name = 'orientation.training.line'
	_description = "Orientation Training Line"
	_inherit = 'mail.thread'
	
	training_id = fields.Many2one('employee.training','Сургалт')
	rate_id = fields.Many2one('employee.orientation',string='Rate')
	period= fields.Char('Хугацаа')
	idea= fields.Char('Агуулга')
	type_n = fields.Selection([('Танилцуулга, зааварчилгаа','Танилцуулга, зааварчилгаа'),('Танилцуулга','Танилцуулга'),('Танилцуулга, асуулт хариулт','Танилцуулга, асуулт хариулт'),('Асуумжийн хуудас бөглүүлэх','Асуумжийн хуудас бөглүүлэх')],'Сургалтын хэлбэр')
	user_id = fields.Many2one('res.users', string='Хариуцах ажилтан', size=32, required=True)
	date_from = fields.Datetime(string="Эхлэх")
	date_to = fields.Datetime(string="Дуусах")
	sequence = fields.Integer('Дугаарлалт')
	check = fields.Selection([('Хамрагдсан','Хамрагдсан'),('Хамрагдаагүй','Хамрагдаагүй')],'Хамрагдсан эсэх')


class EmployeeTraining(models.Model):
	_inherit = 'employee.training'
	
	rate_id = fields.Many2one('employee.orientation',string='Rate')
	period= fields.Char('Хугацаа')
	idea= fields.Char('Агуулга')
	type_n = fields.Selection([('Танилцуулга, зааварчилгаа','Танилцуулга, зааварчилгаа'),('Танилцуулга','Танилцуулга'),('Танилцуулга, асуулт хариулт','Танилцуулга, асуулт хариулт'),('Асуумжийн хуудас бөглүүлэх','Асуумжийн хуудас бөглүүлэх')],'Сургалтын хэлбэр')
	

class OrientationHourLine(models.Model):
	_name = 'orientation.hour.line'
	_description = "Orientation Hour Line"
	_inherit = 'mail.thread'

	rate_id = fields.Many2one('employee.orientation',string='Rate')
	hour_to_work= fields.Float("Ажиллавал зохих цаг", digits=(2, 0))
	worked_hour = fields.Float("Ажилласан цаг", digits=(3, 2))
	score = fields.Integer('Авбал зохих оноо',default=20)
	get_score = fields.Float('Авсан оноо',compute='_compute_get_score',store=True)
	sequence = fields.Integer('Дугаарлалт')
	month = fields.Selection(
		[
			("1", "1 сар"),
			("2", "2 сар"),
			("3", "3 сар"),
			("4", "4 сар"),
			("5", "5 сар"),
			("6", "6 сар"),
			("7", "7 сар"),
			("8", "8 сар"),
			("9", "9 сар"),
			("90", "10 сар"),
			("91", "11 сар"),
			("92", "12 сар"),
		],"Ажилласан сар",
	)


	@api.depends('score','hour_to_work','worked_hour')
	def _compute_get_score(self):
		for item in self:
			get_score=0
			if item.hour_to_work and item.score and item.worked_hour:
				get_score = (item.worked_hour * item.score)/item.hour_to_work
				if get_score>item.score:
					get_score=item.score
			item.get_score = get_score
	

	
class TraineeEmpLine(models.Model):
	_inherit = 'trainee.emp.line'

	question_id = fields.Many2one('rate.question',string='Үнэлгээ')