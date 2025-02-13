# -*- coding: utf-8 -*-
from io import BytesIO
import base64
from xlsxwriter.utility import xl_rowcol_to_cell
import xlsxwriter
from tempfile import NamedTemporaryFile
import os
import xlrd
import pytz
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare, float_is_zero
from odoo.addons.base.models.ir_model import MODULE_UNINSTALL_FLAG


class Inventory(models.Model):
	_name = "stock.inventory"
	_inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
	_description = "Inventory"
	_order = "date desc, id desc"

	state = fields.Selection(string='Status', selection=[
		('draft', 'Draft'),
		('cancel', 'Cancelled'),
		('confirm', 'In Progress'),
		('done', 'Validated')],
							 copy=False, index=True, readonly=True,
							 default='draft', tracking=True)
	filter_inv = fields.Selection(string='Тоолох сонголт', selection='_selection_filter', default='all_product')
	import_data_ids = fields.Many2many('ir.attachment', 'stock_inventory_attach_import_data_rel', 'inventory_id',
									   'attachment_id', 'Импортлох эксел', copy=False)
	price_diff_total = fields.Float(string=u'Нийт зөрүү',
									readonly=True, compute='_compute_diff_total_in_out', store=True)
	price_diff_total_in = fields.Float(string=u'Нийт дутуу',
									   readonly=True, compute='_compute_diff_total_in_out', store=True)
	price_diff_total_out = fields.Float(string=u'Нийт илүү',
										readonly=True, compute='_compute_diff_total_in_out', store=True)
	is_barcode_reader = fields.Boolean('Offline Баркод уншигчаар', default=False, copy=False)
	many_categ_ids = fields.Many2many('product.category', string=u'Ангилалууд')
	warning_messages = fields.Html('Warning Message', compute='_compute_wc_messages')
	outdated_mw = fields.Boolean(string="outdated_mw", readonly=True, compute='_compute_outdated_mw')

	name = fields.Char(
		'Inventory Reference', default="Inventory",
		readonly=True, required=True,
		states={'draft': [('readonly', False)]})
	date = fields.Datetime(
		'Inventory Date',
		readonly=True, required=True,
		default=fields.Datetime.now,
		help="If the inventory adjustment is not validated, date at which the theoritical quantities have been checked.\n"
			 "If the inventory adjustment is validated, date at which the inventory adjustment has been validated.")
	line_ids = fields.One2many(
		'stock.inventory.line', 'inventory_id', string='Inventories',
		copy=False, readonly=False,
		states={'done': [('readonly', True)]})
	move_ids = fields.One2many(
		'stock.move', 'inventory_id', string='Created Moves',
		states={'done': [('readonly', True)]})
	company_id = fields.Many2one(
		'res.company', 'Company',
		readonly=True, index=True, required=True,
		states={'draft': [('readonly', False)]},
		default=lambda self: self.env.company)
	branch_id = fields.Many2one('res.branch', 'Branch', index=True, readonly=True, store=True, default=lambda self: self.env.user.branch_id)
	location_ids = fields.Many2many(
		'stock.location', string='Locations',
		readonly=True, check_company=True,
		states={'draft': [('readonly', False)]},
		domain="[('company_id', '=', company_id), ('usage', 'in', ['internal', 'transit'])]")
	product_ids = fields.Many2many(
		'product.product', string='Products', check_company=True,
		domain="[('type', '=', 'product'), '|', ('company_id', '=', False), ('company_id', '=', company_id)]",
		readonly=True,
		states={'draft': [('readonly', False)]},
		help="Specify Products to focus your inventory on particular Products.")
	start_empty = fields.Boolean('Empty Inventory',
								 help="Allows to start with an empty inventory.")
	prefill_counted_quantity = fields.Selection(string='Counted Quantities',
												help="Allows to start with prefill counted quantity for each lines or "
													 "with all counted quantity set to zero.", default='counted',
												selection=[('counted', 'Default to stock on hand'),
														   ('zero', 'Default to zero')])
	export_group_type = fields.Selection([('by_category','Ангилал'), ('by_location','Байрлал')], string='Экспорт Бүлэглэх төрөл', default='by_location', help='Тооллого экспортлоход байрлалаар эсвэл ангилалаар бүлэглэх сонголт.')

	@api.onchange('company_id')
	def _onchange_company_id(self):
		# If the multilocation group is not active, default the location to the one of the main
		# warehouse.
		if not self.user_has_groups('stock.group_stock_multi_locations'):
			warehouse = self.env['stock.warehouse'].search([('company_id', '=', self.company_id.id)], limit=1)
			if warehouse:
				self.location_ids = warehouse.lot_stock_id

	def copy_data(self, default=None):
		name = _("%s (copy)") % self.name
		default = dict(default or {}, name=name)
		return super(Inventory, self).copy_data(default)

	def unlink(self):
		for inventory in self:
			if (inventory.state not in ('draft', 'cancel')
					and not self.env.context.get(MODULE_UNINSTALL_FLAG, False)):
				raise UserError(
					_('You can only delete a draft inventory adjustment. If the inventory adjustment is not done, you can cancel it.'))
		return super(Inventory, self).unlink()

	def action_validate(self):
		if not self.exists():
			return
		self.ensure_one()
		if not self.user_has_groups('stock.group_stock_manager'):
			raise UserError(_("Only a stock manager can validate an inventory adjustment."))
		if self.state != 'confirm':
			raise UserError(_(
				"You can't validate the inventory '%s', maybe this inventory " +
				"has been already validated or isn't ready.") % self.name)
		inventory_lines = self.line_ids.filtered(lambda l: l.product_id.tracking in ['lot',
																					 'serial'] and not l.prod_lot_id and l.theoretical_qty != l.product_qty)
		lines = self.line_ids.filtered(lambda l: float_compare(l.product_qty, 1,
															   precision_rounding=l.product_uom_id.rounding) > 0 and l.product_id.tracking == 'serial' and l.prod_lot_id)
		if inventory_lines and not lines:
			wiz_lines = [(0, 0, {'product_id': product.id, 'tracking': product.tracking}) for product in
						 inventory_lines.mapped('product_id')]
			wiz = self.env['stock.track.confirmation'].create({'inventory_id': self.id, 'tracking_line_ids': wiz_lines})
			return {
				'name': _('Tracked Products in Inventory Adjustment'),
				'type': 'ir.actions.act_window',
				'view_mode': 'form',
				'views': [(False, 'form')],
				'res_model': 'stock.track.confirmation',
				'target': 'new',
				'res_id': wiz.id,
			}
		self._action_done()
		self.line_ids._check_company()
		self._check_company()
		return True

	def _action_done(self):
		negative = next((line for line in self.mapped('line_ids') if
						 line.product_qty < 0 and line.product_qty != line.theoretical_qty), False)
		if negative:
			raise UserError(_('You cannot set a negative product quantity in an inventory line:\n\t%s - qty: %s') % (
				negative.product_id.name, negative.product_qty))
		self.action_check()
		self.write({'state': 'done', 'date': fields.Datetime.now()})
		self.post_inventory()
		return True

	def post_inventory(self):
		print ('self.move_ids ',self.move_ids)
		self.mapped('move_ids').filtered(lambda move: move.state != 'done')._action_done()
		return True

	def action_check(self):
		""" Checks the inventory and computes the stock move to do """
		for inventory in self.filtered(lambda x: x.state not in ('done', 'cancel')):
			# first remove the existing stock moves linked to this inventory
			inventory.with_context(prefetch_fields=False).mapped('move_ids').unlink()
			inventory.line_ids._generate_moves()

	def action_cancel_draft(self):
		self.mapped('move_ids')._action_cancel()
		self.line_ids.unlink()
		self.write({'state': 'draft'})

	def action_start(self):
		self.ensure_one()
		self._action_start()
		self._check_company()
		return self.action_open_inventory_lines()

	def _action_start(self):
		""" Confirms the Inventory Adjustment and generates its inventory lines
		if its state is draft and don't have already inventory lines (can happen
		with demo data or tests).
		"""
		for inventory in self:
			if inventory.state != 'draft':
				continue
			vals = {
				'state': 'confirm',
				'date': fields.Datetime.now()
			}
			if not inventory.line_ids and not inventory.start_empty:
				self.env['stock.inventory.line'].create(inventory._get_inventory_lines_values())
			inventory.write(vals)

	def action_open_inventory_lines(self):
		self.ensure_one()
		action = {
			'type': 'ir.actions.act_window',
			'views': [(self.env.ref('mw_stock.stock_inventory_line_tree2').id, 'tree')],
			'view_mode': 'tree',
			'name': _('Inventory Lines'),
			'res_model': 'stock.inventory.line',
		}
		context = {
			'default_is_editable': True,
			'default_inventory_id': self.id,
			'default_company_id': self.company_id.id,
		}
		# Define domains and context
		domain = [
			('inventory_id', '=', self.id),
			('location_id.usage', 'in', ['internal', 'transit'])
		]
		if self.location_ids:
			context['default_location_id'] = self.location_ids[0].id
			if len(self.location_ids) == 1:
				if not self.location_ids[0].child_ids:
					context['readonly_location_id'] = True

		if self.product_ids:
			if len(self.product_ids) == 1:
				context['default_product_id'] = self.product_ids[0].id

		action['context'] = context
		action['domain'] = domain
		return action

	def action_view_related_move_lines(self):
		self.ensure_one()
		domain = [('move_id', 'in', self.move_ids.ids)]
		action = {
			'name': _('Product Moves'),
			'type': 'ir.actions.act_window',
			'res_model': 'stock.move.line',
			'view_type': 'list',
			'view_mode': 'list,form',
			'domain': domain,
		}
		return action

	def _get_inventory_lines_values(self):

		if self.filter_inv == 'manual':
			return []
		if self.location_ids:
			locations = self.env['stock.location'].search([('id', 'child_of', self.location_ids.ids)])
		else:
			locations = self.env['stock.location'].search(
				[('company_id', '=', self.company_id.id), ('usage', 'in', ['internal', 'transit'])])
		domain = ' sq.location_id in %s AND sq.quantity != 0 AND pp.active'
		args = (tuple(locations.ids),)

		vals = []
		Product = self.env['product.product']
		# Empty recordset of products available in stock_quants
		quant_products = self.env['product.product']

		# If inventory by company
		if self.company_id:
			domain += ' AND sq.company_id = %s'
			args += (self.company_id.id,)
		if self.product_ids:
			domain += ' AND sq.product_id in %s'
			args += (tuple(self.product_ids.ids),)

		self.env['stock.quant'].flush_recordset(
			['company_id', 'product_id', 'quantity', 'location_id', 'lot_id', 'package_id', 'owner_id'])
		self.env['product.product'].flush_recordset(['active'])
		self.env.cr.execute("""SELECT sq.product_id, sum(sq.quantity) as product_qty, sq.location_id, sq.lot_id as prod_lot_id, sq.package_id, sq.owner_id as partner_id
				FROM stock_quant sq
				LEFT JOIN product_product pp
				ON pp.id = sq.product_id
				WHERE %s
				GROUP BY sq.product_id, sq.location_id, sq.lot_id, sq.package_id, sq.owner_id """ % domain, args)

		for product_data in self.env.cr.dictfetchall():
			product_data['company_id'] = self.company_id.id
			product_data['inventory_id'] = self.id
			# replace the None the dictionary by False, because falsy values are tested later on
			for void_field in [item[0] for item in product_data.items() if item[1] is None]:
				product_data[void_field] = False
			product_data['theoretical_qty'] = product_data['product_qty']
			if self.prefill_counted_quantity == 'zero':
				product_data['product_qty'] = 0
			if product_data['product_id']:
				product_data['product_uom_id'] = Product.browse(product_data['product_id']).uom_id.id
				quant_products |= Product.browse(product_data['product_id'])
			vals.append(product_data)
		return vals

	@api.depends('line_ids.outdated')
	def _compute_outdated_mw(self):
		for item in self:
			if item.line_ids.filtered(lambda r: r.outdated):
				item.outdated_mw = True
			else:
				item.outdated_mw = False

	def action_view_related_move_lines_mw(self):
		self.ensure_one()
		action = {
			'type': 'ir.actions.act_window',
			'views': [(self.env.ref('mw_stock.stock_inventory_line_tree2_mw_real').id, 'tree')],
			'view_mode': 'tree',
			'name': _('Inventory Lines'),
			'res_model': 'stock.inventory.line',
		}
		domain = [
			('inventory_id', '=', self.id),
			('location_id.usage', 'in', ['internal', 'transit'])
		]

		# action['context'] = context
		action['domain'] = domain
		return action

	@api.depends('line_ids')
	def _compute_wc_messages(self):
		for item in self:
			picking_names = False
			location_ids = item.line_ids.mapped('location_id').ids
			product_ids = item.line_ids.mapped('product_id').ids
			move_ids = self.env['stock.move'].search(
				[('picking_id', '!=', False), ('state', 'not in', ['done', 'cancel']),
				 ('product_id', 'in', product_ids)
					, '|', ('location_id', 'in', location_ids), ('location_dest_id', 'in', location_ids)])
			if move_ids:
				picking_names = ', '.join(move_ids.mapped('picking_id.name'))
			if picking_names:
				message = u'Батлагдаагүй хөдөлгөөнүүд: %s' % picking_names
			else:
				message = False
			item.warning_messages = message

	@api.model
	def _selection_filter(self):
		res_filter = [
			('all_product', 'Үлдэгдэлтэй бүх бараагаар тоолох'),
			('category_child_of', 'Дэд ангилалд тоолох'),
			('category_many', 'Олон ангилалаар тоолох'),
			('manual', 'Барааг гараар сонгох /Хоосон эхлэнэ/'),
		]
		return res_filter

	def action_reset_product_qty_mw(self):
		self.line_ids.action_reset_product_qty()

	@api.onchange('filter_inv', 'many_categ_ids')
	def onchange_filter_inv(self):
		product_ids = False
		if self.filter_inv == 'category_child_of' and self.many_categ_ids:
			product_ids = self.env['product.product'].search(
				[('type', 'in', ['product', 'consu']), ('categ_id', 'child_of', self.many_categ_ids.ids)]).ids
		elif self.filter_inv == 'category_many' and self.many_categ_ids:
			product_ids = self.env['product.product'].search(
				[('type', 'in', ['product', 'consu']), ('categ_id', 'in', self.many_categ_ids.ids)]).ids
		self.product_ids = product_ids

	@api.depends('line_ids.price_diff_subtotal')
	def _compute_diff_total_in_out(self):
		for item in self:
			item.price_diff_total = sum(item.line_ids.mapped('price_diff_subtotal'))
			item.price_diff_total_in = sum(
				item.line_ids.filtered(lambda r: r.price_diff_subtotal < 0).mapped('price_diff_subtotal'))
			item.price_diff_total_out = sum(
				item.line_ids.filtered(lambda r: r.price_diff_subtotal > 0).mapped('price_diff_subtotal'))

	def get_inv_header(self, row, wo_sheet, cell_style):
		wo_sheet.write(row, 0, "Баркод", cell_style)
		wo_sheet.write(row, 1, "Дотоод Код", cell_style)
		wo_sheet.write(row, 2, "Бараа", cell_style)
		wo_sheet.write(row, 3, "Хэжих нэгж", cell_style)
		wo_sheet.write(row, 4, "Байх ёстой", cell_style)
		wo_sheet.write(row, 5, "Тоолсон тоо", cell_style)
		wo_sheet.write(row, 6, "Зөрүү", cell_style)
		wo_sheet.write(row, 7, "Зөрүү Дүнгээр", cell_style)
		wo_sheet.write(row, 8, u"Байрлал", cell_style)
		wo_sheet.write(row, 9, u"Барааны Код", cell_style)
		wo_sheet.write(row, 10, u"Лот/Цуврал дугаар", cell_style)
		return wo_sheet

	def get_inv_print_cel(self, row, wo_sheet, item, contest_left, cell_format2, contest_center):
		wo_sheet.write(row, 0, item.product_id.barcode, contest_left)
		wo_sheet.write(row, 1, item.product_id.default_code, contest_left)
		p_name = item.product_id.name
		if item.product_id.product_template_attribute_value_ids:
			p_name += u' (' + u', '.join(item.product_id.product_template_attribute_value_ids.mapped('name')) + u')'
		wo_sheet.write(row, 2, p_name, contest_left)
		wo_sheet.write(row, 3, item.product_id.uom_id.name, contest_center)
		wo_sheet.write(row, 4, item.theoretical_qty, cell_format2)
		wo_sheet.write(row, 5, item.product_qty, cell_format2)
		wo_sheet.write_formula(row, 6, '{=(' + xl_rowcol_to_cell(row, 5) + '-' + xl_rowcol_to_cell(row, 4) + ')}',
							   cell_format2)
		if self.user_has_groups('mw_stock.group_stock_inv_diff_view'):
			wo_sheet.write(row, 7, item.price_diff_subtotal, cell_format2)
		else:
			wo_sheet.write(row, 7, 0, cell_format2)
		wo_sheet.write(row, 8, item.location_id.name, cell_format2)
		wo_sheet.write(row, 9, item.product_id.product_code, cell_format2)
		wo_sheet.write(row, 10, item.prod_lot_id.name if item.prod_lot_id else '', cell_format2)
		return wo_sheet

	def get_last_col(self):
		return 10

	def action_print_inventory(self):
		output = BytesIO()
		workbook = xlsxwriter.Workbook(output)
		worksheet = workbook.add_worksheet('Total')
		worksheet_diff = workbook.add_worksheet('Diffrence')
		# worksheet_not_diff = workbook.add_worksheet(u'Зөрүүгүй')

		h1 = workbook.add_format({'bold': 1})
		h1.set_font_size(9)
		h1.set_align('center')
		h1.set_font_name('Arial')

		header = workbook.add_format({'bold': 1})
		header.set_font_size(9)
		header.set_align('center')
		header.set_align('vcenter')
		header.set_border(style=1)
		header.set_bg_color('#D3D3D3')
		header.set_text_wrap()
		header.set_font_name('Arial')

		header_wrap = workbook.add_format()
		header_wrap.set_text_wrap()
		header_wrap.set_font_size(9)
		header_wrap.set_align('center')
		header_wrap.set_align('vcenter')
		header_wrap.set_border(style=1)
		header_wrap.set_font_name('Arial')
		header_wrap.set_color('red')
		header_wrap.set_bold(True)

		contest_right_no_bor = workbook.add_format()
		contest_right_no_bor.set_text_wrap()
		contest_right_no_bor.set_font_size(9)
		contest_right_no_bor.set_align('right')
		contest_right_no_bor.set_align('vcenter')
		contest_right_no_bor.set_font_name('Arial')

		contest_left_no_bor = workbook.add_format()
		contest_left_no_bor.set_text_wrap()
		contest_left_no_bor.set_font_size(9)
		contest_left_no_bor.set_align('left')
		contest_left_no_bor.set_align('vcenter')
		contest_left_no_bor.set_font_name('Arial')

		contest_left = workbook.add_format()
		contest_left.set_text_wrap()
		contest_left.set_font_size(9)
		contest_left.set_align('left')
		contest_left.set_align('vcenter')
		contest_left.set_border(style=1)
		contest_left.set_font_name('Arial')

		contest_left_bold = workbook.add_format()
		contest_left_bold.set_bold(True)
		contest_left_bold.set_text_wrap()
		contest_left_bold.set_font_size(9)
		contest_left_bold.set_align('left')
		contest_left_bold.set_align('vcenter')
		contest_left_bold.set_border(style=1)
		contest_left_bold.set_font_name('Arial')
		contest_left_bold.set_bg_color('#B9CFF7')

		contest_right = workbook.add_format()
		contest_right.set_text_wrap()
		contest_right.set_font_size(9)
		contest_right.set_align('right')
		contest_right.set_align('vcenter')
		contest_right.set_border(style=1)
		contest_right.set_font_name('Arial')

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
			'font_size': 9,
			'font_name': 'Arial',
			# 'text_wrap':1,
			'num_format': '#,##0.00'
		})

		cell_format_no_border = workbook.add_format({
			'border': 0,
			'align': 'right',
			'font_size': 9,
			'font_name': 'Arial',
			# 'text_wrap':1,
			'num_format': '#,##0.00'
		})

		tz = self.env['res.users'].sudo().browse(self.env.user.id).tz or 'Asia/Ulaanbaatar'
		timezone = pytz.timezone(tz)
		f_date = ''
		if self.date:
			f_date = self.date
			f_date = str(f_date.replace(tzinfo=pytz.timezone('UTC')).astimezone(timezone))[0:20]

		row = 0
		last_col = self.get_last_col()
		worksheet.merge_range(row, 0, row, last_col, _('Material inventory sheet'), contest_center)
		row += 1
		worksheet.write(row, 0, _("Warehouse:"), contest_right)
		worksheet.merge_range(row, 1, row, 2, ', '.join(self.location_ids.mapped('name')), contest_left)
		worksheet.write(row, 5, _("Date:"), contest_right)
		worksheet.merge_range(row, 6, row, last_col, f_date, contest_left)
		row += 1
		worksheet = self.get_inv_header(row, worksheet, header)

		row += 1

		row_diff = 0
		worksheet_diff.merge_range(row_diff, 0, row_diff, last_col, _('Material inventory sheet'), contest_center)
		row_diff += 1
		worksheet_diff.write(row_diff, 0, _("Warehouse:"), contest_right)
		worksheet_diff.merge_range(row_diff, 1, row_diff, 2, ', '.join(self.location_ids.mapped('name')), contest_left)
		worksheet_diff.write(row_diff, 5, _("Date:"), contest_right)
		worksheet_diff.merge_range(row_diff, 6, row_diff, last_col, f_date, contest_left)
		row_diff += 1
		worksheet_diff = self.get_inv_header(row_diff, worksheet_diff, header)
		row_diff += 1


		save_row = row
		save_row_diff = row_diff
		if self.export_group_type == 'by_location':
			location_ids = self.location_ids
			for item_loc in location_ids:
				lines = self.line_ids.filtered(lambda r: r.location_id.id == item_loc.id)
				if lines:
					worksheet.merge_range(row, 0, row, last_col, item_loc.name, contest_left_bold)
					row += 1
				if self.line_ids.filtered(lambda r: r.location_id.id == item_loc.id and r.difference_qty != 0):
					worksheet_diff.merge_range(row_diff, 0, row_diff, last_col, item_loc.name, contest_left_bold)
					row_diff += 1

				for item in lines:
					worksheet = self.get_inv_print_cel(row, worksheet, item, contest_left, cell_format2, contest_center)
					row += 1
					if item.difference_qty != 0:
						worksheet_diff = self.get_inv_print_cel(row_diff, worksheet_diff, item, contest_left, cell_format2,
																contest_center)
						row_diff += 1
		else:
			categ_ids = self.line_ids.mapped('product_id.categ_id')
			for item_cat in categ_ids:
				lines = self.line_ids.filtered(lambda r: r.product_id.categ_id.id == item_cat.id)
				if lines:
					worksheet.merge_range(row, 0, row, last_col, item_cat.name, contest_left_bold)
					row += 1
				if self.line_ids.filtered(lambda r: r.product_id.categ_id.id == item_cat.id and r.difference_qty != 0):
					worksheet_diff.merge_range(row_diff, 0, row_diff, last_col, item_cat.name, contest_left_bold)
					row_diff += 1

				for item in lines:
					worksheet = self.get_inv_print_cel(row, worksheet, item, contest_left, cell_format2, contest_center)
					row += 1
					if item.difference_qty != 0:
						worksheet_diff = self.get_inv_print_cel(row_diff, worksheet_diff, item, contest_left, cell_format2,
																contest_center)
						row_diff += 1

		worksheet.merge_range(row, 0, row, 3, 'Нийт', contest_center)
		worksheet.write_formula(row, 4,
								'{=SUM(' + xl_rowcol_to_cell(save_row + 1, 4) + ':' + xl_rowcol_to_cell(row - 1,
																										4) + ')}',
								cell_format2)
		worksheet.write_formula(row, 5,
								'{=SUM(' + xl_rowcol_to_cell(save_row + 1, 5) + ':' + xl_rowcol_to_cell(row - 1,
																										5) + ')}',
								cell_format2)
		worksheet.write_formula(row, 6,
								'{=SUM(' + xl_rowcol_to_cell(save_row + 1, 6) + ':' + xl_rowcol_to_cell(row - 1,
																										6) + ')}',
								cell_format2)
		worksheet.write_formula(row, 7,
								'{=SUM(' + xl_rowcol_to_cell(save_row + 1, 7) + ':' + xl_rowcol_to_cell(row - 1,
																										7) + ')}',
								cell_format2)
		worksheet.merge_range(row, 8, row, last_col, '', contest_center)
		worksheet_diff.merge_range(row_diff, 0, row_diff, 2, 'Нийт', contest_center)
		worksheet_diff.write_formula(row_diff, 4,
									 '{=SUM(' + xl_rowcol_to_cell(save_row_diff + 1, 4) + ':' + xl_rowcol_to_cell(
										 row_diff - 1, 4) + ')}', cell_format2)
		worksheet_diff.write_formula(row_diff, 5,
									 '{=SUM(' + xl_rowcol_to_cell(save_row_diff + 1, 5) + ':' + xl_rowcol_to_cell(
										 row_diff - 1, 5) + ')}', cell_format2)
		worksheet_diff.write_formula(row_diff, 6,
									 '{=SUM(' + xl_rowcol_to_cell(save_row_diff + 1, 6) + ':' + xl_rowcol_to_cell(
										 row_diff - 1, 6) + ')}', cell_format2)
		worksheet_diff.write_formula(row_diff, 7,
									 '{=SUM(' + xl_rowcol_to_cell(save_row_diff + 1, 7) + ':' + xl_rowcol_to_cell(
										 row_diff - 1, 7) + ')}', cell_format2)
		worksheet_diff.merge_range(row, 8, row, last_col, '', contest_center)
		# Тооллого хийсэн
		# Хүлээн зөвшөөрсөн
		# Тооцоо хийсэн нягтлан хийсэн
		row_diff += 1
		row += 1

		worksheet.write(row, 1, u'Нийт Зөрүү', contest_left_no_bor)
		worksheet.write_formula(row, 2, '{=SUM(' + xl_rowcol_to_cell(save_row + 1, 9) + ':' + xl_rowcol_to_cell(row - 2,
																												9) + ')}',
								cell_format_no_border)
		worksheet.write(row + 1, 1, u'Нийт Дутуу', contest_left_no_bor)
		worksheet.write(row + 1, 2, self.price_diff_total_in, cell_format_no_border)
		worksheet.write(row + 2, 1, u'Нийт Илүү', contest_left_no_bor)
		worksheet.write(row + 2, 2, self.price_diff_total_out, cell_format_no_border)

		worksheet.merge_range(row + 3, 0, row + 3, 1, u'Тооллогын баг', contest_left_no_bor)
		worksheet.merge_range(row + 3, 2, row + 3, 5, u'.........................../___________________/',
							  contest_left_no_bor)
		worksheet.merge_range(row + 4, 0, row + 4, 1, u'Зөвшөөрсөн', contest_left_no_bor)
		worksheet.merge_range(row + 4, 2, row + 4, 5, u'.........................../___________________/',
							  contest_left_no_bor)
		worksheet.merge_range(row + 5, 0, row + 5, 1, u'Тооллого Хийсэн Нягтлан', contest_left_no_bor)
		worksheet.merge_range(row + 5, 2, row + 5, 5, u'.........................../___________________/',
							  contest_left_no_bor)

		worksheet_diff.merge_range(row_diff, 0, row_diff, 1, u'Тооллогын баг', contest_left_no_bor)
		worksheet_diff.merge_range(row_diff, 2, row_diff, 5, u'.........................../____________________/',
								   contest_left_no_bor)
		worksheet_diff.merge_range(row_diff + 1, 0, row_diff + 1, 1, u'Зөвшөөрсөн', contest_left_no_bor)
		worksheet_diff.merge_range(row_diff + 1, 2, row_diff + 1, 5,
								   u'.........................../___________________/', contest_left_no_bor)
		worksheet_diff.merge_range(row_diff + 2, 0, row_diff + 2, 1, u'Тооллого Хийсэн Нягтлан', contest_left_no_bor)
		worksheet_diff.merge_range(row_diff + 2, 2, row_diff + 2, 5,
								   u'.........................../___________________/', contest_left_no_bor)

		# Resize
		worksheet.set_column('A:B', 11)
		worksheet.set_column('C:C', 27)
		worksheet.set_margins(0.2, 0.2, 0, 0)
		worksheet.set_paper(9)
		worksheet.freeze_panes(3, 3)

		worksheet_diff.set_column('A:B', 11)
		worksheet_diff.set_column('C:C', 27)
		worksheet_diff.set_margins(0.2, 0.2, 0, 0)
		worksheet_diff.set_paper(9)
		worksheet_diff.freeze_panes(3, 3)

		workbook.close()

		out = base64.encodebytes(output.getvalue())
		file_name = self.name + '.xlsx'
		excel_id = self.env['report.excel.output'].create({'data': out, 'name': file_name})
		return {
			'type': 'ir.actions.act_url',
			'url': "web/content/?model=report.excel.output&id=" + str(
				excel_id.id) + "&filename_field=filename&download=true&field=data&filename=" + excel_id.name,
			'target': 'new',
		}

	def create_inv_line(self, inv_id, product_id, product_qty, loc_id, lot_id=False):
		line_obj = self.env['stock.inventory.line']
		line_obj.create({
			'product_id': product_id.id,
			'inventory_id': inv_id.id,
			'product_qty': product_qty,
			'location_id': loc_id.id,
			'prod_lot_id': lot_id.id if lot_id else False,
		})

	def get_value_text(self, value):
		if isinstance(value, float) or isinstance(value, int):
			if value == 0:
				return False
			return str(value)
		value = value.encode("utf-8")
		value = value.decode('utf-8')

		return value

	def action_import_inventory_update(self, barcode, product_qty, location_name=False, lot_name=False):
		if isinstance(barcode, float):
			barcode = int(barcode)
		else:
			barcode = barcode
		location_obj = self.env['stock.location']
		lot_obj = self.env['stock.lot']
		product_id = self.env['product.product'].search(
			['|', ('barcode', '=', barcode), ('default_code', '=', barcode)], limit=1)
		loc_id = False
		lot_id = False
		if location_name:
			loc_id = location_obj.search([('name', '=', location_name), ('usage', '=', 'internal')], limit=1)
			if not loc_id and product_id:
				raise UserError(u'%s Байрлал олдсонгүй' % location_name)

		if lot_name:
			lot_id = lot_obj.search([('name', '=', lot_name), ('product_id', '=', product_id.id)], limit=1)
			if not lot_id and product_id:
				raise UserError(u'%s Нэртэй лот/сериал олдсонгүй' % lot_name)

		line_id = self.line_ids.filtered(lambda r: r.product_id.id == product_id.id)
		if line_id:
			if loc_id:
				line_id = line_id.filtered(lambda r: r.location_id.id == loc_id.id)

			if lot_id:
				line_id = line_id.filtered(lambda r: r.prod_lot_id.id == lot_id.id)

			if not line_id:
				self.create_inv_line(self, product_id, product_qty, loc_id, lot_id)
			else:
				line_id.product_qty = product_qty
			# if len(line_id)>1:
			#     raise UserError(u'%s Бараа давхардаж байна'%(line_id.mapped('product_id.display_name')))
			# print 'line_id',line_id
			# if not line_id:
			#     raise UserError(u'%s энэ БАЙРЛАЛ дээр бараа алга'%(location_name))

		elif product_id:
			self.create_inv_line(self, product_id, product_qty, loc_id, lot_id)

	def action_import_inventory(self):
		if not self.import_data_ids:
			raise UserError('Оруулах эксэлээ UPLOAD хийнэ үү ')
		fileobj = NamedTemporaryFile('w+b')
		fileobj.write(base64.decodebytes(self.import_data_ids[0].datas))
		fileobj.seek(0)
		if self.is_barcode_reader:
			myreader = fileobj.read().splitlines()
			for row in myreader:
				print ("--row", row)
				row_data = row.split(',')
				barcode = row_data[0]
				qty = row_data[1]
				self.action_import_inventory_update(barcode, qty)
		else:

			if not os.path.isfile(fileobj.name):
				raise UserError(_('Reading file error.\nChecking for excel file!'))
			book = xlrd.open_workbook(fileobj.name)

			try:
				sheet = book.sheet_by_index(0)
			except:
				raise UserError(_("Sheet's number error"))
			nrows = sheet.nrows

			for item in range(0, nrows):
				row = sheet.row(item)
				barcode = row[0].value
				barcode = self.get_value_text(barcode)
				if not barcode:
					barcode = row[1].value
				elif barcode.lower() == 'false':
					barcode = row[1].value

				product_qty = row[5].value
				location_name = row[8].value
				lot_name = row[10].value
				self.action_import_inventory_update(barcode, product_qty, location_name, lot_name)

	def action_update_inventory(self):
		for item in self.line_ids:
			item.action_refresh_quantity()

	def get_inv_header_pdf(self):
		headers = [
			'№',
			'Баркод',
			'Барааны нэр',
			'Хэмжих нэгж',
			'Үлдэгдэл',
			'Тоолсон тоо',
		]
		if self.get_stock_inv_pdf_lot_ok():
			headers.insert(3, 'Цуврал')
		return headers

	def get_stock_inv_pdf_lot_ok(self):
		if self.line_ids.filtered(lambda r: r.product_id.tracking in ['lot', 'serial']):
			return True
		return False

	def get_inv_data_pdf(self, number, line, qty_total):
		if line:
			datas = [
				'<p style="text-align: center;">' + str(number) + '</p>',
				'<p style="text-align: left;">' + (line.product_id.barcode or '') + '</p>',
				'<p style="text-align: left;">' + (line.product_id.name[:50]) + '</p>',
				'<p style="text-align: center;">' + line.product_uom_id.name + '</p>',
				'<p style="text-align: right;">' + "{0}".format(line.theoretical_qty) + "</p>",
				'<p style="text-align: right;"></p>',
			]
			if self.get_stock_inv_pdf_lot_ok():
				datas.insert(3, '<p style="text-align: left;">' + (
						line.prod_lot_id and line.prod_lot_id.name or '') + '</p>')
		else:
			datas = [
				'<p style="text-align: center;"></p>',
				'<p style="text-align: left;">Нийт</p>',
				'<p style="text-align: left;"></p>',
				'<p style="text-align: center;"></p>',
				'<p style="text-align: right;">' + "{0}".format(qty_total) + "</p>",
				'<p style="text-align: right;"></p>',
			]
			if self.get_stock_inv_pdf_lot_ok():
				datas.insert(3, '')
		return datas

	def get_inv_lines_for_print(self, ids):
		inventory = self.browse(ids)
		headers = inventory.get_inv_header_pdf()
		datas = []
		number = 1
		lines = inventory.line_ids.sorted(key=lambda l: (l.product_id, l.theoretical_qty))
		for line in lines:
			datas.append(inventory.get_inv_data_pdf(number, line, 0))
			number += 1
		if datas:
			qty_total = sum(lines.mapped('theoretical_qty'))
			datas.append(inventory.get_inv_data_pdf(number, False, qty_total))
		else:
			return ''
		res = {'header': headers, 'data': datas}
		return res

	def get_location_names(self, ids):
		inventory = self.browse(ids)
		if inventory.location_ids:
			name = ', '.join(inventory.location_ids.mapped('name'))
		else:
			name = ', '.join(inventory.line_ids.mapped('location_id').mapped('name'))
		return name

	def get_category_names(self, ids):
		inventory = self.browse(ids)
		name = 'Бүх'
		if inventory.filter_inv == 'category_child_of' or inventory.filter_inv == 'category_many':
			name = ''
			for cat in inventory.many_categ_ids:
				if cat == inventory.many_categ_ids[0]:
					name = cat.name_get()[0][1]
				else:
					name += ', %s' % cat.name_get()[0][1]
		return name

	def do_print_inventory_sheet(self):
		self.ensure_one()
		model_id = self.env['ir.model'].sudo().search([('model', '=', 'stock.inventory')], limit=1)
		template = self.env['pdf.template.generator'].sudo().search(
			[('model_id', '=', model_id.id), ('name', '=', 'inventory_sheet')], limit=1)
		if not template:
			raise UserError(_(u'Хэвлэх загварын тохиргоо хийгдээгүй байна, Системийн админд хандана уу!'))

		html = ''
		if template:
			html = template.sudo().get_template_data_html(self.id)

		return template.sudo().print_template_html(html)


