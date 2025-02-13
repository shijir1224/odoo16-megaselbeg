# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo import _, tools
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, time, timedelta
from dateutil.relativedelta import relativedelta
import collections
from odoo.osv import expression

import polib
from googletrans import Translator

# Initialize the Google Translator
translator = Translator()

import logging
_logger = logging.getLogger(__name__)

FUEL_TYPE = [
			('gasoline', 'Gasoline'),
			('diesel', 'Diesel'),
			('electric', 'Electric'),
			('petrol', 'Petrol'),
			('hybrid', 'Hybrid')]

ENGINE_DESIGN = [
		('line', 'Цуваа'),
		('fork', 'Салаа')]

TRANSMISSION = [
		('manual', 'Механик'),
		('automatic', 'Автомат'),
		('electric', 'Цахилгаан'),
		('hydro', 'Гидро')]

ODOMETER_UNIT = [
		('m3','м3'),
		('km','Км'),
		('motoh','Мото/цаг'),
		('kmh','Км/цаг')]

TECHNIC_TYPE = [
		('excavator','Экскаватор'),
		('dump','Автосамосвал'),
		('dozer','Бульдозер'),
		('grader','Автогрейдер'),
		('loader','Дугуйт ачигч'),
		('wheel_excavator','Дугуйт экскаватор'),
		('wheel_dozer','Дугуйт түрэгч'),
		# ('wheel_loader','Wheel loader'),
		('tank_truck','Түлш цэнэглэх машин'),
		('water_truck','Усны машин'),
		('service_car',"Тосолгооны машин"),
		('fire_truck','Галын машин'),
		('ambulance_car','Эмнэлэгийн машин'),
		('mechanizm','Өргөх механизм'),
		('forklift','Сэрээт өргөгч'),
		('transportation_vehicle',"Хөнгөн тэрэг"),
		('passenger_bus',"Автобус"),
		('achaanii_mashin',u'Ачааны машин'),
		('drill',"Өрмийн машин"),
		('indvv',"Индүү"),
		('light_tower','Гэрэлт цамхаг'),
		('electric_generator','Цахилгаан үүсгүүр'),
		('air_compressor','Хийн компрессор'),
		# ('support_equipment',"Support equipment"),
		# ('technology_technic',u'Технологийн автомашин'),
		('welding_machine','Гагнуурын аппарат'),
		('heater','Халаагч'),
		('dolli' ,'Долли'),
		('asphalt_flatener','Материал дэвсэгч'),
		('transfer_trailer' ,'Чиргүүл'),
		('transfer_truck' ,'Чирэгч'),
		('wagon','Зүтгүүр')]

TECHNIC_SUB_TYPE = [
		('tseneglegch',u'Цэнэглэгч'),
		('tugjigch',u'Түгжигч'),
		('autobus',u'Автобус'),
		('microbus',u'Микробус'),
		('pickup',u'Пикап'),
		('sedan',u'Суудлын')]

OWNER_TYPE = [
		('own_asset',u'Өөрийн хөрөнгө'),
		('contracted',u'Гэрээт'),
		('rent',u'Түрээс')]

FIRE_SYSTEM_STATE = [
		('normal',u'Хэвийн'),
		('with_certification',u'Чанарын гэрчилгээтэй'),
		('require_repair',u'Засвар үйлчилгээ хийх шаардлагатай'),
		('not_working',u'Ажиллагаагүй')]

FIRE_SYSTEM_BRAND = [
		('fsi',u'FSI'),
		('ansul',u'Ansul'),
		('musterfire',u'Musterfire'),
		('fire_hydrant',u'Гар галын хортой')]

class TechnicModelBrand(models.Model):
	_name = 'technic.model.brand'
	_description = 'Brand model of the technic equipment'
	_order = 'name'

	name = fields.Char(string=u'Үйлдвэрлэгч', required=True, copy=False)
	description = fields.Text(string=u'Тайлбар', )
	image = fields.Binary(string='Logo', required=True, attachment=True,
		help="This field holds the image used as logo for the brand, limited to 1024x1024px.")

	image_medium = fields.Binary(string="Medium-sized image", attachment=True,
		help="Medium-sized logo of the brand. It is automatically "
			 "resized as a 128x128px image, with aspect ratio preserved. "
			 "Use this field in form views or some kanban views.")
	image_small = fields.Binary(string="Small-sized image", attachment=True,
		help="Small-sized logo of the brand. It is automatically "
			 "resized as a 64x64px image, with aspect ratio preserved. "
			 "Use this field anywhere a small image is required.")
	company_id = fields.Many2one('res.company', string="Компани")
	_sql_constraints = [
		('name_uniq', 'unique(name,company_id)', 'Нэр давхардсан байна!'),
	]


class TechnicModelModel(models.Model):
	_name = 'technic.model.model'
	_description = 'Model of the technic equipment'
	_order = 'name'

	@api.depends('brand_id', 'modelname')
	def _set_modelname(self):
		for item in self:
			if item.brand_id and item.modelname:
				item.name = str(item.brand_id.name)+' / '+str(item.modelname)
			else:
				item.name = "New"

	name = fields.Char(compute='_set_modelname', string=u'Нэр',
					   readonly=True, store=True, default="-", copy=False)
	modelname = fields.Char(string=u'Загварын нэр', required=True,)
	brand_id = fields.Many2one('technic.model.brand',
							   string=u'Үйлдвэрлэгч', required=True,)
	image = fields.Binary(related='brand_id.image_medium', string='Зураг', readonly=True,
		help="This field holds the image used as logo for the brand, limited to 1024x1024px.", )
	technic_setting_id = fields.Many2one(
		'technic.equipment.setting', string=u'Техник тохиргоо', )
	technic_type = fields.Selection(
		related='technic_setting_id.technic_type', readonly=True, store=True)
	technic_type_id = fields.Many2one(
		related='technic_setting_id.technic_type_id', readonly=True, store=True)
	company_id = fields.Many2one('res.company', string="Компани")
	_sql_constraints = [
		('name_uniq', 'unique(name,company_id)', 'Нэр давхардсан байна!'),
	]

class TechnicType(models.Model):
	_name = 'technic.type'
	_description = 'Technic type'

	name = fields.Char(string='Төрлийн нэршил', required=True, copy=False)
	technic_type = fields.Selection(TECHNIC_TYPE, string ='Техникийн төрөл', store=True)
	is_on_app = fields.Boolean(string='Хялбар апп-д ашиглах эсэх?', default=False)

