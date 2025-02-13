# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo.exceptions import UserError
from datetime import datetime, timedelta
import pytz
import logging
_logger = logging.getLogger(__name__)


class power_workorder(models.Model):
	_name = 'power.workorder'
	_inherit = ['mail.thread']
	_description = 'power workorder'
	_order = 'date desc, shift'

	number = fields.Char('ELECTRICAL ORDER: EO', readonly=True, copy=False)
	page_number = fields.Char('Ажлын захиаллага')
	date = fields.Date(
		'Огноо', default=fields.Date.context_today, required=True)
	state = fields.Selection([
		('draft', 'Ноорог'),
		('open', 'Нээгдсэн'),
		('confirmed', 'Баталгаажсан'),
		('waiting_part', u'Зарлага Хүлээж Буй'),
		('ordered_part', u'Сэлбэг Хүлээж Буй'),
		('processing', u'Хийгдэж байгаа'),
		('finished', u'Дууссан'),
		('done', 'Хаагдсан'),
		('cancel', 'Цуцлагдсан')], string='Төлөв', default='draft', track_visibility='onchange')
	shift = fields.Selection([('night', 'Шөнө'), ('day', 'Өдөр')],
							 string='Ээлж', default='day', track_visibility='onchange')
	customer_department_id = fields.Many2one(
		'power.selection', domain="[('type','=','company_department')]", string='Захиалагч байгууллага Хэлтэс')
	customer_partner_id = fields.Many2one(
		'res.partner',  string='Ажилын хүсэлт гаргагч', default=lambda self: self.env.user.partner_id.id,)
	breakdown_id = fields.Many2one(
		'power.selection', domain="[('type','=','breakdown')]", string='Эвдрэлийн Мэдээлэл')
	breakdown_note = fields.Text(string='Эвдрэлийн Мэдээлэл')
	time_start = fields.Float('Эхэлсэн цаг:')
	time_end = fields.Float('Дууссан цаг:')
	time_plan = fields.Float('Төлөвлөсөн цаг:')
	time_spent = fields.Float(
		'Зарцуулсан цаг:', compute='_compute_time_spent', store=True)
	time_extend_hour = fields.Float(
		'Сунаж ажилласан цаг:', compute='_compute_time_spent', store=True)
	priority = fields.Selection([('1', u'1'),
								 ('2', u'2'),
								 ('3', u'3')], string='Зэрэглэл', default='1', track_visibility='onchange')
	work_type_id = fields.Many2one(
		'power.selection', domain="[('type','=','work_type')]",  string='Ажлын хүсэлтийн төрөл')

	done_desc = fields.Text('Гүйцэтгэлийн тайлбар')
	completed_repairs = fields.Text('Хийгдэх ажил:')
	partner_add = fields.One2many(
		'power.workorder.partner', 'workorder_id', string='Захиалагч дэлгэрэнгүй')

	warehouse_config_id = fields.Many2one(
		'power.warehouse.config', string='Агуулахын тохиргоо')
	product_expense_ids = fields.One2many(
		'power.product', 'workorder_id', string='Шаардлагатай байгаа бараа материал')
	stock_move_ids = fields.One2many(
		'stock.move', compute='_compute_stock_move_ids')
	user_id = fields.Many2one(
		'res.users',  string='Хариуцагч', default=lambda self: self.env.user.id)
	open_user_id = fields.Many2one(
		'res.users',  string='Нээсэн хэрэглэгч', readonly=True)
	confirmed_user_id = fields.Many2one(
		'res.users',  string='Баталгаажсан хэрэглэгч', readonly=True)
	done_user_id = fields.Many2one(
		'res.users',  string='Хаасан хэрэглэгч', readonly=True)

	brigad_ids = fields.One2many(
		'power.workorder.brigad', 'workorder_id', string='Ажилласан Бригад')
	picking_count = fields.Integer('Тоо', compute='_compute_picking_count')

	device_type = fields.Selection([('power_device', 'Тоног төхөөрөмж/Цахилгаан/'), ('device',
								   'Тоног төхөөрөмж')], string='Төрөл', track_visibility='onchange', default='device')
	power_device_id = fields.Many2one(
		'power.category', domain="[('main_type','in',['group','categ'])]", string='Тоног төхөөрөмж/Цахилгаан/')
	device_id = fields.Many2one(
		'power.selection', domain="[('type','in',['technic','object'])]", string='Тоног төхөөрөмж')
	asset_id = fields.Many2one(
		'power.category', domain="[('main_type','=','asset'),('parent_id','child_of',power_device_id)]", string='Хөрөнгө')
	level_id = fields.Many2one(
		'power.selection', domain="[('type','=','power_level')]", string='Хүчдлийн түвшин', track_visibility='onchange')
	work_type_id = fields.Many2one(
		'power.selection', domain="[('type','=','work_type')]",  string='Ажлын төрөл')
	technic_id = fields.Many2one(
		'technic.equipment', string='Сонгогдсон техник', compute='_compute_technic_id')
	origin = fields.Char('Эх Баримт')
	print_count = fields.Integer(
		string=u'Хэвлэсэн Тоо', readonly=True, default=0, copy=False)
	total_cost = fields.Float(
		string='Нийт Өртөг', compute_sudo=True, compute='_compute_total_cost', store=True)
	is_expensive = fields.Boolean(
		'Үнэтэй эсэх', compute='_compute_total_cost', store=True)
	chairman_user_id = fields.Many2one(
		'res.users',  string='УД', readonly=True, track_visibility='onchange')
	chairman_deputy_user_id = fields.Many2one(
		'res.users',  string='УОД', readonly=True, track_visibility='onchange')
	down_id = fields.Many2one(
		'power.down', string='Үйл Ажиллагаанд', readonly=True)

	@api.depends('product_expense_ids')
	def _compute_total_cost(self):
		for item in self.sudo():
			item.sudo().total_cost = sum(item.sudo().product_expense_ids.mapped('total_cost'))
			if item.sudo().total_cost >= 5000000:
				item.is_expensive = True
			else:
				item.is_expensive = False

	def _compute_stock_move_ids(self):
		for item in self:
			item.stock_move_ids = item.mapped(
				'product_expense_ids.stock_move_ids').ids

	@api.onchange('device_type')
	def onch_device_type(self):
		if self.device_type == 'power_device':
			self.device_id = False
		elif self.device_type == 'device':
			self.power_device_id = False
			self.asset_id = False

	@api.depends('device_id')
	def _compute_technic_id(self):
		for item in self:
			technic = item.device_id.technic_id
			item.technic_id = technic.id if technic else False

	@api.depends('time_start', 'time_end', 'shift', 'time_plan')
	def _compute_time_spent(self):
		for item in self:
			if item.shift == 'night' and item.time_end < item.time_start:
				item.time_spent = item.time_end+24-item.time_start
			else:
				item.time_spent = item.time_end-item.time_start
			ex_hour = 0
			if item.shift == 'night' and item.time_plan < item.time_spent:
				ex_hour = item.time_plan+24-item.time_spent
			else:
				ex_hour = item.time_plan-item.time_spent
			item.time_extend_hour = 0 if ex_hour < 0 else ex_hour

	_sql_constraints = [
		('wo_name_uniq', 'unique(number)', 'Name must be unique!')]

	@api.depends('date', 'shift', 'device_id', 'power_device_id')
	def name_get(self):
		result = []
		for s in self:
			d_name = ''
			if s.device_id and s.device_type == 'device':
				d_name = s.device_id.display_name
			elif s.power_device_id:
				d_name = s.power_device_id.display_name
			name = (s.number or '')+' / ' + \
				(unicode(s.date) or '') + ' / ' + (s.shift or '')
			if d_name:
				name += ' / '+d_name
			result.append((s.id, name))
		return result

	def _set_wo_sequence(self):
		temp = '1'
		wos = self.env['power.workorder'].search([
			('date', '=', self.date),
			# ('state','not in',['draft','cancelled']),
			('number', '!=', False),
		], order='number desc', limit=1)
		_logger.info(
			u'-***********-NEW WO NUMBER--************* %d \n' % (wos.id))
		if wos:
			try:
				temp = str(int(wos.number[9:])+1)
			except Exception as e:
				pass
		number = 'EO'+self.date[2:4]+self.date[5:7] + \
			self.date[8:]+'-' + temp.zfill(3)
		return number

	# def action_to_waiting_part(self):
	#     self.state = 'waiting_part'

	def action_to_ready(self):
		# Дууссан байхад READY рүү ордоггүй болгох
		if self.state == 'closed':
			raise UserError('Хаагдсан WO ажлыг засах боломжгүй!')
		# MOVE шалгах
		not_done = self.stock_move_ids.filtered(
			lambda l: l.state not in ['done', 'cancel'])
		if not_done:
			raise UserError('Агуулахын зарлагын баримт дуусаагүй байна!')
		if self.product_expense_ids and self.picking_count == 0:
			raise UserError('Агуулахын зарлагын баримт ҮҮСЭЭГҮЙ байна!')
		self.state = 'processing'
		self.send_chat_next()

	def action_to_done(self):
		if self.stock_move_ids and self.stock_move_ids.filtered(lambda r: r.state not in ['done', 'cancel']):
			raise UserError('Агуулахын зарлага дуусаагүй байна дуусгана уу')
		self.done_user_id = self.env.user.id
		self.state = 'done'
		self.send_chat_next()

	def action_to_draft(self):
		self.state = 'draft'
		self.send_chat_next()

	def action_to_cancel(self):
		self.state = 'cancel'
		picking_ids = self.stock_move_ids.mapped('picking_id')
		for item in picking_ids:
			item.action_cancel()
		self.send_chat_next()

	def action_to_open(self):
		if not self.env.user.has_group('mw_power.group_power_dispatcher'):
			raise UserError(u'Цахилгааны диспетчер нээнэ')
		if not self.number:
			self.number = self._set_wo_sequence()
		self.open_user_id = self.env.user.id
		self.state = 'open'
		self.send_chat_next()

	def action_to_confirm(self):
		if not self.env.user.has_group('mw_power.group_power_engineer'):
			raise UserError(u'Цахилгааны инженер батлана')
		self.confirmed_user_id = self.env.user.id
		self.state = 'confirmed'
		self.send_chat_next()

	def get_chairman(self):
		return self.env['power.eo.user'].search([('type', '=', 'chairman')], limit=1).user_ids

	def get_chairman_deputy(self):
		return self.env['power.eo.user'].search([('type', '=', 'chairman_deputy')], limit=1).user_ids

	# def _check_night_expenses(self):
	#     if self.total_no_pm_amount > 5000000 and not self.engineer_user_id and not self.chief_user_id and not self.senior_user_id:
	#         raise UserError(_(u'Менежер, Инженер болон Удирдлагаар хянуулна уу!\nДараа нь хаана уу!'))
	#     return True
	def get_is_expensive(self):
		return self.is_expensive

	def action_to_create_picking(self):
		picking = False
		wh_ids = self.env['stock.warehouse']
		warehouse_ids = []
		warehouse_ids.extend(self.product_expense_ids.mapped('src_warehouse_id'))
		warehouse_ids.extend(self.warehouse_config_id.mapped('warehouse_id'))
		if not warehouse_ids:
			raise UserError((u'Сэлбэгийн зарлага хийх агуулахыг сонгоно уу!!'))
		if self.product_expense_ids and self.picking_count == 0:
			if self._get_is_night():
				picking = self.create_picking()
				self.state == 'waiting_part'
				self.send_chat_next()
			else:
				if self.get_is_expensive():
					if not self.chairman_deputy_user_id and self.env.user.id not in self.get_chairman_deputy().ids:
						raise UserError(u'Төслийн менежер Батлаагүй байна %s ' % (
							', '.join(self.get_chairman_deputy().mapped('name'))))
					elif not self.chairman_deputy_user_id and self.env.user.id in self.get_chairman_deputy().ids:
						self.chairman_deputy_user_id = self.env.user.id
					elif not self.chairman_user_id and self.env.user.id not in self.get_chairman().ids:
						raise UserError(u'УД Батлаагүй байна %s ' % (
							', '.join(self.get_chairman().mapped('name'))))
					elif not self.chairman_user_id and self.env.user.id in self.get_chairman().ids:
						self.chairman_user_id = self.env.user.id

				elif not self.env.user.has_group('mw_power.group_power_manager'):
					raise UserError(u'Цахилгааны МЕНЕЖЕР Зарлага үүсгэнэ')
				if self.get_is_expensive():
					if self.chairman_deputy_user_id and self.chairman_user_id:
						picking = self.create_picking()
						self.state = 'waiting_part'
					self.send_chat_next()
				else:
					picking = self.create_picking()
					self.state = 'waiting_part'
					self.send_chat_next()
		else:
			raise UserError('Зарлага аль хэдийн үүссэн байна')

	def _compute_picking_count(self):
		for item in self:
			pick_ids = item.product_expense_ids.mapped(
				'stock_move_ids.picking_id')
			not_cancel = pick_ids.filtered(lambda r: r.state != 'cancel')
			item.picking_count = len(not_cancel)

	def get_move_line(self, picking, technic_id, warehouse_id):
		for item in self.product_expense_ids.filtered(lambda r: r.src_warehouse_id == warehouse_id):
			product = item.product_id
			self.env['stock.move'].create({
				'picking_id': picking.id,
				'picking_type_id': picking.picking_type_id.id,
				'product_id': product.id,
				'company_id': picking.company_id.id,
				'date': picking.scheduled_date,
				'date_expected': picking.scheduled_date,
				'location_id': picking.location_id.id,
				'location_dest_id': picking.location_dest_id.id,
				'procure_method': 'make_to_stock',
				'product_uom': product.uom_id.id,
				'product_uom_qty': item.product_qty,
				'name': product.display_name+picking.origin,
				'state': 'draft',
				'power_product_id': item.id,
				'technic_id': technic_id.id if technic_id else False
			})

	def create_picking(self):
		if not self.product_expense_ids:
			return False
		if self.picking_count > 0:
			raise UserError(u'Агуулахын зарлага үүссэн байна')
		origin = 'ЦАХИЛГААН %s' % (self.display_name)
		if self.completed_repairs:
			origin += ' %s' % (self.completed_repairs)
		if self.asset_id:
			origin += ' %s' % (self.asset_id.display_name)
		warehouse_ids = []
		warehouse_ids.extend(self.product_expense_ids.mapped('src_warehouse_id'))
		warehouse_ids.extend(self.warehouse_config_id.mapped('warehouse_id'))
		picking_ids = []
		for warehouse in warehouse_ids:
			wh_id = warehouse
			if not wh_id:
				raise UserError(u'Цахилгааны агуулах тохируулагдаагүй байна')
			dest_id = self.env['stock.location'].search(
				[('usage', '=', 'customer')], limit=1)
			picking = self.env['stock.picking'].create({
				'picking_type_id': wh_id.out_type_id.id,
				'location_id': wh_id.lot_stock_id.id,
				'location_dest_id': dest_id.id,
				'move_type': 'direct',
				'origin': origin,
				'company_id': self.env.user.company_id.id,
				'scheduled_date': self.date,
				'state': 'draft',
				'technic_id2': self.technic_id.id or False
			})
			picking_ids.append(picking)
			self.get_move_line(picking, self.technic_id, wh_id)
			picking.action_confirm()
		# self.action_to_waiting_part()
		return picking_ids

	def view_picking_ids(self):
		tree_view_id = self.env.ref('stock.vpicktree').id
		form_view_id = self.env.ref('stock.view_picking_form').id
		return {
			'name': 'Хөдөлгөөн',
			'type': 'ir.actions.act_window',
			'view_mode': 'form',
			'res_model': 'stock.picking',
			'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
			'view_id': tree_view_id,
			'domain': [('id', 'in', self.stock_move_ids.mapped('picking_id').ids)],
			'context': {},
		}

	def unlink(self):
		for s in self:
			if s.state not in ['draft', 'cancelled']:
				raise UserError(
					'Ноорог болон Цуцлагдсан төлөвтэй бичлэгийг устгаж болно!')
			if s.stock_move_ids.filtered(lambda r: r.state not in ['cancel']):
				raise UserError('Агуулахын хөдөлгийн үүссэн байна')
		return super(power_workorder, self).unlink()

	def send_chat_next(self):
		partner_ids = []
		str_html = ''
		if self.state == 'open':
			group_id = self.env.ref("mw_power.group_power_engineer")
			str_html = 'Баталгаажуулна уу'
			partner_ids = group_id.mapped('users.partner_id')
			if self._get_is_night():
				self.state = 'confirmed'
		if self.state == 'confirmed' and self.product_expense_ids and self.get_is_expensive():
			if not self.chairman_deputy_user_id:
				partner_ids = self.get_chairman_deputy().mapped('partner_id')
			elif not self.chairman_user_id:
				partner_ids = self.get_chairman().mapped('partner_id')
			str_html = 'Цахилгааны Зарлага Батлана уу'

		elif self.state == 'confirmed' and self.product_expense_ids and not self.get_is_expensive():
			group_id = self.env.ref("mw_power.group_power_manager")
			str_html = 'Барааны зарлага үүсгэнэ үү'
			partner_ids = group_id.mapped('users.partner_id')
		elif self.state == 'confirmed' and not self.product_expense_ids:
			# group_id = self.env.ref( "mw_power.action_to_ready")
			str_html = ''
			partner_ids = self.user_id.partner_id
		if self.state == 'waiting_part':
			str_html = ''
			partner_ids = self.user_id.partner_id
		if self.state == 'processing':
			str_html = ''
			partner_ids = self.user_id.partner_id
		if partner_ids:
			state = dict(self._fields['state'].selection).get(self.state)
			html = u' Elecricatl Order </br>%s <b>%s</b> төлөвт орлоо <span style="color: blue;">%s</span>' % (
				self.get_url(), state, str_html)
			self.env['power.warehouse.config'].send_chat(html, partner_ids)

	def get_url(self):
		base_url = self.env['ir.config_parameter'].sudo(
		).get_param('web.base.url')
		action_id = self.env['ir.model.data'].get_object_reference(
			'mw_power', 'action_power_workorder_tree')[1]
		html = u"""<a target="_blank" href=%s/web#id=%s&view_type=form&model=power.workorder&action=%s>%s</a>""" % (
			base_url, self.id, action_id, self.number)
		return html

	def _get_shift_by_datetime(self, now):
		if now.strftime("%Y-%m-%d 06:30") < now.strftime("%Y-%m-%d %H:%M") and now.strftime("%Y-%m-%d %H:%M") < now.strftime("%Y-%m-%d 18:30"):
			return 'day'
		else:
			return 'night'

	def _get_is_night(self):
		date_time = datetime.now()
		tz = self.env.user.tz or 'Asia/Ulaanbaatar'
		timezone = pytz.timezone(tz)
		date_time = (date_time.replace(
			tzinfo=pytz.timezone('UTC'))).astimezone(timezone)
		# return True
		if self._get_shift_by_datetime(date_time) == 'night':
			return True
		return False

	@api.onchange('time_start', 'time_end', 'done_desc')
	def onch_time(self):
		if self.down_id:
			if self.time_end:
				if self.down_id.type in ['order']:
					self.down_id.write({'plug_time': self.time_end})
				elif self.down_id.type in ['plan']:
					self.down_id.write({'plug_time': self.time_end})
				elif self.down_id.type in ['call']:
					self.down_id.write({'call_time_end': self.time_end})
				elif self.down_id.type in ['daily']:
					self.down_id.write({'end_time': self.time_end})
			if self.time_start:
				if self.down_id.type in ['order']:
					self.down_id.write({'down_time': self.time_start})
				elif self.down_id.type in ['plan']:
					self.down_id.write({'down_time': self.time_start})
				elif self.down_id.type in ['call']:
					self.down_id.write({'call_time_start': self.time_start})
				elif self.down_id.type in ['daily']:
					self.down_id.write({'start_time': self.time_start})
			if self.done_desc:
				self.down_id.write({'description': self.done_desc})


class power_workorder_partner(models.Model):
	_name = 'power.workorder.partner'
	_description = 'power workorder partner'

	workorder_id = fields.Many2one('power.workorder', string='Parent')
	partner_name = fields.Char('Байгууллага')
	employee_name = fields.Char('Ажилтаны нэр')
	job_name = fields.Char('Албан тушаал')
	phone_number = fields.Char('Утасны дугаар')


class power_workorder_brigad(models.Model):
	_name = 'power.workorder.brigad'
	_description = 'power workorder brigad'

	workorder_id = fields.Many2one(
		'power.workorder', string='Parent', ondelete='cascade')
	employee_id = fields.Many2one('hr.employee', string='Ажилтан')
	time_start = fields.Float('Эхэлсэн цаг')
	time_end = fields.Float('Дууссан цаг')
	time_spent = fields.Float(
		'Зарцуулсан цаг:', compute='_compute_time_spent', store=True)

	@api.depends('time_start', 'time_end', 'workorder_id')
	def _compute_time_spent(self):
		for item in self:
			if item.workorder_id.shift == 'night' and item.time_end < item.time_start:
				item.time_spent = item.time_end+24-item.time_start
			else:
				item.time_spent = item.time_end-item.time_start
