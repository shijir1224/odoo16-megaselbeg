# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models, fields
from odoo.exceptions import UserError, ValidationError
import logging
from calendar import monthrange
import json
_logger = logging.getLogger(__name__)
import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
import threading
from odoo.tests import Form

MAP_INVOICE_TYPE_PARTNER_TYPE = {
	'out_invoice': 'customer',
	'out_refund': 'customer',
	'in_invoice': 'supplier',
	'in_refund': 'supplier',
}

class MwMobile(models.Model):
	_name = 'mw.mobile'
	_description = "mw mobile"

	desc = fields.Text('Text')
	insert_value = fields.Text('Insert value')
	# ----------------- METHODs -----------------
	# Харилцагчийн ангилал татах - Зөвхөн цэгийн ангилал
	@api.model
	def get_partner_category_names(self):
		categs = []
		_logger.info("-----------------mobile ====== get_partner_category_names ")
		for ll in self.env['res.partner.category'].sudo().search([
			('active','=',True),
			# ('name','ilike','Цэгийн ангилал')
			]):
			categs.append({'id': ll.id, 'name': ll.display_name})
			_logger.info("-----------------mobile ===category=== %s ", ll.display_name)
		return categs

	# Буцаалт, даралтын шалтгаан
	@api.model
	def get_return_reason_names(self):
		reasons = [
			# {'value':'daralt_payment', 'description':u'Даралт - Төлбөр бүрэн биш'},
			# {'value':'daralt_quality', 'description': u'Даралт - Чанарын буцаалт'},
			# {'value':'daralt_wrong_order','description': u'Даралт - Буруу захиалга'},
			# {'value':'daralt_full_daralt','description': u'Даралт - Бүтэн даралт'},
			
			{'value':'return_expired','description': u'Буцаалт - Хугацаа дөхсөн'},
			{'value':'return_complaints','description': u'Буцаалт - Хэрэглэгчийн гомдол'},
			{'value':'return_event_back','description': u'Буцаалт - Event-ийн буцаан таталт'},
			{'value':'return_nuuts_ikhtei','description': u'Буцаалт - Нөөц ихтэй'},
			{'value':'return_wrong_data','description': u'Буцаалт - Буруу мэдээлэл, өгөгдөлтэй'},
			{'value':'return_closed','description': u'Буцаалт - Дэлгүүр хаалттай'},
			{'value':'return_no_shop','description': u'Буцаалт - Татан буугдсан'},
		]
		return reasons

	# Бараа татах
	def get_product_product2(self):
		res = self.get_product_product()
		self.desc = str(res) if res else '===='
	
	@api.model
	def get_product_product(self):
		products = []
		print('=====', self._context)
		_logger.info("-----------------mobile ====== get_product_product 1")
		base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
		url = "/web/image/product.product/%d/image"
		# 
		# Утсан дээр зөвхөн үлдэгдэлтэй барааг харуулах эсэх
		# Тохиргооноос авч шалгах
		res_config = self.env['res.config.settings']
		available_qty_on_mobile = res_config.sudo().create({}).available_qty_on_mobile
		# Бар код шалгах
		see_barcode_on_mobile = res_config.sudo().create({}).see_barcode_on_mobile
		# ===============
		quant_obj = self.env['stock.quant']
		for product in self.env['product.product'].with_context(self._context).search([('sale_ok','=',True),('active','=',True),('see_mobile','=',True)], order='report_order, name'):
			img_link = base_url+url%product.id
			available_qty = 0
			main_wh_available_qty = 0
			if self.env.user.team_type=='salesman':
				available_qty = self.get_available(product, self.env.user.warehouse_id)
				# Барааны үндсэн агуулахын үлдэгдэл
				main_wh_available_qty = self.get_available(product, self.env.user.warehouse_ids) - available_qty
			else:
				available_qty = self.get_available(product, self.env.user.warehouse_id)
			
			if available_qty_on_mobile and available_qty <= 0:
				continue

			package_qty = 1
			if product.uom_po_id and product.uom_po_id.factor > 0:
				package_qty = product.uom_po_id.factor
			display_name_temp = "[%s] %s" % (product.default_code, product.name)
			temp = {
				'product_id':product.id,
				'default_code': product.default_code,
				'name': display_name_temp,
				'mobile_list_price': product.list_price,
				'available_qty': available_qty,
				'main_wh_available_qty': main_wh_available_qty,
				'image': img_link,
				'package_qty': package_qty,
				'warehouse_id': self.env.user.warehouse_id.id,
				'brand_name': product.brand_id.name,
				'categ_name': product.categ_id.name,
				'barcode': product.barcode,
				'report_order': product.report_order,
			}
			if see_barcode_on_mobile and product.barcode:
				temp['name'] = display_name_temp +' ('+str(product.barcode)+')'
			products.append(temp)
		_logger.info("------ mobile -----len(products)  %s",len(products))
		return products

	# Барааны үлдэгдэл авах
	@api.model
	def get_available(self, product_id, warehouse_ids):
		total_available_qty = 0
		quant_obj = self.env['stock.quant']
		
		for item in warehouse_ids:
			quant_ids = quant_obj.search([('product_id','=',product_id.id),('location_id','=',item.lot_stock_id.id)])
			for qq in quant_ids:
				total_available_qty += (qq.quantity-qq.reserved_quantity)
			# Bayaraa 
			# total_available_qty += quant_obj._get_available_quantity(self.env['product.product'].browse(product_id), item.lot_stock_id)
		
		return total_available_qty

	# Харилцагчийн үнэ авах
	def get_partner_price_test(self):
		self.get_partner_price()

	@api.model
	def get_partner_price(self):
		partners_price = []
		_logger.info("-------- mobile --------- get_partner_price %s ", self.env.user.login)
		res_config = self.env['res.config.settings']
		main_price_unit_on_mobile = res_config.sudo().create({}).main_price_unit_on_mobile
		if not main_price_unit_on_mobile:
			products = self.env['product.product'].search([('sale_ok','=',True),('active','=',True),('see_mobile','=',True)])
			if self.env.user.team_type == 'driver':
				domains = [
					 ('route_id.driver_id','=',self.env.user.id),
					 ('is_mobile_active','=',True)]
			else:
				domains = [
					 ('user_id','=',self.env.user.id),
					 ('is_mobile_active','=',True)]
			partners = self.env['res.partner'].search(domains)
			_logger.info("-------- mobile --------- products %d, partners %d", len(products), len(partners))
			temp_dict = {}
			for partner in partners:
				if partner.property_product_pricelist:
					if partner.property_product_pricelist.id not in temp_dict:
						for product in products:
							price = partner.property_product_pricelist.get_product_price(product, 1.0, partner)
							precent = 0
							# Хурдан болгох гэж хассан ==== Хурдан болсон
							# pricelist_item = partner.property_product_pricelist.item_ids.filtered(lambda r: r.product_tmpl_id.id==product.product_tmpl_id.id)
							# if pricelist_item:
							# 	precent = pricelist_item[0].price_discount
							vals = {
								'pricelist_id': partner.property_product_pricelist.id,
								'product_id': product.id,
								'partner_price': price,
								'precent': precent,
							}
							partners_price.append(vals)
						temp_dict[partner.property_product_pricelist.id] = partner.property_product_pricelist.id

		_logger.info("------ mobile -------get_partner_price len(partner's pricelist)  %s ",len(partners_price))
		return partners_price

	# Агуулахын мэдээлэл татах
	def get_stock_warehouse2(self):
		res = self.get_stock_warehouse()
		self.desc = str(len(res))

	@api.model
	def get_stock_warehouse(self):
		warehouses = []
		_logger.info("-----------------mobile ====== get_stock_warehouse ")
		for wh in self.env.user.warehouse_ids:
			warehouses.append({
				'warehouse_id':wh.id,
				'code': wh.code,
				'name': wh.name,
			})
		# if self.env.user.warehouse_id:
		#	 warehouses.append({
		#		 'warehouse_id':self.env.user.warehouse_id.id,
		#		 'code': self.env.user.warehouse_id.code,
		#		 'name': self.env.user.warehouse_id.name,
		#	 })
		_logger.info("------ mobile -----len(warehouses)  %s",len(warehouses))
		return warehouses

	# Явсан Маршрутын мэдээлэл оруулах
	def create_salesman_route_test(self):
		route = self.env['salesman.route.planner.line']
		res = route._check_partner_route(10, 19607, '2020-04-14')
		# res = self.create_salesman_route(10, 19607, '2020-04-14','successful')
		self.desc = str(res)

	@api.model
	def create_salesman_route(self, user_id, partner_id, date_order, state):
		_logger.info("-----------------mobile ====== create salesman route ,,,,,,,,,,,,,,,,,,")
		route = self.env['salesman.route.planner.line']
		check = route._check_partner_route(user_id, partner_id, date_order)
		vals = {
			'user_id': user_id,
			'partner_id': partner_id,
			'date_order': date_order,
			'check_route': check,
			'state': state,
		}
		r = self.env['salesman.route.performance.line'].create(vals)
		_logger.info("------ mobile ----- route performance line)  %d %s",r.id,check)
		return r.id

	@api.model
	def create_salesman_route_mobile(self, data):
		_logger.info("-----mobile ====== create salesman route from MOBILE %s ", str(data))
		res = self.create_salesman_route(self.env.user.id, data['partner_id'], data['date_order'], data['state'])
		return True if res else False

	# Харилцагчийн чиглэл авах
	@api.model
	def get_partner_route(self):
		routes = []
		_logger.info("-----------------mobile ====== get ROUTES ")
		for rr in self.env['res.partner.route'].sudo().search([('user_ids','in',self.env.user.id)]):
			routes.append({
				'route_id':rr.id,
				'name': rr.name,
			})
		_logger.info("------ mobile -----len(routes)  %s",len(routes))
		return routes

	# Хэрэглэгчийн мэдээлэл татах
	@api.model
	def get_res_user(self):
		_logger.info("-------- mobile ---------- get_res_user INFO ")
		base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
		url = "/web/image/res.users/%d/image"
		login = self.env.user.login
		phone = ''
		if self.env.user.partner_id and self.env.user.partner_id.phone:
			phone = self.env.user.partner_id.phone
		user_info = {
			'user_id':self.env.user.id,
			'login': login,
			'pass': self.env.user.password,
			'image': base_url+url%self.env.user.id,
			'team_type': self.env.user.team_type,
			'my_warehouse_id': self.env.user.warehouse_id.id or 0,
			'company_name': self.env.user.company_id.name,
			'company_register': self.env.user.company_id.vat,
			'version': '1.0',
			'locked_product_ids': self.env['product.mobile.lock'].sudo().get_mobile_lock_product_ids(),
			'is_create_expense': False,
			'is_create_ebarimt': True,
			'user_phone': phone,
		}
		_logger.info("------ mobile ----USER INFO - %s ",user_info)
		return user_info

	# Харилцагч татах
	def get_res_partner2(self):
		res = self.get_res_partner()
		base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
		url = "/web/image/res.partner/%d/image"
		self.desc = str(len(res)) + ' URL:'+base_url+url

	@api.model
	def get_res_partner(self):
		partners = []
		_logger.info("-------- mobile ---------- get_res_partner ")
		base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
		url = "/web/image/res.partner/%d/image"
		now = datetime.datetime.now()
		date_str = now.strftime("%Y-%m")
		temp_ids = []
		team_type = self.env.user.team_type
		domains = []
		# if team_type == 'salesman':
		# 	domains = [
		# 		 ('route_id.user_ids','in',self.env.user.id),
		# 		 ('is_mobile_active','=',True)]
		if team_type == 'driver':
			domains = [
				 ('route_id.driver_id','=',self.env.user.id),
				 ('is_mobile_active','=',True)]
		else:
			domains = [
				 ('user_id','=',self.env.user.id),
				 ('is_mobile_active','=',True)]
		so_s = []
		for line in self.env['res.partner'].search(domains, order="name"):
			p_debt = 0
			if team_type == 'driver':
				p_debt = sum(self.env['account.move'].search([('partner_id','=',line.id)]).mapped('amount_residual'))
			else:
				p_debt = sum(self.env['account.move'].search([('partner_id','=',line.id),('user_id','=',self.env.user.id)]).mapped('amount_residual'))	
			so_s = self.env['sale.order'].search([('user_id','=',self.env.user.id),
												  ('state','in',['sale','done']),
												  ('partner_id','=',line.id),
												  ('picking_date','like',date_str)])
			sub_name = ' '.join([x.name.split('(')[0] for x in line.category_id.filtered(lambda r: u'Борлуулалтын ангилал' in r.name)])
			full_name = line.name
			if sub_name:
				full_name = line.name+u' '+sub_name
			# if line.vat:
			# 	full_name += ' - '+str(line.vat) 

			# Харилцагч дээр байгаа эрхийн бичгийн дүнг авах --
			gift_amount = sum(self.env['mw.sales.gift.cart'].search([('partner_id','=',line.id),('state','=','confirmed')]).mapped('bonus_amount'))
			partners.append({
				'partner_id':line.id,
				'vat':line.vat,
				'name': full_name,
				'phone': line.phone,
				'image': base_url+url%line.id,
				'route_id': line.route_id.id,
				'street': line.street,
				'lat': line.partner_latitude,
				'lng': line.partner_longitude,
				'pricelist_id': line.property_product_pricelist.id,
				'ordered': True if so_s else False,
				'payment_type':line.payment_type,
				'tin_type':line.tin_type,
				'debt':round(p_debt,2),
				'gift_amount': gift_amount,
			})
			temp_ids.append(line.id)

		# Жолооч харилцагч татвал
		if self.env.user.team_type == 'driver':
			# Өөрийг нь заасан харилцагч байвал бас нэмнэ
			for line in self.env['res.partner'].search([('driver_id','=',self.env.user.id),
														('is_mobile_active','=',True)], order="name"):
				if line.id not in temp_ids:
					sub_name = ' '.join([x.name.split('(')[0] for x in line.category_id.filtered(lambda r: u'Борлуулалтын ангилал' in r.name)])
					full_name = line.name
					if sub_name:
						full_name = line.name+u' '+sub_name
					partners.append({
						'partner_id':line.id,
						'vat':line.vat,
						'name': full_name,
						'phone': line.phone,
						'image': base_url+url%line.id,
						'route_id': line.route_id.id,
						'street': line.street,
						'lat': line.partner_latitude,
						'lng': line.partner_longitude,
						'pricelist_id': line.property_product_pricelist.id,
						'ordered': True if so_s else False,
						'payment_type':line.payment_type,
						'tin_type':line.tin_type,
					})
					_logger.info("------ mobile ---additional--(partners)  %s ",full_name)
		_logger.info("------ mobile -----len(partners)  %s ",len(partners))
		return partners

	# Харилцагч дээр байгаа эрхийн бичгийн дүнг авах ----------------------
	@api.model
	def get_partner_gift_amount(self, data):
		_logger.info("------ mobile -----get_partner_gift_amount %s  %s", str(data), type(data))
		res = []
		partner = self.env['res.partner'].browse(data['partner_id'])
		if partner:
			gift_amount = sum(self.env['mw.sales.gift.cart'].search([('partner_id','=',data['partner_id']),('state','=','confirmed')]).mapped('bonus_amount'))
			temp = {
				'gift_amount': gift_amount,
			}
			res.append(temp)
			return res
		else:
			return False

	# Харилцагч татах
	def get_promotion_test(self):
		res = self.get_promotion_products()
		res = self.get_promotion(False)
		self.desc = str(res)

	@api.model
	def get_promotion_products(self):
		_logger.info("------ mobile ----- get_promotion_products ")
		partners = self.env['res.partner'].search([('user_id','=',self.env.user.id),
												   ('is_mobile_active','=',True)])
		now = datetime.datetime.now()
		promotions = self.env['mw.sales.promotion'].search([
					('is_pos','=',False),
					('state','=','confirmed'),
					('reward_type','=','free_product'),
					('free_product_type','=','choose'),
					('reward_product_line','!=',False),
					('date_start','<=',now),
					('date_end','>=',now)])
		datas = []
		for promo in promotions:
			for partner in partners:
				if set(promo.partner_category_ids.mapped('id')).issubset(partner.category_id.mapped('id')):
					datas.append(promo.id)

		tmp = list(set(datas))
		datas = []
		for promo in self.env['mw.sales.promotion'].search([('id','in',tmp)], order='name'):
			for line in promo.reward_product_line:
				temp = {
					'product_id':line.product_id.id,
					'default_code': line.product_id.default_code,
					'name': line.product_id.display_name,
				}
				datas.append(temp)
		_logger.info("------ mobile ----- get_promotion_products DATA %s " % str(datas))
		return datas
		
	@api.model
	def get_promotion(self, data):
		_logger.info("------ mobile ----- get_promotion %s " % str(data))
		partners = self.env['res.partner'].search([('user_id','=',self.env.user.id),
												   ('is_mobile_active','=',True)])
		now = datetime.datetime.now()
		promotions = self.env['mw.sales.promotion'].search([
					('is_pos','=',False),
					('state','=','confirmed'),
					('date_start','<=',now),
					('date_end','>=',now)])
		datas = []
		for promo in promotions:
			for partner in partners:
				if set(promo.partner_category_ids.mapped('id')).issubset(partner.category_id.mapped('id')):
					datas.append(promo.id)

		tmp = list(set(datas))
		promotions = []
		for promo in self.env['mw.sales.promotion'].search([('id','in',tmp)], order='name'):
			temp = {
				'promotion_id': promo.id,
				'name': promo.name,
				'can_be_selected': promo.can_be_selected,
				'start': promo.date_start,
				'end': promo.date_end,
			}
			promotions.append(temp)
		_logger.info("------ mobile ----- get_promotion   %s " % str(promotions))
		return promotions

	@api.model
	def update_res_partner(self, data):
		partners = []
		_logger.info("------ mobile -----update_res_partner %s  %s", str(data), type(data))
		partner_id = self.env['res.partner'].browse(int(float(data['partner_id'])))
		if partner_id:
			partner_id.partner_latitude = data['lat']
			partner_id.partner_longitude = data['lng']
		return True

	# Partner Үүсгэх
	def create_partner_test(self):
		vals = {
			'name': 'Mobile Test partner',
			'phone': 765555,
			'group_name': 'Test group',
			'street': 'SBD',
			'tin_type': 'person',
			'vat': '3456789',
			'customer': True,
			'ref': 'from_mobile',
		}
		self.create_partner(vals)

	@api.model
	def create_partner(self, data):
		_logger.info("------ mobile -----partner create datas %s  %s", str(data), type(data))
		vals = {}
		categs = [int(data['category_id'])]

		# Жижиглэн бол
		if self.env.user.team_type == 'small':
			cat = self.env['res.partner.category'].search([('name','ilike','Жижиглэн')], limit=1)
			if cat:
				categs.append(cat.id)
			cat = self.env['res.partner.category'].search([('name','ilike','С-Гоо')], limit=1)
			if cat:
				categs.append(cat.id)
			cat = self.env['res.partner.category'].search([('name','ilike','С-Хүнс')], limit=1)
			if cat:
				categs.append(cat.id)

		vals = {
			'name': data['name'],
			'phone': data['phone'],
			'group_name': data['group_name'],
			'street': data['street'],
			'tin_type': data['tin_type'],
			'vat': data['vat'],
			'route_id': int(float(data['route_id'])) if data['route_id'] > 0 else False,
			'customer': True,
			'category_id': [(6,0,categs)],
			'property_product_pricelist': self.env.user.partner_id.property_product_pricelist or False,
		}
		try:
			par = self.env['res.partner'].sudo().create(vals)
			_logger.info("------ mobile -----partner created ID  %d ",par.id)
			return {'partner_id': par.id}
		except Exception as e:
			_logger.info("------ mobile -----partner ERROR %s ",str(e))
			return {'partner_id': False, 'error': str(e)}

	# Зээлийн үлдэгдэл байгаа эсэхийг шалгах
	@api.model
	def get_payment_debt(self, data):
		_logger.info("------ get_payment_debt --------------- %s "%(data))
		if data['partner_id'] in [7463,3914,3011,3649,3152,3459]:
			return False
		if sum(self.env['account.move'].search([('partner_id','=',data['partner_id']),('user_id','in',self.env.user.ids)]).mapped('amount_residual'))>1000:
			return True
		return False

	# Өөрт ирсэн чат болон өөрийн үүсгэсэн захиалгууд төлөгдсөн урамшуулал батлагдсан эсэх мэдээлэл авах
	@api.model
	def get_information(self, data):
		_logger.info("------ get_information --------------- %s "%(data))
		result = []
		team_type = self.env.user.team_type
		parent_id = self.env.user.partner_id.id
		user_id = self.env.user.id
		t_where = ""
		t_where1 = ""

		if self.env.user.team_type == 'small':		
			t_where = "abc"
			t_where1 = ""
		else: 
			if self.env.user.team_type == 'salesman':		
				t_where = "bm1"
				t_where1 = "bm3"
			else: 
				if self.env.user.team_type == 'small_market':		
					t_where = "bm2"
					t_where1 = "bm4"
				else:
					if self.env.user.team_type == 'driver':		
						t_where = "driver"
						t_where1 = "driver"
		query = """
			SELECT 
				id as last_id, 
				date,
				email_from,
				body,
				record_name,
				model,
				--website_published,
				(select CONCAT((select name from res_partner where id = partner_id limit 1), ' Дүн: ', amount_total) from sale_order where id = res_id limit 1) as add
			FROM mail_message 
			WHERE (res_id in (select channel_id from mail_channel_partner where partner_id = %d) and 
				   author_id <> %s and subtype_id = 1 ) or (body<>'' and 
				   model = 'mw.sales.promotion' and 
				   (record_name::text ilike '%s%%' or record_name::text ilike '%s%%') and 
				   parent_id > 0 ) or (body<>'' and model = 'sale.order' and parent_id > 0 and (select user_id from sale_order where id=res_id limit 1)=%d)
			ORDER BY id desc limit 30
		""" % (parent_id, parent_id, t_where, t_where, user_id)
		self.env.cr.execute(query)
		query_result = self.env.cr.dictfetchall()
		for line in query_result:
			last_id = line['last_id']
			email_from = line['email_from']
			email_from = email_from.split()[0]
			email_from = email_from.replace('"', '')
			model = line['model']
			record_name = line['record_name']
			date = line['date']
			add = line['add']
			body = line['body']
			body = body[3:-4]
			email_from = email_from+' : '+body
			result.append({'email_from': email_from, 'last_id': last_id, 'record_name': record_name, 'add': add, 'model': model, 'date': date})
			# result.append({'body': body})

		mail_message = self.env['mail.message'].browse(int(float(last_id)))
		#	return True
		if result:
			return result
		return False

	# Хүргэгдээгүй захиалгыг жагсаалт
	@api.model
	def get_must_deliver_so_list(self, data):
		_logger.info("------ get_must_deliver_so_list --------------- %s "%(data))
		result = []
		product_id = data['product_id']
		partner_id = data['partner_id']

		query_plan = '''
			SELECT  
				sol.product_id as product_id,
				sol.order_id as order_id,
				max(so.name) as so_name,
				max(so.date_order) as so_date,
				ROUND(sum(sol.product_uom_qty),2) as product_uom_qty,
				ROUND(sum(sol.qty_delivered),2) as qty_delivered,
				SUM(so.amount_total) as amount_total 
			FROM sale_order_line as sol 
			JOIN sale_order as so on sol.order_id = so.id 
			WHERE so.state <> 'cancel' and 
				  so.partner_id in (%s) and 
				  sol.product_id in (%s) and 
				  sol.product_uom_qty <> sol.qty_delivered 
			GROUP BY sol.order_id, sol.product_id 
			ORDER BY max(so.create_date), sol.product_id asc
		''' % (partner_id, product_id)
		# print '===============PLAN MUST DELIVER SO LIST======-------------', query_plan
		self.env.cr.execute(query_plan)
		query_result = self.env.cr.dictfetchall()
		for line in query_result:
			order_id = line['order_id']
			so_date = line['so_date']
			so_name = line['so_name']
			product_id = line['product_id']
			product_uom_qty = line['product_uom_qty']
			qty_delivered = line['qty_delivered']
			amount_total = line['amount_total']
			result.append({'order_id': order_id, 
						   'so_date': so_date, 
						   'so_name': so_name, 
						   'product_uom_qty': product_uom_qty, 
						   'qty_delivered': qty_delivered, 
						   'amount_total': amount_total, 
						   'product_id': product_id})
		if result:
			return result
		return False
		
	def create_sale_order2(self):
		res = self.create_sale_order([{
			'partner_id': 1,
			'validity_date': '2019-07-06 09:26:09',
			'warehouse_id': 1,
			'mobile_id':4414,
			'is_gift_sale': 'no',
			'order_line': [
				{'product_id': 12,
				'product_uom_qty': 30,
				'price_unit': 1000,},
				{'product_id': 13,
				'product_uom_qty': 40,
				'price_unit': 3000,}
				]
			}
			])
		
		self.desc = str(res)

	def _days_between(self, d1, d2):
		d1 = datetime.datetime.strptime(d1, "%Y-%m-%d")
		d2 = datetime.datetime.strptime(d2, "%Y-%m-%d")
		return abs((d2 - d1).days)

	# Захиалга үүсгэх
	@api.model
	def create_sale_order(self, data):
		res = []
		s_val = []
		_logger.info("------create_sale_order --------------- %s " % (data))
		sale_obj = self.env['sale.order']
		sale_line_obj = self.env['sale.order.line']
		product_lock = self.env['product.mobile.lock']
		user_id = self.env.user

		# Нэхэмжлэлийн бодлого шалгах
		res_config = self.env['res.config.settings']
		delivery_policy = res_config.sudo().create({}).default_invoice_policy
		
		for item in data:
			is_gift_sale = item['is_gift_sale']
			payment_type = item.get('payment_type', '')
			# Жолоочийг SET хийх
			picking_date = item.get('picking_date',False)
			partner0 = self.env['res.partner'].browse(item['partner_id'])
			vals = {
				'partner_id': item['partner_id'],
				'is_gift_sale': True if is_gift_sale=='yes' else False,
				'validity_date': item['validity_date'],
				'picking_date': picking_date or item['validity_date'] ,
				'warehouse_id': item['warehouse_id'],
				'origin': 'from_mobile',
				'mobile_id': item['mobile_id'],
				'payment_type': payment_type,
				'driver_id': partner0.driver_id.id if partner0.driver_id else False,
				'note': item['note'] if 'note' in item else '',
				'custom_promotion_id': item['custom_promotion_id'] if 'custom_promotion_id' in item else False,
			}
			if 'with_e_tax' in item and item['with_e_tax'] == 'yes':
				vals['with_e_tax'] = True
			else:
				vals['with_e_tax'] = False
			line_vals = []
			
			# SOL бэлдэх
			not_available = []
			for line in item['order_line']:
				product = self.env['product.product'].browse(line['product_id'])
				package_qty = 1
				if product.uom_po_id and product.uom_po_id.factor > 0:
					package_qty = product.uom_po_id.factor
				# Барааг цоожлосон эсэхийг шалгах
				is_locked_product = product_lock.sudo().get_mobile_lock(product,user_id.crm_team_id)
				if is_locked_product:
					_logger.info("-----mobile---- SO product lock  %s %s",product.id,product.display_name)
					return [{
							'mobile_id': False,
							'order_line': False,
							'error_type': 'locked_product',
							'lottery': False, 
							'qrdata': False,
							'ddtd': False,
							'new_amount': False,
							'reward_product': False
							}]

				# Агуулахын үлдэгдэл хүрэлцэж байгаа эсэхийг шалгах ===============
				# Агуулахтай борлуулагч бол
				wh_ids = self.env['stock.warehouse'].browse(item['warehouse_id'])
				total_available_qty = self.get_available(product, wh_ids)
				_logger.info("\n-----mobile---- SO product QTY p_id %d, vld %d %d, wh %s \n",line['product_id'], total_available_qty, line['product_uom_qty'], str(wh_ids))
				if self.env.user.team_type=='salesman':
					if item['direct_deliver']=='yes':
						if line['product_uom_qty'] > total_available_qty:
							not_available.append({
								'product_id': line['product_id'],
								'product_uom_qty': total_available_qty,
								'product_name': product.display_name, 
								})
					line_vals.append((0,0,{
						'product_id': line['product_id'],
						'product_uom_qty': line['product_uom_qty'],
						'price_unit': line['price_unit'],
						'package_qty': line['product_uom_qty']/package_qty,
						}))
				else:
					if line['product_uom_qty'] <= total_available_qty:
						line_vals.append((0,0,{
							'product_id': line['product_id'],
							'product_uom_qty': line['product_uom_qty'],
							'price_unit': line['price_unit'],
							'package_qty': line['product_uom_qty']/package_qty,
							}))
					else:
						not_available.append({
							'product_id': line['product_id'],
							'product_uom_qty': total_available_qty,
							'product_name': product.display_name, 
							})
			# Бараа гаргах боломжтой эсэх, Батлах, нэхэмжлэх үүсгэх =================
			# Агуулахтай борлуулагч бол =============
			if self.env.user.team_type=='salesman':
				if not_available and item['direct_deliver']=='yes':
					reward_product = []
					res.append({
						'mobile_id': item['mobile_id'],
						'order_line': False,
						'error_type': 'not_available',
						'not_available': not_available,
						'lottery': False, 
						'qrdata': False,
						'ddtd': False,
						'new_amount': 0,
						'reward_product': reward_product if reward_product else False
						})
				else:
					if line_vals:
						vals['order_line'] = line_vals
						if item['direct_deliver'] != 'yes':
							vals['picking_policy'] = 'one'
						c_id = sale_obj.create(vals)
						c_id.button_dummy()

						so_context = {
							'reward_line': item['reward_line'] if 'reward_line' in item else False
						}
						c_id.with_context(so_context).action_confirm()
						# =======================================

						# Хэрэв борлуулагч төв агуулахаас захисан бол шууд хүргэлт хийхгүй болгох
						if item['warehouse_id'] != self.env.user.warehouse_id.id:
							item['direct_deliver'] = 'no'
						# =======================================
						# Шууд хүргэлт бол
						if item['direct_deliver']=='yes':
							direct_data_line = []
							direct_data = {
								'so_id': c_id.id,
								'order_line': [],
								'delivery_type': 'delivery',
							}
							for cc in c_id.order_line:
								direct_data_line.append({
									'product_id': cc.product_id.id,
									'product_uom_qty': cc.product_uom_qty,
									})
							direct_data['order_line'] = direct_data_line
							# Дутуу хүргэж болно, тэгвэл backorder үүсгэнэ
							# Хүргэлтийг яг одоо дуусгах THREAD ===================
							self._cr.commit()
							thread1 = threading.Thread(target=self._picking_to_done, args=(direct_data,))
							_logger.info("\n----THREADing=====CALL========COUNT=== %d " % threading.activeCount())
							thread1.start()
							# ==== OLD =========
							# self.create_back_so_back_order(direct_data)
						else:
							# =======================================
							c_id.picking_ids.do_unreserve()
							for ppick in c_id.picking_ids:
								if ppick.picking_type_id.code=='outgoing':
									ppick.priority=='0'
									if ppick.state=='assigned':
										ppick.do_unreserve()
						# Урамшууллын барааг бэлдэх 
						reward_product = []
						for rew in c_id.order_line.filtered(lambda r: r.is_reward_product):
							reward_product.append({
								'product_id': int(rew.product_id.id),
								'product_uom_qty': int(rew.product_uom_qty),
								'price_unit': int(rew.price_unit),
								})
						_logger.info("-----mobile---- SO created  %d ",c_id.id)
						
						# НӨАТ өгөх ===================================
						if c_id.with_e_tax and c_id.partner_id.tin_type in ['person','company']:
							# Үйлдэл хэмнэсэн ==============
							# c_id.create_ebarimt()
							vals['lottery'] = c_id.lottery
							vals['qrdata'] = c_id.qrdata
							vals['ddtd'] = c_id.ddtd

						vals = {
							'mobile_id': item['mobile_id'],
							'order_line': True,
							'error_type': 'success',
							'order_name': c_id.name,
							'new_amount': c_id.amount_total,
							'discount_amount': c_id.total_discount,
							'reward_product': reward_product if reward_product else False
							}
						res.append(vals)
			# ХТ-ийн борлуулалт =====================================================
			# ХТ бол хүргэлтийг дуусгахгүй
			else:
				# uldegdel shalgah
				if not not_available:
					if line_vals:
						vals['order_line'] = line_vals
						c_id = sale_obj.create(vals)
						c_id.button_dummy()

						so_context = {
							'reward_line': item['reward_line'] if 'reward_line' in item else False
						}
						c_id.with_context(so_context).action_confirm()				
						# =======================================
						reward_product = []
						for rew in c_id.order_line.filtered(lambda r: r.is_reward_product):
							reward_product.append({
								'product_id': int(rew.product_id.id),
								'product_uom_qty': int(rew.product_uom_qty),
								'price_unit': int(rew.price_unit),
								})

						_logger.info("-----mobile---- SO created  %d ",c_id.id)
						vals = {
							'mobile_id': item['mobile_id'],
							'order_line': True,
							'error_type': 'success',
							'order_name': c_id.name,
							'new_amount': c_id.amount_total,
							'discount_amount': c_id.total_discount,
							'lottery': False, 
							'qrdata': False,
							'ddtd': False,
							'reward_product': reward_product if reward_product else False
							}
						res.append(vals)
						# Борлуулагчийн маршрут үүсгэх
						route_res = self.create_salesman_route(self.env.user.id, item['partner_id'], item['validity_date'], 'successful')
				else:
					reward_product = []
					res.append({
						'mobile_id': item['mobile_id'],
						'order_line': False,
						'error_type': 'not_available',
						'not_available': not_available,
						'lottery': False, 
						'qrdata': False,
						'ddtd': False,
						'new_amount': 0,
						'reward_product': reward_product if reward_product else False
						})
		_logger.info("----mobile----- SO done -- res  %s ",res)
		return res

	# THREAD нэхэмжлэх үүсгэх, батлах
	def _approve_invoice(self, args):
		with api.Environment.manage():
			_logger.info("\n -----THREAD STARTING!!!!----------args %s \n" % (args))
			
			new_cr = self.pool.cursor()
			self = self.with_env(self.env(cr=new_cr))
			# try:
			so_id = args
			so = self.env['sale.order'].browse(so_id)
			_logger.info("\n -----THREAD SO---------- %s " % (so_id))
			
			# Нэхэмжлэх батлах
			context = {
				"active_model": 'sale.order',
				"active_ids": [so_id],
				"active_id": so_id,
				'open_invoices': False,
			}
			payment = self.env['sale.advance.payment.inv'].with_context(context).create({
				'advance_payment_method': 'delivered',
			})
			payment.with_context(context).create_invoices()
			so.invoice_ids.action_post()
			
			new_cr.commit()
			new_cr.close()
			_logger.info("\n -----THREAD finish---INVOICE------- \n\n\n")
			return

	# THREAD ээр хүргэлтийг дуусгах ===============================
	def _picking_to_done(self, args):
		with api.Environment.manage():
			_logger.info("\n -----THREAD STARTING Picking done!!!!----------args %s \n" % (args))
			
			new_cr = self.pool.cursor()
			self = self.with_env(self.env(cr=new_cr))
			data = args
			sale_obj = self.env['sale.order']
			so = sale_obj.browse(int(float(data['so_id'])))
			_logger.info("\n -----THREAD SO---------- %s " % (data['so_id']))
			# ================== PICKING =========================================
			sale_orders = []
			lines=[]
			if data['delivery_type'] =='delivery':
				not_done_pick = so.picking_ids.filtered(lambda r: r.state not in ['done','cancel'])
				_logger.info("------ mobile -----hudulguun batlagdaagui %s  ", not_done_pick)
				if not_done_pick:
					for line in data['order_line']:
						product = self.env['product.product'].browse(int(line['product_id']))
						not_product = False
						for pick in not_done_pick:
							if pick.state in ['confirmed','draft']:
								pick.action_assign()
							for item in pick.move_lines.filtered(lambda r: r.product_id.id==product.id and  r.product_uom_qty>=float(line['product_uom_qty'])):
								if not item.quantity_done:
									_logger.info("------  %s %d ", product.name, line['product_uom_qty'] )
									# item.quantity_done = line['product_uom_qty']
									item._set_quantity_done(line['product_uom_qty'])
									not_product = True
				# Back order үүсгэх
				pick_backorder = self.env['stock.backorder.confirmation']
				done_transfer = self.env['stock.immediate.transfer']
				for item in not_done_pick:
					if item._check_backorder():
						_logger.info("------ mobile -----BACK ORDER ")
						pick_id = [(4, item.id)]
						backorder_id = pick_backorder.create({
							'pick_ids': pick_id
							})
						backorder_id.process()
					else:
						_logger.info("------ mobile ---THREAD...SP--DONE transfer ")
						pick_id = [(4, item.id)]
						done_transfer_id = done_transfer.create({
							'pick_ids': pick_id
							})
						done_transfer_id.process()

				for item in not_done_pick:
					if item.state in ['assigned']:
						item.do_unreserve()
				_logger.info("------ mobile ----T SP-not_done_pick %s ", str(not_done_pick))
				not_done_pick = so.picking_ids.filtered(lambda r: r.state not in ['done','cancel'])
			# ===========================================================
			# ================== INVOICE =========================================
			# Нэхэмжлэлийн бодлого шалгах
			res_config = self.env['res.config.settings']
			delivery_policy = res_config.sudo().create({}).default_invoice_policy
			# Хүргэсэн тооноос нэхэмжлэх үүсгэхгүй бол нэхэмжлэх үүсгэнэ
			if delivery_policy != 'delivery':
				# Нэхэмжлэх батлах
				context = {
					"active_model": 'sale.order',
					"active_ids": [data['so_id']],
					"active_id": data['so_id'],
					'open_invoices': False,
				}
				payment = self.env['sale.advance.payment.inv'].with_context(context).create({
					'advance_payment_method': 'delivered',
				})
				payment.with_context(context).create_invoices()
				so.invoice_ids.action_post()
			# ===========================================================
			new_cr.commit()
			new_cr.close()
			_logger.info("\n -----THREAD finish---PICKINGs------- \n\n\n")
			return

	# Захиалгыг хүргэлтийг цувуулж өгөх ======
	# Бүрэн бол шууд дуусгах =================
	@api.model
	def create_back_so_back_order(self, data):
		_logger.info("------ mobile -----create_back_so_back_order %s  %s", str(data), type(data))
		sale_orders = []
		sale_obj = self.env['sale.order']
		lines=[]
		sale_order_id = sale_obj.browse(int(float(data['so_id'])))
		if data['delivery_type'] =='delivery':
			not_done_pick = sale_order_id.picking_ids.filtered(lambda r: r.state not in ['done','cancel'])
			_logger.info("------ mobile -----hudulguun batlagdaagui %s  ", not_done_pick)
			if not_done_pick:
				for line in data['order_line']:
					product = self.env['product.product'].browse(int(line['product_id']))
					not_product = False
					for pick in not_done_pick:
						if pick.state in ['confirmed','draft']:
							pick.action_assign()
						for item in pick.move_lines.filtered(lambda r: r.product_id.id==product.id and  r.product_uom_qty>=float(line['product_uom_qty'])):
							if not item.quantity_done:
								_logger.info("------  %s %d ", product.name, line['product_uom_qty'] )
								# item.quantity_done = line['product_uom_qty']
								item._set_quantity_done(line['product_uom_qty'])
								not_product = True
			else:
				return False
			# Back order үүсгэх
			pick_backorder = self.env['stock.backorder.confirmation']
			done_transfer = self.env['stock.immediate.transfer']
			for item in not_done_pick:
				if item._check_backorder():
					_logger.info("------ mobile -----BACK ORDER ")
					pick_id = [(4, item.id)]
					backorder_id = pick_backorder.create({
						'pick_ids': pick_id
						})
					backorder_id.process()
				else:
					_logger.info("------ mobile -----DONE transfer ")
					pick_id = [(4, item.id)]
					done_transfer_id = done_transfer.create({
						'pick_ids': pick_id
						})
					done_transfer_id.process()

			for item in not_done_pick:
				if item.state in ['assigned']:
					item.do_unreserve()
			_logger.info("------ mobile -----not_done_pick %s ", str(not_done_pick))
			not_done_pick = sale_order_id.picking_ids.filtered(lambda r: r.state not in ['done','cancel'])
			if not_done_pick:
				return False
			return True
		return False

	# Барааны буцаалт --------------
	@api.model
	def so_return_product(self, data):
		_logger.info("------ mobile -----so_return_product %s  %s", str(data), type(data))
		sale_orders = []
		sale_obj = self.env['sale.order']
		pick_obj = self.env['stock.picking']
		lines=[]
		sale_order_id = sale_obj.browse(int(float(data['so_id'])))
		# Гарсан picking г олох
		done_pick = sale_order_id.picking_ids.filtered(lambda r: r.state in ['done'] and r.picking_type_id.code=='outgoing')
		_logger.info("------ mobile ----- butsaah hudulguun START...%s  ", done_pick)
		if done_pick:
			done_pick = done_pick[0]
			save_data_orderline = data['order_line']
			# NEW ===== Барааны буцаалт ============
			stock_return_picking_form = Form(self.env['stock.return.picking'].with_context(
				active_id=done_pick.id,
				active_model='stock.picking'
			))
			stock_return_picking_form.return_reason = data['return_reason']
			return_picking_id = stock_return_picking_form.save()
			refund_invoice_lines = []
			for ret in return_picking_id.product_return_moves:
				is_found = False
				for line in data['order_line']:
					p_id = int(float(line['product_id']))
					if p_id == ret.product_id.id and ret.quantity>=line['product_uom_qty'] and line['product_uom_qty']!=0:
						ret.quantity = line['product_uom_qty']
						ret.to_refund = True
						is_found = True
						break
				if not is_found:
					ret.unlink()
			pick_id, spt_id = return_picking_id._create_returns()
			# Буцаалтын хөдөлгөөн дуусгах
			done_transfer = self.env['stock.immediate.transfer']
			done_transfer_id = done_transfer.create({
				'pick_ids': [pick_id]
				})
			done_transfer_id.process()
			_logger.info("------ mobile -----so_return_product: RETURN picking ===========\n")

			# Нэхэмжлэх буцаах
			posted_inv = sale_order_id.sudo().invoice_ids.filtered(lambda r: r.state in ['posted'] and r.type == 'out_invoice')
			if posted_inv:
				moves = posted_inv[0]
				# ======================
				default_values_list = []
				for move in moves:
					default_values_list.append({
						'ref': ('Reversal of: %s') % (move.name),
						'date': datetime.datetime.now(),
						'invoice_date': move.is_invoice(include_receipts=True) and (move.date) or False,
						'journal_id': move.journal_id.id,
					})
				new_moves = moves.sudo()._reverse_moves(default_values_list)
				invoice_lines = self.env['account.move.line']
				for line in data['order_line']:
					p_id = int(float(line['product_id']))
					for inv_line in new_moves.sudo().invoice_line_ids:
						if p_id == inv_line.product_id.id and line['product_uom_qty']!=0:
							# inv_line.quantity = line['product_uom_qty']
							inv_line.with_context(check_move_validity=False).sudo().write({'quantity': line['product_uom_qty']})
							invoice_lines |= inv_line
				# Шинэ line update хийх
				new_moves.with_context(check_move_validity=False).sudo().write({'invoice_line_ids': [(6, 0, invoice_lines.ids)]})
			_logger.info("------ mobile -----so_return_product FINISH ===========\n")
			return True
		
		return False

	def create_user_location2(self):
		data = []
		data.append({'user_id':self.env.user.id,'lng':1000,'lat':2000})
		res = self.create_user_location(data)
		self.desc = str(len(res))

	# Борлуулагчийн байрлал зурах
	@api.model
	def create_user_location(self, data):
		_logger.info("create_user_location --------------- %s "%(data))
		loc_obj = self.env['res.user.location']
		if data:
			vals = {
				'user_id': data['user_id'],
				'lng': data['lng'],
				'lat': data['lat'],
			}
			c_id = loc_obj.create(vals)
			_logger.info(" location ID  %d ", c_id.id)
		return True

	# Дотоод хөдөлгөөн үүсгэх - TEST
	def create_internal_move_test(self):
		data = {}
		data['src'] = 30
		# data['dest'] = 2
		data['lines'] = [
			{'product_id':26456, 'qty':10},
			{'product_id':26143, 'qty':8}
		]
		res = self.create_internal_move(data)
		self.desc = str(res)

	# Дотоод хөдөлгөөн үүсгэх
	@api.model
	def create_internal_move(self, datas):
		products = []
		_logger.info("-----------------mobile ====== create_internal_move %s " % str(datas))
		# Агуулахтай борлуулагч бол дотоод хөдөлгөөн үүсгэнэ
		if datas and self.env.user.team_type=='salesman':
			warehouse_1_id = datas['src']
			# Ижил агуулах бол үүсгэхгүй
			if warehouse_1_id == self.env.user.warehouse_id.id:
				return False

			src_warehouse = self.env['stock.warehouse'].search([('id','=',warehouse_1_id)], limit=1)
			dest_warehouse = self.env.user.warehouse_id
			if src_warehouse.id == dest_warehouse.id:
				_logger.info("-----------------mobile ====== create_internal_move === SAME warehouses")
				return False
			if not src_warehouse or not dest_warehouse:
				_logger.info("-----------------mobile ====== create_internal_move === NOT FOUND warehouses")
				return False

			# Дотоод хөдөлгөөн үүсгэх
			sp_id = self.env['stock.picking'].create(
				{'picking_type_id': src_warehouse.int_type_id.id,
				 'location_id': src_warehouse.lot_stock_id.id,
				 'location_dest_id': dest_warehouse.lot_stock_id.id,
				 'state': 'draft',
				 'origin': 'Mobile - '+self.env.user.name,
				})
			for line in datas['lines']:
				_logger.info("-----------------mobile ====== create_internal_move === LINE %s " % str(line))
				product = self.env['product.product'].browse(int(line['product_id']))
				if product:
					vals = {
						'name': 'Mobile - '+self.env.user.name,
						'picking_id': sp_id.id,
						'product_id': product.id,
						'product_uom': product.uom_id.id,
						'product_uom_qty': line['qty'],
						'origin': 'Mobile - '+self.env.user.name,
						'price_unit': product.standard_price,
						'location_id': src_warehouse.lot_stock_id.id,
						'location_dest_id': dest_warehouse.lot_stock_id.id,
						'state': 'draft',
					}
					line_id = self.env['stock.move'].create(vals)
					_logger.info("-----------------mobile ====== create_internal_move === MOVE created %d " % line_id.id )
				else:
					_logger.info("-----------------mobile ====== create_internal_move === NOT FOUND product")
			_logger.info("-----------------mobile ====== create_internal_move === CONFIRM picking %s " % sp_id.name )
			sp_id.action_confirm()
			_logger.info("-----------------mobile ====== create_internal_move === CREATED %s " % sp_id.name)
			return True if sp_id else False

	# Харилцагчаар нь SO нууд харах, Дотоод хөдөлгөөнүүд харах, Тухайн өдрийн SO нууд харах
	@api.model
	def get_payment_so_list(self,data):