class TechnicEquipmentSetting(models.Model):
	_name = 'technic.equipment.setting'
	_description = 'Setting of the technic equipment'
	_inherit = ["analytic.mixin","mail.thread", "mail.activity.mixin"]
	_order = 'report_order, name'

	@api.depends('model_id','model_id.modelname','model_id.brand_id','model_id.brand_id.name')
	def _set_name(self):
		for item in self:
			if item.model_id:
				item.name = item.model_id.name+' : Тохиргоо'
			else:
				item.name = "New"

	name = fields.Char(compute='_set_name', string=u'Нэр',
					   readonly=True, store=True, default="-")
	model_id = fields.Many2one('technic.model.model',
							   string=u'Загварын нэр', required=True, copy=False)
	inspection_config_id = fields.Many2one('technic.inspection.setting',
		string=u'Үзлэгийн тохиргоо', required=True,)

	report_order = fields.Char(string='Тайлангийн эрэмбэ', default='999')

	seats = fields.Integer(string='Суудлын тоо',
						   help='Number of seats of the vehicle')
	doors = fields.Integer(string='Хаалганы тоо',
						   help='Number of doors of the vehicle')
	fuel_type = fields.Selection(FUEL_TYPE, string='Энергийн эх үүсвэр', help='Fuel Used by the vehicle')
	engine_design = fields.Selection(ENGINE_DESIGN, string='Хөдөлгүүрийн хийц', help='Engine design')

	engine_power = fields.Float(
		string='Хөдөлгүүрийн чадал, квт', digits=(16, 1),)
	engine_capacity = fields.Float(string='Хөдөлгүүрийн багтаамж, литр',
		digits=(16, 1), help='Engine capacity litre')
	engine_mark = fields.Char(string='Хөдөлгүүрийн модель', help='Engine mark...')
	engine_type = fields.Char(string='Хөдөлгүүрийн бренд', help='Engine type...')

	carrying_capacity = fields.Float(
		string='Тэвшний багтаамж, м³', digits=(16, 1), help='Struck capacity(m3)')
	carrying_tonnage = fields.Float(
		string='Тэвшний даац, тн', digits=(16, 1), help='Struck tonnage')
	bucket_capacity = fields.Float(
		string='Шанаганы багтаамж, м³', digits=(16, 1), help='Bucket capacity(m3)')
	blade_capacity = fields.Float(
		string='Хутганы багтаамж, м³', digits=(16, 1), help='Blade capacity(m3)')
	blade_width = fields.Float(
		string='Хусуурын өргөн, м', digits=(16, 1), help='Blade width(m)')
	lifting_capacity = fields.Float(
		string='Өргөх хүчин чадал, тн', digits = (16,1), help='Lifting capacity')
	power_capacity = fields.Float(
		string='Чадал, квт', digits = (16,1), help='power capacity(kilowatt)')
	pressure_capacity = fields.Float(
		string='Даралт, bar', digits = (16,1), help='pressure capacity(bar)')
	volume = fields.Float(
		string='Эзэлхүүн, м³/мин', digits = (16,1), help='volume(bar)')
	electric_current = fields.Float(
		string='Гүйдэл, ампер', digits = (16,1), help='electric_current(A)')
	vibration_power = fields.Float(
		string='Чичиргээний чадал, квт', digits = (16,1), help='vibration power(kilowatt)')


	body_length = fields.Float(string='Нийт урт, м', digits = (16,1), )
	body_width = fields.Float(string='Нийт өргөн, м', digits = (16,1), )
	body_height = fields.Float(string='Нийт өндөр, м', digits = (16,1), )

	fuel_tank_capacity = fields.Float(string='Түлшний танкны багтаамж, литр', digits = (16,1), )
	operating_weight = fields.Float(string='Ажлын жин, тн', digits = (16,1), )

	transmission = fields.Selection(TRANSMISSION,
		string='Төрөл', help='Transmission Used by the vehicle')
	transmission_type = fields.Char(string="Модель", help="Transmission type")
	transmission_mark = fields.Char(string="Бренд", help="Transmission mark")
	transmission_power = fields.Float(string="Transmission Чадал, квт", help="Transmission power")

	rpm_min = fields.Float(string='RPM Min',digits = (16,1), required=True)
	rpm_ave = fields.Float(string='RPM Average',digits = (16,1), required=True)
	rpm_max = fields.Float(string='RPM Max',digits = (16,1), required=True)
	fuel_low_idle = fields.Float(string='Fuel low idle',digits = (16,1), required=True)
	fuel_medium_idle = fields.Float(string='Fuel medium idle',digits = (16,1), required=True)
	fuel_high_idle = fields.Float(string='Fuel high idle',digits = (16,1), required=True)

	odometer_unit = fields.Selection(ODOMETER_UNIT,
		string='Гүйлтийн нэгж',required=True)

	technic_type = fields.Selection(related="technic_type_id.technic_type", string ='Техникийн төрөл', store=True)
	technic_type_id = fields.Many2one('technic.type', string ='Техникийн төрөл',required=True)

	# technic_sub_type = fields.Selection(TECHNIC_SUB_TYPE,
	#     string =u'Техникийн дэд төрөл')

	rubber_tired = fields.Boolean(string='Дугуйтай эсэх?', default=True)
	is_plan_by_time = fields.Boolean(string=u'Хугацаагаар төлөвлөх эсэх?', default=False)
	is_tbb_report = fields.Boolean(string=u'ТББ тооцох эсэх?', default=False)
	is_tbb_mining = fields.Boolean(string=u'Уул ТББ тооцох эсэх?', default=False, tracking=True)
	position_format = fields.Char(string='Байрлалын формат', help=u'ЖШ: 1-2,2-2, дамп 1-2,2-4 гэх мэт')
	tire_counts = fields.Integer(string=u'Нийт дугуйн тоо', default=0)

	component_config_line = fields.One2many('technic.component.config', 'parent_id', string='Компонентийн тохиргоо', )
	img_of_parts = fields.Binary(string='Схем зураг', attachment=True, copy=False,
		help="Picture of parts")
	pic_width = fields.Float(string='Зурагны өргөн', digits = (16,1))
	pic_height = fields.Float(string='Зурагны өндөр', digits = (16,1))

	# Баталгаат хугацаа, гүйлт
	warranty_period = fields.Integer(string=u'Баталгаат хугацаа, сар', help=u'Баталгаат хугацааг сараар тооцно')
	warranty_odometer = fields.Integer(string=u'Баталгаат гүйлт', help=u'Баталгаа өгсөн гүйлт')
	technic_ids = fields.One2many('technic.equipment', 'technic_setting_id', string=u'Техникүүд', readonly=True)
	company_id = fields.Many2one('res.company', string="Компани")

	# Асфальт дэвсэгч
	work_mass = fields.Float(string=u'Ажлын жин, тн')
	length_flat_min = fields.Float(string=u'Дэвсэлтийн ХБ өргөн, м')
	length_flat_max = fields.Float(string=u'Дэвсэлтийн ХИ өргөн, м')
	bunker_capacity = fields.Float(string=u'Бункерийн багтаамж, м3')

	
	# дата бэлдэх
	def get_datas(self, c_id, context=None):
		obj = self.env['technic.equipment.setting'].browse(c_id)
		parts = []
		for line in obj.component_config_line:
				temp = {
				'number': line.sequence,
				'title': '['+line.component_id.default_code+'] '+line.component_id.name,
				'top': line.position_y,
				'left': line.position_x,
				}
				parts.append(temp)
		return parts

	_sql_constraints = [
		('name_uniq', 'unique(model_id)', 'Model must be unique!'),
	]

	# ------------ OVERRIDE ================
	def write(self, vals):
		res = super(TechnicEquipmentSetting, self).write(vals)
		if 'model_id' in vals:
			model = self.env['technic.model.model'].browse(vals['model_id'])
			model.technic_setting_id = self.id
		return res

	# Methods
	def get_position_format(self, setting_id, context=None):
		obj = self.env['technic.equipment.setting'].browse(setting_id)
		return obj.position_format or False

	# Default PM тохиргоо үүсгэх
	def set_default_pm_line(self):
		type_ids = self.env['maintenance.type'].sudo().search([('is_pm','=',True)])
		setting_ids = self.env['technic.equipment.setting'].sudo().search([('is_tbb_report','=',True)])
		for setting in setting_ids:
			if setting.technic_type in ['dump','excavator','wheel_excavator','wheel_loader','service_car','loader','dozer','wheel_dozer','grader','water_truck']:
				setting.pm_material_config.sorted('priority')
				if not setting.pm_material_config:
					vals = {
						'technic_setting_id': setting.id,
						'priority': 1,
						'maintenance_type_id': self.env['maintenance.type'].sudo().search([('is_pm','=', True), ('name','=','PM 250')], limit=1).id,
						'interval': 250,
						'work_time': 1,
					}
					self.env['maintenance.pm.material.config'].create(vals)
					vals = {
						'technic_setting_id': setting.id,
						'priority': 2,
						'maintenance_type_id': self.env['maintenance.type'].sudo().search([('is_pm','=', True), ('name','=','PM 500')], limit=1).id,
						'interval': 250,
						'work_time': 1,
					}
					self.env['maintenance.pm.material.config'].create(vals)
					vals = {
						'technic_setting_id': setting.id,
						'priority': 3,
						'maintenance_type_id': self.env['maintenance.type'].sudo().search([('is_pm','=', True), ('name','=','PM 250')], limit=1).id,
						'interval': 250,
						'work_time': 1,
					}
					self.env['maintenance.pm.material.config'].create(vals)
					vals = {
						'technic_setting_id': setting.id,
						'priority': 4,
						'maintenance_type_id': self.env['maintenance.type'].sudo().search([('is_pm','=', True), ('name','=','PM 1000')], limit=1).id,
						'interval': 250,
						'work_time': 1,
					}
					self.env['maintenance.pm.material.config'].create(vals)
					vals = {
						'technic_setting_id': setting.id,
						'priority': 5,
						'maintenance_type_id': self.env['maintenance.type'].sudo().search([('is_pm','=', True), ('name','=','PM 250')], limit=1).id,
						'interval': 250,
						'work_time': 1,
					}
					self.env['maintenance.pm.material.config'].create(vals)
					vals = {
						'technic_setting_id': setting.id,
						'priority': 6,
						'maintenance_type_id': self.env['maintenance.type'].sudo().search([('is_pm','=', True), ('name','=','PM 500')], limit=1).id,
						'interval': 250,
						'work_time': 1,
					}
					self.env['maintenance.pm.material.config'].create(vals)
					vals = {
						'technic_setting_id': setting.id,
						'priority': 7,
						'maintenance_type_id': self.env['maintenance.type'].sudo().search([('is_pm','=', True), ('name','=','PM 250')], limit=1).id,
						'interval': 250,
						'work_time': 1,
					}
					self.env['maintenance.pm.material.config'].create(vals)
					vals = {
						'technic_setting_id': setting.id,
						'priority': 8,
						'maintenance_type_id': self.env['maintenance.type'].sudo().search([('is_pm','=', True), ('name','=','PM 2000')], limit=1).id,
						'interval': 250,
						'work_time': 1,
					}
					self.env['maintenance.pm.material.config'].create(vals)
				# for config in setting.pm_material_config.sorted('priority'):
				# 	if config.priority == 1:
				# 	# type_ids = self.env['maintenance.type'].sudo().search([('is_pm','=',True)])
				# 	if 'PM 250' not in self.env['maintenance.type'].sudo().search([('is_pm','=',True),('name','=ilike','PM 250')]):
				# 		type_ids
				# 	if 'PM 500' not in self.env['maintenance.type'].sudo().search([('is_pm','=',True),('name','=ilike','PM 250')]):
				# 		type_ids
				# 	if 'PM 1000' not in self.env['maintenance.type'].sudo().search([('is_pm','=',True),('name','=ilike','PM 250')]):
				# 		type_ids
				# 	if 'PM 2000' not in self.env['maintenance.type'].sudo().search([('is_pm','=',True),('name','=ilike','PM 250')]):
				# 		type_ids
				# 	if 'PM 3000' not in self.env['maintenance.type'].sudo().search([('is_pm','=',True),('name','=ilike','PM 250')]):
				# 		type_ids
				# 	if 'PM 4000' not in self.env['maintenance.type'].sudo().search([('is_pm','=',True),('name','=ilike','PM 250')]):
				# 		type_ids
					# config

	def _change(self):
		for item in self:
			for tech in item.technic_ids:
				tech.is_tbb_report = item.is_tbb_report
				tech.is_tbb_mining = item.is_tbb_mining

	@api.onchange('is_tbb_mining','is_tbb_report')
	def onchange_is_tbb(self):
		self._change()

	def force_name(self):
		technis = self.env['technic.equipment.setting'].sudo().search([])
		for item in technis:
			item._set_name()

