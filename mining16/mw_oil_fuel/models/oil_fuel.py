# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo import _, tools
from odoo.exceptions import UserError, ValidationError, Warning
from datetime import date, datetime, timedelta
import collections
from calendar import monthrange
from io import BytesIO
import base64
import xlsxwriter
from tempfile import NamedTemporaryFile
import os,xlrd
from odoo.osv import expression

import logging
_logger = logging.getLogger(__name__)

class stock_picking(models.Model):
	_inherit = 'stock.picking'

	oil_fuel_line_ids = fields.One2many('oil.fuel','picking_id', 'Oil Fuel')
	oil_fuel_id = fields.Many2one('oil.fuel', 'Түлш Тосны бүртгэл', readonly=True)


	def get_user_signature(self,ids):
		res = super(stock_picking, self).get_user_signature(ids)
		report_id = self.browse(ids)
		if report_id.oil_fuel_line_ids:
			return report_id.oil_fuel_line_ids[0].get_user_signature(report_id.oil_fuel_line_ids[0].id)
		return res

	def action_view_oil_fuel_id_mw(self):
		view = self.env.ref('mw_oil_fuel.oil_fuel_form')
		return {
			'name': 'Түлш Тос',
			'type': 'ir.actions.act_window',
			'view_mode': 'form',
			'res_model': 'oil.fuel',
			'views': [(view.id, 'form')],
			'view_id': view.id,
			# 'target': 'new',
			'res_id': self.oil_fuel_line_ids[0].id or self.oil_fuel_id.id,
			'context': dict(
				self.env.context
			),
		}





