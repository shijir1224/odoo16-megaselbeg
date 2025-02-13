from odoo import api, fields, models, _
from xlsxwriter.utility import xl_rowcol_to_cell

import logging
_logger = logging.getLogger(__name__)

class ProductTemplate(models.Model):
	_inherit = 'product.template'

	product_specification = fields.Char(string='Барааны үзүүлэлт')
	comp_tmpl_ids = fields.One2many('purchase.order.comparison.line', related='product_variant_ids.comparison_ids', readonly=True)
	comp_po_ids = fields.One2many('purchase.order', related='product_variant_ids.comparison_po_ids', readonly=True)

class ProductProduct(models.Model):
	_inherit = 'product.product'

	comparison_ids = fields.One2many('purchase.order.comparison.line', 'product_id', 'Vendors')
	comparison_po_ids = fields.One2many('purchase.order', 'product_id', 'Comparison')

class InheritStockProductExpensiveLine(models.Model):
	_inherit = 'stock.product.other.expense.line'

	product_specification = fields.Char(string='Барааны үзүүлэлт', related='product_id.product_specification')

class StockInventoryLine(models.Model):
	_inherit = 'stock.inventory.line'

	product_brand_id = fields.Many2one(related='product_id.product_brand_id', string='Brand', store=True)
	default_code = fields.Char(related='product_id.default_code', string='Эдийн дугаар', store=True)
	product_specification = fields.Char(related='product_id.product_specification', string='Барааны үзүүлэлт', store=True)

class Inventory(models.Model):
	_inherit = 'stock.inventory'

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
		wo_sheet.write(row, 11, u"Brand", cell_style)
		wo_sheet.write(row, 12, u"Барааны үзүүлэлт", cell_style)

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
		wo_sheet.write_formula(row, 6, '{=(' + xl_rowcol_to_cell(row, 5) + '-' + xl_rowcol_to_cell(row, 4) + ')}', cell_format2)
		if self.user_has_groups('mw_stock.group_stock_inv_diff_view'):
			wo_sheet.write(row, 7, item.price_diff_subtotal, cell_format2)
		else:
			wo_sheet.write(row, 7, 0, cell_format2)
		wo_sheet.write(row, 8, item.location_id.name, cell_format2)
		wo_sheet.write(row, 9, item.product_id.product_code, cell_format2)
		wo_sheet.write(row, 10, item.prod_lot_id.name if item.prod_lot_id else '', cell_format2)
		wo_sheet.write(row, 11, item.product_id.product_brand_id.name if item.product_id.product_brand_id else '', cell_format2)
		wo_sheet.write(row, 12, item.product_id.product_specification if item.product_id.product_specification else '', cell_format2)

		return wo_sheet

class StockQuantReport(models.Model):
	_inherit = "stock.quant.report"
	
	product_brand_id = fields.Many2one('product.brand', string='Brand')
	product_specification = fields.Char(string='Барааны үзүүлэлт')

	def _select(self):
		select_str = super(StockQuantReport, self)._select()
		select_str += """
			,
			pt.product_brand_id,
			pt.product_specification
		"""
		return select_str

	def _from(self):
		select_str = super(StockQuantReport, self)._from()
		select_str += """
			LEFT JOIN product_brand as pb ON (pb.id = pt.product_brand_id)
		"""
		return select_str

class StockMove(models.Model):
	_inherit = "stock.move"
	
	product_brand_id = fields.Many2one(related='product_id.product_brand_id', string='Brand')
	product_specification = fields.Char(related='product_id.product_specification', string='Барааны үзүүлэлт')
	product_template_variant_value_ids = fields.Many2many(related='product_id.product_template_variant_value_ids', string='Хувилбарын утга')

class StockMove(models.Model):
	_inherit = "stock.move.line"

	product_brand_id = fields.Many2one(related='product_id.product_brand_id', string='Brand')
	product_specification = fields.Char(related='product_id.product_specification', string='Барааны үзүүлэлт')
	product_template_variant_value_ids = fields.Many2many(related='product_id.product_template_variant_value_ids', string='Хувилбарын утга')

class RequiredPartLine(models.Model):
	_inherit= 'required.part.line'
 
	product_specification = fields.Char(related='product_id.product_specification', string='Барааны үзүүлэлт')