class InventoryLine(models.Model):
	_name = "stock.inventory.line"
	_description = "Inventory Line"
	_order = "product_id, inventory_id, location_id, prod_lot_id, categ_id"

	@api.model
	def _domain_location_id(self):
		if self.env.context.get('active_model') == 'stock.inventory':
			inventory = self.env['stock.inventory'].browse(self.env.context.get('active_id'))
			if inventory.exists() and inventory.location_ids:
				return "[('company_id', '=', company_id), ('usage', 'in', ['internal', 'transit']), ('id', 'child_of', %s)]" % inventory.location_ids.ids
		return "[('company_id', '=', company_id), ('usage', 'in', ['internal', 'transit'])]"

	@api.model
	def _domain_product_id(self):
		if self.env.context.get('active_model') == 'stock.inventory':
			inventory = self.env['stock.inventory'].browse(self.env.context.get('active_id'))
			if inventory.exists() and len(inventory.product_ids) > 1:
				return "[('type', '=', 'product'), '|', ('company_id', '=', False), ('company_id', '=', company_id), ('id', 'in', %s)]" % inventory.product_ids.ids
		return "[('type', '=', 'product'), '|', ('company_id', '=', False), ('company_id', '=', company_id)]"

	is_editable = fields.Boolean(help="Technical field to restrict the edition.")
	inventory_id = fields.Many2one('stock.inventory', 'Inventory', check_company=True,
		index=True, ondelete='cascade')
	partner_id = fields.Many2one('res.partner', 'Owner', check_company=True)
	product_id = fields.Many2one('product.product', 'Product', check_company=True,
		domain=lambda self: self._domain_product_id(), index=True, required=True)
	product_uom_id = fields.Many2one('uom.uom', 'Product Unit of Measure', 
		required=True, readonly=True)
	product_qty = fields.Float('Counted Quantity', digits='Product Unit of Measure', 
		default=0)
	categ_id = fields.Many2one(related='product_id.categ_id', store=True)
	location_id = fields.Many2one('stock.location', 'Location', check_company=True,
		domain=lambda self: self._domain_location_id(), index=True, required=True)
	package_id = fields.Many2one('stock.quant.package', 'Pack', index=True, 
		check_company=True, domain="[('location_id', '=', location_id)]",)
	prod_lot_id = fields.Many2one('stock.lot', 'Lot/Serial Number', check_company=True,
		domain="[('product_id','=',product_id), ('company_id', '=', company_id)]")
	company_id = fields.Many2one('res.company', 'Company', related='inventory_id.company_id',
		index=True, readonly=True, store=True)
	state = fields.Selection('Status', related='inventory_id.state')
	theoretical_qty = fields.Float('Theoretical Quantity', digits='Product Unit of Measure', 
		readonly=True)
	inventory_date = fields.Datetime('Inventory Date', readonly=True, default=fields.Datetime.now,
		help="Last date at which the On Hand Quantity has been computed.")
	outdated = fields.Boolean(string='Quantity outdated', compute='_compute_outdated', 
		search='_search_outdated')
	product_tracking = fields.Selection('Tracking', related='product_id.tracking', readonly=True)
	erosion_qty = fields.Float('Quantity erosion', default=0)
	erosion_description = fields.Char('Quantity description')

	@api.depends('product_qty', 'theoretical_qty')
	def _compute_difference(self):
		for line in self:
			line.difference_qty = line.product_qty - line.theoretical_qty

	@api.depends('inventory_date', 'product_id.stock_move_ids', 'theoretical_qty', 'product_uom_id.rounding')
	def _compute_outdated(self):
		grouped_quants = self.env['stock.quant'].read_group(
			[('product_id', 'in', self.product_id.ids), ('location_id', 'in', self.location_id.ids)],
			['product_id', 'location_id', 'lot_id', 'package_id', 'owner_id', 'quantity:sum'],
			['product_id', 'location_id', 'lot_id', 'package_id', 'owner_id'],
			lazy=False)
		quants = {
			(quant['product_id'][0],
			 quant['location_id'][0],
			 quant['lot_id'] and quant['lot_id'][0],
			 quant['package_id'] and quant['package_id'][0],
			 quant['owner_id'] and quant['owner_id'][0]): quant['quantity']
			for quant in grouped_quants
		}
		for line in self:
			if line.state == 'done' or not line.id:
				line.outdated = False
				continue
			qty = quants.get((
				line.product_id.id,
				line.location_id.id,
				line.prod_lot_id.id,
				line.package_id.id,
				line.partner_id.id,
			), 0
			)
			if float_compare(qty, line.theoretical_qty, precision_rounding=line.product_uom_id.rounding) != 0:
				line.outdated = True
			else:
				line.outdated = False

	@api.model
	def get_theoretical_quantity(self, product_id, location_id, lot_id=None, package_id=None, owner_id=None, to_uom=None):
		product_id = self.env['product.product'].browse(product_id)
		product_id.check_access_rights('read')
		product_id.check_access_rule('read')

		location_id = self.env['stock.location'].browse(location_id)
		lot_id = self.env['stock.production.lot'].browse(lot_id)
		package_id = self.env['stock.quant.package'].browse(package_id)
		owner_id = self.env['res.partner'].browse(owner_id)
		to_uom = self.env['uom.uom'].browse(to_uom)
		quants = self.env['stock.quant']._gather(product_id, location_id, lot_id=lot_id, package_id=package_id, owner_id=owner_id, strict=True)
		if lot_id:
			quants = quants.filtered(lambda q: q.lot_id == lot_id)
		theoretical_quantity = sum([quant.quantity for quant in quants])
		if to_uom and product_id.uom_id != to_uom:
			theoretical_quantity = product_id.uom_id._compute_quantity(theoretical_quantity, to_uom)
		return theoretical_quantity

	@api.onchange('product_id', 'location_id', 'product_uom_id', 'prod_lot_id', 'partner_id', 'package_id')
	def _onchange_quantity_context(self):
		if self.product_id:
			self.product_uom_id = self.product_id.uom_id
		if self.product_id and self.location_id and self.product_id.uom_id.category_id == self.product_uom_id.category_id:
			theoretical_qty = self.get_theoretical_quantity(
				self.product_id.id,
				self.location_id.id,
				lot_id=self.prod_lot_id.id,
				package_id=self.package_id.id,
				owner_id=self.partner_id.id,
				to_uom=self.product_uom_id.id,
			)
		else:
			theoretical_qty = 0
		# Sanity check on the lot.
		if self.prod_lot_id:
			if self.product_id.tracking == 'none' or self.product_id != self.prod_lot_id.product_id:
				self.prod_lot_id = False

		if self.prod_lot_id and self.product_id.tracking == 'serial':
			# We force `product_qty` to 1 for SN tracked product because it's
			# the only relevant value aside 0 for this kind of product.
			self.product_qty = 1
		elif self.product_id and float_compare(self.product_qty, self.theoretical_qty,
											   precision_rounding=self.product_uom_id.rounding) == 0:
			# We update `product_qty` only if it equals to `theoretical_qty` to
			# avoid to reset quantity when user manually set it.
			self.product_qty = theoretical_qty
		self.theoretical_qty = theoretical_qty

	@api.model_create_multi
	def create(self, vals_list):
		""" Override to handle the case we create inventory line without
		`theoretical_qty` because this field is usually computed, but in some
		case (typicaly in tests), we create inventory line without trigger the
		onchange, so in this case, we set `theoretical_qty` depending of the
		product's theoretical quantity.
		Handles the same problem with `product_uom_id` as this field is normally
		set in an onchange of `product_id`.
		Finally, this override checks we don't try to create a duplicated line.
		"""
		for values in vals_list:
   # if 'theoretical_qty' not in values:
   # 	theoretical_qty = self.env['product.product'].get_theoretical_quantity(
   # 		values['product_id'],
   # 		values['location_id'],
   # 		lot_id=values.get('prod_lot_id'),
   # 		package_id=values.get('package_id'),
   # 		owner_id=values.get('partner_id'),
   # 		to_uom=values.get('product_uom_id'),
   # 	)
   # 	values['theoretical_qty'] = theoretical_qty
			if 'product_id' in values and 'product_uom_id' not in values:
				values['product_uom_id'] = self.env['product.product'].browse(values['product_id']).uom_id.id
		res = super(InventoryLine, self).create(vals_list)
		res._check_no_duplicate_line()
		return res

	def write(self, vals):
		res = super(InventoryLine, self).write(vals)
		self._check_no_duplicate_line()
		return res

	def _check_no_duplicate_line(self):
		for line in self:
			domain = [
				('id', '!=', line.id),
				('product_id', '=', line.product_id.id),
				('location_id', '=', line.location_id.id),
				('partner_id', '=', line.partner_id.id),
				('package_id', '=', line.package_id.id),
				('prod_lot_id', '=', line.prod_lot_id.id),
				('inventory_id', '=', line.inventory_id.id)]
			existings = self.search_count(domain)
			if existings:
				raise UserError(_("There is already one inventory adjustment line for this product,"
								  " you should rather modify this one instead of creating a new one."))

	@api.constrains('product_id')
	def _check_product_id(self):
		""" As no quants are created for consumable products, it should not be possible do adjust
		their quantity.
		"""
		for line in self:
			if line.product_id.type != 'product':
				raise ValidationError(_("You can only adjust storable products.") + '\n\n%s -> %s' % (line.product_id.display_name, line.product_id.type))

	def _get_move_values(self, qty, location_id, location_dest_id, out):
		self.ensure_one()
		return {
			'name': _('INV:') + (self.inventory_id.name or ''),
			'product_id': self.product_id.id,
			'product_uom': self.product_uom_id.id,
			'product_uom_qty': qty,
			'date': self.inventory_id.date,
			'company_id': self.inventory_id.company_id.id,
			'inventory_id': self.inventory_id.id,
			'state': 'confirmed',
			'restrict_partner_id': self.partner_id.id,
			'location_id': location_id,
			'location_dest_id': location_dest_id,
			'move_line_ids': [(0, 0, {
				'product_id': self.product_id.id,
				'lot_id': self.prod_lot_id.id,
				'reserved_uom_qty': 0,  # bypass reservation here
				'product_uom_id': self.product_uom_id.id,
				'qty_done': qty,
				'package_id': out and self.package_id.id or False,
				'result_package_id': (not out) and self.package_id.id or False,
				'location_id': location_id,
				'location_dest_id': location_dest_id,
				'owner_id': self.partner_id.id,
			})]
		}

	def _get_virtual_location(self):
		return self.product_id.with_company(self.company_id).property_stock_inventory

	def _generate_moves(self):
		vals_list = []
		for line in self:
			virtual_location = line._get_virtual_location()
			rounding = line.product_id.uom_id.rounding
			if float_is_zero(line.difference_qty, precision_rounding=rounding):
				continue
			if line.difference_qty > 0:  # found more than expected
				vals = line._get_move_values(line.difference_qty, virtual_location.id, line.location_id.id, False)
			else:
				vals = line._get_move_values(abs(line.difference_qty), line.location_id.id, virtual_location.id,
											 True)
			vals_list.append(vals)
		return self.env['stock.move'].create(vals_list)

	def _refresh_inventory(self):
		return self[0].inventory_id.action_open_inventory_lines()

	def action_refresh_quantity(self):
		filtered_lines = self.filtered(lambda l: l.state != 'done')
		for line in filtered_lines:
			if line.outdated:
				quants = self.env['stock.quant']._gather(line.product_id, line.location_id, lot_id=line.prod_lot_id,
														 package_id=line.package_id, owner_id=line.partner_id,
														 strict=True)
				if quants.exists():
					quantity = sum(quants.mapped('quantity'))
					if line.theoretical_qty != quantity:
						line.theoretical_qty = quantity
				else:
					line.theoretical_qty = 0
				line.inventory_date = fields.Datetime.now()

	def action_reset_product_qty(self):
		""" Write `product_qty` to zero on the selected records. """
		impacted_lines = self.env['stock.inventory.line']
		for line in self:
			if line.state == 'done':
				continue
			impacted_lines |= line
		impacted_lines.write({'product_qty': 0})

	def _search_difference_qty(self, operator, value):
		if operator == '=':
			result = True
		elif operator == '!=':
			result = False
		else:
			raise NotImplementedError()
		lines = self.search([('inventory_id', '=', self.env.context.get('default_inventory_id'))])
		line_ids = lines.filtered(
			lambda line: float_is_zero(line.difference_qty, line.product_id.uom_id.rounding) == result).ids
		return [('id', 'in', line_ids)]

	def _search_outdated(self, operator, value):
		if operator != '=':
			if operator == '!=' and isinstance(value, bool):
				value = not value
			else:
				raise NotImplementedError()
		lines = self.search([('inventory_id', '=', self.env.context.get('default_inventory_id'))])
		line_ids = lines.filtered(lambda line: line.outdated == value).ids
		return [('id', 'in', line_ids)]

	difference_qty = fields.Float('Difference', compute='_compute_difference',
								  help="Indicates the gap between the product's theoretical quantity and its newest quantity.",
								  readonly=True, digits='Product Unit of Measure', search="_search_difference_qty",
								  store=True)
	diff_price_unit = fields.Float('Нэгж үнэ/өртөг', compute='_compute_diff_qty', store=True, readonly=True)
	sum_qty_price_unit = fields.Float('Нийт нэгж үнэ/өртөг', compute='_compute_diff_qty', store=True, readonly=True)
	price_diff_subtotal = fields.Float(string='Нийт зөрүү үнэ',
									   readonly=True, compute='_compute_diff_qty', store=True)
	product_name = fields.Char(
		'Product Name', related='product_id.name', store=True, readonly=True)
	product_code = fields.Char(
		'Product Code', related='product_id.default_code', store=True, readonly=True)
	location_name = fields.Char(
		'Location Name', related='location_id.complete_name', store=True, readonly=True)
	prod_barcode = fields.Char('Баркод', compute='set_prod_barcode', readonly=True)

	@api.depends('product_id')
	def set_prod_barcode(self):
		for item in self:
			item.prod_barcode = item.product_id.barcode

	@api.depends('theoretical_qty', 'product_qty', 'difference_qty')
	def _compute_diff_qty(self):
		for item in self:
			st_price = item.product_id.standard_price
			if item.product_id.cost_method == 'fifo' and item.product_qty != 0:
				quantity = item.product_qty
				company = item.company_id
				fifo_vals = item.product_id._run_fifo(abs(quantity), company)
				average_cost = 0
				if fifo_vals.get('unit_cost', False):
					average_cost = abs(fifo_vals.get('unit_cost', False))

				st_price = abs(average_cost)
			item.diff_price_unit = st_price if item.product_id.list_price <= 10 else item.product_id.list_price
			item.sum_qty_price_unit = item.diff_price_unit * item.product_qty
			item.price_diff_subtotal = item.diff_price_unit * item.difference_qty
