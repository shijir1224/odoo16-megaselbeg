
from urllib.parse import uses_fragment
from odoo import  api, fields, models, _
from datetime import datetime, timedelta
import time

class HseDangerousRegistration(models.Model):
	_name ='hse.dangerous.registration'
	_inherit = ["mail.thread", "mail.activity.mixin"]
	_description = 'Hse Dangerous Registration'
   
	name = fields.Char(string='Нэр', tracking=True)
	company_id = fields.Many2one('res.partner', string=' Компани', tracking=True)
	employee_id = fields.Many2one('hr.employee', string='Бүртгэл хөтөлсөн ажилтан', tracking=True)
	job_id = fields.Many2one(related='employee_id.job_id', string="Бүртгэл хөтөлсөн ажилтны албан тушаал")
	check_employee_id = fields.Many2one('hr.employee', string='Хянасан ажилтан', tracking=True)
	check_job_id = fields.Many2one(related='check_employee_id.job_id', string="Хянасан ажилтны албан тушаал")
	review = fields.Text(string='Тайлбар')
	dangerous_waste_ids = fields.One2many('hse.dangerous.waste', 'parent_id', string='Аюултай хог хаягдал')
	other_waste_ids = fields.One2many('hse.other.waste', 'parent_id', string='Бусад хог хаягдал')
	waste_con_ids = fields.One2many('hse.waste.con', 'parent_id', string='Үүнээс')
	simple_waste_ids = fields.One2many('hse.simple.waste', 'parent_id', string='Энгийн хог хаягдал')


class HseDangerousWaste(models.Model):
	_name ='hse.dangerous.waste'
	_description = 'Hse Dangerous Waste'
	_inherit = ["mail.thread", "mail.activity.mixin"]
   
	parent_id = fields.Many2one('hse.dangerous.registration', string='Хог хаягдал бүртгэл') 
	date = fields.Date(string='Огноо', default=fields.Date.context_today, tracking=True, required=True)
	air_filter = fields.Float(string='Агаар шүүгч',)
	oil_filter = fields.Float(string='Тосны шүүр',)
	trash_box = fields.Float(string='Хаягдал сав, торх(поошиг)',)
	culyator = fields.Float(string='Аккумулятор',)
	trash_tire = fields.Float(string='Хаягдал дугуй',)
	clean_material = fields.Float(string='Арчих материал/даавуу/',)
	fire_ballon = fields.Float(string='Галын хорны баллон',)
	air_ballon = fields.Float(string='Хийн баллон',)
	battery = fields.Float(string='Баттерей',)
	trash_oil = fields.Float(string='Хаягдал тос, масло',)
	hospital_waste = fields.Float(string='Эмнэлгийн хаягдал',)


class HseOtherWaste(models.Model):
	_name ='hse.other.waste'
	_description = 'Hse Other Waste'
	_inherit = ["mail.thread", "mail.activity.mixin"]
   
	parent_id = fields.Many2one('hse.dangerous.registration', string='Эцэг', index=True) 
	date = fields.Date(string='Огноо', default=fields.Date.context_today, tracking=True, required=True)
	iron = fields.Float(string='Төмөр',)
	tree = fields.Float(string='Мод',)
	car_parts = fields.Float(string='Авто машины эд анги',)

class HseWasteCon(models.Model):
	_name ='hse.waste.con'
	_description = 'Hse Waste Con'
	_inherit = ["mail.thread", "mail.activity.mixin"]
   
	parent_id = fields.Many2one('hse.dangerous.registration', string='Эцэг', index=True)
	date = fields.Date(string='огноо',  default=fields.Date.context_today,)
	date_to = fields.Date(string='Эхлэх огноо', default=time.strftime('%Y-%m-01'), tracking=True, required=True)
	date_from = fields.Date(string='Дуусах огноо',  default=fields.Date.context_today, tracking=True, required=True)
	baked = fields.Float(string='Шатаасан')
	centralized_waste = fields.Float(string='Хог хаягдлын төвлөрсөн цэгт нийлүүлсэн')
	recycle_plant = fields.Float(string='Дахин боловсруулах үйлдвэрт нийлүүлсэн')
	savings = fields.Float(string='Хадгалж байгаа')

class HseSimpleWaste(models.Model):
	_name ='hse.simple.waste'
	_description = 'Hse Simple Waste'
	_inherit = ["mail.thread", "mail.activity.mixin"]
   
	parent_id = fields.Many2one('hse.dangerous.registration', string='Эцэг', index=True) 
	date = fields.Date(string='Огноо', default=fields.Date.context_today, tracking=True, required=True)
	paper = fields.Float(string='Цаас')
	plastic = fields.Float(string='Хуванцар')
	glass = fields.Float(string='Шил')
	food_trash = fields.Float(string='Хоолны үлдэгдэл')
	food_waste = fields.Float(string='Хүнсний хаягдал')
	can = fields.Float(string='Лааз')
	card_paper = fields.Float(string='Картон цаас')
	ash = fields.Float(string='Үнс')
	const_waste = fields.Float(string='Барилгын хаягдал')
	others = fields.Float(string='Бусад')