class TechnicEquipment(models.Model):
    _name = 'technic.equipment'
    _description = 'Technic equipment'
    _inherit = ['mail.thread']
    _order = 'report_order, name'

    def translate_po_file(input_file='mining16/mw_technic_equpment/i18n/en_US.po', output_file='mining16/mw_technic_equpment/i18n/en_US.po', target_language='mn'):
        # Load the .po file
        po = polib.pofile('mining16/mw_technic_equpment/i18n/en_US.po')
        print('po========', po)
        _logger.info('/n /n ================po=======================' %(po))
        
        # Iterate over each entry in the .po file
        for entry in po:
            print('entry======', entry)
            _logger.info('/n /n ================entry=======================' %(entry))
            if entry.msgid and not entry.msgstr:
                # Translate the msgid (original text)
                translated_text = translator.translate(entry.msgid, dest=target_language).text
                # Set the translated text as msgstr
                entry.msgstr = translated_text
        
        # Save the updated .po file
        po.save(output_file)

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if name:
            domain = ['|', '|', '|', '|',('program_code', operator, name),('park_number', operator, name),('name', operator, name),('vin_number', operator, name),('state_number', operator, name)]
            # if operator in expression.NEGATIVE_TERM_OPERATORS:
            # 	domain = ['&'] + domain
        technics = self.search(domain + args, limit=limit)
        return technics.name_get()
    
    def name_get(self):
        res = []
        for item in self:
            name = item.name or ''
            if item.park_number and item.state_number and item.model_id:
                name = item.state_number+'/ ' + item.park_number+' /'+item.model_id.name+'/ '
            res.append((item.id, name))
        return res

    @api.depends('owner_type','program_code','park_number', 'model_id', 'model_id.name', 'model_id.brand_id', 'model_id.brand_id.name')
    def _set_name(self):
        for obj in self:
            # if obj.owner_type == 'own_asset' and obj.park_number:
            #     obj.name = obj.park_number+' /'+obj.model_id.name+'/'+obj.state_number+'/' if obj.state_number else obj.park_number+' /'+obj.model_id.name
            # elif obj.owner_type == 'rent' and obj.park_number:
            #     obj.name = obj.park_number+' /'+obj.model_id.name+' /RENT'+obj.state_number+'/' if obj.state_number else obj.park_number+' /'+obj.model_id.name
            # elif obj.owner_type == 'contracted' and obj.park_number:
            #     obj.name = obj.park_number+' /'+obj.model_id.name+' /CONT'+obj.state_number+'/' if obj.state_number else obj.park_number+' /'+obj.model_id.name
            # else:
            #     obj.name = obj.park_number+' /'+obj.model_id.name+'/'+obj.state_number+'/' if obj.state_number else obj.park_number+' /'+obj.model_id.name
            obj.name = obj.park_number
    def force_name(self):
        technis = self.env['technic.equipment'].sudo().search([])
        for item in technis:
            item._set_name()

    company_id = fields.Many2one('res.company', string='Компани', default=lambda self: self.env.user.company_id)
    branch_id = fields.Many2one('res.branch', string=u'Салбар', required=True,)


    name = fields.Char(compute='_set_name',string=u'Нэр', readonly=True, store=True, default="-")
    vin_number = fields.Char(string='Сериал дугаар', required=True,)
    park_number = fields.Char(string='Парк дугаар', required=True, tracking=True,
        states={'stopped':[('readonly',True)],'working':[('readonly', True)],'parking':[('readonly', True)],
                'repairing':[('readonly',True)],'inactive':[('readonly', True)]})
    state_number = fields.Char(string='Улсын дугаар',
        states={'stopped':[('readonly',True)],'working':[('readonly', True)],'parking':[('readonly', True)],
                'repairing':[('readonly',True)],'inactive':[('readonly', True)]})
    document_number = fields.Char(string='Гэрчилгээний дугаар',
        states={'stopped':[('readonly',True)],'working':[('readonly', True)],'parking':[('readonly', True)],
                'repairing':[('readonly',True)],'inactive':[('readonly', True)]})
    engine_serial = fields.Char(string='Хөдөлгүүрийн сериал',)

    program_code = fields.Char(string=u'Програм код',
        states={'stopped':[('readonly',True)],'working':[('readonly', True)],'parking':[('readonly', True)],
                'repairing':[('readonly',True)],'inactive':[('readonly', True)]})

    manufactured_date = fields.Date(string=u'Үйлдвэрлэсэн огноо', required=True,
        states={'stopped':[('readonly',True)],'working':[('readonly', True)],'parking':[('readonly', True)],
                'repairing':[('readonly',True)],'inactive':[('readonly', True)]})
    start_date = fields.Date(string=u'Эхлэсэн огноо', required=True,
        states={'stopped':[('readonly',True)],'working':[('readonly', True)],'parking':[('readonly', True)],
                'repairing':[('readonly',True)],'inactive':[('readonly', True)]})
    color = fields.Char(string='Өнгө',
        states={'stopped':[('readonly',True)],'working':[('readonly', True)],'parking':[('readonly', True)],
                'repairing':[('readonly',True)],'inactive':[('readonly', True)]})
    asset_id = fields.Many2one('account.asset.asset', string='Холбоотой хөрөнгө', # required=True,
        states={'stopped':[('readonly',True)],'working':[('readonly', True)],'parking':[('readonly', True)],
                'repairing':[('readonly',True)],'inactive':[('readonly', True)]}
                )
    partner_id = fields.Many2one('res.partner', string=u'Холбоотой харилцагч', )
    department_id = fields.Many2one('hr.department', string=u'Холбоотой хэлтэс', )

    owner_type = fields.Selection(OWNER_TYPE,
        string=u'Эзэмшлийн төрөл', default='own_asset', required=True, tracking=True)

    technic_setting_id = fields.Many2one('technic.equipment.setting', string=u'Техникийн тохиргоо', help='Technic norn and setting',
        states={'stopped':[('readonly',True)],'working':[('readonly', True)],'parking':[('readonly', True)],
                'repairing':[('readonly',True)],'inactive':[('readonly', True)]})
    model_id = fields.Many2one(related='technic_setting_id.model_id', string='Загвар', readonly=True, store=True)
    image = fields.Binary(related='model_id.image', string='Зураг', readonly=True, )

    technic_type_id = fields.Many2one(related='technic_setting_id.technic_type_id', readonly=True, store=True)
    technic_type = fields.Selection(related='technic_setting_id.technic_type', string='Техникийн төрөл',
        readonly=True, store=True)
    report_order = fields.Char(related='technic_setting_id.report_order', string='Тайлангийн эрэмбэ',
        readonly=True, store=True)

    # technic_sub_type = fields.Selection(related='technic_setting_id.technic_sub_type', string=u'Дэд төрөл',
    #     readonly=True, store=True)
    odometer_unit = fields.Selection(related='technic_setting_id.odometer_unit', string='Гүйлтийн нэгж',
        readonly=True, store=True)
    rubber_tired = fields.Boolean(related='technic_setting_id.rubber_tired', string='Дугуйтай эсэх?',
        readonly=True, store=True)
    position_format = fields.Char(related='technic_setting_id.position_format', readonly=True)

    # OTHER INFO
    carrying_capacity = fields.Float(string='Тэвшний багтаамж, м³', digits=(16, 1), help='Struck capacity(m3)',
        states={'stopped':[('readonly',True)],'working':[('readonly', True)],'parking':[('readonly', True)],
                'repairing':[('readonly',True)],'inactive':[('readonly', True)]})
    carrying_tonnage = fields.Float(string='Тэвшний даац, тн', digits=(16, 1), help='Struck tonnage',
        states={'stopped':[('readonly',True)],'working':[('readonly', True)],'parking':[('readonly', True)],
                'repairing':[('readonly',True)],'inactive':[('readonly', True)]})

    bucket_capacity = fields.Float(string='Шанаганы багтаамж, м³', digits=(16, 1), help='Bucket capacity(m3)',
        states={'stopped':[('readonly',True)],'working':[('readonly', True)],'parking':[('readonly', True)],
                'repairing':[('readonly',True)],'inactive':[('readonly', True)]})
    blade_capacity = fields.Float(string='Хутганы багтаамж, м³', digits=(16, 1), help='Blade capacity(m3)',
        states={'stopped':[('readonly',True)],'working':[('readonly', True)],'parking':[('readonly', True)],
                'repairing':[('readonly',True)],'inactive':[('readonly', True)]})

    blade_width = fields.Float(string='Хусуурын өргөн, м', digits=(16, 1), help='Blade width(m)',
        states={'stopped':[('readonly',True)],'working':[('readonly', True)],'parking':[('readonly', True)],
                'repairing':[('readonly',True)],'inactive':[('readonly', True)]})
    lifting_capacity = fields.Float(string='Өргөх хүчин чадал, тн', digits = (16,1), help='Lifting capacity',
        states={'stopped':[('readonly',True)],'working':[('readonly', True)],'parking':[('readonly', True)],
                'repairing':[('readonly',True)],'inactive':[('readonly', True)]})

    power_capacity = fields.Float(string='Чадал, квт', digits = (16,1), help='power capacity(kilowatt)',
        states={'stopped':[('readonly',True)],'working':[('readonly', True)],'parking':[('readonly', True)],
                'repairing':[('readonly',True)],'inactive':[('readonly', True)]})
    pressure_capacity = fields.Float(string='Даралт, bar', digits = (16,1), help='pressure capacity(bar)',
        states={'stopped':[('readonly',True)],'working':[('readonly', True)],'parking':[('readonly', True)],
                'repairing':[('readonly',True)],'inactive':[('readonly', True)]})

    volume = fields.Float(string='Эзэлхүүн, м³/мин', digits = (16,1), help='volume(bar)',
        states={'stopped':[('readonly',True)],'working':[('readonly', True)],'parking':[('readonly', True)],
                'repairing':[('readonly',True)],'inactive':[('readonly', True)]})
    electric_current = fields.Float(string='Гүйдэл, ампер', digits = (16,1), help='electric_current(A)',
        states={'stopped':[('readonly',True)],'working':[('readonly', True)],'parking':[('readonly', True)],
                'repairing':[('readonly',True)],'inactive':[('readonly', True)]})

    vibration_power = fields.Float(string='Чичиргээний чадал, квт', digits = (16,1), help='vibration power(kilowatt)',
        states={'stopped':[('readonly',True)],'working':[('readonly', True)],'parking':[('readonly', True)],
                'repairing':[('readonly',True)],'inactive':[('readonly', True)]})

    operating_weight = fields.Float(string='Ажлын жин, тн', digits = (16,1),
        states={'stopped':[('readonly',True)],'working':[('readonly', True)],'parking':[('readonly', True)],
                'repairing':[('readonly',True)],'inactive':[('readonly', True)]})
    seats = fields.Integer(string='Суудлын тоо', help='Number of seats of the vehicle',
        states={'stopped':[('readonly',True)],'working':[('readonly', True)],'parking':[('readonly', True)],
                'repairing':[('readonly',True)],'inactive':[('readonly', True)]})

    total_km = fields.Float(string='Нийт KM', digits = (16,1), default=0,
        states={'stopped':[('readonly',True)],'working':[('readonly', True)],'parking':[('readonly', True)],
                'repairing':[('readonly',True)],'inactive':[('readonly', True)]})
    total_odometer = fields.Float(string='Нийт гүйлт', digits = (16,1), default=0,)

    state = fields.Selection([
        ('draft','Draft'),
        ('stopped','Stopped'),
        ('working','Working'),
        ('parking','Parking'),
        ('repairing','Repairing'),
        ('inactive',u'Актласан')],
        string='Төлөв', default='draft', tracking=True)
    status_note = fields.Text(string='Статус тайлбар', readonly=True, )


    tire_line = fields.One2many('technic.tire.line', 'technic_id',string='Дугуй', readonly=True, domain=[('state','=','set')])
    tire_counts = fields.Integer(related="technic_setting_id.tire_counts", readonly=True, store=True,)

    move_line_ids = fields.One2many('technic.move.history', 'technic_id',string='Шилжсэн түүх', readonly=True)

    component_part_line = fields.One2many('technic.component.part', 'current_technic_id',string='Components',
        # readonly=True, domain=[('state','=','set')],
        )
    img_of_parts = fields.Binary(related='technic_setting_id.img_of_parts',
        string='Схем зураг', readonly=True, )
    pic_width = fields.Float(related='technic_setting_id.pic_width',
        string='Зурагны өргөн', digits = (16,1))
    pic_height = fields.Float(related='technic_setting_id.pic_height',
        string='Зурагны өндөр', digits = (16,1))

    # Баталгаат хугацаа, гүйлт
    with_warrenty = fields.Boolean(string=u'Баталгаат эсэх?', default=False)
    warranty_period = fields.Integer(related='technic_setting_id.warranty_period', string=u'Баталгаат хугацаа',
        help=u'Баталгаат хугацааг сараар тооцно', store=True, readonly=True, )
    warranty_odometer = fields.Integer(related='technic_setting_id.warranty_odometer', string=u'Баталгаат гүйлт',
        help=u'Баталгаа өгсөн гүйлт', store=True, readonly=True, )
    warrenty_date = fields.Date(string=u'Баталгаа эхэлсэн огноо',
        states={'stopped':[('readonly',True)],'working':[('readonly', True)],'parking':[('readonly', True)],
                'repairing':[('readonly',True)],'inactive':[('readonly', True)]})

    # Даатгалын мэдээлэл
    with_insurance = fields.Boolean(string='Даатгалтай эсэх?', default=False,)
    insurance_company_name = fields.Char(string=u'Даатгалын газар', )
    insurance_payment_amount = fields.Float(string=u'Даатгалын төлбөр', )
    insurance_contract_number = fields.Char(string=u'Даатгал гэрээний дугаар', )
    insurance_date_end = fields.Date(string=u'Даатгал дуусах', )
    # Татвар үзлэг хийх өдөр
    state_inspection_date_end = fields.Date(string=u'Улсын үзлэг дуусах огноо', )
    state_tax_date_end = fields.Date(string=u'Татвар төлөх огноо', )

    # Краны магадлагаа
    validation_register_id = fields.Char(string=u"МХЕГ-н краны бүртгэлийн дугаар")
    validation_start_date = fields.Date(string=u"Магадлагаа хийгдсэн огноо")
    validation_end_date = fields.Date(string=u"Магадлагаа дуусах огноо")

    @api.depends('warranty_period','warranty_odometer','warrenty_date','with_warrenty')
    def _get_warranty_info(self):
        for obj in self:
            if obj.with_warrenty:
                txt = "-"
                if obj.warrenty_date and obj.technic_setting_id.warranty_period > 0:
                    a = obj.warrenty_date
                    b = datetime.now().date()
                    delta = b - a
                    days = obj.warranty_period * 30
                    if days > delta.days:
                        date1 = obj.warrenty_date
                        date2 = date1 + timedelta(days=days)
                        txt = u"<b style='color:green;'>Дуусах өдөр: %s, Үлдсэн: %d өдөр</b>" % (date2.strftime('%Y-%m-%d'), days-delta.days)
                    else:
                        txt = u"<b style='color:red;'>Баталгаа дууссан! Хэтэрсэн өдөр: %d</b>" % (delta.days-days)
                if obj.technic_setting_id.warranty_odometer > 0:
                    delta = obj.technic_setting_id.warranty_odometer - (obj.total_odometer if obj.odometer_unit == 'motoh' else obj.total_km)
                    if delta > 0:
                        txt += u"<br/><b style='color:green;'>Үлдсэн: %d гүйлт</b>" % (delta)
                    else:
                        txt += u"<br/><b style='color:red;'>Баталгаа дууссан! Хэтэрсэн гүйлт: %d</b>" % (delta)
                obj.warranty_info = txt
            else:
                obj.warranty_info = '-'
    warranty_info = fields.Html(string='Warranty info',
        readonly=True, compute="_get_warranty_info", )

    # Галын системийн бүртгэл
    with_fire_system = fields.Boolean(string=u'Галын системтэй эсэх?', default=False)
    fire_system_state = fields.Selection(FIRE_SYSTEM_STATE,
        string=u'Галын системийн төлөв', default='normal', )
    fire_system_brand = fields.Selection(FIRE_SYSTEM_BRAND,
        string=u'Системийн бренд', default='fsi', )
    fire_system_type = fields.Char(string=u'Системийн төрөл', help=u'Fire system type')
    # fire_system_type = fields.Selection([
    # 	('fsi',u'FSI'),
    # 	('ansul',u'Ansul'),
    # 	('ansul_china',u'Ansul/China')],
    # 	string=u'Системийн төрөл', default='fsi', )
    fire_system_install_date = fields.Date(string=u'Суурьлуулсан огноо')
    fire_system_last_date = fields.Date(string=u'Сүүлд үйлчилгээ хийгдсэн огноо', )
    fire_system_period = fields.Integer(string=u'Засвар үйлчилгээний давтамж', help=u"Сараар тооцож оруулна уу")

    @api.depends('with_fire_system','fire_system_last_date','fire_system_period')
    def get_next_date(self):
        for obj in self:
            if obj.with_fire_system and obj.fire_system_period and obj.fire_system_last_date:
                date1 = obj.fire_system_last_date
                obj.fire_system_next_date = date1 + relativedelta(months=+obj.fire_system_period)
            else:
                obj.fire_system_next_date = ''
    fire_system_next_date = fields.Date(string=u"Дараагийн үйлчилгээ хийх огноо", readonly=True,
        compute=get_next_date, store=True, default=False)

    # ТББК
    is_tbb_report = fields.Boolean(string=u'ТББ тооцох эсэх?', default=False)
    is_tbb_mining = fields.Boolean(string=u'Уул ТББ тооцох эсэх?', default=False, tracking=True)

    # =================== Overrided methods ================
    def unlink(self):
        for s in self:
            if s.state != 'draft':
                raise UserError(_('Ноороглох ёстой!'))
        return super(TechnicEquipment, self).unlink()

    # =================== Custom methods ===================
    def get_odometer_datas(self, t_id, context=None):
        if t_id:
            obj = self.env['technic.equipment'].browse(t_id)
            return {'total_odometer': obj.total_odometer, 'total_km': obj.total_km}
        else:
            return {'total_odometer': 0, 'total_km': 0}

    # Компонентийн ДАТА бэлдэх
    def get_component_datas(self, t_id, context=None):
        parts = []
        if t_id:
            obj = self.env['technic.equipment'].browse(t_id)
            for line in obj.component_part_line:
                position_y = 0
                position_x = 0
                if line.component_config_id:
                    position_y = line.component_config_id.position_y
                    position_x = line.component_config_id.position_x
                else:
                    if line.sequence:
                        if line.current_technic_id:
                            config_id = line.current_technic_id.technic_setting_id.component_config_line.filtered(lambda l: l.sequence == line.sequence)
                            position_y = config_id.position_y
                            position_x = config_id.position_x
                temp = {
                    'top': position_y,
                    'left': position_x,
                    'number': line.sequence,
                    'title': '['+line.product_id.default_code+'] '+line.product_id.name,
                    'total_odometer': line.total_odometer,
                    'last_odometer': line.last_odometer,
                    'diff': line.total_odometer - line.last_odometer,
                }
                parts.append(temp)
        return parts

    # Холбоотой үзлэгүүдийг харах
    def see_inspections(self):
        action = self.env.ref('mw_technic_equipment.action_technic_inspection').read()[0]
        action['domain'] = [('technic_id','=', self.id)]
        return action

    # Компонент эд ангийн бүрэн эсэхийг шалгах
    @api.depends('component_part_line','technic_setting_id.component_config_line')
    def check_components(self):
        for obj in self:
            message = '-'
            for cl in obj.technic_setting_id.component_config_line:
                if cl.component_id.product_tmpl_id.id not in obj.component_part_line.mapped('product_id.product_tmpl_id.id'):
                        message += u'<font color="red"><b>[%s] %s</b></font> - эд анги дутуу байна.<br>' % (cl.component_id.default_code, cl.component_id.name)
            for cl in obj.component_part_line:
                if cl.product_id.product_tmpl_id.id not in obj.technic_setting_id.component_config_line.mapped('component_id.product_tmpl_id.id'):
                        message += u'<font color="green"><b>[%s] %s</b></font> - эд анги илүү байна.<br>' % (cl.product_id.default_code, cl.product_id.name)
            obj.components_info = message

    components_info = fields.Html(string=u"Компонентийн мэдээлэл", readonly=True,
        compute=check_components, store=True, )

    retire_attachment_ids = fields.Many2many('ir.attachment', string=u'Хавсралтууд', readonly=True,)

    # Санхүү
    account_id = fields.Many2one('account.account', string=u'Данс', copy=False,
        states={'confirmed': [('readonly', True)], 'done': [('readonly', True)]},)
    account_analytic_id = fields.Many2one('account.analytic.account', string=u'Аналитик данс', copy=False,
        states={'done': [('readonly', True)]}, )

    # tulshnii_zarlaga_ids = fields.Many2one('oil.fuel.line', string='Түлшний зарлагын мэдээлэл',)

    is_active = fields.Boolean(string=u'Is Active', default=False)

    _sql_constraints = [
        ('technic_uniq', 'unique(vin_number,company_id)', "Техникийн арлын дугаар давхардсан байна!"),
    ]

    # Зарагдсан техникийг идэвхигүй болгох
    def make_deactive(self):
        self.is_active = True

    def make_active(self):
        self.is_active = True

    @api.onchange('technic_setting_id')
    def onchange_technic_setting_id(self):
        if self.technic_setting_id:
            self.carrying_capacity = self.technic_setting_id.carrying_capacity
            self.carrying_tonnage = self.technic_setting_id.carrying_tonnage
            self.bucket_capacity = self.technic_setting_id.bucket_capacity
            self.write({'is_tbb_report': self.technic_setting_id.is_tbb_report})
            self.write({'is_tbb_mining': self.technic_setting_id.is_tbb_mining})

    # ================= CUSTOM METHODs =============
    # Шилжүүлэх
    def move_to_branch(self):
        context = dict(self._context)
        context.update({'technic_id': self.id})
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'technic.move.history.wizard',
            'view_mode': 'form',
            'context': context,
            'target': 'new',
        }
    # Гараар нэмэгдүүлэх
    def manual_increase_odometer(self):
        context = dict(self._context)
        context.update({'technic_id': self.id})
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'technic.odometer.increase',
            'view_mode': 'form',
            'context': context,
            'target': 'new',
        }
    # Техник статус оруулах
    def create_technic_status(self):
        context = dict(self._context)
        context.update({'technic_id': self.id})
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'technic.equipment.log.status',
            'view_mode': 'form',
            'context': context,
            'target': 'new',
        }

    def _check_past_days(self, i_date):
        past_date = datetime.now() + timedelta(days=-4)
        if past_date.date() > i_date:
            return True
        else:
            return False

    # Техник МЦ, КМ нэмэгдүүлэх func
    def _increase_odometer(self, i_date, last_motoh, last_km, diff, diff_km, shift, is_manual=None):
        if self.state not in ['draft']:
            # Гараар нэмж байгаа бол хамаагүй
            if not is_manual:
                # Уулаас нэмж байгаа өдөр нь хэд хоногийн өмнөх эсэхийг шалгана.
                # Заасан хугацаанаас хэтэрсэн бол мото цагийг нэмэхгүй
                if self._check_past_days(i_date):
                    return

            motoh = last_motoh - self.total_odometer
            km = last_km - self.total_km
            # Шинэчлэх
            self.total_odometer = last_motoh
            if self.total_km > 0 and last_km > 0:
                self.total_km = last_km
            else:
                self.total_km +=  diff_km

            # Нэмэгдүүлэлт байвал
            if diff > 0:
                motoh = diff
            if diff_km > 0:
                km = diff_km

            # Дугуйтай бол дугуй нэмэгдүүлэх
            if self.rubber_tired:
                for t_line in self.tire_line:
                    t_line.tire_id._increase_odometer(i_date, motoh, km, shift)
            # Компоненттэй бол компонент нэмэгдүүлэх
            if self.component_part_line:
                for c_line in self.component_part_line:
                    c_line._increase_odometer(i_date, motoh, shift)

    # Дугуйн мэдээлэл зурах
    def get_tire_line_datas(self, technic_id, context=None):
        data = {}
        obj = self.env['technic.equipment'].browse(technic_id)
        for line in obj.tire_line:
            data[line.position] = {'serial': line.serial,'tire_id': line.tire_id.id}
        return data

    def action_to_draft(self):
        self.state = 'draft'

    def action_to_parking(self):
        self.state = 'parking'

    def action_to_inactive(self):
        context = dict(self._context)
        context.update({'technic_id': self.id})
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'technic.retire.history.wizard',
            'view_mode': 'form',
            'context': context,
            'target': 'new',
        }

    def action_to_stop(self):
        self.state = 'stopped'

    def action_to_working(self):
        self.state = 'working'

    # Техникийн Баталгаат хугацаа шалгах - Крон метод - CRON
    def _get_warrenty_period(self):
        if self.with_warrenty:
            if self.start_date and self.technic_setting_id.warranty_period > 0:
                a = self.start_date
                b = datetime.now().date()
                delta = b - a
                days = self.warranty_period * 30
                return days - delta.days
            else:
                return 0
        else:
            return -1

    def _get_warrenty_odometer(self):
        if self.with_warrenty:
            if self.technic_setting_id.warranty_odometer > 0:
                delta = self.technic_setting_id.warranty_odometer - (self.total_odometer if self.odometer_unit == 'motoh' else self.total_km)
                return delta
            else:
                return 0
        return -1

    def test_check_technic_warrenty(self):
        self._check_technic_warrenty()

    @api.model
    def _check_technic_warrenty(self):
        technics = self.env['technic.equipment'].search([
                ('state','!=','draft'),
                ('owner_type','=','own_asset'),
                ('with_warrenty','=',True)
                ], order='report_order, program_code')
        msg = []
        for line in technics:
            txt = ""
            days = line._get_warrenty_period()
            if 0 < days and days < 6:
                txt = u"%d Өдөр дутуу байна" % days
            motoh = line._get_warrenty_odometer()
            if 0 < motoh and motoh < 100:
                txt += u"%d Гүйлт дутуу байна" % motoh

            if txt:
                msg.append(str(line.program_code)+': '+txt)
        if msg:
            # Get group
            res_model = self.env['ir.model.data'].search([
                ('module','=','mw_technic_equipment'),
                ('name','in',['group_technic_module_admin'])])
            group = self.env['res.groups'].search([('id','in',res_model.mapped('res_id'))])
            partners = []
            for receiver in group.users:
                if receiver.partner_id:
                    if self.env.user.partner_id.id != receiver.partner_id.id:
                        partners.append(receiver.partner_id)
            html = u"<span style='font-size:8pt; font-weight:bold; color:blue;'>Баталгаат хугацаа дуусч байгаа:<br/>" + ','.join(msg)+'</span>'
            # self.env.user.send_chat(html, partners)
            self.env.user.send_emails(partners=partners,body=html, attachment_ids=False)

    @api.model
    def _check_technic_insurance(self):
        today = datetime.now()
        date_stop = today + timedelta(days=7)
        msg = []
        # Даатгалын огноо шалгах
        technics = self.env['technic.equipment'].search([
                ('state','!=','draft'),
                ('insurance_date_end','=',date_stop.date()),
                ('with_insurance','=',True)
                ], order='report_order, program_code')
        for tt in technics:
            txt = "%s-ын даатгал(%s)" % (tt.park_number, tt.insurance_date_end.strftime("%Y-%m-%d"))
            msg.append(txt)
        # Татвар огноо шалгах
        technics = self.env['technic.equipment'].search([
                ('state','!=','draft'),
                ('state_tax_date_end','=',date_stop.date()),
                ('with_insurance','=',True)
                ], order='report_order, program_code')
        for tt in technics:
            txt = "%s-ын татвар(%s)" % (tt.park_number, tt.insurance_date_end.strftime("%Y-%m-%d"))
            msg.append(txt)
        # Үзлэг огноо шалгах
        technics = self.env['technic.equipment'].search([
                ('state','!=','draft'),
                ('state_inspection_date_end','=',date_stop.date()),
                ('with_insurance','=',True)
                ], order='report_order, program_code')
        for tt in technics:
            txt = "%s-ын үзлэг(%s)" % (tt.park_number, tt.insurance_date_end.strftime("%Y-%m-%d"))
            msg.append(txt)

        # ===========================
        if msg:
            # Get group
            res_model = self.env['ir.model.data'].search([
                ('module','=','mw_technic_equipment'),
                ('name','in',['group_technic_insurance_user'])])
            group = self.env['res.groups'].search([('id','in',res_model.mapped('res_id'))])
            partner_ids = group.mapped('users.partner_id')
            html = u"<span style='font-size:8pt; font-weight:bold; color:blue;'>Хугацаа дуусч байгаа:<br/>" + ','.join(msg)+'</span>'
            # self.env.user.send_chat(html, partner_ids)
            self.env.user.send_emails(partners=partner_ids, body=html, attachment_ids=False)