#		 data={'date':'2018-09-10','partner_id':self.partner_id.id}
		_logger.info("------ mobile -----get_payment_so_list %s  %s", str(data), type(data))
		sale_orders = []
		sale_obj = self.env['sale.order']
		pick_obj = self.env['stock.picking']
		m_date = data['date'][:7]+'%'
		current_date = data['date']
		sdate = data['date'].split('-')[0]+'-'+data['date'].split('-')[1]+'-01'
		edate = data['date'].split('-')[0]+'-'+data['date'].split('-')[1]+'-'+str(monthrange(int(data['date'].split('-')[0]), int(data['date'].split('-')[1]))[1])
		_logger.info("------ mobile ----- **** sdate: %s  edate: %s", sdate, edate)
		_logger.info("------ mobile ----- **** part: %d %s", data['partner_id'], m_date)
		# Dotood hudulguun
		if data['partner_id']==-1:
			so_ids = pick_obj.search([
				  ('date','>=',sdate),
				  ('date','<=',edate),
				  ('location_id.usage','=','internal'),
				  ('state','not in',['cancel','draft']),
				  ('location_dest_id','=',self.env.user.warehouse_id.lot_stock_id.id),
				  ])
			for so in so_ids:
				sale_orders.append({
					'so_id':so.id,
					'so_name':so.name,
					'so_date':so.date,
					'qty_inch': 0,
					'payment':0,
					'amount_total':0,
					'discount_amount': 0,
					})
			_logger.info("------ mobile -----len(Pickings)  %s",len(sale_orders))
		# Тухайн өдрийн SO бөөнд нь явуулах ======================
		elif data['partner_id']==0:
			so_ids = []
			pay_obj=self.env['sale.payment.info']
			# Жолооч SO татвал
			if self.env.user.team_type == 'driver':
				so_ids = sale_obj.sudo().search([
					  ('picking_date','=',current_date),
					  ('state','in',['sale','done']),
					  ('driver_id','=',self.env.user.id)
					])
			else:
				so_ids = sale_obj.sudo().search([
					  ('validity_date','=',current_date),
					  ('state','in',['sale','done']),
					  ('partner_id.user_id','=',self.env.user.id)
					])
			_logger.info("------ mobile -----SO ids ===== %s \n",str(so_ids.ids))

			if so_ids:
				for so in so_ids:
					is_rew = 0
					if so.order_line.filtered(lambda r: r.is_reward_product):
						is_rew = 5
					ppick_id = pick_obj.search([('sale_id','=',so.id), ('picking_type_id.code','=','outgoing'),('state','=','done')], order='date_done desc', limit=1)
					delivery_date = False
					if ppick_id:
						delivery_date = ppick_id.date_done
						delivery_date = delivery_date.strftime('%Y-%m-%d')
					pick_ids = so.picking_ids.filtered(lambda r: r.state in ['done'] and r.picking_type_id.code=='outgoing')

					# payments = pay_obj._compute_partner_sale_payment(so.partner_id.id,sdate,edate)
					pay_residual = sum(so.invoice_ids.filtered(lambda r: r.type=='out_invoice' and r.state != 'cancel').mapped('amount_residual'))
					pay_out_total = sum(so.invoice_ids.filtered(lambda r: r.type=='out_invoice' and r.state != 'cancel').mapped('amount_total'))
					pay_refund_total = sum(so.invoice_ids.filtered(lambda r: r.type=='out_refund' and r.state != 'cancel').mapped('amount_total'))
					sale_orders.append({
						'so_id':so.id,
						'partner_id':so.partner_id.id,
						'warehouse_id':so.warehouse_id.id,
						'qty_inch': is_rew,
						'so_name':so.name,
						'so_date':so.validity_date,
						# 'payment': sum([x['amount'] if x['so_id'] == so.id else 0 for x in payments]),
						'payment':pay_out_total-pay_refund_total-pay_residual,
						# Bayasaa haav
						'amount_total':so.amount_total,
						'discount_amount': so.total_discount,
						'invoice_amount_total':so.invoice_amount_total,
						'is_delivered': False if so.picking_ids.filtered(lambda r: r.state not in ['done','cancel']) else True,
						'delivery_date': delivery_date,
						'is_return': True if so.order_line.filtered(lambda r: r.return_qty>0) else False,
						'is_daralt': False,
						'printed': ppick_id.printed,
						'payment_type':so.payment_type,
					})
		# Харилцагчаар нь Sale order явуулах =====================
		else:
			so_ids = sale_obj.sudo().search([
				('state','in',['sale','done','draft']),
				('partner_id','=',data['partner_id']),
				('state','in',['sale','done']),
				('validity_date','>=',sdate),
				('validity_date','<=',edate)])
			if so_ids:
				if len(so_ids) > 1:
					so_ids = str(tuple(so_ids.ids))
				elif len(so_ids) == 1:
					so_ids = '('+str(so_ids.id)+')'

				sql_query = """
					SELECT so.id
					FROM sale_order so 
					LEFT JOIN
						res_partner rp on rp.id = so.partner_id
					WHERE so.id in %s
					ORDER BY rp.name
				""" % (so_ids)
				self.sudo().env.cr.execute(sql_query)
				res = self.sudo().env.cr.dictfetchall()

				pay_obj = self.env['sale.payment.info']
				# _logger.info("------ mobile -----payments===:  %s",payments)
				for item in res:
					so = self.env['sale.order'].sudo().browse(item['id'])
					pay_residual = sum(so.invoice_ids.filtered(lambda r: r.type=='out_invoice' and r.state != 'cancel').mapped('amount_residual'))
					pay_out_total = sum(so.invoice_ids.filtered(lambda r: r.type=='out_invoice' and r.state != 'cancel').mapped('amount_total'))
					pay_refund_total = sum(so.invoice_ids.filtered(lambda r: r.type=='out_refund' and r.state != 'cancel').mapped('amount_total'))
					ppick_id = pick_obj.search([('sale_id','=',so.id), ('picking_type_id.code','=','outgoing'),('state','=','done')], order='date_done desc', limit=1)
					delivery_date = False
					if ppick_id:
						delivery_date = ppick_id.date_done
						delivery_date = delivery_date.strftime('%Y-%m-%d')

					is_rew = 0
					if so.order_line.filtered(lambda r: r.is_reward_product):
						is_rew = 5
					sale_orders.append({
						'so_id':so.id,
						'qty_inch': is_rew,
						'so_name':so.name,
						'warehouse_id':so.warehouse_id.id,
						'so_date':so.validity_date,
						'payment':pay_out_total-pay_refund_total-pay_residual,
						'amount_total':so.amount_total,
						'discount_amount': so.total_discount,
						'invoice_amount_total':so.invoice_amount_total,
						'is_delivered': False if so.picking_ids.filtered(lambda r: r.state not in ['done','cancel']) else True,
						'delivery_date': delivery_date,
						'is_return': True if so.order_line.filtered(lambda r: r.return_qty>0) else False,
						'is_daralt': False,
						'printed': ppick_id.printed,
						'payment_type':so.payment_type,
						})
		_logger.info("------ mobile -----get_payment_so_list SOs DATA %s %d ", str(sale_orders), len(sale_orders))							
		return sale_orders

	# 1 SO харах, Бараагаар нь харах, Дотоод хөдөлгөөн орж харах
	@api.model
	def get_payment_so_product_list(self,data):
