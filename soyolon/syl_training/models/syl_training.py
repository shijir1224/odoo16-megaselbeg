from odoo import api, fields, models, _
import datetime
from datetime import  datetime, timedelta

class TrainingRequest(models.Model):
	_inherit = 'training.request'

	is_need = fields.Boolean(
		'Сургалт хэрэгтэй эсэх', default=False, tracking=True)
	process = fields.Text(
		'2', tracking=True)
	process_def = fields.Text(
		's', tracking=True)
	topic = fields.Char('Сургалтын сэдэв', tracking=True)
	name_id = fields.Many2one(
		'training.register', 'Сургалтын сэдэв', tracking=True, required=True)
	result = fields.Text('Хүлээж буй үр дүн', tracking=True)
	tr_time = fields.Integer('Сургалтын цаг', tracking=True)
	tr_date = fields.Date('Сургалтын огноо', tracking=True)
	emp_count = fields.Integer(
		'Хүний тоо', compute='_compute_employee_line_ids')
	mentor = fields.Text('1')
	req_type = fields.Selection([
		('a', 'Суурь ур чадварын хүрээнд нэмэгдүүлэх сургалт'),
		('b', 'Мэргэжлийн ур чадварыг нэмэгдүүлэх сургалт'),
		('c', 'Хөдөлмөрийн аюулгүй байдал, эрүүл ахиун сургалт'),
		('d', 'Бусад сургалт')
	], string='Сургалтын төрөл', tracking=True)
	type = fields.Selection([('in', 'Дотоод'), ('out', 'Гадаад'),('abroad', 'Гадаад улсын')], 'Сургалтын ангилал', tracking=True)
	req_text = fields.Char('Сургалтын хэрэгцээ', tracking=True)
	fi_season = fields.Boolean(
		'1-р улирал', default=False, tracking=True)
	s_season = fields.Boolean(
		'2-р улирал', default=False, tracking=True)
	t_season = fields.Boolean(
		'3-р улирал', default=False, tracking=True)
	fo_season = fields.Boolean(
		'4-р улирал', default=False, tracking=True)
	month_o = fields.Boolean(
		'1 сар', default=False, tracking=True)
	month_tw = fields.Boolean(
		'2 сар', default=False, tracking=True)
	month_th = fields.Boolean(
		'3 сар', default=False, tracking=True)
	month_fo = fields.Boolean(
		'4 сар', default=False, tracking=True)
	month_fi = fields.Boolean(
		'5 сар', default=False, tracking=True)
	month_si = fields.Boolean(
		'6 сар', default=False, tracking=True)
	month_se = fields.Boolean(
		'7 сар', default=False, tracking=True)
	month_e = fields.Boolean(
		'8 сар', default=False, tracking=True)
	month_n = fields.Boolean(
		'9 сар', default=False, tracking=True)
	month_te = fields.Boolean(
		'10 сар', default=False, tracking=True)
	month_el = fields.Boolean(
		'11 сар', default=False, tracking=True)
	month_twl = fields.Boolean(
		'12 сар', default=False, tracking=True)

	ask_skill = fields.Text(
		'Б', tracking=True)
	ask_skill_two = fields.Text(
		's', tracking=True)

	@api.depends('employee_ids')
	def _compute_employee_line_ids(self):
		for item in self:
			if item.employee_ids:
				item.emp_count = len(item.employee_ids)
			else:
				item.emp_count = ''

	def name_get(self):
		res = []
		for obj in self:
			if obj.name_id:
				res.append((obj.id, obj.name_id.name))
		return res