class TechnicTireLine(models.Model):
	_name = 'technic.tire.line'
	_description = 'Tire info on Vehicle'
	_order = 'position'

	date = fields.Date(string=u'Дугуйг тавьсан өдөр', required=True)
	technic_id = fields.Many2one('technic.equipment', string='Техник', ondelete='cascade')
	technic_odometer = fields.Float(string='Техникийн гүйлт',digits = (16,1))
	tire_id = fields.Many2one('technic.tire', string='Дугуй')
	current_odometer_value = fields.Float(related='tire_id.total_moto_hour', string=u'Одоогийн гүйлт',digits = (16,1), readonly=True, )
	warning_deep = fields.Selection(related='tire_id.warning_deep', string=u'Анхааруулах статус', readonly=True, )
	new_or_old = fields.Selection(related='tire_id.new_or_old',
		string=u'Дугуйны шилжилт', readonly=True, store=True)

	brand = fields.Many2one('technic.model.brand', string='Үйлдвэрлэгч', required=True)
	serial = fields.Char(string='Сериал', required=True)
	position = fields.Integer(string='Байрлал', required=True)
	odometer_value = fields.Float(string='Дугуйн гүйлт',digits = (16,1), required=True,
		help=u"Дугуйг суурьлуулах үеийн гүйлт")
	odometer_km = fields.Float(string=u'Дугуйн КМ',digits = (16,1), required=True)
	set_tread_depreciation = fields.Float(string='Суурьлуулсан үеийн хээний(%)',digits = (16,1), required=True)
	current_tread_depreciation = fields.Float(related='tire_id.tread_depreciation_percent', string='Одоогийн хээний(%)', readonly=True, )
	state = fields.Selection([
					('draft','Draft'),
					('set','Set')], string='Төлөв',required=True)

	@api.constrains('technic_id', 'tire_id')
	def _check_tire_counts(self):
		for obj in self:
			if obj.technic_id.technic_setting_id.tire_counts < len(obj.technic_id.tire_line):
				raise ValidationError(_('Анхааруулга!\nТехникийн нийт дугуйны тоо тохиргооноос их байна!'))

	_sql_constraints = [
		('technic_position_uniq', 'unique(technic_id, position)','Техник дээр байрлал давхардсан байна!')]