#		 data={'date':'2018-09-10','partner_id':self.partner_id.id}
		_logger.info("------ mobile -----get_payment_so_product_list %s  %s", str(data), type(data))
		sale_obj = self.env['sale.order']
		pick_obj = self.env['stock.picking']
		sdate=data['so_id']
		lines=[]
		# Бараагаар нь бүлэглэж харах ==========================
		if data['so_id'] == -1 and data['internal_move'] == 'false':
			current_date = data['date']
			sale_line_obj = self.env['sale.order.line']

			sql_query = """
				SELECT 
					so.warehouse_id,
					sol.product_id,
					sol.price_unit,
					sol.is_reward_product,
					sum(sol.product_uom_qty) as product_uom_qty,
					sum(sol.return_qty) as return_qty,sum(0) as daralt_qty, 
					sum(sol.product_uom_qty)*sol.price_unit as sub_total
				FROM sale_order_line as sol
				LEFT JOIN sale_order as so on sol.order_id=so.id
				LEFT JOIN res_partner as rp on rp.id=so.partner_id
				WHERE 
					(so.validity_date + interval '8 hour')::date  = %s and 
					rp.user_id = %s and 
					so.warehouse_id in %s
			  	GROUP BY sol.product_id, sol.price_unit, sol.is_reward_product, so.warehouse_id
			"""
			if self.env.user.team_type == 'driver':
				sql_query = """
					SELECT 
						so.warehouse_id,
						sol.product_id,
						sol.price_unit,
						sol.is_reward_product,
						sum(sol.product_uom_qty) as product_uom_qty,
						sum(sol.return_qty) as return_qty,sum(0) as daralt_qty, 
						sum(sol.product_uom_qty)*sol.price_unit as sub_total
					FROM sale_order_line as sol 
					LEFT JOIN sale_order as so on sol.order_id=so.id
					LEFT JOIN res_partner as rp on rp.id=so.partner_id
					WHERE 
						(so.picking_date + interval '8 hour')::date  = %s and 
						rp.driver_id = %d and 
						so.warehouse_id in %s
					GROUP BY sol.product_id, sol.price_unit, sol.is_reward_product, so.warehouse_id
				  """
			params = (current_date,self.env.user.id,tuple(self.env.user.warehouse_ids.ids))
			_logger.info("------ mobile -----get_payment_so_product_list QUERY - %s", str(sql_query))
			self.env.cr.execute(sql_query, params)
			res=self.env.cr.dictfetchall()
			for item in res:
				lines.append({
					'product_id': item['product_id'],
					'price_unit': item['price_unit'],
					'product_uom_qty': item['product_uom_qty'],
					'return_qty': item['return_qty'],
					'daralt_qty': item['daralt_qty'],
					'sub_total': item['sub_total'],
					'qty_inch': 5 if item['is_reward_product'] else 0,
					'warehouse_id': item['warehouse_id'],
				})
		# Дотоод хөдөлгөөн орж харах =======================
		elif data['internal_move']=='true':
			_logger.info("------ mobile -----get_payment_so_product_list INTERNAL MOVE %s", str(data['so_id']))
			pick = pick_obj.browse(int(float(data['so_id'])))
			for sol in pick.move_lines:
				lines.append({
					'product_id':sol.product_id.id,
					'qty': sol.product_uom_qty,
					'qty_delivered': sol.product_uom_qty,
					'price_unit': 0,
					'product_name': sol.product_id.display_name,
					'order_line_id': 0,
					'warehouse_id': sol.picking_type_id.warehouse_id.id,
				})
		
		# so_id тай борлуулалтыг харах =====================================
		elif data['so_id'] and int(float(data['so_id'])) > 1:
			sale_order = sale_obj.sudo().browse(int(float(data['so_id'])))
			_logger.info("------ mobile -----get_payment_so_product_list SO DATA %s", str(sale_order.name))
			# Бар код шалгах
			# Тохиргооноос авч шалгах
			res_config = self.env['res.config.settings']
			see_barcode_on_mobile = res_config.sudo().create({}).see_barcode_on_mobile
			# ========================================================================
			for sol in sale_order.order_line:
				temp = self._get_sol_data(sol)
				if see_barcode_on_mobile and sol.product_id.barcode:
					temp['product_name'] = sol.product_id.display_name +' ('+str(sol.product_id.barcode)+')'
				lines.append(temp)
				
		_logger.info("------ mobile -----get_payment_so_product_list DATA %s", str(lines))
		return lines

	@api.model
	def get_payment_list(self,data):