class TrainingPlan(models.Model):
	_inherit = "training.plan"

	tr_count = fields.Integer('Сургалтын тоо',compute='_compute_line_ids')
	full_amount = fields.Float('Нийт төсөв', compute='_compute_sum_amount', store=True)
	all_employee = fields.Integer('Хүний тоо', compute='_compute_emp_count', store=True)
	all_time = fields.Integer('Нийт цаг', compute='_compute_emp_time', store=True)
	name_id = fields.Many2one('training.request', 'Сургалтын нэр', tracking=True)
	desc = fields.Text('Товч мэдээлэл')

	@api.depends('line_ids')
	def _compute_line_ids(self):
		for item in self:
			if item.line_ids:
				item.tr_count = len(item.line_ids)
			else:
				item.tr_count = ''

	@api.depends('line_ids.budget')
	def _compute_sum_amount(self):
		for item in self:
			item.full_amount = sum(item.line_ids.mapped('budget'))

	@api.depends('line_ids.employee_count')
	def _compute_emp_count(self):
		for item in self:
			item.all_employee = sum(item.line_ids.mapped('employee_count'))

	@api.depends('line_ids.emp_time')
	def _compute_emp_time(self):
		for item in self:
			item.all_time = sum(
				item.line_ids.mapped(str('emp_time')))

	def create_plan_line(self):
		if self.line_ids:
			self.line_ids.unlink()
		requests = self.env['training.request'].search([('year', '=', self.year),('state', '=', 'done')])
		for rec in requests:
			e_ids = rec.employee_ids.mapped('id')
			line_line_id = self.env['training.plan.line'].create({
				'parent_id': self.id,
				'department_id': rec.department_id.id,
				'name_ids': rec.id,
				'name_id': rec.name_id.id,
				'req_type':rec.req_type,
				'company_id': rec.company_id.id,
				'employee_count': rec.emp_count,
				'type': rec.type,
				'tr_date': rec.tr_date,
				'month_o': rec.month_o,
				'month_tw': rec.month_tw,
				'month_th': rec.month_th,
				'month_fo': rec.month_fo,
				'month_fi': rec.month_fi,
				'month_si': rec.month_si,
				'month_se': rec.month_se,
				'month_e': rec.month_e,
				'month_n': rec.month_n,
				'month_te': rec.month_te,
				'month_el': rec.month_el,
				'month_twl': rec.month_twl,
				'employee_ids': e_ids,
				'fi_season':rec.fi_season,
				's_season':rec.s_season,
				't_season':rec.t_season,
				'fo_season':rec.fo_season,

			})


class TrainingPLanLine(models.Model):
	_inherit = 'training.plan.line'

	def name_get(self):
		res = []
		for obj in self:
			if obj.name_id:
				res.append((obj.id, obj.name_id.name))
		return res

	type = fields.Selection([('in', 'Дотоод'),('out', 'Гадаад'),('emp', 'Ажилтан өөрөө бие даан'),('abroad', 'Мэдлэг хуваалцах')], 'Сургалтыг хаанаас авах', tracking=True)
	emp_time = fields.Integer('Нийт цаг')
	employee_count = fields.Integer('Хүний тоо')
	emp_each_time = fields.Integer('Хүн цаг', compute='_compute_emp_time')
	each_amount = fields.Float('Нэгж үнэ',  digits=(16, 2))
	budget = fields.Float('Төсөв', compute='_compute_budget', digits=(16, 2))
	teacher = fields.Char('Сургагч багш')
	desc = fields.Char('Тайлбар')
	tr_date = fields.Date('Огноо', tracking=True)
	employee_ids = fields.Many2many('hr.employee',string='Оролцох ажилчид')
	fi_season = fields.Boolean('1-р улирал', default=False, tracking=True)
	s_season = fields.Boolean('2-р улирал', default=False, tracking=True)
	t_season = fields.Boolean('3-р улирал', default=False, tracking=True)
	fo_season = fields.Boolean('4-р улирал', default=False, tracking=True)
	month_o = fields.Boolean('1', default=False, tracking=True)
	month_tw = fields.Boolean('2', default=False, tracking=True)
	month_th = fields.Boolean('3', default=False, tracking=True)
	month_fo = fields.Boolean('4', default=False, tracking=True)
	month_fi = fields.Boolean('5', default=False, tracking=True)
	month_si = fields.Boolean('6', default=False, tracking=True)
	month_se = fields.Boolean('7', default=False, tracking=True)
	month_e = fields.Boolean('8', default=False, tracking=True)
	month_n = fields.Boolean('9', default=False, tracking=True)
	month_te = fields.Boolean('10', default=False, tracking=True)
	month_el = fields.Boolean('11', default=False, tracking=True)
	month_twl = fields.Boolean('12', default=False, tracking=True)
	req_id = fields.Char('Хүний тоо', tracking=True)
	name_ids = fields.Many2one('training.request', 'Сургалтын сэдэв', tracking=True)
	req_type = fields.Selection([
		('a', 'Суурь ур чадварын хүрээнд нэмэгдүүлэх сургалт'),
		('b', 'Мэргэжлийн ур чадварыг нэмэгдүүлэх сургалт'),
		('c', 'Хөдөлмөрийн аюулгүй байдал, эрүүл ахиун сургалт'),
		('d', 'Бусад сургалт')
	], string='Сургалтын төрөл', tracking=True)
	@api.depends('employee_count', 'each_amount', 'emp_time')
	def _compute_budget(self):
		for item in self:
			if item.employee_count and item.each_amount and not item.emp_time:
				item.budget = item.each_amount * item.employee_count
			elif item.emp_time and item.each_amount and not item.employee_count:
				item.budget = item.each_amount * item.emp_time
			elif item.emp_time and item.each_amount and item.employee_count:
				item.budget = item.each_amount * item.emp_time * item.employee_count
			else:
				item.budget = 0

	@api.depends('emp_time', 'budget')
	def _compute_emp_time(self):
		for item in self:
			if item.emp_time and item.budget:
				item.emp_each_time = item.budget / float(item.emp_time)
			else:
				item.emp_each_time = ''