class TechnicOdometerIncrease(models.TransientModel):
	_name = 'technic.odometer.increase'
	_description = 'Technic odometer increase'

	# Columns
	date = fields.Date('Огноо', required=True)
	last_odometer =  fields.Float('Сүүлийн гүйлт',digits = (16,1), required=True,)
	last_km =  fields.Float(u'Сүүлийн KM',digits = (16,1), required=True,)

	def save_and_increase(self):
		if self._context.get('technic_id'):
			technic = self.env['technic.equipment'].browse(self._context.get('technic_id'))
			technic._increase_odometer(self.date, self.last_odometer, self.last_km, 0, 0, 'day',True)
		return True

class TechnicDepreciationLine(models.Model):
	_name = 'technic.depreciation.line'
	_description = 'Technic depreciation history'
	_order = 'date desc'

	date = fields.Date(string='Огноо', required=True, readonly=True)
	technic_id = fields.Many2one('technic.equipment', string='Техник', required=True, readonly=True)
	current_motoh =  fields.Float(string='Гүйлт', digits = (16,1), readonly=True)
	start_motoh = fields.Float(string="Эхлэхэд гүйлт", digits = (16,1), readonly=True)
	end_motoh = fields.Float(string="Дуусхад гүйлт", digits = (16,1), readonly=True)
	start_km = fields.Float(string="Эхлэхэд км", digits = (16,1), readonly=True)
	end_km = fields.Float(string="Эхлэхэд км", digits = (16,1), readonly=True)
	increasing_motoh =  fields.Float(string=u'Нэмэгдүүлсэн мото/ц', digits = (16,1), readonly=True)
	increasing_km =  fields.Float(string=u'Нэмэгдүүлсэн КМ', digits = (16,1), readonly=True)
	odometer_unit = fields.Selection(ODOMETER_UNIT, string="Гүйлт хэмжих нэгж", readonly=True)
	user_id = fields.Many2one('res.users', string='Бүртгэсэн', required=True, readonly=True)
	shift = fields.Selection([
			('day', u'Өдөр'),
			('night', u'Шөнө'),],
			string=u'Ээлж', readonly=True)