#		 data={'date':'2018-09-10','partner_id':self.partner_id.id}
#		 data={'date':'2018-10-10','partner_id':False}
		_logger.info("------ mobile -----get_payment_list %s  %s", str(data), type(data))
		sale_orders = []
		sale_obj = self.env['sale.order']
		m_date = data['date'][:7]+'%'
		current_date = data['date']
		names = []
#		sdate = data['date'].split('-')[0]+'-'+data['date'].split('-')[1]+'-01'
#		edate = data['date'].split('-')[0]+'-'+data['date'].split('-')[1]+'-'+str(monthrange(int(data['date'].split('-')[0]), int(data['date'].split('-')[1]))[1])
		#udruur bolgoh
		sdate=current_date
		edate=current_date
		_logger.info("------ mobile ----- **** sdate: %s  edate: %s", sdate, edate)
		# _logger.info("------ mobile ----- **** part: %d %s", data, m_date)
		pay_obj=self.env['sale.payment.info']
		acc_pay_obj=self.env['account.payment']
		so_names = acc_pay_obj.search([
										('payment_date','=',current_date),
										('create_uid','=',self.env.user.id)
										])
		for r in so_names:
			names.append(r['communication'])			 
		#		 print 'self.env.user.id ',self.env.user.id
		so_ids = sale_obj.search([
									('name','in',names),
									('partner_id.route_id','in',self.env.user.route_ids.ids)
		#								   ('validity_date','=',current_date),
#								  ('user_id','=',self.env.user.id)
								  ])
		pay_obj=self.env['sale.payment.info']
		so_amount=0
		for so in so_ids:
			invoice_ids = so.order_line.mapped('invoice_lines').mapped('invoice_id').filtered(lambda r: r.type in ['out_invoice', 'out_refund'])
		#			 print 'invoice_ids ',invoice_ids
		# payments = pay_obj._compute_partner_user_so_payment(False,sdate,edate,so_ids)	
		payments = pay_obj._compute_partner_user_so_payment2(False,sdate,edate,so_ids)	

		return payments

	# Борлуулалтын мөрийн дата бэлдэх
	def _get_sol_data(self, sol):
		temp = {
			'product_id':sol.product_id.id,
			'qty': sol.product_uom_qty,
			'return_qty': sol.return_qty,
			'daralt_qty': 0,
			'qty_delivered': sol.qty_delivered,
			'qty_return': sol.return_qty_non_store or 0,
			'main_price_unit': sol.main_price_unit if sol.main_price_unit > 0 else sol.price_unit,
			'price_unit': sol.price_unit,
			'product_name':sol.product_id.display_name,
			'order_line_id': 5 if sol.is_reward_product else 0,
			'warehouse_id': sol.order_id.warehouse_id.id,
		}
		return temp

	def get_payment_so_product_list_test(self):
		res = self.get_payment_so_product_list({'so_id': 131, 'internal_move':'false'})
		self.desc = str(res)

	def create_back_so_back_order2(self):
		# 
		ins_value = {
			'so_id': 834,
			'order_line': [
				{'product_id': 768,
				'product_uom_qty': 288,
				},
				{
				'product_id': 718,
				'product_uom_qty': 792,
				}
				]
			}
			# {u'so_id': u'833.0', u'order_line': [{u'product_uom_qty': u'288.0', u'product_id': u'768'}, {u'product_uom_qty': u'792.0', u'product_id': u'718'}]}
		# datastore = self.insert_value
		# json_string = json.dumps(datastore)
		# datastore = json.loads(json_string)
		# print datastore,type(datastore)
		# # print type(self.insert_value)
		# # ins_value = json.loads(self.insert_value)
		# # print type(ins_value)
		# # ins_value = dict(self.insert_value)
		# print 'ins_value',datastore
		res = self.create_back_so_back_order(ins_value)
		
		self.desc = str(res)

	@api.model
	def create_deliver_advanced(self, data):
		_logger.info("------ mobile -----create_deliver_advanced %s  %s", str(data), type(data))
		sale_orders = []
		sale_obj = self.env['sale.order']
		pick_obj = self.env['stock.picking']
		lines=[]
		sale_order_id = sale_obj.browse(int(float(data['so_id'])))
		# engiin hurgelt so-iin hurgeltiig tsuvuulj uguh
		if data['delivery_type'] =='delivery':
			not_done_pick = sale_order_id.picking_ids.filtered(lambda r: r.state not in ['done','cancel'])
			not_found_product = []
			_logger.info("------ mobile -----hudulguun batlagdaagui %s  ", not_done_pick)
			if not_done_pick:
				for line in data['order_line']:
					product = self.env['product.product'].browse(int(float(line['product_id'])))
					not_product = False
					for pick in not_done_pick:
						if pick.state in ['confirmed','draft']:
							pick.action_assign()
						for item in pick.move_lines.filtered(lambda r: r.product_id.id==product.id and  r.product_uom_qty>=float(line['product_uom_qty'])):
							if not item.quantity_done:
								_logger.info("------  %s  ", product.name)
								item.quantity_done = float(line['product_uom_qty'])
								not_product = True

					if not not_product:
						not_found_product.append(product.id)
			else:
				return False

			pick_backorder = self.env['stock.backorder.confirmation']
			done_transfer = self.env['stock.immediate.transfer']
			# tur haav
			# if not not_found_product:
			for item in not_done_pick:
				if item._check_backorder():
					pick_id = [(4, item.id)]
					backorder_id = pick_backorder.create({
						'pick_ids': pick_id
						})
					backorder_id.process()
				else:
					pick_id = [(4, item.id)]
					done_transfer_id = done_transfer.create({
						'pick_ids': pick_id
						})
					done_transfer_id.process()

			for item in not_done_pick:
				if item.state in ['assigned']:
					item.do_unreserve()

			not_done_pick = sale_order_id.picking_ids.filtered(lambda r: r.state not in ['done','cancel'])
			if not_done_pick:
				return False
			# else:
			#	 return False
			return True
		return False

	@api.model
	def create_payment(self,data):
