# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models, fields
from odoo.exceptions import UserError, ValidationError
import logging
from calendar import monthrange
import json
_logger = logging.getLogger(__name__)
import datetime

class product_mobile_lock(models.Model):
	_name = "product.mobile.lock"
	_description = 'Product mobile lock'

	product_ids = fields.Many2many('product.product', 'product_mobile_lock_product_product_rel', 'lock_id', 'product_id', string="Бараанууд")
	team_ids = fields.Many2many('crm.team', 'product_mobile_lock_crm_team_rel', 'lock_id', 'team_id', string="Сувгууд")
	user_ids = fields.Many2many('res.users', 'product_mobile_lock_res_users_rel', 'lock_id', 'user_id', string="Борлуулагч")
	
	def get_mobile_lock(self, product_id, user_id):
		obj = self.env['product.mobile.lock']
		if obj.search([('product_ids','in',product_id.id),('user_ids','in',user_id.id)]):
			return True

		if obj.search([('product_ids','in',product_id.id),('user_ids','=',False)]):
			return True
		return False

	def get_mobile_lock_product_ids(self):
		obj = self.env['product.mobile.lock']
		# team_id = self.env.user.crm_team_id
		user_id = self.env.user
		p_ids = obj.search([('user_ids','in',user_id.id)]).mapped('product_ids').ids
		
		p_ids += obj.search([('user_ids','=',False)]).mapped('product_ids').ids
		if p_ids:
			p_ids = list(set(p_ids))
		return p_ids

class StockPicking(models.Model):
	_inherit = "stock.picking"
	
	driver_user_id = fields.Many2one(related='sale_id.driver_id', string='Жолооч/Хүргэсэн',
		domain=[('team_type','in',['driver','salesman','supermarket','small'])], readonly=False)
	is_picked = fields.Boolean(string=u'Цуглуулсан эсэх', default=False)
	return_reason = fields.Selection([
			('return_closed', u'Буцаалт - Дэлгүүр хаалттай'),
			('return_complaints', u'Буцаалт - Хэрэглэгчийн гомдол'),
			('return_event_back', u'Буцаалт - Event-ийн буцаан таталт'),
			('return_nuuts_ikhtei', u'Буцаалт - Нөөц ихтэй'),
			('return_expired', u'Буцаалт - Хугацаа дөхсөн'),
			('return_no_shop', u'Буцаалт - Татан буугдсан'),
			('return_wrong_data', u'Буцаалт - Буруу мэдээлэл, өгөгдөлтэй'),
			('return_back', u'Буцаан татсан'),
		], string=u'Буцаалтын шалтгаан', tracking=True)

# Буцаалтын дэлгэц
class ReturnPicking(models.TransientModel):
	_inherit = 'stock.return.picking'

	picking_type_id = fields.Many2one(related="picking_id.picking_type_id" ,readonly=True, )
	code = fields.Selection(related="picking_type_id.code", readonly=True, )

	return_reason = fields.Selection([
			('return_closed', u'Буцаалт - Дэлгүүр хаалттай'),
			('return_complaints', u'Буцаалт - Хэрэглэгчийн гомдол'),
			('return_event_back', u'Буцаалт - Event-ийн буцаан таталт'),
			('return_nuuts_ikhtei', u'Буцаалт - Нөөц ихтэй'),
			('return_expired', u'Буцаалт - Хугацаа дөхсөн'),
			('return_no_shop', u'Буцаалт - Татан буугдсан'),
			('return_wrong_data', u'Буцаалт - Буруу мэдээлэл, өгөгдөлтэй'),
			('return_back', u'Буцаан татсан'),
		], string=u'Буцаалтын шалтгаан', )

	def create_returns(self):
		res = super(ReturnPicking, self).create_returns()
		# Шалтгаан хадгалах
		ctx = res['context']
		ctx['reason'] = self.return_reason
		res['context'] = ctx
		return res
	
	def _create_returns(self):
		new_picking_id, pick_type_id = super(ReturnPicking, self)._create_returns()
		if new_picking_id and self.return_reason:
			pick_id = self.env['stock.picking'].browse(new_picking_id)
			pick_id.return_reason = self.return_reason
			
		return new_picking_id, pick_type_id