class TechnicMoveHistory(models.Model):
	_name = 'technic.move.history'
	_description = 'Technic move history'
	_order = 'date desc'

	technic_id = fields.Many2one('technic.equipment', string='Техник', ondelete='cascade',)
	date = fields.Date(string=u'Огноо', required=True, default=datetime.now())
	moto_hour = fields.Float(string=u'Мото цаг',digits = (16,1), help=u'Шилжих үеийн мото цаг',
		required=True, )
	km = fields.Float(string=u'Километр',digits = (16,1), help=u'Шилжих үеийн километр',
		required=True, )
	old_branch_id = fields.Many2one('res.branch', string=u'Хуучин төсөл', readonly=True, )
	new_branch_id = fields.Many2one('res.branch', string=u'Шинэ төсөл', required=True)
	move_type = fields.Selection([('move','Төсөл хооронд шилжсэн'),('sale','Зарагдсан'),('rent','Түрээслэсэн')])
	user = fields.Many2one('res.users', string=u'Төлөвлөгч', readonly=True, )
	description = fields.Char(string=u'Тайлбар')

class TechnicMoveHistoryWizard(models.TransientModel):
	_name = 'technic.move.history.wizard'
	_description = 'Technic move history wizard'
	_order = 'date desc'

	@api.model
	def _get_branch(self):
		if 'technic_id' in self.env.context:
			t = self.env['technic.equipment'].search([('id','=',self.env.context['technic_id'])])
			if t:
				return t.branch_id.id
		else:
			return False
	@api.model
	def _get_motohour(self):
		if 'technic_id' in self.env.context:
			t = self.env['technic.equipment'].search([('id','=',self.env.context['technic_id'])])
			if t:
				return t.total_odometer
		else:
			return 0

	@api.model
	def _get_km(self):
		if 'technic_id' in self.env.context:
			t = self.env['technic.equipment'].search([('id','=',self.env.context['technic_id'])])
			if t:
				return t.total_km
		else:
			return 0

	@api.model
	def _get_user(self):
		return self.env.user.id

	date = fields.Date(string=u'Огноо', required=True, default=datetime.now())
	moto_hour = fields.Float(string=u'Мото цаг',digits = (16,1), help=u'Шилжих үеийн мото цаг',
		required=True, default=_get_motohour)
	km = fields.Float(string=u'Километр',digits = (16,1), help=u'Шилжих үеийн километр',
		required=True, default=_get_km)
	old_branch_id = fields.Many2one('res.branch', string=u'Хуучин төсөл', readonly=True,
		default=_get_branch)
	new_branch_id = fields.Many2one('res.branch', string=u'Шинэ төсөл', required=True)
	user = fields.Many2one('res.users', string=u'Төлөвлөгч', readonly=True, default=_get_user)
	description = fields.Char(string=u'Тайлбар')

	def create_move_history(self):
		if self.old_branch_id.id == self.new_branch_id.id:
			raise UserError(_('Same branch names!'))
		if self._context.get('technic_id'):
			vals = {
				'technic_id': self._context.get('technic_id'),
				'date': self.date,
				'moto_hour': self.moto_hour,
				'km': self.km,
				'old_branch_id': self.old_branch_id.id,
				'new_branch_id': self.new_branch_id.id,
				'user': self.env.user.id,
				'description': self.description,
			}
			history = self.env['technic.move.history'].create(vals)
			t = self.env['technic.equipment'].search([('id','=',self.env.context['technic_id'])])
			t.branch_id = self.new_branch_id.id
			# Дугуйны төсөл солих
			for tline in t.tire_line:
				tline.tire_id.brand_id = self.new_branch_id.id
		return True