#		 data={'date':'2018-09-10','partner_id':self.partner_id.id,'so_id':self.so_id.id,'amount':self.pay_amount, 'journal_id':9}
		_logger.info("------ mobile -----payment create datas 11111 %s  %s", str(data), type(data))
		sale_obj = self.env['sale.order']
		journal_obj = self.env['account.journal']
		invoice_obj = self.env['account.move']
		cash_journal_id = False
		if data.get('journal_id',False):
			cash_journal_id = journal_obj.browse(int(float(data['journal_id'])))
		elif self.env.user.cash_journal_id:
			cash_journal_id = self.env.user.cash_journal_id
		else:
			_logger.info(u"------ mobile -----absl ERROR journal not found ")
			return {'payment_id': False, 'error': 'journal not found'}		
			
		
		sale_order = sale_obj.browse(int(float(data['so_id'])))
		invoices = set()
		partner_id=False
		discount = 0
		with_discount=False
		with_discount=False
		for so in sale_order:
			print ('so ',so)
#			partner_id=so.partner_id.id
			partner_id=so.partner_invoice_id.id
			for sol in so.order_line:
				for ail in sol.invoice_lines.filtered(lambda r: r.move_id.state!='draft'):
					invoices.add(ail.move_id.id)
		invoice_br= invoice_obj.browse(list(invoices))
		print ('invoice_br ',invoice_br)
		amsl_vals=[]
		payment_methods = (float(data['pay_amount'])>0) and cash_journal_id.inbound_payment_method_ids or cash_journal_id.outbound_payment_method_ids
