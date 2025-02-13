from odoo import SUPERUSER_ID, api, fields, models, _
from odoo.exceptions import UserError
from collections import defaultdict
from dateutil import relativedelta
from odoo.tools import float_compare, split_every

class StockWarehouseOrderpoint(models.Model):
	_inherit = 'stock.warehouse.orderpoint'

	send_chat_check = fields.Boolean(default=False)
	purchase_request_ids = fields.Many2many('purchase.request',string='ХА Хүсэлт')

	def send_notif(self):
		html_notif = ''
		setting_ids = self.env['pr.mail.settings'].search([('state','=','approved'),('category_ids','!=',[])])
		for setting in setting_ids:
			orders = self.env['stock.warehouse.orderpoint'].search([('product_id.categ_id','child_of',setting.category_ids.ids)])
			# channel_id = self.env['mail.channel'].search([('name','=','Нөхөн дүүргэлт')])
			for i in orders:
				i.send_chat_check = False
				if i.qty_on_hand <= i.product_min_qty:
					if i.send_chat_check == False:
						i.send_chat_check = True
						base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
						action_id = self.env.ref('stock.action_orderpoint_replenish').id
						html_notif += u"""<b><a target="_blank" href=%s/web#action=%s&id=%s&view_type=form&model=stock.warehouse.orderpoint>%s</a></b> дугаартай нөхөн дүүргэлтийг хянана уу!<br/>  %s - барааны тоо хэмжээ заасан хамгийн бага хэмжээнээс бага байгаа тул /%s/ тоо хэмжээгээр нөхөн дүүргэнэ үү!<br/><br/>"""%(base_url,  action_id,i.id, i.name, i.product_id.display_name, i.qty_to_order) 
			if html_notif: 
				users_ids = setting.user_ids
				for user in users_ids:
					# channel_id.channel_member_ids.unlink()
					# self.env['mail.channel.member'].create({
					#   'partner_id': u.partner_id.id,
					#   'channel_id': channel_id.id,
					# }) 
					# notification_ids = [((0, 0, {
					# 'res_partner_id': u.partner_id.id,
					# 'notification_type': 'inbox'}))]
					# channel_id.message_post(
					# 	author_id=self.env.user.id,
					#   body=html_notif,
					#   message_type='comment',
					#   subtype_xmlid='mail.mt_comment',
					# 	partner_ids = [u.partner_id.user_ids.id],
					# 	notification_ids=notification_ids,
					# )
					# mail_pool = self.env['mail.mail']
					# values={}
					# values.update({'subject': 'Нөхөн дүүргэлт мэдээлэл'})
					# values.update({'email_to': u.partner_id.email})
					# values.update({'body_html': html_notif})
					# msg_id = mail_pool.create(values)
					# msg_id.send()
					# self.env.user.send_chat(html_notif, [user.partner_id], with_mail=True, subject_mail='Нөхөн дүүргэлт мэдээлэл')
					self.env.user.send_emails(partners=[user.partner_id], subject='Нөхөн дүүргэлт мэдээлэл', body=html_notif, attachment_ids=False)

	def open_wizard(self):
		return {
			'name': 'Нөхөн дүүргэлтээс Худалдан авалтын хүсэлт',
			'type': 'ir.actions.act_window',
			'view_mode': 'form',
			"view_type": "form",
			'res_model': 'create.purchase.request',
			'target': 'new',
		}

	def _get_orderpoint_action(self):
		"""Create manual orderpoints for missing product in each warehouses. It also removes
		orderpoints that have been replenish. In order to do it:
		- It uses the report.stock.quantity to find missing quantity per product/warehouse
		- It checks if orderpoint already exist to refill this location.
		- It checks if it exists other sources (e.g RFQ) tha refill the warehouse.
		- It creates the orderpoints for missing quantity that were not refill by an upper option.

		return replenish report ir.actions.act_window
		"""
		action = self.env["ir.actions.actions"]._for_xml_id("stock.action_orderpoint_replenish")
		action['context'] = self.env.context
		# Search also with archived ones to avoid to trigger product_location_check SQL constraints later
		# It means that when there will be a archived orderpoint on a location + product, the replenishment
		# report won't take in account this location + product and it won't create any manual orderpoint
		# In master: the active field should be remove
		orderpoints = self.env['stock.warehouse.orderpoint'].with_context(active_test=False).search([])
		# Remove previous automatically created orderpoint that has been refilled.
		orderpoints_removed = orderpoints._unlink_processed_orderpoints()
		orderpoints = orderpoints - orderpoints_removed
		to_refill = defaultdict(float)
		all_product_ids = self._get_orderpoint_products().ids
		all_replenish_location_ids = self.env['stock.location'].search([('replenish_location', '=', True)])
		ploc_per_day = defaultdict(set)
		# For each replenish location get products with negative virtual_available aka forecast
		for products in map(self.env['product.product'].browse, split_every(5000, all_product_ids)):
			for loc in all_replenish_location_ids:
				quantities = products.with_context(location=loc.id).mapped('virtual_available')
				for product, quantity in zip(products, quantities):
					if float_compare(quantity, 0, precision_rounding=product.uom_id.rounding) >= 0:
						continue
					# group product by lead_days and location in order to read virtual_available
					# in batch
					rules = product._get_rules_from_location(loc)
					lead_days = rules.with_context(bypass_delay_description=True)._get_lead_days(product)[0]
					ploc_per_day[(lead_days, loc)].add(product.id)
			products.invalidate_recordset()

		# recompute virtual_available with lead days
		today = fields.datetime.now().replace(hour=23, minute=59, second=59)
		for (days, loc), product_ids in ploc_per_day.items():
			products = self.env['product.product'].browse(product_ids)
			qties = products.with_context(
				location=loc.id,
				to_date=today + relativedelta.relativedelta(days=days)
			).read(['virtual_available'])
			for (product, qty) in zip(products, qties):
				if float_compare(qty['virtual_available'], 0, precision_rounding=product.uom_id.rounding) < 0:
					to_refill[(qty['id'], loc.id)] = qty['virtual_available']
			products.invalidate_recordset()
		if not to_refill:
			return action

		# Remove incoming quantity from other origin than moves (e.g RFQ)
		product_ids, location_ids = zip(*to_refill)
		qty_by_product_loc, dummy = self.env['product.product'].browse(product_ids)._get_quantity_in_progress(location_ids=location_ids)
		rounding = self.env['decimal.precision'].precision_get('Product Unit of Measure')
		# Group orderpoint by product-location
		orderpoint_by_product_location = self.env['stock.warehouse.orderpoint']._read_group(
			[('id', 'in', orderpoints.ids)],
			['product_id', 'location_id', 'qty_to_order:sum'],
			['product_id', 'location_id'], lazy=False)
		orderpoint_by_product_location = {
			(record.get('product_id')[0], record.get('location_id')[0]): record.get('qty_to_order')
			for record in orderpoint_by_product_location
		}
		for (product, location), product_qty in to_refill.items():
			qty_in_progress = qty_by_product_loc.get((product, location)) or 0.0
			qty_in_progress += orderpoint_by_product_location.get((product, location), 0.0)
			# Add qty to order for other orderpoint under this location.
			if not qty_in_progress:
				continue
			to_refill[(product, location)] = product_qty + qty_in_progress
		to_refill = {k: v for k, v in to_refill.items() if float_compare(
			v, 0.0, precision_digits=rounding) < 0.0}

		# With archived ones to avoid `product_location_check` SQL constraints
		orderpoint_by_product_location = self.env['stock.warehouse.orderpoint'].with_context(active_test=False)._read_group(
			[('id', 'in', orderpoints.ids)],
			['product_id', 'location_id', 'ids:array_agg(id)'],
			['product_id', 'location_id'], lazy=False)
		orderpoint_by_product_location = {
			(record.get('product_id')[0], record.get('location_id')[0]): record.get('ids')[0]
			for record in orderpoint_by_product_location
		}

		orderpoint_values_list = []
		for (product, location_id), product_qty in to_refill.items():
			orderpoint_id = orderpoint_by_product_location.get((product, location_id))
			if orderpoint_id:
				self.env['stock.warehouse.orderpoint'].browse(orderpoint_id).qty_forecast += product_qty

		orderpoints = self.env['stock.warehouse.orderpoint'].with_user(SUPERUSER_ID).create(orderpoint_values_list)
		for orderpoint in orderpoints:
			orderpoint._set_default_route_id()
			orderpoint.qty_multiple = orderpoint._get_qty_multiple_to_order()
		return action