class TrainingRegistrationParent(models.Model):
	_name = 'training.registration.parent'
	_description = 'Traing registration parent'

	name = fields.Char('Нэр')
	date = fields.Date('Огноо', tracking=True)
	line_ids = fields.One2many('training.registration', 'parent_id', 'Сургалт хөгжил')

	state = fields.Selection([('draft', 'Ноорог'),
							  ('done', u'Дууссан')], 'Төлөв', readonly=True, default='draft', tracking=True, copy=False)

	def action_done(self):
		self.write({'state': 'done'})

	def action_draft(self):
		self.write({'state': 'draft'})


	def create_line(self):
		if self.line_ids:
			self.line_ids.unlink()
		tr_registration = self.env['training.registration']
		tr_registration_line = self.env['training.registration.line']
		records_loc = self.env['training.plan.line'].search([('tr_date', '=', self.date)])
		for loc in records_loc:
			tr_registration = tr_registration.create({
				'name_id': loc.name_id.id,
				'type': loc.type,
				'company_id': loc.company_id.id,
				'cost':loc.budget,
				'parent_id': self.id,
				'is_plan':True,
				'plan_line_id':loc.id
			})
			for em in loc.employee_ids:
				tr_registration_line = tr_registration_line.create({
					't_employee_id': em.id,
					'job_id': em.job_id.id,
					'parent_id': tr_registration.id,
				})


class TrainingRegistration(models.Model):
	_inherit = 'training.registration'

	def name_get(self):
		res = []
		for item in self:
			if item.name_id:
				res_name = ' ['+item.name_id.name+']'
				if item.start_date:
					DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
					start_date = datetime.strptime(str(item.start_date), DATETIME_FORMAT)
					res_name = ' ['+item.name_id.name+']' + '  ' + str(start_date)
				res.append((item.id, res_name))
			else:
				res.append(res_name[0])
		return res

	t_type = fields.Selection([('a', 'Танхим'),('b', 'Цахим'),], string='Сургалтын хэлбэр', tracking=True)
	type = fields.Selection([('in', 'Дотоод'),('out', 'Гадаад'),('emp', 'Ажилтан өөрөө бие даан'),('abroad', 'Мэдлэг хуваалцах')], 'Сургалтыг хаанаас авах', tracking=True)
	job_ids = fields.Many2many('hr.job', string='Хамрах хүрээ')
	where = fields.Char('Хаана')
	place_id = fields.Many2one('training.place', 'Сургалт зохион байгуулах байгууллага', tracking=True)
	loc_id = fields.Many2one('training.location', 'Сургалт болох газар', tracking=True)
	name_id = fields.Many2one('training.register', 'Сургалтын сэдэв', tracking=True)
	plan_line_id = fields.Many2one('training.plan.line', 'Сургалтын төлөвлөгөө', tracking=True)
	train_name = fields.Char('Сургалтын нэр', tracking=True)
	is_plan = fields.Boolean('Төлөвлөгөөт эсэх')
	parent_id = fields.Many2one('training.registration.parent','parent')
   
	t_rate = fields.Float('Үнэлгээний дундаж хувь', compute='_compute_procent', tracking=True,store=True)
	att_procent = fields.Float('Ирцийн хувь', compute='_compute_att_procent', tracking=True,store=True)
	type_id = fields.Many2one('training.type',string='Сургалтын төрөл')
	
	# Ажилчид татах
	def set_conditions(self):
		conditions = ""
		if self.department_id:
			conditions = " and hd.id = %s" % self.department_id.id 
		if self.job_ids:
			conditions += " and hj.id in (" + ','.join(map(str, self.job_ids.ids))+")"
		return conditions

	def create_line(self):
		if self.line_ids:
			self.line_ids.unlink()

		balance_data_pool = self.env['training.registration.line']
		j_ids = self.job_ids.mapped('id')
		hj_ids = self.env['hr.job'].search([('id', 'in', j_ids)]).mapped('id')
		query = """SELECT
			he.id as emp_id,
			hj.id as hj_id,
			hd.id as hd_id
			FROM hr_employee he
			LEFT JOIN hr_job hj On hj.id=he.job_id
			LEFT JOIN hr_department hd On hd.id=he.department_id
			WHERE employee_type in ('employee','trainee','contractor') %s """ % (self.set_conditions())
		self.env.cr.execute(query)
		records_loc = self.env.cr.dictfetchall()
		for loc in records_loc:
			balance_data_pool = balance_data_pool.create({
				't_employee_id': loc['emp_id'],
				'job_id': loc['hj_id'],
				'parent_id': self.id,
			})

	@api.depends('line_ids.procent')
	def _compute_procent(self):
		for item in self:
			lens = len(self.line_ids)
			total_rate= sum(item.line_ids.mapped('procent'))
			if lens>0:
				item.t_rate = total_rate/lens
			else:
				item.t_rate = 0

	@api.depends('plan_employee_count','study_employee_count')
	def _compute_att_procent(self):
		for item in self:
			if item.plan_employee_count>0:
				item.att_procent = item.study_employee_count*100/item.plan_employee_count
			else:
				item.att_procent = 0
	# Үнэлгээ татах

	def create_rate_line(self):
		for rec in self.line_ids:
			vals = self.env['training.val'].search([('training_reg_id', '=', self.id), ('employee_id', '=', rec.t_employee_id.id)],limit=1)
			if vals:
				rec.update({
					'score': vals.t_rate,
					'val_id': vals.id,
				})


