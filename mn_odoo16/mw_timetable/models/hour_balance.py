# -*- coding: utf-8 -*-
import time
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval as eval

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"


class HourBalanceDynamic(models.Model):
	_name = "hour.balance.dynamic"
	_inherit = ["mail.thread", "mail.activity.mixin"]
	_description = "Hour Balance"
	_order = "year desc,month desc,department_id"

	def unlink(self):
		for bl in self:
			if bl.state != "draft":
				raise UserError(_("Ноорог төлөвтэй биш бол устгах боломжгүй."))
		return super(HourBalanceDynamic, self).unlink()

	def _default_employee(self):
		return self.env.context.get("default_employee_id") or self.env[
			"hr.employee"
		].search([("user_id", "=", self.env.uid)], limit=1)

	name = fields.Char("Нэр")
	year = fields.Char(store=True, type="char", string="Жил", size=8, required=True)
	day_to_work_month = fields.Float("Ажиллавал зохих өдөр", digits=(2, 0))
	hour_to_work_month = fields.Float("Ажиллавал зохих цаг", digits=(2, 0))
	date_from = fields.Date("Эхлэх огноо", default=time.strftime("%Y-%m-01"))
	date_to = fields.Date("Дуусах огноо")
	data = fields.Binary("Эксел файл")
	department_id = fields.Many2one("hr.department", "Хэлтэс")
	work_location_id = fields.Many2one(
		"hr.work.location", "Ажлын байршил", required=True
	)
	employee_id = fields.Many2one(
		"hr.employee", "Үүсгэсэн ажилтан", default=_default_employee, required=True
	)
	company_id = fields.Many2one(
		"res.company",
		string="Компани",
		required=True,
		default=lambda self: self.env.user.company_id,
	)
	balance_line_ids = fields.One2many(
		"hour.balance.dynamic.line", "parent_id", "Employee hour balance"
	)
	type = fields.Selection(
		[("final", "Сүүл"), ("advance", "Урьдчилгаа")], "Төрөл", required=True, default='advance'
	)
	state = fields.Selection(
		[
			("draft", "Ноорог"),
			("send", "Илгээсэн"),
			("confirm_ahlah", "ШУ баталсан"),
			("done", "НЯБО хүлээж авсан"),
			("refuse", "Цуцлагдсан"),
		],
		"Төлөв",
		readonly=True,
		default="draft",
		tracking=True,
		copy=False,
	)
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
		],
		"Сар",
		required=True,
	)
	is_htw_plan = fields.Boolean("АЗЦ төлөвлөгөөнөөс татах эсэх")
	register_import = fields.Boolean("Регистрээр импортлох")
	confirm_emp_id = fields.Many2one("hr.employee", "Баталсан")
	confirm_job_id = fields.Many2one(
		"hr.job", "Албан тушаал", related="confirm_emp_id.job_id"
	)
	employee_ids = fields.Many2many('hr.employee', string="Нэмэх ажилчид", domain="[('company_id', '=', company_id)]")

	def add_balance_employee(self):
		balance_pool =  self.env['hour.balance.dynamic.line']
		balance_line_pool =  self.env['hour.balance.dynamic.line.line']
		balance_line_hour_pool =  self.env['hour.balance.dynamic.line.line.hour']

		for obj in self.employee_ids:

			emp_ids = self.env['hr.employee'].search([('id','=',obj.id)])
			if emp_ids:
				cont_ids = self.env['hr.contract'].search([('employee_id','=',obj.id),('active','=',True)],limit=1)
				balance_data_ids = balance_pool.create({'employee_id':emp_ids.id,
						"year": self.year,
						"month": self.month,
						"day_to_work_month": self.day_to_work_month,
						"hour_to_work_month": self.hour_to_work_month,
						"parent_id": self.id,
						"identification_id": emp_ids.identification_id,
						"department_id": emp_ids.department_id.id,
						"job_id": emp_ids.job_id.id,
						# "sequence":sequence
						})
				for dd in balance_data_ids:
					conf_id = self.env['hour.balance.dynamic.configuration'].search([('company_id','=',self.company_id.id),('work_location_id','=',self.work_location_id.id)])
					for conf in conf_id:
						balance_line_pool = balance_line_pool.create({
							'parent_id':dd.id,
							"conf_id": conf.id,
							})
						balance_line_hour_pool = balance_line_hour_pool.create({
								'parent_id':dd.id,
								"conf_id": conf.id,
								})


	def action_cancel(self):
		for line in self.balance_line_ids:
			line.write({"state": "draft"})
		self.write({"state": "draft"})
	
	def action_draft(self):
		for line in self.balance_line_ids:
			line.write({"state": "draft"})
		self.write({"state": "draft"})

	def action_send(self):
		for line in self.balance_line_ids:
			line.write({"state": "send"})
		self.write({"state": "send"})

	def action_confirm_ahlah(self):
		for line in self.balance_line_ids:
			line.write({"state": "confirm_ahlah"})
		self.write({"state": "confirm_ahlah"})

	def action_done(self):
		for line in self.balance_line_ids:
			line.write({"state": "done"})
		self.write({"state": "done"})

	def create_conf(self, bp):
		if bp.balance_line_line_ids:
			bp.balance_line_line_ids.unlink()
		if bp.balance_line_line_hour_ids:
			bp.balance_line_line_hour_ids.unlink()
		conf_lines = self.env["hour.balance.dynamic.configuration"].search([('company_id','=',self.company_id.id)])
		for cl in conf_lines:
			if cl.work_location_id:
				if cl.work_location_id.id == self.work_location_id.id:
					self.create_query_tomyo(cl,bp)
			else:
				self.create_query_tomyo(cl,bp)

	def create_query_tomyo(self,cl,bp):
		balance_line_data_pool = self.env["hour.balance.dynamic.line.line"]
		balance_line_hour_data_pool = self.env["hour.balance.dynamic.line.line.hour"]
		hour = 0
		if cl.type == "query":
			if self.date_from and self.date_to:
				query_ex = cl.query % (
					bp.timetable_line_id.id,
					self.date_from,
					self.date_to,
				)
			self.env.cr.execute(query_ex)
			records = self.env.cr.dictfetchall()
			for rec in records:
				if rec["hour"]:
					hour = round(rec["hour"],2)
				else:
					hour = 0
				balance_line_pool = balance_line_data_pool.create(
					{"parent_id": bp.id, "hour": hour, "conf_id": cl.id,"hour_type": cl.hour_type}
				)
				balance_line_hour_pool = balance_line_hour_data_pool.create(
					{"parent_id": bp.id, "name": hour, "conf_id": cl.id,}
				)
		elif cl.type == "tomyo":
			localdict = {"bll": bp, "result": None}
			"resutl=basic*0.1 гм байна"
			tomyo = cl.type.tomyo.replace("нийт цаг", "cl.hour")
			if "/" in tomyo:
				try:
					eval("%s" % (tomyo), localdict, mode="exec", nocopy=True)
				except ValueError:
					raise Warning(
						(
							"%s ажилтны %s ийн томъёонд 0 өгөгдөл орсоноос алдаа гарлаа."
							% (cl.balance_pool.employee_id.name, cl.name)
						)
					)
			else:
				eval("%s" % (tomyo), localdict, mode="exec", nocopy=True)
			balance_line_pool = balance_line_data_pool.create(
				{"parent_id": bp.id, "hour": cl.hour, "conf_id": cl.id,"hour_type": cl.hour_type}
			)
			balance_line_hour_pool = balance_line_hour_data_pool.create({"parent_id": bp.id, "name": cl.hour, "conf_id": cl.id})
		elif cl.type == "both":
			self.create_conf_both(cl, bp, balance_line_data_pool)
		else:
			balance_line_pool =balance_line_data_pool.create(
				{"parent_id": bp.id, "hour": hour, "conf_id": cl.id,"hour_type": cl.hour_type}
			)
			balance_line_hour_pool = balance_line_hour_data_pool.create({"parent_id": bp.id, "name": hour, "conf_id": cl.id})

	def create_conf_both(self, cl, bp, balance_line_data_pool):
		balance_line_hour_data_pool = self.env["hour.balance.dynamic.line.line.hour"]
		hour=0
		hour2=0
		hour1=0
		if self.date_from and self.date_to:
			if cl.query:
				query_ex = cl.query % (
					bp.timetable_line_id.id,
					self.date_from,
					self.date_to,
				)
				self.env.cr.execute(query_ex)
				records = self.env.cr.dictfetchall()
			for rec in records:
				if rec["hour"]:
					hour = round(rec["hour"],2)
				else:
					hour = 0
				if 'hour2' in cl.query:
					if rec["hour2"]:
						hour2 = round(rec["hour2"],2)
					else:
						hour2 = 0
				if 'hour1' in cl.query:
					if rec["hour1"]:
						hour1 = round(rec["hour1"],2)
					else:
						hour1 = 0
				balance_line_pool = balance_line_data_pool.create({"parent_id": bp.id, "hour": hour, "conf_id": cl.id,"hour_type": cl.hour_type})

				balance_line_hour_pool = balance_line_hour_data_pool.create({"parent_id": bp.id, "name": hour,"conf_id": cl.id})
				if balance_line_pool:
					localdict={'line':balance_line_pool,'result':None,'htw':bp.hour_to_work_month,'hour':hour,'hour2':hour2,'hour1':hour1}
					tomyo=balance_line_pool.conf_id.tomyo
					if '/' in tomyo:
						try:
							eval('%s'%(tomyo), localdict, mode='exec', nocopy=True) 
						except ValueError:
							raise Warning((u'%s цагийн балансын мэдээлэл дээр 0 өгөгдөл орсоноос алдаа гарлаа'%(cl.name)))
					else:
						eval('%s' %(tomyo), localdict, mode='exec', nocopy=True)#  
						balance_line_pool.write({"hour":localdict['result']})
				if balance_line_hour_pool:
					localdict={'result':None,'htw':bp.hour_to_work_month,'hour':hour,'hour2':hour2,'hour1':hour1}
					tomyo=balance_line_hour_pool.conf_id.tomyo
					eval('%s' %(tomyo), localdict, mode='exec', nocopy=True)#  
					balance_line_hour_pool.write({"name":localdict['result']})
						

	def create_pool(self, bll, emp, htw, htd,sequence):
		balance_data_pool = self.env["hour.balance.dynamic.line"]
		
		bp = balance_data_pool.create(
			{
				"timetable_line_id": bll.id,
				"employee_id": emp.id,
				"year": self.year,
				"month": self.month,
				"day_to_work_month": htd,
				"hour_to_work_month": htw,
				"parent_id": self.id,
				"identification_id": emp.identification_id,
				"department_id": emp.department_id.id,
				"job_id": emp.job_id.id,
				"sequence":sequence
			}
		)
		
		self.create_conf(bp)

	def balance_line_create(self):
		timetable_data_pool = self.env["hr.timetable.line"].search(
			[("year", "=", self.year), ("month", "=", self.month)]
		)
		htw = 0
		htd = 0
		if self.balance_line_ids:
			self.balance_line_ids.unlink()
		sequence=1
		for bll in timetable_data_pool:
			if self.is_htw_plan == True:
				query = """SELECT sum(tl.hour_to_work) as hour
						FROM hr_timetable_line_line tl
						LEFT JOIN hr_timetable_line al ON al.id=tl.parent_id 
						WHERE al.id=%s and date>='%s' and date<='%s'
						""" % (
					bll.id,
					self.date_from,
					self.date_to,
				)
				self.env.cr.execute(query)
				records = self.env.cr.dictfetchall()
				if records[0]:
					htw = records[0]["hour"]
				else:
					htw = 0

				query_day = """SELECT count(tl.id) as count
						FROM hr_timetable_line_line tl
						LEFT JOIN hr_timetable_line al ON al.id=tl.parent_id 
						LEFT JOIN hr_shift_time sht ON sht.id=tl.shift_plan_id 
						WHERE al.id=%s and sht.is_work not in ('none','public_holiday','out') and date>='%s' and date<='%s'
						""" %(
					bll.id,
					self.date_from,
					self.date_to,
				)
				self.env.cr.execute(query_day)
				recs = self.env.cr.dictfetchall()
				if recs[0]:
					htd = recs[0]["count"]
				else:
					htd = 0
			else:
				htw = self.hour_to_work_month
				htd = self.day_to_work_month
			emp = self.env["hr.employee"].search(
				[
					("id", "=", bll.employee_id.id),
					("company_id", "=", self.company_id.id),
					("work_location_id", "=", self.work_location_id.id),
				],
				limit=1,
			)

			if self.department_id:
				if emp.department_id == self.department_id:
					self.create_pool(bll, emp, htw, htd,sequence)
					sequence+=1
			elif self.work_location_id:
				if emp.work_location_id.id == self.work_location_id.id:
					self.create_pool(bll, emp, htw, htd,sequence)
					sequence+=1
			else:
				emp_all = self.env["hr.employee"].search(
				[("id", "=", bll.employee_id.id),("company_id", "=", self.company_id.id)],
				limit=1,)
				self.create_pool(bll, emp_all, htw, htd,sequence)
				sequence+=1

	def _symbol(self, row, col):
		return self._symbol_col(col) + str(row + 1)

	def _symbol_col(self, col):
		excelCol = str()
		div = col + 1
		while div:
			(div, mod) = divmod(div - 1, 26)
			excelCol = chr(mod + 65) + excelCol
		return excelCol