#		 payment_methods = self.payment_type == 'inbound' and self.journal_id.inbound_payment_method_ids or self.journal_id.outbound_payment_method_ids
		p_vals={
				'payment_method_id': payment_methods and payment_methods[0].id or False,
				'partner_id': partner_id,
#				 'partner_type': MAP_INVOICE_TYPE_PARTNER_TYPE[invoices[0].type],
				'journal_id': cash_journal_id.id,
				'payment_date': data['date'],	
				'state': 'draft',
#				 'branch_id': self.branch_id.id,
#				 'communication': self.env.user.name+u' орлого' or '',
			   'name': self.env.user.name+u' орлого',
			   'amount': float(data['pay_amount']),
# 			   'discount': discount,
#			   'discount':flaot(data['discount']),
# 			'with_discount':with_discount

			}		
		for inv in invoice_br:
# 			account_id= inv.account_id.id
				#/////////////////////////////////////////////////////
#			 if invoice_defaults and len(invoice_defaults) == 1:
# invoices[0].invoice_payment_ref or invoices[0].ref or invoices[0].name,
			p_vals['communication'] = inv.invoice_payment_ref or inv.ref or inv.name
			p_vals['currency_id'] = inv.currency_id.id
# 			p_vals['payment_type'] = inv.type in ('out_invoice', 'in_refund') and 'inbound' or 'outbound'
			p_vals['payment_type'] = 'inbound' if float(data['pay_amount']) > 0 else 'outbound'
			p_vals['partner_type'] = MAP_INVOICE_TYPE_PARTNER_TYPE[inv.type]
			
			
