from odoo import api, fields, models
from odoo.exceptions import UserError
from datetime import date
import math
from datetime import datetime, time, timedelta

class MaintenanceWorkorder(models.Model):
	_inherit = 'maintenance.workorder'

	workorder_category = fields.Selection([('workorder','Механик засвар'),('electric','Цахилгаан')], string='Засварын ангилал')
	equipment_id = fields.Many2one('factory.equipment', string='Equipment')

	def action_to_close(self):
		# Хянасан эсэхийг шалгах
		self._check_night_expenses()
		# Техникийн засвар бол
		if self.maintenance_type not in ['other_repair','daily_works','component_repair','other_repair2','other_repair3','other_repair4']:
			# Гүйлтийг шалгах
			if self.start_odometer <= 0 or self.finish_odometer <= 0 or self.start_odometer > self.finish_odometer:
				raise UserError((u'Техникийн эхлэх, дуусах гүйлтийг шалгана уу!'))
			if not self.is_checked :
				raise UserError((u'Хянасан уу!'))
			# Сүүлд хийгдсэн PM, гүйлт шалгах
			if self.maintenance_type == 'pm_service' and self.maintenance_type_id.is_pm:
				self.technic_id.last_pm_odometer = self.finish_odometer
				self.technic_id.last_pm_id = self.maintenance_type_id.id
				self.technic_id.last_pm_priority = self.pm_priority
				self.technic_id.last_pm_date = self.date_required

		# Засварчдын ажлын цагийг шалгах
		if not self.employee_timesheet_lines and self.contractor_type == 'internal':
			raise UserError((u'Засварчны цагийг оруулна уу! WO'))
		else:
			for line in self.employee_timesheet_lines:
				if not line.date_start or not line.date_end:
					raise UserError((u'Засварчны эхэлсэн, дууссан цагийг оруулна уу!'))

		# Засварын цагийг шалгах
		if not self.work_timesheet_lines:
			raise UserError((u'Засварын цагийг оруулна уу!'))

		# Үнэлгээ шалгах
		if not self.workorder_rate or self.workorder_rate == '0':
			raise UserError((u'Та засварын ажлыг үнэлнэ үү!'))
		# if not self.workorder_rate_description_id:
		# 	raise UserError(_(u'Үнэлгээний тайлбарыг сонгоно уу!'))

		self.state = 'closed'
		self.date_closed = datetime.now()
		self.close_user_id = self.env.user.id

	def create_expense_for_parts(self):
		req_part_line = self.get_part_line()
		if req_part_line:
			# Гарах байрлалыг олох
			dest_loc = self.env['stock.location'].sudo().search(
							[('usage','=','customer')], limit=1)
			if not dest_loc:
				raise UserError((u'Зарлагадах байрлал олдсонгүй!'))

			pickings = {}
			for line in req_part_line:
				if not line.is_ordered:
					# Агуулах олох
					temp_warehouse = line.src_warehouse_id if line.src_warehouse_id else self.warehouse_id
					if not temp_warehouse:
						raise UserError((u'Сэлбэгийн зарлага хийх агуулахыг сонгоно уу!'))

					# Picking шалгах
					t_name = ''
					if temp_warehouse.id not in pickings:
						if self.technic_id:
							t_name = self.technic_id.name
						picking = self.env['stock.picking'].create(
							{'picking_type_id': temp_warehouse.out_type_id.id,
							 'state': 'draft',
							 'move_type': 'one',
							 'partner_id': self.branch_id.partner_id.id if self.branch_id.partner_id else False,
							 'eh_barimt_user_id': self.create_uid.id,
							 'shaardah_partner_id': self.create_uid.partner_id.id if self.create_uid.partner_id else False,
# 							 'min_date': datetime.now(),
							 'location_id': temp_warehouse.lot_stock_id.id,
							 'location_dest_id': dest_loc.id,
							 'origin': self.name +', '+t_name+': '+self.description,
							 'maintenance_workorder_id': self.id,
							})
						pickings[ temp_warehouse.id ] = picking
					product = line.product_id
					# TTJV-ийн warrenty-г болиулсан
					# if line.is_warrenty:
					# 	warrenty_product = self.env['product.product'].search([
					# 		('default_code','=',line.product_id.default_code+'WAR')], limit=1)
					# 	if warrenty_product:
					# 		product = warrenty_product
					# 	else:
					# 		raise UserError(_(u'Warrenty бараа олдсонгүй!'))
					# MOVE үүсгэх
					sp_id = pickings[temp_warehouse.id]
					vals = {
						'name': self.technic_id.name or '-',
						'origin': self.name,
						'picking_id': sp_id.id,
						'product_id': product.id,
						'product_uom': product.uom_id.id,
						'product_uom_qty': line.qty,
						'location_id': temp_warehouse.lot_stock_id.id,
						'location_dest_id': dest_loc.id,
						'state': 'draft',
					}
					line_id = self.env['stock.move'].create(vals)
					line.is_ordered = True
					line.move_id = line_id.id

			# Picking batlax
			con = dict(self._context)
			con['from_code'] = True
			# print(aaa)
			for key in pickings:
				sp_id = pickings[key]
				print('con)_0-0-00-0---0-0-0-00-0-0-00--00-0-0-0-0-',con)
				sp_id.with_context(con).action_confirm()
			self.state = 'waiting_part'
			self.parts_user_id = self.env.user.id
			self.date_parts = datetime.now()
			self.warehouse_id = False
		else:
			raise UserError((u'Сэлбэг, материалын мэдээллийг оруулна уу!'))

class MaintenanceCall(models.Model):
	_inherit = 'maintenance.call'

	work_call_id = fields.Many2one('work.call', 'Ажлын хүсэлтийн төрөл/шинэ/')
class MaintenanceEmployeeTimesheetLineInherit(models.Model):
	_inherit = 'maintenance.employee.timesheet.line'

	emp_partner_id = fields.Many2one('res.partner', string=u'Засварчин', domain="[('employee','=',True)]")