class HourBalanceLineDynamic(models.Model):
	_name = "hour.balance.dynamic.line"
	_description = "Hour Balance Line"
	_inherit = ["mail.thread"]
	_order = "sequence,department_id"

	@api.onchange("employee_id")
	def onchange_employee_id(self):
		self.department_id = self.employee_id.department_id
		self.job_id = self.employee_id.job_id

	sequence = fields.Integer('Дугаар')
	parent_id = fields.Many2one("hour.balance.dynamic", "Balance", ondelete="cascade")
	balance_line_line_ids = fields.One2many(
		"hour.balance.dynamic.line.line", "parent_id", "Employee hour balance"
	)
	balance_line_line_hour_ids = fields.One2many(
		"hour.balance.dynamic.line.line.hour", "parent_id", "Employee hour balance"
	)
	year = fields.Char(
		store=True,
		type="char",
		related="parent_id.year",
		string="Жил",
	)
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
		],
		related="parent_id.month",
		store=True,
		string="Сар",
	)
	date_from = fields.Date("Эхлэх огноо", related="parent_id.date_from", store=True)
	date_to = fields.Date("Дуусах огноо", related="parent_id.date_to", store=True)

	employee_type = fields.Selection(related='employee_id.employee_type',string="Ажилтны төлөв",store=True)

	state = fields.Selection(
		[
			("draft", "Ноорог"),
			("send", "Илгээсэн"),
			("confirm_ahlah", "ШУ Баталсан"),
			("done", "НЯБО хүлээж авсан"),
			("refuse", "Цуцлагдсан"),
		],
		"Төлөв",
		readonly=True,
		tracking=True,
		copy=False,
		related="parent_id.state",
	)

	description = fields.Char("Тайлбар", size=150)
	employee_id = fields.Many2one("hr.employee", "Ажилтан", required=True)
	identification_id= fields.Char('Ажилтны код', readonly='1',related='employee_id.identification_id')
	timetable_line_id = fields.Many2one("hr.timetable.line", "Timetable line")
	identification_id = fields.Char(
		"Код", related="employee_id.identification_id", store=True
	)
	department_id = fields.Many2one("hr.department", string="Нэгж")
	job_id = fields.Many2one("hr.job", string="Албан тушаал")
	day_to_work_month = fields.Float("Ажиллавал зохих өдөр", digits=(2, 0))
	hour_to_work_month = fields.Float("Ажиллавал зохих цаг", digits=(2, 0))

	att_procent = fields.Float(
		"Ирцийн хувь",
		digits=(3, 1),
		default=0,compute='_compute_att_procent',
		store=True,
	)

	@api.depends("hour_to_work_month")
	def _compute_att_procent(self):
		for obj in self:
			line_line_id = self.env["hour.balance.dynamic.line.line"].search(
				[
					("parent_id", "=", obj.id),
					("hour_type", "=", "working"),
				],
				limit=1,
			)
			if line_line_id.hour and obj.hour_to_work_month:
				obj.att_procent = line_line_id.hour * 100 / obj.hour_to_work_month
			else:
				obj.att_procent = 0