# 			'currency_id': invoices[0].currency_id.id,
# 			'amount': abs(amount),
# 			'payment_type': 'inbound' if amount > 0 else 'outbound',
# 			'partner_id': invoices[0].commercial_partner_id.id,
# 			'partner_type': MAP_INVOICE_TYPE_PARTNER_TYPE[invoices[0].type],
# 			'communication': invoices[0].invoice_payment_ref or invoices[0].ref or invoices[0].name,
# 			'invoice_ids': [(6, 0, invoices.ids)],
			
		if list(invoices):
			p_vals.update({
					'invoice_ids': [(6, 0, list(invoices))],
				})
				
				#/////////////////////////////////////////////////////					   
		try:
			payment = self.env['account.payment'].create(p_vals)
# 			payment.action_validate_invoice_payment()
			payment.post()
			_logger.info("return ------ mobile -----payment  %s  ", str(payment))
			
			return {'payment_id':payment.id}

		except Exception as e:
			_logger.info(u"------ mobile -----payment ERROR %s ",str(e))
			return {'payment_id': False, 'error': str(e)}
		
	@api.model
	def create_payment_bank_statement(self,data):
		#хэрэв касс харилцахын гүйлгээ хэлээд үүсгээд батлахад payment үүсгэх бол ашиглана
