# -*- coding: utf-8 -*-

from odoo import tools
from odoo import api, fields, models
from odoo.addons.mw_technic_equipment.models.technic_equipment import OWNER_TYPE

class TechnicTireCountPivotReport(models.Model):
	_name = "technic.tire.count.pivot.report"
	_description = "Technic Tire Count Pivot Report"
	_inherit = ["analytic.mixin","mail.thread", "mail.activity.mixin"]
	_auto = False
	_order = 'technic_id'

	technic_id = fields.Many2one('technic.equipment', string=u'Техник', readonly=True,)
	owner_type = fields.Selection(OWNER_TYPE,
		string=u'Эзэмшлийн төрөл', )

	tire_counts = fields.Integer(string=u'Нийт дугуйн тоо', default=0)
	current_counts = fields.Integer(string='Дугуйны тоо', default=0)
	less_counts = fields.Integer(string='Дутуу тоо', default=0)
	is_less_tire = fields.Selection([
		('no','Дутуу'),
		('yes','Бүрэн')], string='Бүрэн эсэх', )

	state = fields.Selection([
		('draft','Draft'),
		('stopped','Stopped'),
		('working','Working'),
		('parking','Parking'),
		('repairing','Repairing'),
		('inactive',u'Актласан')],
		string='Төлөв', default='draft', tracking=True)

	def init(self):
		tools.drop_view_if_exists(self.env.cr, self._table)
		self.env.cr.execute("""CREATE or REPLACE VIEW %s as (
			SELECT  
				tt.id as id,
				tt.id as technic_id,
				tt.owner_type as owner_type,
				tt.tire_counts as tire_counts,
				(select count(ll.id) from technic_tire_line as ll where ll.technic_id = tt.id) as current_counts,
				tt.tire_counts-(select count(ll.id) from technic_tire_line as ll where ll.technic_id = tt.id) as less_counts,
				CASE WHEN (select count(ll.id) from technic_tire_line as ll where ll.technic_id = tt.id) < tt.tire_counts THEN 'no' ELSE 'yes' END as is_less_tire,
				tt.state as state
			FROM technic_equipment as tt
			WHERE tt.tire_counts > 0 and 
			      tt.rubber_tired = 't'and 
                  tt.technic_type in ('dump','loader','grader') and tt.owner_type = 'own_asset'
		)""" % self._table)