class oil_fuel(models.Model):
	_name = 'oil.fuel'
	_inherit = ['mail.thread','analytic.mixin']
	_description = 'Oil fuel'
	_order = 'date desc, shift desc'

	@api.model
	def _default_get_tye(self):
		type = self.env.context.get('type', False)
		if type=='oil':
			return 'oil'
		elif type=='fuel_in':
			return 'fuel_in'
		return 'fuel'
	
	@api.model
	def create(self, vals):
		if not vals.get('name'):
			vals['name'] = self.env['ir.sequence'].next_by_code('oil.fuel') or 'New'
		return super(oil_fuel, self).create(vals)

	def admin_button(self):
		ids = self.env['oil.fuel'].sudo().search([('id','!=',False)])
		for item in ids:
			if item.picking_id not in item.picking_ids:
				item.picking_ids = item.picking_id
			if not item.name:
				item.name = self.env['ir.sequence'].next_by_code('oil.fuel') or 'New'

	@api.depends('picking_ids')
	def _comute_expense_picking_count(self):
		for item in self:
			item.picking_count = len(item.picking_ids)

	def action_view_expense_picking_ids(self):
		tree_view_id = self.env.ref('stock.vpicktree').id
		form_view_id = self.env.ref('stock.view_picking_form').id
		return {
			'name': 'Хөдөлгөөн',
			'type': 'ir.actions.act_window',
			'view_mode': 'form',
			'res_model': 'stock.picking',
			'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
			'view_id': tree_view_id,
			'domain': [('id','in',self.picking_ids.ids)],
			'context': {},
		}

	name = fields.Char('Нэр', readonly=True)
	date = fields.Date('Огноо', required=True)
	shift = fields.Selection([('day','Өдөр'), ('night','Шөнө')], string='Ээлж', required=True)
	line_ids = fields.One2many('oil.fuel.line','parent_id',string='Мөрүүд', copy=True)
	line_in_ids = fields.One2many('oil.fuel.line','parent_id',string='Мөрүүд орлогын', copy=True)
	state = fields.Selection([('draft','Ноорог'), ('check','Хянасан'),('done','Дууссан'),('cancel','Цуцласан')], default='draft', string='Төлөв', tracking=True)
	picking_id = fields.Many2one('stock.picking', string='Зарлагын баримт', readonly=True, copy=False)
	picking_ids = fields.One2many('stock.picking','oil_fuel_id', 'Баримтууд')
	picking_count = fields.Integer(u'Зарлагын баримтын тоо', readonly=True, compute='_comute_expense_picking_count')
	incoming_picking_id = fields.Many2one('stock.picking', string='Зөрүү орлого зарлагын Баримт', readonly=True)
	partner_id = fields.Many2one('res.partner', string='Нийлүүлэгч')
	warehouse_id = fields.Many2one('stock.warehouse', string='Агуулах')
	location_id = fields.Many2one('stock.location', string='Байрлал', domain=[('usage','=','internal')])
	type = fields.Selection([
		('fuel_in','Түлшний орлого'),
		('oil','Тос тосолгоо'),
		('fuel','Түлш')],
		default=_default_get_tye, string='Төрөл')
	# import_data = fields.Binary('Импортлох эксел', copy=False)
	import_data_ids = fields.Many2many('ir.attachment', 'oil_fuel_ir_attachment_rel', 'oil_fuel_id', 'attach_id', string='Импортлох эксел', copy=False)

	attachment_ids = fields.Many2many('ir.attachment', 'oil_fuel_ir_attachment_rel1', 'oil_fuel_id', 'attach_id', string='Импортлох эксел', copy=False)

	product_id = fields.Many2one('product.product', related='line_ids.product_id')

	sum_total = fields.Float(string='Нийт', compute='_compute_sum_expense', store=True)
	sum_in_total = fields.Float(string='Орлогын дүн', compute='_compute_sum_in_total', store=True)
	diff_in_total = fields.Float(string='Зөрүү дүн', compute='_compute_sum_in_total', store=True)
	purchase_order_id = fields.Many2one('purchase.order', string='Худалдан авалтын захиалга', readonly=True)

	is_view_check = fields.Boolean(string='Хянах харах', compute='_compute_state_view')
	is_view_done = fields.Boolean(string='Батлах харах', compute='_compute_state_view')

	warning_messages = fields.Html(string='Warning Message', compute='_compute_wc_messages')
	is_danger_norm = fields.Boolean(string='Хэмжээнээс хэтэрсэн', compute='_compute_wc_messages')

	technic_id = fields.Many2one('technic.equipment', related='line_ids.technic_id')
	product_id = fields.Many2one('product.product', related='line_ids.product_id')
	check_user_id = fields.Many2one('res.users', string='Хянасан Ажилтан')
	done_user_id = fields.Many2one('res.users', string='Батласан Ажилтан')
	company_id =fields.Many2one('res.company', string='Компани', default=lambda self: self.env.user.company_id)
	branch_id =fields.Many2one('res.branch', string='Салбар', default=lambda self: self.env.user.branch_id)
	desc = fields.Text(string='Тайлбар', tracking=True)
	sar_zuruutei = fields.Boolean(readonly=True, search='_search_sar_zuruutei', compute='com_sar_zuruutei', string='Агуулахын сар зөрүүтэй')
	account_id = fields.Many2one('account.account', string="Данс")

	def change_line_account(self):
		for item in self:
			if item.line_ids:
				for line in item.line_ids:
					if item.account_id:
						line.account_id = item.account_id.id
					if item.analytic_distribution:
						line.analytic_distribution = item.analytic_distribution
					if item.branch_id:
						line.branch_id = item.branch_id.id


	def com_sar_zuruutei(self):
		for item in self:
			item.sar_zuruutei = False

	def _search_sar_zuruutei(self, operator, value):
		query ="""
		select of.id from oil_fuel of
		left join stock_picking sp on (of.id=sp.oil_fuel_id)
		where to_char(of.date,'YYYY-MM')!= to_char(sp.date_done,'YYYY-MM')
		"""
		self.env.cr.execute(query)
		result  = self.env.cr.dictfetchall() 
		ids = []
		for item in result:
			ids.append(item['id'])
		# print ('ids',ids)
		return [('id', 'in', ids)]

	def get_user_signature(self,ids):
		report_id = self.browse(ids)
		html = '<table>'
		user_id = report_id.check_user_id
		image_str = ''
		if user_id.digital_signature:
			image_str = '<img alt="Embedded Image" width="240" src="data:image/png;base64,'+user_id.digital_signature+'" />'
		user_str =  '________________________'
		if user_id:
			user_str = user_id.name
		html += u'<tr><td><p>Тос Хянасан </p></td><td>'+image_str+u'</td><td> <p>/'+user_str+u'/</p></td></tr>'

		user_id = report_id.done_user_id
		image_str = ''
		if user_id.digital_signature:
			image_str = '<img alt="Embedded Image" width="240" src="data:image/png;base64,'+user_id.digital_signature+'" />'
		user_str =  '________________________'
		if user_id:
			user_str = user_id.name
		html += u'<tr><td><p>Тос Батласан </p></td><td>'+image_str+u'</td><td> <p>/'+user_str+u'/</p></td></tr>'


		html += '</table>'
		return html


	def action_compute_run_hour(self, multi_obj=False, obj_id=False):
		line_obj = self.env['oil.fuel.line']
		oil_obj = self.env['oil.fuel']
		if obj_id:
			obj_ids = self
		else:
			year = self.date.year
			month = self.date.month
			days = monthrange(year, month)[1]
			ds = datetime.strftime(self.date,'%Y-%m-01')
			de = datetime.strftime(self.date, '%Y-%m-' + str(days))
			obj_ids = oil_obj.search([('date', '>=', ds), ('date', '<=', de), ('type', '=', self.type)], order='date desc, shift desc')
		i = len(obj_ids)
		for item in obj_ids:
			j = len(item.line_ids)
			for line in item.line_ids:
				line._compute_before_line()
				_logger.info(u'-****-Fuel line --****- uldsen %s-' % (j))
				j -= 1
			_logger.info(u'-***********-Fuel update moto_hour --*************- uldsen %s-' % (i))
			i -= 1


	@api.depends('line_ids.product_id','line_ids.product_qty', 'line_ids.technic_id')
	def _compute_wc_messages(self):
		for item in self:
			message = []
			danger = False
			if item.type in ['oil'] and item.id:
				query = """
					SELECT
						oil_tem.technic_setting_id,
						oil_tem.categ_id,
						ofn.id as norm_id,
						ofn.is_danger,
						case when product_qty>coalesce(ofn.qty,0) then product_qty-ofn.qty else 0 end as product_qty
					FROM (
					SELECT te.technic_setting_id,pt.categ_id,sum(ofl.product_qty) as product_qty from oil_fuel_line  ofl
					left join technic_equipment te on (te.id=ofl.technic_id)
					left join product_product pp on (pp.id=ofl.product_id)
					left join product_template pt on (pt.id=pp.product_tmpl_id)
					where ofl.parent_id={0}
					group by 1,2
					) as oil_tem
						left join oil_fuel_norm ofn on (ofn.technic_setting_id=oil_tem.technic_setting_id and ofn.categ_id=oil_tem.categ_id)
					where ofn.id is not null and (case when product_qty>coalesce(ofn.qty,0) then product_qty-ofn.qty else 0 end)>0
					""".format(item.id)
				self.env.cr.execute(query)
				query_result = self.env.cr.fetchall()
				for line in query_result:
					t1_name = self.env['technic.equipment.setting'].sudo().browse(line[0])
					t2_name = self.env['product.category'].sudo().browse(line[1])
					if line[3]:
						danger=True
					val = u"""<tr><td><b>%s</b></td><td>%s</td><td>%s</td></tr>"""%(t2_name.display_name,t1_name.display_name, line[4])
					message.append(val)

				# product_ids = item.line_ids.mapped('product_id').ids
				# for line in item.line_ids.filtered(lambda r: r.norm_diff>0):
					# val = u"""<tr><td><b>%s</b></td><td>%s</td><td>%s</td></tr>"""%(line.product_id.display_name,line.technic_id.display_name, line.norm_diff)
					# message.append(val)
			elif item.type in ['fuel'] and item.id:
				message = []
				for line in item.line_ids:
					norm_diff = line.product_qty-line.technic_id.technic_setting_id.fuel_norm
					if norm_diff>0 and line.technic_id.technic_setting_id.fuel_norm>0:
						danger = True
						val = u"""<tr><td><b>%s</b></td><td>%s</td><td>%s</td></tr>"""%(line.product_id.display_name, line.technic_id.display_name, norm_diff)
						message.append(val)

			if message==[]:
				message = False
			else:
				message = u'<table style="width: 100%;"><tr><td colspan="4" style="text-align: center;">Нормоос Хэтэрсэн</td></tr><tr style="width: 40%;"><td style="width: 50%;">Барааны Ангилал</td> <td style="width: 30%;">Техник</td><td style="width: 10%;">Хэтэрсэн Хэмжээ</td></tr>'+u''.join(message)+u'</table>'
			item.warning_messages = message
			item.is_danger_norm = danger

	@api.depends('state','type')
	def _compute_state_view(self):
		for item in self:
			if item.state=='draft' and item.type in ['oil']:
				item.is_view_check = True
			else:
				item.is_view_check = False

			if item.state=='draft' and item.type in ['fuel_in','fuel']:
				item.is_view_done = True
			elif item.state=='check' and item.type in ['oil']:
				item.is_view_done = True
			else:
				item.is_view_done = False


	def update_date_move(self, move_lines, update_date):
		if move_lines.filtered(lambda r: r.state in ['draft','waiting','confirmed','partially_available','assigned']):
			raise UserError(u'Батлагдаагүй хөдөлгөөн байна ')

		for item in move_lines:
			check_date = str(item.date)[:10]
			time_date = str(item.date)[10:20]
			if update_date:
				set_date = update_date+time_date
			else:
				set_date = str(item.picking_id.scheduled_date)
			item.date = set_date
			item.date_expected = set_date

			move_line_ids = self.env['stock.move.line'].search([('move_id','=',item.id)])
			if move_line_ids:
				move_line_ids.write({'date':set_date})

			if item.picking_id:
				# item.picking_id.scheduled_date = set_date
				item.picking_id.date_done = set_date

			move_id = self.env['account.move'].search([('stock_move_id','=',item.id)], limit=1)
			if move_id:
				scheduled_date = datetime.strptime(set_date , "%Y-%m-%d %H:%M:%S")+timedelta(hours=8)
				sched_date = scheduled_date.strftime( "%Y-%m-%d")
				query = """
				UPDATE account_move set date='%s' where id=%s
				"""%(sched_date,move_id.id)

				self._cr.execute(query)
				query = """
				UPDATE account_move_line set date='%s' where move_id=%s
				"""%(sched_date,move_id.id)
				self._cr.execute(query)

	def action_update_date(self):
		if self.purchase_order_id:
			line_ids = self.env['stock.move'].search([('purchase_line_id.order_id','=',self.purchase_order_id.id)])
			self.update_date_move(line_ids, str(self.purchase_order_id.date_order)[:10])

		if self.picking_id:
			line_ids = self.picking_id.move_ids+self.picking_ids.mapped('move_ids')

			if self.type in ['fuel']:
				year = self.date.year
				month = self.date.month
				days = monthrange(year,month)[1]
				ds = datetime.strftime(self.date,'%Y-%m-01')
				de = datetime.strftime(self.date, '%Y-%m-' + str(days))
				#line_ids = self.env['oil.fuel'].search([('type','in',['fuel']), ('date','>=',ds), ('date','<=',de), ('partner_id','=',self.partner_id.id)]).mapped('picking_id').mapped('move_ids')
				for ooo in self.env['oil.fuel'].search([('type','in',['fuel']), ('date','>=',ds), ('date','<=',de), ('partner_id','=',self.partner_id.id)]):
					self.update_date_move(ooo.picking_id.move_ids, str(ooo.date))
			self.update_date_move(line_ids, False)

		if self.incoming_picking_id:
			line_ids = self.incoming_picking_id.move_ids
			self.update_date_move(line_ids, str(self.incoming_picking_id.scheduled_date)[:10])



	def action_create_po(self):
		if self.purchase_order_id:
			raise UserError(u'PO үүссэн байна')
		obj = self.env['oil.fuel']
		purchase_obj = self.env['purchase.order']
		purchase_line_obj = self.env['purchase.order.line']

		year = self.date.year
		month = self.date.year
		days = monthrange(year,month)[1]
		ds = datetime.strftime(self.date,'%Y-%m-01')
		de = datetime.strftime(self.date, '%Y-%m-' + str(days))
		obj_ids = obj.search([('date','>=',ds),
		('date','<=',de),('type','=','fuel_in'),
		('purchase_order_id','=',False),
		('partner_id','=',self.partner_id.id),
		('state','=','done'),
		('location_id','=',self.location_id.id),
		])

		date_set = set(obj_ids.mapped('date'))
		vals = {
			'date_order': ds+' 08:00:00',
			'picking_type_id': self.location_id.set_warehouse_id.in_type_id.id,
			'date_planned': self.date,
			'origin': ', '.join(date_set),
			'partner_id': self.partner_id.id,
			'state': 'draft',
		}
		linevals = []
		obj_line_ids = obj_ids.mapped('line_in_ids')
		product_ids = obj_line_ids.mapped('product_id')

		for item in product_ids:
			product_qty = sum(obj_line_ids.filtered(lambda r: r.product_id.id==item.id).mapped('product_qty'))

			linevals.append((0,0, {
				'product_id': item.id,
				'name': item.name,
				'date_planned': ds,
				'product_qty': product_qty,
				'price_unit': 1,
				'product_uom': item.uom_id.id,
			}))

		vals['order_line'] = linevals

		po_id = self.env['purchase.order'].create(vals)
		for item in po_id.order_line:
			item._onchange_quantity()
		for item in obj_ids:
			item.purchase_order_id = po_id.id


	def action_create_in_out(self):
		if self.incoming_picking_id:
			raise UserError(u'Зөрүүгийн орлогын Баримт үүссэн байна')
		picking_obj = self.env['stock.picking']
		move_obj = self.env['stock.move']
		location_id = self.env['stock.location'].search([('usage','=','supplier')], limit=1)
		location_dest_id = self.location_id

		wh_id = self.location_id.set_warehouse_id

		obj = self.env['oil.fuel']
		obj_line = self.env['oil.fuel.line']

		year = self.date.year
		month = self.date.month
		days = monthrange(year,month)[1]
		ds = datetime.strftime(self.date,'%Y-%m-01')
		de = datetime.strftime(self.date,'%Y-%m-' + str(days))
		obj_ids = obj.search([('date','>=',ds),('date','<=',de),('type','=','fuel'),('partner_id','=',self.partner_id.id),('incoming_picking_id','=',False)])
		sum_product_qty = sum(obj_ids.mapped('diff_in_total'))
		date_set = set([str(x) for x in obj_ids.mapped('date')])
		name = (', '.join(date_set)+u' Зөрүүгийн орлого') or ''
		pick_type_id = wh_id.in_type_id
		if sum_product_qty>0:
			name = (', '.join(date_set)+u' Зөрүүгийн зарлага') or ''
			pick_type_id = wh_id.out_type_id
			location_id = location_dest_id
			location_dest_id = location_id

		sum_product_qty = abs(sum_product_qty)
		picking_id = picking_obj.create({
				'picking_type_id': pick_type_id.id,
				'location_id': location_id.id,
				'location_dest_id': location_dest_id.id,
				'scheduled_date': ds,
				'move_ids': [],
				'origin': name,
				'partner_id': self.partner_id.id,
			})
		product_id = self.line_ids[0].product_id
		move_ids = []
		# for item in product_ids:

		move ={
			'partner_id': self.partner_id.id,
			'name': name+u' '+product_id.name,
			'product_id': product_id.id,
			'product_uom': product_id.uom_id.id,
			'product_uom_qty': sum_product_qty,
			'picking_type_id': wh_id.out_type_id.id,
			'location_id': location_id.id,
			'location_dest_id': location_dest_id.id,
			'date_deadline': ds,
			'picking_id': picking_id.id,
		}
		move_id = move_obj.create(move)
		move_id._action_confirm()

		obj_ids.write({'incoming_picking_id':picking_id.id})

	def action_view_in_out_account(self):
		if not self.incoming_picking_id:
			return False
		account_move_ids = self.env['account.move'].search([('stock_move_id','in',self.incoming_picking_id.move_ids.ids)])
		context = {}
		context['create']= False
		tree_view_id = self.env.ref('account.view_move_tree').id
		form_view_id = self.env.ref('account.view_move_form').id
		action = {
				'name': self.name,
				'view_mode': 'tree',
				'res_model': 'account.move',
				'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
				'view_id': tree_view_id,
				'domain': [('id','in',account_move_ids.ids)],
				'type': 'ir.actions.act_window',
				'context': context,
				'target': 'current'
			}
		return action


	@api.depends('line_ids.product_qty','line_in_ids.product_qty')
	def _compute_sum_expense(self):
		for item in self:
			if item.type=='fuel_in':
				item.sum_total = sum(item.line_in_ids.mapped('product_qty'))
			else:
				item.sum_total = sum(item.line_ids.mapped('product_qty'))


	@api.depends('date','partner_id','shift','location_id', 'line_ids.product_qty')
	def _compute_sum_in_total(self):
		for item in self:
			if item.type in ['fuel']:
				sum_in_total = sum(self.env['oil.fuel'].search([('type','=','fuel_in'),('date','=',item.date),('shift','=',item.shift),('partner_id','=',item.partner_id.id),('location_id','=',item.location_id.id)]).mapped('sum_total'))
				item.sum_in_total = sum_in_total
				item.diff_in_total = sum_in_total-item.sum_total

	def create_expense_picking(self):
		if self.picking_id:
			raise UserError(u'Агуулахын үүссэн хөдөлгөөн байна')
		picking_obj = self.env['stock.picking']
		move_obj = self.env['stock.move']
		location_id = self.location_id
		location_dest_id = self.env['stock.location'].search([('usage','=','customer')], limit=1)
		name = (str(self.name or '')+u' Зарлага') or ''
		if self.desc:
			name +=' '+self.desc 
		line_names = ', '.join(self.line_ids.filtered(lambda r: r.desc).mapped('name'))
		if line_names:
			name +='\n'+line_names
		wh_id = self.location_id.set_warehouse_id
		picking_id = picking_obj.create({
				'picking_type_id': wh_id.out_type_id.id,
				'location_id': location_id.id,
				'location_dest_id': location_dest_id.id,
				'scheduled_date': self.date,
				'move_ids': [],
				'origin': name,
				'oil_fuel_id': self.id,
			})
		move_ids = []

		if self.is_danger_norm:
			raise UserError(u'Нормоос Хэтэрсэн байна батлах боломжгүй')

		for item in self.line_ids:

			if not item.product_id:
				raise UserError(u'%s техник дээр бараа сонгогдоогүй байна'%(item.technic_id.name))

			move ={
				'name': name+u' '+item.product_id.name,
				'product_id': item.product_id.id,
				'product_uom': item.product_id.uom_id.id,
				'product_uom_qty': item.product_qty,
				'picking_type_id': wh_id.out_type_id.id,
				'location_id': location_id.id,
				'location_dest_id': location_dest_id.id,
				'date_deadline': self.date,
				'picking_id': picking_id.id,
				'technic_id2': item.technic_id.id if item.technic_id else False,
				# stock move deer shiftgui bolgov bhgui bsan daraa uchiriig ni olno
				# 'shift': self.shift,
				}
			move_id = move_obj.create(move)
			move_id._action_confirm(merge=False, merge_into=False)

		# if picking_id:
		#     picking_id.action_confirm()

		self.picking_id = picking_id.id


	# @api.depends('date','shift')
	# def _compute_name(self):
	#     for item in self:
	#         item.name = str(item.date)+' '+str(item.shift)+' '+str(item.type)


	def send_chat(self, html, partner_ids):
		if not partner_ids:
			raise UserError(u'Мэдэгдэл хүргэх харилцагч байхгүй байна!!!')
		channel_obj = self.env['mail.channel']
		for item in partner_ids:
			if self.env.user.partner_id.id!=item.id:
				channel_ids = channel_obj.search([
					('channel_partner_ids', 'in', [item.id])
					,('channel_partner_ids', 'in', [self.env.user.partner_id.id])
					]).filtered(lambda r: len(r.channel_partner_ids) == 2).ids
				if not channel_ids:
					vals = {
						'channel_type': 'chat',
						'name': u''+item.name+u', '+self.env.user.name,
						'public': 'private',
						'channel_partner_ids': [(4, item.id), (4, self.env.user.partner_id.id)],
						'email_send': False
					}
					new_channel = channel_obj.create(vals)
					notification = _('<div class="o_mail_notification">created <a href="#" class="o_channel_redirect" data-oe-id="%s">#%s</a></div>') % (new_channel.id, new_channel.name,)
					new_channel.message_post(body=notification, message_type="notification", subtype="mail.mt_comment")
					channel_info = new_channel.channel_info('creation')[0]
					self.env['bus.bus'].sendone((self._cr.dbname, 'res.partner', self.env.user.partner_id.id), channel_info)

					channel_ids = [new_channel.id]

				self.env['mail.message'].create({
						'message_type': 'comment',
						'subtype_id': 1,
						'body': html,
						'channel_ids':  [(6, 0, channel_ids),]
						})



	def action_check(self):
		partner_ids = []
		res_model = self.env['ir.model.data'].search([
				('module','=','mw_oil_fuel'),
				('name','in',['group_oil_fuel_done'])])
		groups = self.env['res.groups'].search([('id','in',res_model.mapped('res_id'))])
		for group in groups:
			for receiver in group.users:
				if receiver.partner_id:
					partner_ids.append(receiver.partner_id.id)

		base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
		action_id = self.env['ir.model.data']._xmlid_lookup('mw_oil_fuel.action_oil')[2]
		html = u'<b>Тосны бүртгэлийг батлана уу</b><br/>'
		html += u"""<b><a target="_blank" href=%s/web#id=%s&model=oil.fuel&action=%s>%s</a></b>, дугаартай Тосны бүртгэлийг батлана уу"""% (base_url,self.id,action_id,self.name)
		self.send_chat(html, self.env['res.partner'].browse(partner_ids))
		self.check_user_id = self.env.user.id
		self.write({'state':'check'})


	def action_send_checker(self):
		partner_ids = []
		res_model = self.env['ir.model.data'].search([
				('module','=','mw_oil_fuel'),
				('name','in',['group_oil_fuel_check'])])
		groups = self.env['res.groups'].search([('id','in',res_model.mapped('res_id'))])
		for group in groups:
			for receiver in group.users:
				if receiver.partner_id:
					partner_ids.append(receiver.partner_id.id)

		base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
		action_id = self.env['ir.model.data']._xmlid_lookup('mw_oil_fuel.action_oil')[2]
		html = u'<b>Тосны бүртгэлийг Хянана уу</b><br/>'
		html += u"""<b><a target="_blank" href=%s/web#id=%s&model=oil.fuel&action=%s>%s</a></b>, дугаартай Тосны бүртгэлийг Хянана уу"""% (base_url,self.id,action_id,self.name)
		self.send_chat(html, self.env['res.partner'].browse(partner_ids))


	def action_done(self):
		if self.type in ['fuel','oil']:
			self.create_expense_picking()
			if self.type in ['fuel']:
				self.action_compute_run_hour(False, self.env['oil.fuel'].browse(self.id))
		self.done_user_id = self.env.user.id
		self.write({'state':'done'})


	def action_draft(self):
		if self.picking_ids.filtered(lambda r: r.state in ['done']):
			raise Warning(('Агуулахын баримт батлагдсан байна!'))
		elif self.picking_ids:
			self.picking_ids.action_cancel()
		self.write({'state':'draft'})

	def action_cancel(self):
		if self.picking_ids.filtered(lambda r: r.state in ['done']):
			raise Warning(('Агуулахын баримт батлагдсан байна!'))
		elif self.picking_ids:
			self.picking_ids.action_cancel()
		self.write({'state':'cancel'})


	def action_import_technic(self):
		if self.state == 'draft':
			tech_ids = self.env['technic.equipment'].search([('state','=','working'), ('id','not in',self.line_ids.ids)])
			line_obj = self.env['oil.fuel.line']

			for item in tech_ids:
				line_obj.create({
					'parent_id': self.id,
					'technic_id': item.id,
					})


	def action_export(self):
		output = BytesIO()
		workbook = xlsxwriter.Workbook(output)
		worksheet = workbook.add_worksheet(u'Гүйцэтгэл')

		h1 = workbook.add_format({'bold': 1})
		h1.set_font_size(9)
		h1.set_align('center')
		h1.set_font_name('Arial')

		header = workbook.add_format({'bold': 1})
		header.set_font_size(9)
		header.set_align('center')
		header.set_align('vcenter')
		header.set_border(style=1)
		header.set_bg_color('#9ad808')
		header.set_text_wrap()
		header.set_font_name('Arial')

		header_wrap = workbook.add_format({'bold': 1})
		header_wrap.set_text_wrap()
		header_wrap.set_font_size(11)
		header_wrap.set_align('center')
		header_wrap.set_align('vcenter')
		header_wrap.set_border(style=1)
		# header_wrap.set_fg_color('#6495ED')

		contest_left = workbook.add_format()
		contest_left.set_text_wrap()
		contest_left.set_font_size(9)
		contest_left.set_align('left')
		contest_left.set_align('vcenter')
		contest_left.set_border(style=1)

		contest_right = workbook.add_format()
		contest_right.set_text_wrap()
		contest_right.set_font_size(9)
		contest_right.set_align('right')
		contest_right.set_align('vcenter')
		contest_right.set_border(style=1)
		contest_right.set_num_format('#,##0.00')

		contest_center = workbook.add_format()
		contest_center.set_text_wrap()
		contest_center.set_font_size(9)
		contest_center.set_align('center')
		contest_center.set_align('vcenter')
		contest_center.set_border(style=1)
		contest_center.set_font_name('Arial')

		cell_format2 = workbook.add_format({
		'border': 1,
		'align': 'right',
		'font_size':9,
		'font_name': 'Arial',
		# 'text_wrap':1,
		'num_format':'#,####0'
		})


		row = 0
		last_col = 9
		worksheet.merge_range(row, 0, row, last_col, u'"'+self.location_id.name+'"'+u' Агуулах', header_wrap)

		row += 1
		worksheet.merge_range(row, 0, row, last_col, (u'Тосны' if self.type=='oil' else u'Түлшний')+u' бүртгэл импортолох загвар', contest_center)

		# row += 1
		# worksheet.merge_range(row, 0, row, last_col, self.drill_technic_id.name+u' Өрмийн машины '+self.location_id.name+u' өрөмдсөн цооног хүлээн авсан акт', contest_center)

		row += 1
		if self.type=='oil':
			worksheet.merge_range(row, 0, row, last_col-4, u'', contest_left)
		else:
			worksheet.merge_range(row, 0, row, last_col-4, self.partner_id.name+u' Харилцагч', contest_left)
		worksheet.merge_range(row, last_col-3, row, last_col, self.date, contest_right)
		row += 1

		worksheet.write(row, 0, u"Техник", header)
		worksheet.write(row, 1, u"Теникийн Код", header)
		worksheet.write(row, 2, u"Бараа", header)
		worksheet.write(row, 3, u"Тоо хэмжээ", header)
		if self.type=='oil':
			worksheet.write(row, 4, u"Тосны төрөл", header)
			worksheet.write(row, 5, u"Мотоцаг", header)
			worksheet.write(row, 6, u"Салбар", header)
			worksheet.write(row, 7, u"Шинжилгээний данс", header)
			worksheet.write(row, 8, u"Тайлбар", header)
		elif self.type=='fuel':
			worksheet.write(row, 4, u"Мотоцаг/Км", header)
			worksheet.write(row, 5, u"Салбар", header)
			worksheet.write(row, 6, u"Шинжилгээний данс", header)
			worksheet.write(row, 7, u"Тайлбар", header)
		for item in self.line_ids:
			row+=1
			worksheet.write(row, 0, item.technic_id.park_number, cell_format2)
			worksheet.write(row, 1, item.technic_id.program_code, cell_format2)
			worksheet.write(row, 2, item.product_id.default_code, cell_format2)
			worksheet.write(row, 3, item.product_qty, cell_format2)
			if self.type=='oil':
				worksheet.write(row, 4, item.oil_type, cell_format2)
				worksheet.write(row, 5, item.moto_hour, cell_format2)
			elif self.type=='fuel':
				worksheet.write(row, 4, item.moto_hour, cell_format2)
		# inch = 3000
		# worksheet.col(0).width = int(0.7*inch)
		# worksheet.col(1).width = int(0.7*inch)
		# worksheet.col(2).width = int(0.7*inch)

		workbook.close()

		out = base64.encodebytes(output.getvalue())
		file_name = self.name+'.xlsx'
		excel_id = self.env['report.excel.output'].create({'data': out, 'name': file_name})
		return {
			 'type' : 'ir.actions.act_url',
			 'url': "web/content/?model=report.excel.output&id=" + str(excel_id.id) + "&filename_field=filename&download=true&field=data&filename=" + excel_id.name,
			 'target': 'new',
		}



	def action_import(self):
		if not self.import_data_ids:
			raise UserError('Оруулах эксэлээ UPLOAD хийнэ үү ')
		if self.line_ids:
			raise UserError('Мөр оруулсан байна')

		fileobj = NamedTemporaryFile('w+b')
		import_data = self.import_data_ids[0].datas
		fileobj.write(base64.decodebytes(import_data))
		fileobj.seek(0)
		if not os.path.isfile(fileobj.name):
			raise osv.except_osv(u'Алдаа',u'Мэдээллийн файлыг уншихад алдаа гарлаа.\nЗөв файл эсэхийг шалгаад дахин оролдоно уу!')
		book = xlrd.open_workbook(fileobj.name)

		try :
			sheet = book.sheet_by_index(0)
		except:
			raise osv.except_osv(u'Алдаа', u'Sheet -ны дугаар буруу байна.')
		nrows = sheet.nrows

		rowi = 4
		line_obj = self.env['oil.fuel.line']
		product_obj = self.env['product.product']
		technic_obj = self.env['technic.equipment']
		branch_obj = self.env['res.branch']
		analytic_obj = self.env['account.analytic.account']
		description = ''
		for item in range(rowi,nrows):
			row = sheet.row(item)
			technic_name = row[0].value
			technic_code = row[1].value
			product_name = row[2].value
			print(row[3].value, type(row[3].value))
			product_qty = int(row[3].value) if row[3].value else 0
			oil_type = False
			moto_hour = False
			analytic_code =False
			if self.type=='oil':
				oil_type = row[4].value.lower()
				moto_hour = row[5].value
				branch = row[6].value
				analytic_code = row[7].value
				description  = row[8].value
			elif self.type=='fuel':
				moto_hour = row[4].value
				branch = row[5].value
				analytic_code = row[6].value
				description  = row[7].value
			# if self.type=='oil':
			#     worksheet.write(row, 4, item.oil_type, cell_format2)
			analityc_lines={}
			if analytic_code:
				analytic_datas=analytic_code.split(',')
				print ('analytic_datas ',analytic_datas)
				
				for ad in analytic_datas:
					print ('ad ',ad)
					aa=ad.split(':')
					print ('aa[0] ',aa)
					analytic_id = analytic_obj.search([('name','=',aa[0])], limit=1)
					line = ''
					if analytic_id:
						# analityc_lines.append({str(analytic_id.id):float(aa[1])})
						analityc_lines[str(analytic_id.id)]=100

			# print ('analityc_lines ',analityc_lines)
			product_name = str(product_name).split('.')[0]
			tech_id = technic_obj.search([('program_code','=',technic_code)], limit=1)
			if not tech_id:
				tech_id = technic_obj.search([('park_number','=',technic_name)], limit=1)
			if tech_id and product_qty>0:
				line_id = self.line_ids.filtered(lambda r: r.technic_id.id==tech_id.id)
				p_id = product_obj.search([('default_code','=',product_name)], limit=1)
				branch_id = branch_obj.search([('name','=',branch)], limit=1)
				if line_id:

					if p_id:
						found_line_id = line_obj.search([('product_id','=',p_id.id),('id','in',line_id.ids)], limit=1)
						if found_line_id:
							found_line_id.write({
								'product_qty': product_qty,
								'product_id': p_id.id,
								'oil_type': oil_type if oil_type and self.type=='oil' else False,
								'branch_id': branch_id.id if branch_id else False,
								'analytic_distribution':analityc_lines if analityc_lines else False,
								'description':description
								# 'moto_hour': moto_hour,
							})
							if found_line_id.odometer_unit == 'motoh':
								found_line_id.moto_hour = moto_hour
							elif found_line_id.odometer_unit == 'km':
								found_line_id.current_km = moto_hour
						else:
							if not p_id:
								raise UserError(u'%s нэртэй бараа олдсонгүй'%(product_name))
							line_id = line_obj.create({
								'parent_id': self.id,
								'technic_id': tech_id.id,
								'product_id': p_id.id,
								'product_qty': product_qty,
								'oil_type': oil_type if oil_type and self.type=='oil' else False,
								'branch_id': branch_id.id if branch_id else False,
								'analytic_distribution':analityc_lines if analityc_lines else False,
								'description':description
								# 'moto_hour': moto_hour,
								})
							if line_id.odometer_unit == 'motoh':
								line_id.moto_hour = moto_hour
							elif line_id.odometer_unit == 'km':
								line_id.current_km = moto_hour
					else:
						line_id.write({
							'product_qty': product_qty,
							'product_id': False,
							'oil_type': oil_type if oil_type and self.type=='oil' else False,
							'branch_id': branch_id.id if branch_id else False,
							'analytic_distribution':analityc_lines if analityc_lines else False,
							'description':description
							# 'moto_hour': moto_hour,
							})
						if line_id.odometer_unit == 'motoh':
							line_id.moto_hour = moto_hour
						elif line_id.odometer_unit == 'km':
							line_id.current_km = moto_hour
				else:
					if not p_id:
						raise UserError(u'%s нэртэй бараа олдсонгүй'%(product_name))
					line_id = line_obj.create({
						'parent_id': self.id,
						'technic_id': tech_id.id,
						'product_id': p_id.id,
						'product_qty': product_qty,
						'oil_type': oil_type if oil_type and self.type=='oil' else False,
						'branch_id': branch_id.id if branch_id else False,
						'analytic_distribution':analityc_lines if analityc_lines else False,
						'description':description
						# 'moto_hour': moto_hour,
						})
					if line_id.odometer_unit == 'motoh':
						line_id.moto_hour = moto_hour
					elif line_id.odometer_unit == 'km':
						line_id.current_km = moto_hour
			elif not tech_id:
				raise UserError(u'%s %s техникийн нэрээ оруулна уу'%(technic_name,technic_code))

	def action_create_po(self):
		obj = self.env['oil.fuel']
		purchase_obj = self.env['purchase.order']
		purchase_line_obj = self.env['purchase.order.line']

		year = self.date.year
		month = self.date.month
		days = monthrange(year,month)[1]
		ds = datetime.strftime(self.date,'%Y-%m-01')
		de = datetime.strftime(self.date, '%Y-%m-' + str(days))
		obj_ids = obj.search([('date','>=',ds),('date','<=',de),('type','=','fuel_in'),('purchase_order_id','=',False),('partner_id','=',self.partner_id.id)])

		vals = {
			'date_order': self.date,
			'picking_type_id': self.location_id.set_warehouse_id.in_type_id.id,
			'date_planned': self.date,
			'origin': ','.join([str(x) for x in obj_ids.mapped('date')]),
			'partner_id': self.partner_id.id,
			'state': 'draft',
		}
		linevals = []
		obj_line_ids = obj_ids.mapped('line_in_ids')
		product_ids = obj_line_ids.mapped('product_id')

		for item in product_ids:
			product_qty = sum(obj_line_ids.filtered(lambda r: r.product_id.id==item.id).mapped('product_qty'))

			linevals.append((0,0, {
				'product_id': item.id,
				'name': item.name,
				'date_planned': self.date,
				'product_qty': product_qty,
				'price_unit': 1,
				'product_uom': item.uom_id.id,
			}))

		vals['order_line'] = linevals

		po_id = self.env['purchase.order'].create(vals)
		for item in po_id.order_line:
			item._onchange_quantity()
		for item in obj_ids:
			item.purchase_order_id = po_id.id


	def unlink(self):
		for item in self:
			if item.state!='draft' or item.picking_id:
				raise UserError(u'Заралгын хөдөлгөөн байна эсвэл Ноорог биш хөдөлгөөн байна')
		return super(oil_fuel, self).unlink()