# Илгээх үед notification илгээх

	def action_to_sent(self):
		self.write({'state': 'sent'})

	def action_send_notification_(self):
		
		base_url = self.env['ir.config_parameter'].sudo(
		).get_param('web.base.url')
		action_id = self.env.ref('hr.view_employee_form').id
		subject_mail = u'СУРГАЛТЫН ЗАР'
		body = u"""<b><a target="_blank" href=%s/web#id=%s&view_type=form&model=training.registration&action=%s></a></b>" %s " сургалт нь %s газарт %s-нд зарлагдсан байна!""" % (base_url, self.id, action_id, self.name_id.name, self.loc_id.name, self.start_date)
		for receiver in self.line_ids:
			mail_obj = self.env['mail.mail'].sudo().create({
				'email_from': self.company_id.email,
				'email_to': receiver.t_employee_id.partner_id.email,
				'subject': subject_mail,
				'body_html': '%s' % body,
			})
			mail_obj.send()
		

class TrainingRegistrationLine(models.Model):
	_inherit = 'training.registration.line'

	score = fields.Integer('Үнэлгээ', tracking=True)
	val_id = fields.Many2one('training.val', 'Үнэлгээ харах', tracking=True)
	name_id = fields.Many2one('training.register', 'Сургалтын нэр',related='parent_id.name_id')
	subject = fields.Char('Тайлбар',related='parent_id.subject')
	start_date = fields.Datetime('Эхлэх огноо',related='parent_id.start_date')
	end_date = fields.Datetime('Дуусах огноо',related='parent_id.end_date')
	procent = fields.Float('Хувь',compute='_compute_score',store=True)
	department_id = fields.Many2one('hr.department','Хэлтэс',related='t_employee_id.department_id',store=True)

	@api.depends('score')
	def _compute_score(self):
		for item in self:
			if item.score>0:
				item.procent = item.score*100/5
			else:
				item.procent = 0


class TrainingPlace(models.Model):
	_name = 'training.place'
	_description = 'Traing place'

	type = fields.Char('Төрөл', tracking=True)
	address = fields.Char('Хаяг', tracking=True)
	phone = fields.Char('Утас', tracking=True)
	cost = fields.Char('Сургалтын чиглэл', tracking=True)
	name = fields.Char('Нэр', tracking=True)
	history = fields.Text('Түүх', tracking=True)

	def name_get(self):
		res = []
		for item in self:
			if item.type:
				res.append((item.id, item.type))
		return res
	