class TechnicTirePivotReport(models.Model):
	_name = "technic.tire.pivot.report"
	_description = "Technic Tire Pivot Report"
	_auto = False
	_order = 'tire_id, current_technic_id'

	branch_id = fields.Many2one('res.branch', string=u'Салбар', readonly=True,)
	tire_id = fields.Many2one('technic.tire', string=u'Дугуй', readonly=True,)
	date_of_record = fields.Date(u'Эхэлсэн огноо', readonly=True, )
	date_of_manufactured = fields.Date(u'Үйлдвэрлэсэн', readonly=True, )
	date_of_retired = fields.Date(u'Актласан огноо', readonly=True, )
	serial_number = fields.Char(string='Сериал дугаар', readonly=True,)
	tire_setting_id = fields.Many2one('technic.tire.setting', string=u'Дугуйн тохиргоо',)
	model_id = fields.Many2one('technic.model.model', string='Модель', readonly=True,)
	brand_id = fields.Many2one('technic.model.brand', string='Brand', readonly=True, )

	norm_tire_size = fields.Char(string='Хэмжээ/Size', readonly=True, )
	norm_tread_deep = fields.Integer(string='Норм хээний гүн', readonly=True, ) 
	odometer_unit = fields.Selection([
		('km','Km'),
		('motoh','Moto/h')], string='Хэмжих нэгж',
		readonly=True, help='Km on service cars, Moto/h on mining vehicles')
	purchase_value = fields.Float('Худалдаж авсан үнэ', readonly=True, digits = (16,1),)
	residual_value = fields.Float('Үлдэгдэл', digits = (16,1), readonly=True, )
	total_moto_hour = fields.Float('Мото цаг', readonly=True, )	
	total_km = fields.Float('Километр', readonly=True, )  

	odometer_using_type = fields.Selection([
		('odo1_500','0-500'),
		('odo2_2500','501-2500'),
		('odo3_6000','2501-6000'),
		('odo4_6001','6001-с дээш')], string='Гүйлтийн үзүүлэлт', 
		readonly=True, )
	
	tread_current_deep = fields.Float(string='Одоогийн хээний гүн', digits = (16,1),
		group_operator='avg')
	tread_depreciation_percent = fields.Float(string='Хээний элэгдэл', 
		digits = (16,1), group_operator='avg')
	warning_deep = fields.Selection([
			('normal','Normal'),
			('warning','Warning tread'),], default='normal', 
		string=u'Анхааруулах статус', readonly=True)

	current_technic_id = fields.Many2one('technic.equipment', string=u'Одоогийн техник', 
		readonly=True,)
	current_position = fields.Char(string=u'Одоогийн байрлал', readonly=True,)
	tire_line = fields.Char(string=u'Tire line', readonly=True,)

	state = fields.Selection([
		('draft','Draft'),
		('new','New'),
		('using','Using'),
		('inactive','Inactive'),
		('repairing','Repairing'),
		('retired','Retired')], string='Төлөв', 
		readonly=True, default='draft',)

	working_type = fields.Selection([
		('normal',u'Хэвийн'),
		('use_again',u'Дахин ашиглах'),
		('available_repair',u'Засагдах боломжтой'),
		('rear_used','Арын тэнхлэгт шилжүүлсэн'),
		('burny','Халсан'),
		('exploded','Буудсан'),
		('shapeless','Хэлбэр алдсан'),
		('dont_use',u'Ашиглах боломжгүй')], string=u'Ажиллагаа', 
		default='normal', readonly=True, )

	retire_tire_type = fields.Selection([
		('shapeless','Дугуйн хэлбэр алдалт'),
		('burny','Халалт'),
		('odometer_overload','Мото цацгийн хэтрэлт'),
		('depend_roads','Зам талбайгаас хамаарсан'),
		('depend_pressure','Хийн даралтаас хамаарсан'),
		('cut','Дугуйн зүсэлт'),
		('exploded','Буудсан'),
		('tread_warning','Элэгдэл ихтэй'),
		('depend_operator',u'Операторын үйл ажиллагаанаас хамаарсан'),
		('tread_damage',u'Хээ хөндийрсөн')], string=u'Ашиглалтаас гарсан үзүүлэлт', required=True,)

	def init(self):
		tools.drop_view_if_exists(self.env.cr, self._table)
		self.env.cr.execute("""CREATE or REPLACE VIEW %s as (
			SELECT  
				tt.id as id,
				tt.branch_id as branch_id,
				tt.id as tire_id,
				(tt.current_position||' - '||tt.serial_number) as tire_line,
				tt.date_of_record as date_of_record,
				tt.date_of_manufactured as date_of_manufactured,
				tt.date_of_retired as date_of_retired, 
				tt.serial_number as serial_number,
				tt.tire_setting_id as tire_setting_id,
				tt.model_id as model_id,
				tt.brand_id as brand_id,
				tt.norm_tire_size as norm_tire_size,
				tt.norm_tread_deep as norm_tread_deep,
				tt.odometer_unit as odometer_unit,
				tt.purchase_value as purchase_value,
				tt.residual_value as residual_value,
				tt.total_moto_hour as total_moto_hour,
				tt.total_km as total_km,
				tt.tread_current_deep as tread_current_deep,
				tt.tread_depreciation_percent as tread_depreciation_percent,
				tt.warning_deep as warning_deep,
				tt.current_technic_id as current_technic_id,
				tt.current_position as current_position,
				tt.state as state,
				tt.working_type as working_type,
				tt.retire_tire_type as retire_tire_type,
				(CASE 
					WHEN tt.total_moto_hour <= 500 THEN 'odo1_500'
					WHEN tt.total_moto_hour <= 2500 THEN 'odo2_2500'
					WHEN tt.total_moto_hour <= 6000 THEN 'odo3_6000'
					ELSE 'odo4_6001' END) as odometer_using_type
			FROM technic_tire as tt
		)""" % self._table)