# Актлах
class TechnicRetireHistoryWizard(models.TransientModel):
	_name = 'technic.retire.history.wizard'
	_description = 'Technic retire history wizard'

	@api.model
	def _get_user(self):
		return self.env.user.id

	date = fields.Date(string=u'Огноо', required=True, default=datetime.now())
	user = fields.Many2one('res.users',string=u'Төлөвлөгч', readonly=True, default=_get_user)
	description = fields.Text(string=u'Тайлбар', required=True,)

	attachment_ids = fields.Many2many('ir.attachment', string=u'Хавсралтууд', required=True,)

	def technic_retire_history(self):
		if not self.attachment_ids:
			raise UserError(_('Актлахтай холбоотой баримтыг хавсаргана уу!'))

		if self._context.get('technic_id'):
			t = self.env['technic.equipment'].search([('id','=',self.env.context['technic_id'])], limit=1)
			vals = {
				'technic_id': self._context.get('technic_id'),
				'moto_hour': t.total_odometer,
				'km': t.total_km,
				'date': self.date,
				'new_branch_id': t.branch_id.id,
				'user': self.env.user.id,
				'description': self.description,
			}
			history = self.env['technic.move.history'].create(vals)
			t.retire_attachment_ids = self.attachment_ids
			t.state = 'inactive'
		elif self._context.get('component_id'):
			cc = self.env['technic.component.part'].search([('id','=',self.env.context['component_id'])], limit=1)
			# Ашиглалтын түүх оруулах
			vals = {
				'parent_id': cc.id,
				'date': self.date,
				'technic_id': cc.current_technic_id.id,
				'technic_odometer': cc.current_technic_id.total_odometer or 0,
				'component_odometer': cc.total_odometer,
				'description': 'Retired: '+self.description,
			}
			self.env['component.used.history'].sudo().create(vals)
			cc.retire_attachment_ids = self.attachment_ids
			cc.date_of_retired = self.date
			cc.retired_description = self.description
			cc.state = 'retired'
		return True