# ==========================================
class MwMobile(models.Model):
	_inherit = 'mw.mobile'

	so_start_date = fields.Date('SO start date')
	so_end_date = fields.Date('SO end date')

	def test_create_product_expense(self):
		data = {
			'validity_date': '2020-02-27',
			'order_line': [{'product_id':8192,'qty':2},{'product_id':8193,'qty':3}]
		}
		self.create_product_expense([data])

	@api.model
	def create_product_expense(self, data):
		_logger.info("-----------------mobile ====== create_product_expense %s", str(data))
		data = data[0]
		value = self.env['mn.transaction.value'].sudo().search([('code','=','001')], limit=1)
		if value:
			line_datas = []
			for ll in data['order_line']:
				line_datas.append((0,0,{
					'product_id': ll['product_id'],
					'qty': ll['qty'],
				}))
			vals = {
				'date_required': data['validity_date'].replace('/','-'),
				'employee_id': self.env.user.employee_id.id,
				'transaction_value_id': value.id,
				'warehouse_id': self.env.user.warehouse_id.id,
				'branch_id': self.env.user.branch_id.id,
				'account_id': value.account_id.id if value.account_id else False,
				'account_analytic_id': value.account_analytic_id.id if value.account_analytic_id else False,
				'product_expense_line': line_datas,
				'description': value.name,
			}
			expense = self.env['stock.product.other.expense'].create(vals)
			expense.description += ': Хорогдол - From mobile'
			expense.action_next_stage()
			_logger.info("-----------------mobile ====== create_product_expense :) %s %d ",expense.name, expense.id)
			return True
		else:
			_logger.info("-----------------mobile ====== create_product_expense NOT FOUND transaction value!!!")
			return 'Гүйлгээний утга олдсонгүй!'

	def compute_return_daralt_qty(self):
		so_ids = self.env['sale.order'].search([('state','in',['sale','done']),('picking_date','>=',self.so_start_date),('picking_date','<=',self.so_end_date)])
		lens = len(so_ids)
		_logger.info('---- update_daralt --- hiiih %s '%(lens))
		for so in so_ids:
			ll = so.order_line.filtered(lambda r: r.return_qty_non_store > 0)
			for sol in ll:
				sol._compute_get_delivered_qty()
				sol.qty_delivered = sol.product_uom_qty - sol.daralt_qty

			_logger.info('---- update_daralt --- %s  uldsen %s '%(so.name,lens))
			lens -= 1

	def get_stock_picking2(self):
		result = []
		res = self.get_stock_picking()

	# Цуглуулагч нар ирсэн захиалгыг агуулахаас цуглуулахад ашиглана
	@api.model
	def get_stock_picking(self, data):
		_logger.info("------ mobile -----get_stock_picking datas %s  %s", str(data), type(data))
		result = []
		picking_obj = self.env['stock.picking']
		s_date = str(data['date'])+' 00:00:00'
		e_date = str(data['date'])+' 23:59:59'
		picking_ids = picking_obj.search([
			('picking_type_id.warehouse_id','in',[self.env.user.warehouse_id.id]),
			('state','not in',['cancel']),
			('picking_type_id.code','=','outgoing'),
			('scheduled_date','>=',s_date),
			('scheduled_date','<=',e_date),
			])
		if not picking_ids:
			return False
		for item in picking_ids:
			move_lines = []
			vals = {
				'name': item.name,
				'state': item.state,
				'picking_id': item.id,
				'so_name': item.sale_id.name if item.sale_id else '',
				'status': item.picking_type_id.code,
				'picking_type_name': item.picking_type_id.name,
				# 'pick_user_name': item.pick_user_id.name,
				'driver_user_name': item.driver_user_id.name,
				'partner_name': item.partner_id.name,
				'move_lines': move_lines,
				'deliver_date': item.scheduled_date,
				# 'amount_total': item.amount_total_cmo,
				'user_name': item.user_id.name,
				'is_picked': item.is_picked,
			}
			for move in item.move_lines:
				move_lines.append({
					'product_id': move.product_id.id,
					'product_uom_qty': move.product_uom_qty,
					'product_uom': move.product_uom.id,
					})
			vals.update({
				'move_lines': move_lines
				})
			result.append(vals)
		return result

	def action_done_transfer(self, picking_ids):
		transfer = self.env['stock.immediate.transfer']
		transfer_id = transfer.create({'pick_ids':[]})
		transfer_id.pick_ids = picking_ids.ids 
		_logger.info("------ mobile -----action_done_transfer   111 draft %s ", picking_ids)
		_logger.info("------ mobile -----action_done_transfer   draft %s ", picking_ids)
		return transfer_id.process()

	# Хүргэлтийг дуусгах
	@api.model
	def stock_picking_action_confirm(self, data):
		_logger.info("------ mobile -----stock_picking_action_confirm datas %s  %s", str(data), type(data))
		picking_id = int(float(data['picking_id']))
		picking_id = self.env['stock.picking'].browse(picking_id)
		_logger.info("------ mobile -----stock_picking_action_confirm picking_id %s ", picking_id)
		
		if picking_id.state in ['draft','waiting','confirmed']:
			_logger.info("------ mobile -----stock_picking_action_confirm picking_id  draft %s ", picking_id)
			picking_id.action_assign()
			if picking_id.state=='assigned':
				# picking_id.action_done()
				self.action_done_transfer(picking_id)
				return True
			else:
				return False
		if picking_id.state=='assigned':
			self.action_done_transfer(picking_id)
			# picking_id.action_done()
			return True
		return False

	# Захиалгыг цуглуулсан болгох
	@api.model
	def stock_picking_action_picked(self, data):
		_logger.info("------ mobile -----stock_picking_action_confirm datas %s  %s", str(data), type(data))
		picking_id = int(float(data['picking_id']))
		picking_id = self.env['stock.picking'].browse(picking_id)
		if data['picked']=='true':
			picking_id.is_picked = True
		else:
			picking_id.is_picked = False
		return True

	# TOOLLOGIIN HESEG
	@api.model
	def get_inventory_adjustment(self, dddd):
		_logger.info("------ mobile -----get_inventory_adjustment %s ", str(dddd))
		inv_obj = self.env['stock.inventory']
		inv_ids = inv_obj.search([('state','=','confirm'),('location_id','in',self.env.user.warehouse_ids.mapped('lot_stock_id.id'))])
		result = []
		for item in inv_ids:
			_logger.info("------ mobile -----get_inventory_adjustment inventory_id %s ", str(item.id))
			res = {
				'inv_id': item.id,
				'inv_name': item.name,
				'date': item.date,
				'filter': item.filter,
				'location_name': item.location_id.name,
				'line_ids': []
				}
			lines = []
			
			send_product_ids = []
			line_ids = self.env['stock.inventory.line'].search([('inventory_id','=',item.id)], order='product_code')
			for line in line_ids:
				product_qty = line.product_qty
				mobile_id = item.mobile_line_ids.filtered(lambda r: r.inventory_id.id==item.id and r.product_id.id==line.product_id.id and r.send_user_id.id==self.env.user.id)
				if mobile_id:
					product_qty = mobile_id.product_qty
				else:
					product_qty = 0
					
				product_name = line.product_id.mng_name or line.product_id.name
				default_code = str(line.product_id.default_code) or ''
				barcode = str(line.product_id.barcode) or ''
				brand_name = line.product_id.brand_id.name or ''
				lines.append({
					'default_code': '"'+default_code+'"',
					'barcode': '"'+barcode+'"',
					'product_id': line.product_id.id,
					'theoretical_qty': line.theoretical_qty,
					'brand_name': '"'+brand_name+'"',
					'package_qty': line.product_id.package_qty,
					'product_name': '"'+product_name+'"',
					'product_qty': product_qty,
					'is_inventory': '"yes"',
					})
				send_product_ids.append(line.product_id.id)
			product_ids = []
			cat_ids = self.env['product.category'].search([('warehouse_id','in',self.env.user.warehouse_ids.ids)])
			
			if item.filter=='category':
				product_ids = self.env['product.product'].search([('id','not in',send_product_ids),('categ_id','child_of',item.category_id.id),('type','=','product'),('categ_id','child_of',cat_ids.ids)])
				
			else:
				product_ids = self.env['product.product'].search([('id','not in',send_product_ids),('type','=','product'),('categ_id','child_of',cat_ids.ids)])

			for line in product_ids:
				product_name = line.mng_name or line.name
				default_code = str(line.default_code) or ''
				barcode = str(line.barcode) or ''
				brand_name = line.brand_id.name or ''
				lines.append({
					'default_code': '"'+default_code+'"',
					'barcode': '"'+barcode+'"',
					'product_id': line.id,
					'theoretical_qty': 0,
					'brand_name': '"'+brand_name+'"',
					'package_qty': line.package_qty,
					'product_name': '"'+product_name+'"',
					'product_qty': 0,
					'is_inventory': '"no"',
					})
			res['line_ids'] = lines

			result.append(res)
		_logger.info("------ mobile -----get_inventory_adjustment inventory_id result %s ", str(result))
		return result if result else False

	@api.model
	def update_inventory_adjustment(self, dddd):
		_logger.info("------ mobile ----- update_inventory_adjustment %s ", str(dddd))
		inv_obj = self.env['stock.inventory']
		inv_line_obj = self.env['stock.inventory.line']
		mobile_line_obj = self.env['stock.inventory.mobile']

		inventory_id = inv_obj.browse(int(float(dddd['inv_id'])))
		# int(float(data['inv_id']))
		for item in dddd['line_ids']:
			p_id = int(float(item['product_id']))
			product_qty = item['product_qty']
			inv_line_id = inventory_id.mobile_line_ids.filtered(lambda r: r.product_id.id==p_id and r.send_user_id.id==self.env.user.id)
			if inv_line_id:
				if inv_line_id.product_qty!=product_qty:
					inv_line_id.product_qty = product_qty
			else:
				_logger.info("------ mobile -----  %s ", str(p_id))
				mobile_line_obj.create({
					'inventory_id': inventory_id.id,
					# 'location_id': inventory_id.location_id.id,
					'product_id': p_id,
					'product_qty': product_qty,
					'send_user_id': self.env.user.id,
					# 'product_uom_id': self.env['product.product'].browse(p_id).uom_id.id,
					})

		sql_query = """SELECT product_id,sum(product_qty) as product_qty
							 FROM stock_inventory_mobile 
							  where inventory_id = %s
							  group by product_id
					  """%(inventory_id.id)
		self.env.cr.execute(sql_query)
		
		res = self.env.cr.dictfetchall()

		for item in res:
			p_id = item['product_id']
			product_qty = item['product_qty']
			inv_line_id = inventory_id.line_ids.filtered(lambda r: r.product_id.id==p_id)
			if inv_line_id:
				if inv_line_id.product_qty!=product_qty:
					inv_line_id.product_qty = product_qty
			else:
				inv_line_obj.create({
					'inventory_id': inventory_id.id,
					'location_id': inventory_id.location_id.id,
					'product_id': p_id,
					'product_qty': product_qty,
					'product_uom_id': self.env['product.product'].browse(p_id).uom_id.id,
					})
		return True
