from odoo import api, fields, models
from datetime import date
from odoo.exceptions import UserError,ValidationError
from dateutil.relativedelta import relativedelta
import pandas as pd
import datetime

class StockScrap(models.Model):
	_inherit = 'stock.scrap'

	po_number = fields.Many2one('purchase.order', string='Po Number', compute='get_po_number')
	vehicle_number = fields.Char(string='Vehicle Number', related='parent_id.picking_id.car_plate_number')
	po_manager = fields.Many2one('res.users', string='PO Employee', related='po_number.user_id')
	income_date = fields.Datetime(string='Income Date', related='po_number.date_approve')
	supplier = fields.Many2one('res.partner', string='Supplier', related='po_number.partner_id')
	product_code = fields.Char(string='Product Code', related='product_id.default_code')
	product_name = fields.Many2one('product.product', string='Product Name', related='product_id')
	uom_id = fields.Many2one('uom.uom', string='UOM', related='product_uom_id')
	price = fields.Float(string='Price')
	unit_cost = fields.Float(string='Unit Cost' )
	po_qty = fields.Float(string='Purchased QTY')
	po_cost = fields.Float(string='Purchased COST')
	def_qty = fields.Float(string='Defective QTY', related='scrap_qty')
	def_cost = fields.Float(string='Defective COST')
	descriptions = fields.Char(string='Description', related='description')
	is_desided_yes = fields.Char(string='Desided? Yes')
	is_desided_no = fields.Char(string='Desided? No')
	report_branch = fields.Boolean(default=False)
	branch_id = fields.Many2one('res.branch', related='parent_id.branch_id')
	location_id = fields.Many2one(
        'stock.location', 'Гарах байрлал', domain="[('usage', '=', 'internal'), ('company_id', 'in', [company_id, False])]",
        required=True, states={'done': [('readonly', True)]}, related='parent_id.picking_id.location_dest_id', check_company=True)
	
  # Холбоотой тайлант мэдээлэл дуудах
	def get_po_number(self):
		for i in self:
			po = self.env['purchase.order'].search([('name','=',i.parent_id.picking_id.in_coming_picking_id.origin)])
			if po:
				i.po_number = po
			else:
				i.po_number = ''
			if i.parent_id.picking_id.picking_type_id.code == 'internal':
				picking_ids = i.parent_id.picking_id.move_ids_without_package
				for picking_id in picking_ids:
					if i.product_id == picking_id.product_id:
						i.unit_cost = picking_id.price_unit
						i.def_cost = i.unit_cost * i.def_qty
						i.po_cost = i.unit_cost * i.po_qty
				po_picking_ids = i.parent_id.picking_id.in_coming_picking_id.move_ids_without_package
				for po_picking_id in po_picking_ids:
					if i.product_id == po_picking_id.product_id:
						i.po_qty = po_picking_id.product_uom_qty
						i.price = po_picking_id.price_unit
			
class InheritStockScrapMulti(models.Model):
	_inherit = 'stock.scrap.multi'

	@api.model
	def notfication_resolution_period(self):
		unchecked_scrap_ids = self.env['stock.scrap.multi'].search([('state_type','in',['done'])])
		for scrap_id in unchecked_scrap_ids:
			today = date.today()
			due_date = scrap_id.date + relativedelta(days=scrap_id.resolution_period)

			partner_ids = self.env['res.partner']
			if scrap_id.picking_id.picking_type_id.sequence_code == 'INT':
				po_origin = scrap_id.picking_id.in_coming_picking_id.origin
				po_user = self.env['purchase.order'].search([('name','=', po_origin)]).user_id
				manager_ids = self.env['hr.department'].search([('is_po','=',True)]).manager_ids
				partner_ids += po_user.partner_id
				partner_ids += manager_ids.mapped('partner_id')

			if due_date > today:
				hassan_date = due_date - today
				if hassan_date.days <= 14 and hassan_date.days >= 0:
					base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
					action_id = self.env.ref('mw_stock.action_stock_scrap_multi').id
					html = """
						<center><b>Гологдол бараа хянах мэдэгдэл</b><br/><center/>
						<br/>
						<p><b><a target="_blank" href={0}/web#id={1}&action={2}&model=purchase.order&view_type=form>{3}</a></b> дугаартай гологдлыг хянана уу!<p/>
						<p>{4} хоног үлдлээ<p/>
						""".format(base_url, scrap_id.id, action_id, scrap_id.name, hassan_date.days)
					partner_ids += scrap_id.create_uid.partner_id
					self.env.user.send_emails(partners=partner_ids, subject='Гологдол бараа хянах мэдэгдэл', body=html, attachment_ids=False)
			else:
				hassan_date = today - due_date
				if hassan_date.days <= 14 and hassan_date.days > 0:
					base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
					action_id = self.env.ref('mw_stock.action_stock_scrap_multi').id
					html = """
						<center><b>Гологдол бараа хэтэрсэн мэдэгдэл</b><br/><center/>
						<br/>
						<p><b><a target="_blank" href={0}/web#id={1}&action={2}&model=purchase.order&view_type=form>{3}</a></b> дугаартай гологдлыг хянана уу!<p/>
						<p>{4} хоног хэтэрсэн байна<p/>
						""".format(base_url, scrap_id.id, action_id, scrap_id.name, hassan_date.days)
					partner_ids += scrap_id.create_uid.partner_id
					self.env.user.send_emails(partners=partner_ids, subject='Гологдол бараа хэтэрсэн мэдэгдэл', body=html, attachment_ids=False)

	# Гологдол бүртгэлээс удамшуулсан
	def action_next_stage(self):
		# Тоо хэмжээ хэтэрсэн үед анхааруулга өгөх
		for scrap in self.scrap_lines:
			for picking in self.picking_id.move_ids_without_package:
				if scrap.product_id == picking.product_id:
					if scrap.scrap_qty > picking.product_uom_qty:
						raise UserError('Барааны тоо хэмжээ хэтэрсэн байна.')
			next_flow_line_id = self.flow_line_id._get_next_flow_line()
			if next_flow_line_id:
				if self.visible_flow_line_ids and next_flow_line_id.id not in self.visible_flow_line_ids.ids:
					check_next_flow_line_id = next_flow_line_id
					while check_next_flow_line_id.id not in self.visible_flow_line_ids.ids:
						temp_stage = check_next_flow_line_id._get_next_flow_line()
						if temp_stage.id == check_next_flow_line_id.id or not temp_stage:
							break
						check_next_flow_line_id = temp_stage
					next_flow_line_id = check_next_flow_line_id
				if next_flow_line_id._get_check_ok_flow(self.branch_id, False):
					self.flow_line_id = next_flow_line_id
					if self.flow_line_id.state_type == 'done':
						self.action_done()
					self.env['dynamic.flow.history'].create_history(next_flow_line_id, 'scrap_id', self)
					if self.flow_line_next_id:
						self.env.user
						send_users = self.flow_line_next_id._get_flow_users(self.branch_id, False, self.env.user)
						# if send_users:
						# 	self.send_chat_employee(send_users.mapped('partner_id'))
				else:
					self.env.user
					con_user = next_flow_line_id._get_flow_users(self.branch_id, False, self.env.user)
					confirm_usernames = ''
					if con_user:
						confirm_usernames = ', '.join(con_user.mapped('display_name'))
					raise UserError(u'Та батлах хэрэглэгч биш байна\n Батлах хэрэглэгчид %s' % confirm_usernames)
				

class InheritHRDepartment(models.Model):
	_inherit = 'hr.department'

	is_po = fields.Boolean(string='Гологдлын мэдэгдэл хүргэх эсэх', default=False)