class res_partner(models.Model):
	_inherit = 'res.partner'

	technic_ids = fields.One2many('technic.equipment', 'partner_id', string='Техникүүд', groups='mw_technic_equipment.group_technic_module_user', readonly=True)

class WaterWell(models.Model):
	_name = 'water.well'
	_description = 'Water well'
	_rec_name = 'water_well'
	# _order = 'name'

  # Худагны бүртгэл
	water_well = fields.Char(string=u'Бүртгэл', required=True)
	technic_type = fields.Selection([('well','Худаг'),('technic','Тоног төхөөрөмж')], string='Төрөл')

class WellWaterRecord(models.Model):
	_name = 'well.water.record'
	_description = 'Well Water Record'
	# _name = 'Усны заалт'
	# _order = 'name'

  # Худагын усны бүртгэл
	date_start = fields.Date(string='Эхлэх Огноо', required=True)
	date_end = fields.Date(string='Дуусах Огноо', required=True)
	line_ids = fields.One2many('well.water.record.line','parent_id',string=u'Lines')
	technic_line_ids = fields.One2many('well.water.record.line','technic_parent_id',string=u'technic lines')
	technic_type = fields.Selection([('well','Худаг'),('technic','Тоног төхөөрөмж')], string='Төрөл')

class WellWaterRecordLine(models.Model):
	_name = 'well.water.record.line'
	_description = 'Well Water Record Lines'
	_order = 'water_well_id'

  # Худагын усны бүртгэл
	parent_id = fields.Many2one('well.water.record',string=u'Parent', readonly=True)
	technic_parent_id = fields.Many2one('well.water.record',string=u'Technic', readonly=True)
	water_well_id = fields.Many2one('water.well', string='Бүртгэл', required=True)
	start_counter = fields.Float(string='Эхний хэмжилт')
	end_counter = fields.Float(string='Төгсгөл хэмжилт')
	diff_value = fields.Float(compute="compute_diff_value", string="Зөрүү", store=True)

	@api.depends('end_counter', 'start_counter')
	def compute_diff_value(self):
		for item in self:
			item.diff_value = item.end_counter - item.start_counter

# class WaterRecord(models.Model):
#     _name = 'water.record'
#     _description = 'Water Record'

#     date = fields.Date(string='Огноо', required=True)
#     user_id = fields.Many2one(string='Бүртгэсэн', required=True)
#     line_ids = fields.One2many('water.record','parent_id',string=u'Lines')

# class WaterRecordLine(models.Model):
#     _name = 'water.record.line'
#     _description = 'Water Record Lines'
#     _order = 'water_record_id'

#     device = fields.One2many('water.record', string=u'Lines')
#     date = fields.Date(string='Огноо', required=True)

# Ajiltnii medeelel deer holbootoi tehnikiig haruulahiin tuld nemev
class HrEmployee(models.Model):
	_inherit = "hr.employee"

	def action_technic_eq(self):
		self.ensure_one()
		action = self.env["ir.actions.actions"]._for_xml_id(
			'mw_technic_equipment.action_technic_equipment')
		action['domain'] = [('partner_id', '=', self.user_partner_id.id)]
		action['res_id'] = self.id
		return action

class ElectricTechnical(models.Model):
	_name = 'electric.technical'
	_description = 'electric.technical'

	# Basic parameters
	date = fields.Date(string = 'Огноо')
	line_ids = fields.One2many('electric.record.lines' , 'parent_id' , string='Үзүүлэлтийн line' )

class ElectricRecord(models.Model):
	_name = 'electric.record'
	_description = 'Electric Record'
	_order = 'name'

	name =fields.Char(string = 'Үндсэн үзүүлэлт')

class ElectricRecordLines(models.Model):

	_name = 'electric.record.lines'
	_description = 'Electric Record Lines'
	# _order = 'electric.ids'

	parent_id = fields.Many2one('electric.technical',string=u'Parent', readonly=True)
	line_id = fields.One2many('electric.record.line' , 'parent_id' , string='Бүртгэл')
	shch_butluur = fields.Char(string = 'ШЧ-ны бутлуур')
	nuursnii_butluur = fields.Char(string = 'Нүүрсний бутлуур')
	tuuhii_ediin_teerem = fields.Char(string = 'Түүхий эдийн тээрэм')
	nuursnii_teerem = fields.Char(string = 'Нүүрсний тээрэм')
	ergeh_zuuh = fields.Char(string = 'Эргэх зуух')
	cement_teerem = fields.Char(string = 'Цементийн тээрэм')
	sawlah = fields.Char(string = 'Савлах')
	

class ElectricRecordLine(models.Model):

	_name = 'electric.record.line'
	_description = 'Electric Record Line'
	# _order = 'electric_id'

	parent_id = fields.Many2one('electric.record.lines',string=u'Parent', readonly=True)
	types = fields.Float(string='Төрөл')
	basic_indicator = fields.Selection([
		('creation','Бүтээл/т/'),
		('capacity','Хүчин чадал/т/цаг/'),
		('working_hours','Ажилласан цаг/цаг/'),
		('eh_norm','ЭХ-ний норм/кВт/т/'),
		('eh_speding','ЭХ-ний зарцуулалт/кВт*цаг/'),
		('stoppage_time','Оргил цагаар зогсолт хийх цаг /цаг/')
	], string='Үндсэн үзүүлэлт')

	types = fields.Selection([
		('het','Хэт'),
		('hem','Хэм'),
	], string='Төрөл')
	