class HourBalanceDynamicLineLine(models.Model):
	_name = "hour.balance.dynamic.line.line"
	_description = "Hour Balance Line Line"
	_inherit = ["mail.thread", "mail.activity.mixin"]
	_order = "number"

	parent_id = fields.Many2one(
		"hour.balance.dynamic.line", "Balance", ondelete="cascade",index=True)
	employee_id = fields.Many2one(
		"hr.employee", "Ажилтан", related="parent_id.employee_id", store=True
	)
	date_from = fields.Date("Эхлэх огноо", related="parent_id.date_from", store=True)
	date_to = fields.Date("Дуусах огноо", related="parent_id.date_to", store=True)
	conf_id = fields.Many2one(
		"hour.balance.dynamic.configuration", "Configuration", ondelete="cascade",
	index=True)
	number = fields.Integer("Дугаар", related="conf_id.number", store=True,index=True)
	name = fields.Char("Нэр", related="conf_id.name", store=True)
	hour = fields.Float("Цаг", digits=(3, 2), default=0)
	company_id = fields.Many2one(
		"res.company", string="Компани", related="conf_id.company_id"
	)
	hour_type = fields.Selection(
		[("working", "Ажилласан цаг"),("working_day", "Ажилласан өдөр"),("overtime", "Илүү цаг"),
		],
		"Цагийн төрөл",
		tracking=True,
	)
	def write(self,vals):
		res = super(HourBalanceDynamicLineLine, self).write(vals)
		for obj in self:
			if obj.hour:
				message = """
					<!DOCTYPE html>
					<html>
					<style>
						li::marker {
							font-weight: bold;
							color:black;
						}
					</style>
					<body>
						<ul>
							<li>
								<span>%s </span> : <span>%s </span> -> <span>%s </span>
							</li>
						</ul>
					</body>
					</html>
				""" %(obj.employee_id.name,obj.name, obj.hour)
				obj.parent_id.parent_id.message_post(body=message, subject='')
		return res