class CreatePurchaseRequest(models.Model):
	_name = 'create.purchase.request'
	_description = 'Create purchase requests from PO'

	def _get_po_ids(self):
		po_ids = self.env['stock.warehouse.orderpoint'].browse(self.env.context.get('active_ids'))
		return po_ids
	
	po_ids = fields.Many2many('stock.warehouse.orderpoint', string='Нөхөн дүүргэлт дугааарууд', default=_get_po_ids)
	pr_ids = fields.Many2one('purchase.request', string='Худалдан авалтын хүсэлт')
	flow_id = fields.Many2one('dynamic.flow', string='Урсгал Тохиргоо', tracking=True, copy=True, required=True, domain="[('model_id.model', '=', 'purchase.request')]")
	date_required = fields.Date(string='Хэрэгцээт огноо', default=fields.date.today())
	warehouse_id = fields.Many2one('stock.warehouse', string='Агуулах')

	def create_purchase(self):
		parent = self.env['purchase.request'].create({
			'flow_id' : self.flow_id.id,
			'warehouse_id' : self.warehouse_id.id,
			'desc' : 'Нөхөн дүүргэлтээс',
		})
		self.pr_ids = parent
		for po_id in self.po_ids:
			qty = po_id.product_max_qty - po_id.qty_on_hand
			self.env['purchase.request.line'].create({
				'request_id' : parent.id,
				'product_id' : po_id.product_id.id,
				'date_required': self.date_required,
				'requested_qty': qty,
				'po_id': po_id.id,
			})
			po_id.purchase_request_ids += parent

	def action_create_purchase_requests(self):
		for po_id in self.po_ids:
			if po_id.warehouse_id == self.warehouse_id:
				pass
			else:
				raise UserError('Агуулхын мэдээлэл зөрж байна.')
		self.create_purchase()
		return {
			'type': 'ir.actions.client',
			'tag': 'display_notification',
			'params': {
				'title': _('Амжилттай!'),
				'message': 'Худалдан авалтын хүсэлт амжилттай үүслээ' + ' - ' + str(self.pr_ids.name),
				'sticky': True,
			}
		}

class InheritPurchaseOrderLine(models.Model):
	_inherit = 'purchase.request.line'

	po_id = fields.Many2one('stock.warehouse.orderpoint', string='Эх үүсвэр')