class TrainingLocation(models.Model):
	_name = 'training.location'
	_description = 'Traing location'

	name = fields.Char('Сургалт болох газар', tracking=True)

  

class TrainingVal(models.Model):
	_name = 'training.val'
	_description = 'Traing val'

	def _default_employee(self):
		return self.env.context.get('default_employee_id') or self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)

	# def name_get(self):
	#	 res = []
	#	 for item in self:
	#		 if item.t_rate:
	#			 res_name = '[' + item.t_rate+']' + ' ' + item.employee_id.name
	#			 res.append((item.id, res_name))
	#		 else:
	#			 res.append(res_name[0])
	#	 return res

	@api.model
	def _line_item(self):
		cons = self.env['training.ask'].search([])
		w = []
		for cc in cons:
			vals = {
				'parent_id': cc.id,
				'val_id': self.id
			}
			w.append(vals)
		return w

	type = fields.Char('Төрөл', tracking=True)
	employee_id = fields.Many2one('hr.employee', 'Ажилтан')
	job_id = fields.Many2one('hr.job', 'Албан тушаал')
	department_id = fields.Many2one('hr.department', 'Хэлтэс')
	create_date = fields.Date('Үүсгэсэн огноо', readonly=True, default=fields.Date.context_today)
	name_id = fields.Many2one('training.register', 'Сургалтын сэдэв', tracking=True)
	training_reg_id = fields.Many2one('training.registration', 'Сургалтын хөгжил', tracking=True)
	train_name = fields.Char('Сургалтын нэр', tracking=True)
	t_rate = fields.Integer('Дундаж оноо', compute='_compute_answers', tracking=True)
	tr_ask_ids = fields.One2many('training.ask.line', 'val_id', 'Үнэлгээ',  default=_line_item)
	ask_one = fields.Text('Цаашид ямар чиглэлээр сургалт авах саналтай байгаа талаараа бичнэ үү.', tracking=True)
	ask_two = fields.Text('Танд өөр санал шүүмжлэл, зөвлөмж байвал бидэнд харамгүй өгч тусална уу. Баярлалаа.', tracking=True)
	reg_line_id = fields.Many2one('training.registration.line', 'Үнэлгээ харах', tracking=True)


	@api.onchange('employee_id')
	def onchange_employee_id(self):
		if self.employee_id:
			self.job_id = self.employee_id.job_id.id
			self.department_id = self.employee_id.department_id.id

	def name_get(self):
		res = []
		for item in self:
			if item.type:
				res.append((item.id, item.type))
		return res

	@api.depends('tr_ask_ids.answers')
	def _compute_answers(self):
		for item in self:
			lens = len(self.tr_ask_ids)
			total_rate= sum(item.tr_ask_ids.mapped('answers'))
			if lens>0:
				item.t_rate = total_rate/lens
			else:
				item.t_rate = 0
			


class TrainingAsk(models.Model):
	_name = 'training.ask'
	_description = 'Traing val Ask'

	type = fields.Char('Асуулт', tracking=True)
	employee_id = fields.Many2one('hr.employee', string='Employee')
	department_id = fields.Many2one(
		'hr.department', string='Хэлтэс', tracking=True)
	job_id = fields.Many2one('hr.job', string='Албан тушаал', tracking=True)
	name_id = fields.Many2one(
		'training.register', 'Сургалтын сэдэв', tracking=True)
	tr_ask_ids = fields.One2many('training.ask.line', 'parent_id', 'Үнэлгээ')

	def name_get(self):
		res = []
		for item in self:
			if item.type:
				res.append((item.id, item.type))
		return res


class TrainingAskLine(models.Model):
	_name = 'training.ask.line'
	_description = 'Traing ask line'

	parent_id = fields.Many2one('training.ask', 'Үнэлгээний төрөл')
	val_id = fields.Many2one('training.val', 'Parent')
	answer = fields.Selection([('5', '5'),
							   ('4', '4'),
							   ('3', '3'),
							   ('2', '2'),
							   ('1', '1'),
							   ('0', '0'),], string='Оноо')
	answers = fields.Integer(
		'Оноо /Та 1-5 оноогоор үнэлнэ үү!/', required=True)

	ans_ten = fields.Text(
		'Танд өөр санал шүүмжлэл, зөвлөмж байвал бидэнд харамгүй өгч тусална уу. Баярлалаа.')

	def name_get(self):
		res = []
		for item in self:
			if item.type:
				res.append((item.id, item.type))
		return res