#		 data={'date':'2018-09-10','partner_id':self.partner_id.id,'so_id':self.so_id.id,'amount':self.pay_amount}
		
		_logger.info("------ mobile -----payment create datas %s  %s", str(data), type(data))
		statement_obj = self.env['account.bank.statement']
		bank_line_obj = self.env['account.bank.statement.line']
		sale_obj = self.env['sale.order']
		invoice_obj = self.env['account.move']
		cash_journal_id = False
		if self.env.user.cash_journal_id:
			cash_journal_id = self.env.user.cash_journal_id.id
		
		statement_id= statement_obj.sudo().search([('date','=',data['date']),('journal_id','=',self.env.user.cash_journal_id.id)])
		if not statement_id:
			statement_id = statement_obj.sudo().create({'journal_id': self.env.user.cash_journal_id.id,
								 'date':data['date']})
		sale_order = sale_obj.browse(int(float(data['so_id'])))
		invoices = set()
		partner_id=False
		for so in sale_order:
			partner_id=so.partner_id.id
			for sol in so.order_line:
				for ail in sol.invoice_lines:
					invoices.add(ail.invoice_id.id)
		invoice_br= invoice_obj.browse(list(invoices))
		amsl_vals=[]
		for inv in invoice_br:
			account_id= inv.account_id.id
			if inv.move_id:
			   for aml in inv.move_id.line_ids: 
				   if aml.account_id.id==account_id:
					   amsl_vals += [(0,0,{
									'inv_amount':data['pay_amount'],
									'import_inv_id':inv.id
										})]				   
		try:
			bl=bank_line_obj.sudo().create({
										   'name': self.env.user.name+u' орлого',
										   'amount': data['pay_amount'],
										   #				 'date':time.strftime("%Y-%m-%d"),
										   'date':data['date'],
										   'statement_id':statement_id.id,
										   'account_id':account_id,
										   'state':'draft',
										   'partner_id':partner_id,
										   'ref':self.env.user.name+u' орлого',
										   'import_line_ids':amsl_vals
										   })
			bl.button_validate_line()
			return {'payment_id':bl.id}
		except Exception as e:
			_logger.info(u"------ mobile -----absl ERROR %s ",str(e))
			return {'payment_id': False, 'error': str(e)}		

	@api.model
	def get_payment_methods(self):
		journals = []
		journals_ids= []
		cash_journal_id=False
		cash_journal_name=False
		_logger.info("-----------------mobile ====== get_payment_methods ")
		if self.env.user.cash_journal_id:
			cash_journal_id = self.env.user.cash_journal_id.id
			cash_journal_name = self.env.user.cash_journal_id.name
		for journal in self.env.user.cash_journal_ids:
			journals_ids.append({'journal_id': journal.id,
								'journal_name': journal.name,
								})
		journals_ids.append({
				'cash_journal_id': cash_journal_id,
				'cash_journal_name': cash_journal_name,
			})
		_logger.info("------ mobile -----len(journals_ids)  %s",journals_ids)
		return journals_ids

	# ===========PLAN=======================
	def test_plan_data(self):
		res = self.get_payment_methods()
		self.desc = str(res)
	
	# ХТ-ийн төлөвлөгөө гүйцэтгэл QTY, AMOUNT татах
	# TYPE 1
	@api.model
	def get_salesman_plan_amount_qty(self,dddd):
		_logger.info("------ mobile -----get_salesman_plan_amount_qty %s ", str(dddd))
		dd = dddd['date']
		# Огноо сар бэлдэх
		date_temp = dd[:8]+'%'
		year = int(dd[:4])
		month = int(dd[5:7])
		user_id = self.env.user.id
		datas = {}
		# Plan авах
		query_plan = """
			SELECT  
				pivot.product_id as id,
				sum(pivot.amount_fixed) as amount,
				sum(pivot.package_fixed) as qty
			FROM sale_plan_pivot_report as pivot
			WHERE
			      pivot.state in ('confirmed','done') and
				  pivot.year = %d and
				  pivot.month in (%d) and
				  pivot.salesman_id = %d 
			GROUP BY pivot.product_id
		""" % (year, month, user_id)
		# print '===============PLAN======-------------', query_plan
		self.env.cr.execute(query_plan)
		query_result = self.env.cr.dictfetchall()
		for line in query_result:
			temp = {
				'plan_amount': line['amount'],
				'plan_qty': line['qty'],
				'sale_amount': 0,
				'sale_qty': 0,
				'percent_amount': 0,
				'percent_qty': 0,
			}
			datas[ line['id'] ] = temp
		# Борлуулалт авах
		query_sales = """
			SELECT  
				pivot.product_id as id,
				sum(pivot.amount) as amount,
				sum(pivot.package) as qty
			FROM sale_pivot_report as pivot
			WHERE 
				  pivot.validity_date::text ilike '%s' and 
				  pivot.user_id = %d 
			GROUP BY pivot.product_id
		""" % (date_temp, user_id)
		# print '===============Sale======-------------', query_sales
		self.env.cr.execute(query_sales)
		query_result = self.env.cr.dictfetchall()
		for line in query_result:
			if line['id'] in datas:
				datas[line['id']]['sale_amount'] = line['amount']
				datas[line['id']]['sale_qty'] = line['qty']
				# Percent
				per = 0
				if datas[line['id']]['plan_amount'] != 0:
					per = (line['amount']*100) / datas[line['id']]['plan_amount']
				datas[line['id']]['percent_amount'] = round(per,2)
				# qty
				per = 0
				if datas[line['id']]['plan_qty'] != 0:
					per = (line['qty']*100) / datas[line['id']]['plan_qty']
				datas[line['id']]['percent_qty'] = round(per,2)
			else:
				temp = {
					'plan_amount': 0,
					'plan_qty': 0,
					'sale_amount': line['amount'],
					'sale_qty': line['qty'],
					'percent_amount': 100,
					'percent_qty': 100,
				}
				datas[ line['id'] ] = temp

		# Format өөрчлөх
		data_list = []
		for key in datas:
			temp = datas[key]
			temp['product_id'] = key
			data_list.append(temp)

		_logger.info("------ mobile -----get_salesman_plan_amount_qty RESULT: %s ", str(data_list))
		return data_list

	# ХТ-ийн төлөвлөгөө гүйцэтгэл Нийт AMOUNT татах
	# TYPE 2,3
	@api.model
	def get_salesman_plan_total_amount(self,dddd):
		_logger.info("------ mobile -----get_salesman_plan_total_amount %s ", str(dddd))
		# Огноо сар бэлдэх
		datas = False
		dd = dddd['date']
		date_temp = dd[:8]+'%'
		year = int(dd[:4])
		month = int(dd[5:7])
		date_start = dd[:8]+'01'
		date_end = dd[:8]+str(monthrange(year,month)[1])
		user_id = self.env.user.id
		# Plan авах
		query_plan = """
			SELECT  
				sum(pivot.amount_fixed) as amount,
				sum(pivot.package_fixed) as qty
			FROM sale_plan_pivot_report as pivot
			WHERE
			      pivot.state in ('confirmed','done') and
				  pivot.year = %d and
				  pivot.month in (%d) and
				  pivot.salesman_id = %d 
		""" % (year, month, user_id)
		self.env.cr.execute(query_plan)
		query_result = self.env.cr.dictfetchall()
		plan_amount = 0
		plan_qty = 0
		for line in query_result:
			plan_amount = line['amount'] or 0
			plan_qty = line['qty'] or 0
		# Борлуулалт авах
		query_sales = """
			SELECT  
				sum(pivot.amount) as amount,
				sum(pivot.package) as qty
			FROM sale_pivot_report as pivot
			WHERE 
				  pivot.picking_date::text ilike '%s' and 
				  pivot.user_id = %d 
		""" % (date_temp, user_id)
		self.env.cr.execute(query_sales)
		query_result = self.env.cr.dictfetchall()
		sale_amount = 0
		sale_qty = 0
		for line in query_result:
			sale_amount = line['amount'] or 0
			sale_qty = line['qty'] or 0

		# Төлөлт авах
		payment_amount = 0
		payment_obj = self.env['sale.payment.info']
		res = payment_obj._compute_sale_payment_by_user(user_id, date_start, date_end)
		if res:
			payment_amount = res

		# TYPE 2
		if dddd['type'] == '2':
			data_2 = []
			# Захиалга
			per = 0
			if plan_amount != 0:
				per = (sale_amount*100) / plan_amount
			temp = {
				'type': 'order',
				'plan': plan_amount,
				'amount': sale_amount,
				'percent': round(per,2),
			}
			data_2.append(temp)
			# Төлөлт
			per = 0
			if plan_amount != 0:
				per = (payment_amount*100) / plan_amount
			temp = {
				'type': 'payment',
				'plan': plan_amount,
				'amount': payment_amount,
				'percent': round(per,2),
			}
			data_2.append(temp)
			# Төлөгдөөгүй
			per = 0
			if plan_amount != 0:
				per = ((sale_amount-payment_amount)*100) / plan_amount
			temp = {
				'type':'didnt_payment',
				'plan': plan_amount,
				'amount': (sale_amount-payment_amount),
				'percent': round(per,2),
			}
			data_2.append(temp)
			datas = data_2
			_logger.info("------ mobile -----get_salesman_plan_total_amount TYPE 2 RESULT: %s", str(data_2))
		elif dddd['type'] == '3':
			# TYPE 3
			amount_90 = (plan_amount*90)/100
			qty_90 = (plan_qty*90)/100
			amount_80 = (plan_amount*80)/100
			qty_80 = (plan_qty*80)/100
			data_3 = [
				{   'type': 100,
					'plan_amount': plan_amount,
					'plan_qty': plan_qty,
					'sale_amount': sale_amount,
					'sale_qty': sale_qty,
					'vld_amount': plan_amount-sale_amount,
					'vld_qty': plan_qty-sale_qty,},
				{   'type': 90,
					'plan_amount': amount_90,
					'plan_qty': qty_90,
					'sale_amount': sale_amount,
					'sale_qty': sale_qty,
					'vld_amount': amount_90-sale_amount,
					'vld_qty': qty_90-sale_qty,},
				{   'type': 80,
					'plan_amount': amount_80,
					'plan_qty': qty_80,
					'sale_amount': sale_amount,
					'sale_qty': sale_qty,
					'vld_amount': amount_80-sale_amount,
					'vld_qty': qty_80-sale_qty,}
			]
			datas = data_3
			_logger.info("------ mobile -----get_salesman_plan_total_amount TYPE 3 RESULT: %s", str(data_3))

		_logger.info("------ mobile -----get_salesman_plan_total_amount RESULT: %s", str(datas))
		return datas

	# Онцгой барааны төлөвлөгөө гүйцэтгэл
	def test_special_product_plan(self):
		res = self.get_payment_methods()
		_logger.info("------ mobile ---- %s ", str(res))
		self.desc = str(res)

	@api.model
	def get_special_product_plan(self, data):
		_logger.info("------ mobile -----get_special_product_plan %s  %s", str(data), type(data))
		partner = self.env['res.partner'].browse(data['partner_id'])
		if partner:
			user_id = self.env.user.id
			partner_categs = partner.mapped('category_id.id')
			now = datetime.datetime.now()
			date_str = now.strftime("%Y-%m")
			date_str += '%'
			special_plans = self.env['partner.special.product.plan'].search([
				('salesman_id','=',user_id),
				('state','=','confirmed'),
				('date_start','<=',now),
				('date_end','>=',now)])
			_logger.info("------ mobile |||||||||||||get_special_product_plan lens %d", len(special_plans))
			res = []
			for line in special_plans:
				if set(line.partner_category_ids.mapped('id')).issubset(partner_categs):
					for pline in line.line_ids:
						# Борлуулсан тоог авах
						if line.must_sale == 'yes':
							query_sales = """
								SELECT  
									sum(pivot.qty_ordered) as qty
								FROM sale_pivot_report as pivot
								WHERE 
									  pivot.order_date >= '%s' and 
									  pivot.product_id = %d and
									  pivot.user_id = %d
							""" % (line.create_date, pline.product_id.id, user_id)
						else:
							query_sales = """
								SELECT  
									sum(pivot.qty) as qty
								FROM sale_pivot_report as pivot
								WHERE 
									  pivot.validity_date::text ilike '%s' and 
									  pivot.product_id = %d and
									  pivot.user_id = %d and
									  pivot.partner_id = %d
							""" % (date_str, pline.product_id.id, user_id, partner.id)
						self.env.cr.execute(query_sales)
						query_result = self.env.cr.dictfetchall()
						sale_qty = query_result[0]['qty'] or 0
						temp = {
							'p_id': pline.product_id.id,
							'plan_qty': pline.qty,
							'sale_qty': sale_qty,
							'must_sale': line.must_sale,
						}
						res.append(temp)
			return res
		else:
			return False