# Oil Fuel notebook by Purvee
class OilFueNotebook(models.Model):
	_inherit = 'technic.equipment'

	tulshnii_zarlaga_ids = fields.One2many('oil.fuel.line','technic_id', string='Түлшний зарлага', domain=[('type','=','fuel')], groups="stock.group_stock_user")
	tosnii_zarlaga_ids = fields.One2many('oil.fuel.line','technic_id', string='Тосны зарлага', domain=[('type','=','oil')], groups="stock.group_stock_user")

class MaintenanceDamagedType(models.Model):
	_inherit = 'maintenance.damaged.type'

	is_oil_system = fields.Boolean(string='Тосны систем эсэх')

class oil_fuel_line(models.Model):
	_name = 'oil.fuel.line'
	_description = 'Oil fuel line'
	_order = 'program_code, date desc'
	_inherit = ["analytic.mixin"]

	date = fields.Date(related='parent_id.date', store=True)
	# date = fields.Date(related='parent_id.date',)
	shift = fields.Selection(related='parent_id.shift')
	type = fields.Selection(related='parent_id.type', readonly=True)

	system_type_id = fields.Many2one('maintenance.damaged.type', domain=[('is_oil_system','=',True)], string=u'Тос нэмсэн систем')
	parent_id = fields.Many2one('oil.fuel', 'Бүртгэл')
	technic_id = fields.Many2one('technic.equipment', 'Техник')
	tech_branch_id = fields.Many2one('res.branch', string="ТХ салбар", related="technic_id.branch_id", store=True)
	odometer_unit = fields.Selection(related="technic_id.technic_setting_id.odometer_unit", string="Гүйлтийн төрөл")
	program_code = fields.Char('Техникийн код', compute='_compute_program_code', store=True, readonly=True)
	product_id = fields.Many2one('product.product', 'Бараа')
	product_qty = fields.Float('Тоо хэмжээ', default=1, required=True)
	oil_type = fields.Selection([('add','ADD'),('pm','PM'),('rpc','RPC')], string='Тосны төрөл')
	product_id = fields.Many2one('product.product', 'Бараа')
	moto_hour = fields.Float('Мото/цаг')
	current_km = fields.Float('Км')
	run_km = fields.Float('Явсан Км', compute='_compute_km', store=True)
	edit_before_moto_hour = fields.Boolean('Өмнөх мото/цаг ЗАСАХ', default=False)
	run_hour = fields.Float('Ажиласан цаг', compute='_compute_run_hour', store=True)
	# before_line_id = fields.Many2one('oil.fuel.line', 'Өмнөх бүртгэл', compute='_compute_before_line', store=True)
	# before_moto_hour = fields.Float(string='Өмнөх Мотоцаг', compute='_compute_before_line', store=True, readonly=False)
	before_line_id = fields.Many2one('oil.fuel.line', 'Өмнөх бүртгэл', copy=False)
	before_moto_hour = fields.Float(string='Өмнөх Мотоцаг',readonly=False)
	before_km = fields.Float(string='Өмнөх км',readonly=False)
	after_line_ids = fields.One2many('oil.fuel.line', 'before_line_id', 'Өмнөх цаг')
	desc = fields.Text(string='Тайлбар')
	name = fields.Char('Нэр', compute='_compute_name', readonly=True)
	avg_epx = fields.Float('1 мот цагт', compute='_compute_avg_epx', group_operator='avg', store=True)
	description  = fields.Char(string='Тайлбар')
	account_id = fields.Many2one('account.account', string='Данс')
	@api.depends('run_hour','product_qty')
	def _compute_avg_epx(self):
		for item in self:
			if item.run_hour!=0:
				item.avg_epx = item.product_qty/item.run_hour
			else:
				item.avg_epx = 0

	@api.constrains('technic_id', 'parent_id')
	def _validate_tech_part(self):
		# for item in self:
		# 	if item.id and self.env['oil.fuel.line'].search([('id','!=',item.id),('technic_id','=',item.technic_id.id),
		# 	('parent_id','=',item.parent_id.id), ('product_id','=',item.product_id.id)]):
		# 		raise UserError(u'Техник давхардаж болохгүй {0} {1}'.format(item.technic_id.display_name, item.parent_id.display_name))
		return
	@api.depends('product_id','desc')
	def _compute_name(self):
		for item in self:
			desc = item.desc or ''
			item.name = u'%s %s %s %s '%(item.parent_id.date,item.parent_id.shift,item.product_id.display_name,desc)

	def get_other_line(self):
		domain = [
			('parent_id.type','=','fuel'),
			('parent_id.shift','=',self.parent_id.shift),
			('parent_id.date','=',self.parent_id.date),
			('technic_id','=',self.technic_id.id),
			('run_hour','>',0),
			('parent_id','!=',self.parent_id.id),
			]
		return self.env['oil.fuel.line'].search(domain)

	@api.depends('before_moto_hour', 'moto_hour')
	def _compute_run_hour(self):
		for item in self:
			if item.before_moto_hour < item.moto_hour:
				tt = item.get_other_line()
				if not tt:
					item.run_hour = item.moto_hour-item.before_moto_hour
				else:
					item.run_hour = 0
			else:
				item.run_hour = 0
	

	@api.depends('before_km', 'current_km')
	def _compute_km(self):
		for item in self:
			if item.before_km < item.current_km:
				tt = item.get_other_line()
				if not tt:
					item.run_km = item.current_km-item.before_km
				else:
					item.run_km = 0
			else:
				item.run_km = 0

	@api.onchange('technic_id')
	def onchange_before_line(self):
		for item in self:
			item._compute_before_line()

	@api.depends('technic_id')
	def _compute_before_line(self):
		for item in self:
			if item.parent_id.type in ['fuel','oil'] and item.technic_id and item.parent_id.date and item.parent_id.shift:
				line_obj = self.env['oil.fuel.line']
				oil_obj = self.env['oil.fuel']
				line_id = False
				oil_id = False
				date_where = " of.date<'%s' "%(item.parent_id.date)
				if item.parent_id.shift=='night':
					date_where = " ((of.date<='%s' and of.shift!='night') or (of.date<'%s' and of.shift='night')) "%(item.parent_id.date, item.parent_id.date)
				query = """
					SELECT
					ofl.id
						from oil_fuel_line ofl
						left join oil_fuel of on (ofl.parent_id=of.id)
						where of.type='fuel' and ofl.technic_id={0} and {1}
						order by of.date desc, of.shift desc
						limit 1
					""".format(item.technic_id.id, date_where)
				self.env.cr.execute(query)
				oil_id = self.env.cr.fetchone()
				if oil_id:
					line_id = oil_id[0]
					if line_id:
						item.before_line_id = line_id
						if item.edit_before_moto_hour == 0:
							item.before_moto_hour = item.before_line_id.moto_hour
							item.before_km = item.before_line_id.current_km

	# norm_id = fields.Many2one('oil.fuel.norm', 'Бараа', compute='_compute_norm_diff', readonly=True)
	# norm_diff = fields.Float('Нормын зөрүү', compute='_compute_norm_diff', store=True, readonly=True)


	# @api.depends('technic_id', 'product_id', 'product_qty', 'parent_id.type')
	# def _compute_norm_diff(self):
	#     norm_obj = self.env['oil.fuel.norm']
	#     for item in self:
	#         domain = [('product_id','=',item.product_id.id),('technic_setting_id','=',item.technic_id.technic_setting_id.id),('is_fuel','=',False)]
	#         if item.parent_id.type=='oil':
	#             domain = [('product_id','=',item.product_id.id),('technic_setting_id','=',item.technic_id.technic_setting_id.id),('is_fuel','=',False)]
	#         elif item.parent_id.type=='fuel':
	#             domain = [('technic_setting_id','=',item.technic_id.technic_setting_id.id),('is_fuel','=',True)]

	#         norm_id = norm_obj.search(domain , limit=1)
	#         if norm_id:
	#             norm_qty = sum(norm_id.mapped('qty'))
	#             if item.product_qty>norm_qty:
	#                 item.norm_diff = item.product_qty-norm_qty
	#             else:
	#                 item.norm_diff = 0
	#             item.norm_id = norm_id.id
	#         else:
	#             item.norm_diff = 0
	#             item.norm_id = False

	@api.depends('technic_id.program_code')
	def _compute_program_code(self):
		for item in self:
			item.program_code = item.technic_id.program_code