class HourBalanceDynamicLineLinehour(models.Model):
	_name = "hour.balance.dynamic.line.line.hour"
	_description = "Hour Balance Line Line"

	parent_id = fields.Many2one(
		"hour.balance.dynamic.line", "Balance", ondelete="cascade"
	)
	name = fields.Float("Цаг", compute='_compute_name')
	conf_id = fields.Many2one(
		"hour.balance.dynamic.configuration", "Configuration"
	)

	hr_contract_count = fields.Integer(string='Цалингийн гэрээний тоо')

	def _compute_name(self):
	
		for obj in self:
			bl_ll_id = self.env['hour.balance.dynamic.line.line'].search([('parent_id', '=', obj.parent_id.id),
			('conf_id','=',obj.conf_id.id)])
			obj.name = bl_ll_id.hour

class HourBalanceDynamicConfiguration(models.Model):
	_name = "hour.balance.dynamic.configuration"
	_description = "Hour Balance Line Line"
	_order = "number"
	_inherit = ["mail.thread"]

	number = fields.Integer("Дугаар", tracking=True)
	name = fields.Char("Нэр", tracking=True)
	hour = fields.Float("Цаг", digits=(3, 2), default=0, tracking=True)
	type = fields.Selection(
		[("query", "Query"), ("tomyo", "Томьёо"),("both", "Query,Томьёо"),("fixed", "Тогтмол")],
		"Төрөл",
		default="fixed",
		required=True,
		tracking=True,
	)
	active = fields.Boolean("Active", default=True, store=True, readonly=False)
	hour_type = fields.Selection(
		[
			("working", "Ажилласан цаг"),
			("working_day", "Ажилласан өдөр"),
			("overtime", "Илүү цаг"),
		],
		"Цагийн төрөл",
		tracking=True,
	)
	tomyo = fields.Text("Томьёо", tracking=True)
	query = fields.Text("Query", tracking=True)
	query2 = fields.Text("Query2", tracking=True)
	company_id = fields.Many2one(
		"res.company", string="Компани", default=lambda self: self.env.user.company_id
	)
	work_location_id = fields.Many2one("hr.work.location", "Ажлын байршил")
