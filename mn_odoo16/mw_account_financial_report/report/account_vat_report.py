from odoo import fields, models, api
from io import BytesIO
import xlsxwriter
import base64
from datetime import date
from odoo.exceptions import UserError

fmt_time = '%Y-%m-%d %H:%M:%S'
fmt = '%Y-%m-%d'

class MwVatReport(models.TransientModel):
	_name = 'mw.vat.report'

	date_range_id = fields.Many2one('date.range', 'Date range')
	date_start = fields.Date(string='Эхлэх огноо', required=True)
	date_end = fields.Date(string='Дуусах огноо', required=True)
	journal_ids = fields.Many2many('account.journal', string='Журнал')
	include_account = fields.Boolean(string='НӨАТ оруулахгүй?', default=False, compute='compute_journal',readonly=True)
	account_ids = fields.Many2many('account.account', string='Данс')
	partner_id = fields.Many2one('res.partner', string='Харилцагч')

	@api.depends('journal_ids')
	def compute_journal(self):
		if self.journal_ids:
			self.include_account = True
		else:
			self.include_account = False

	@api.onchange('date_range_id')
	def onchange_date_range_id(self):
		if self.date_range_id:
			self.date_start = self.date_range_id.date_start
			self.date_end = self.date_range_id.date_end
		else:
			self.date_start = self.date_end = None

	def download_report(self):
		output = BytesIO()
		workbook = xlsxwriter.Workbook(output)
		file_name = 'Худалдан авалтын дэвтэр.xlsx'

		header = workbook.add_format({'bold': 1})
		header.set_font_size(14)
		header.set_font('Times new roman')
		header.set_align('center')
		header.set_align('vcenter')

		contest_number_right = workbook.add_format({'num_format': '###,###,###.##'})
		contest_number_right.set_text_wrap()
		contest_number_right.set_font_size(9)
		contest_number_right.set_font('Times new roman')
		contest_number_right.set_align('right')
		contest_number_right.set_align('vcenter')
		contest_number_right.set_border(style=1)

		contest_center = workbook.add_format({'bold':1})
		contest_center.set_text_wrap()
		contest_center.set_font_size(11)
		contest_center.set_font('Times new roman')
		contest_center.set_align('center')
		contest_center.set_align('vcenter')
		contest_center.set_border(style=1)

		contest_left_borderless = workbook.add_format()
		contest_left_borderless.set_font_size(9)
		contest_left_borderless.set_font('Times new roman')
		contest_left_borderless.set_align('left')
		contest_left_borderless.set_align('vcenter')

		contest_left = workbook.add_format()
		contest_left.set_text_wrap()
		contest_left.set_font_size(9)
		contest_left.set_font('Times new roman')
		contest_left.set_align('left')
		contest_left.set_align('vcenter')
		contest_left.set_border(style=1)

		contest_center_bold = workbook.add_format({'bold':1})
		contest_center_bold.set_text_wrap()
		contest_center_bold.set_font_size(9)
		contest_center_bold.set_font('Times new roman')
		contest_center_bold.set_align('center')
		contest_center_bold.set_align('vcenter')
		contest_center_bold.set_border(style=1)
		contest_center_bold.set_bg_color('#4da1ee')

		sheet = workbook.add_worksheet(u'')
		sheet.merge_range(0, 0, 0, 7, u'Худалдан авалтын дэвтэр', header)
		sheet.write(2, 0, 'Компани', contest_left_borderless)
		sheet.write(3, 0, self.env.user.company_id.name, contest_left_borderless)
		sheet.write(2, 3, 'Эхлэх огноо: ' + str(self.date_start.strftime("%Y-%m-%d")), contest_left_borderless)
		sheet.write(3, 3, 'Дуусах огноо: ' + str(self.date_end.strftime("%Y-%m-%d")), contest_left_borderless)
		sheet.write(4, 0, 'Хэвлэсэн огноо: ' + str(date.today().strftime("%Y-%m-%d")), contest_left_borderless)
		row = 5
		sheet.write(row, 0, u'Дд', contest_center_bold)
		sheet.write(row, 1, u'Огноо', contest_center_bold)
		sheet.write(row, 2, u'Дугаар', contest_center_bold)
		sheet.write(row, 3, u'Харилцагчийн нэр', contest_center_bold)
		sheet.write(row, 4, u'Харилцагчийн регистр', contest_center_bold)
		sheet.write(row, 5, u'Нийт дүн', contest_center_bold)
		sheet.write(row, 6, u'Ногдуулсан НӨТ', contest_center_bold)
		sheet.write(row, 7, u'Цэвэр дүн', contest_center_bold)
		sheet.autofilter(row, 0, row, 7)
		sheet.freeze_panes(6, 0)
		sheet.set_row(0, 30)
		sheet.set_row(5, 30)
		sheet.set_column(0, 0, 4)
		sheet.set_column(1, 1, 8)
		sheet.set_column(2, 2, 10)
		sheet.set_column(3, 3, 20)
		sheet.set_column(4, 4, 10)
		sheet.set_column(5, 5, 10)
		sheet.set_column(6, 6, 10)
		sheet.set_column(7, 7, 10)
		row += 1
		domains_external=[
			('date', '>=', self.date_start.strftime("%Y-%m-%d")),
			('date', '<=', self.date_end.strftime("%Y-%m-%d")),
			('debit', '>', 0),
			('move_id.state', '=', 'posted'),
			('partner_id.country_id.name','!=','Монгол')
			]
		domains_internal=[
			('date', '>=', self.date_start.strftime("%Y-%m-%d")),
			('date', '<=', self.date_end.strftime("%Y-%m-%d")),
			('debit', '>', 0),
			('move_id.state', '=', 'posted'),
			('partner_id.country_id.name','=','Монгол')
			]
		domains_undefined=[
			('date', '>=', self.date_start.strftime("%Y-%m-%d")),
			('date', '<=', self.date_end.strftime("%Y-%m-%d")),
			('debit', '>', 0),
			('move_id.state', '=', 'posted'),
			('partner_id.country_id','=',False)
			]
		if self.partner_id:
			domains_external.append(('partner_id','=',self.partner_id.id))
			domains_internal.append(('partner_id','=',self.partner_id.id))
			domains_undefined.append(('partner_id','=',self.partner_id.id))
		if self.journal_ids and self.include_account and self.account_ids:
			domains_external.append(('move_id.journal_id','in',self.journal_ids.ids))
			domains_external.append(('tax_ids','!=',False))
			domains_internal.append(('move_id.journal_id','in',self.journal_ids.ids))
			domains_internal.append(('tax_ids','!=',False))
			domains_undefined.append(('move_id.journal_id','in',self.journal_ids.ids))
			domains_undefined.append(('tax_ids','!=',False))
			if self.include_account:
				domains_external.append(('account_id','not in', self.account_ids.ids))
				domains_internal.append(('account_id','not in', self.account_ids.ids))
				domains_undefined.append(('account_id','not in', self.account_ids.ids))
			aml_in=self.env['account.move.line'].search(domains_internal)
			aml_ex=self.env['account.move.line'].search(domains_external)
			aml_un=self.env['account.move.line'].search(domains_undefined)
			dd = 1
			sheet.merge_range(row, 0, row, 7, u'А. Дотоодын борлуулалт', contest_center)
			row += 1
			sheet.write(5, 8, u'Татвар', contest_center_bold)
			for move in aml_in:
				check = any(ch in move.move_id.line_ids.account_id.ids for ch in self.account_ids.ids)
				if check == False and self.include_account:
					sheet.write(row, 0, dd, contest_left)
					sheet.write(row, 1, move.date.strftime("%Y-%m-%d"), contest_left)
					sheet.write(row, 2, move.move_id.name, contest_left)
					sheet.write(row, 3, move.partner_id.name, contest_left)
					sheet.write(row, 4, move.partner_id.vat if move.partner_id.vat else '', contest_left)
					sheet.write(row, 5, move.debit, contest_number_right)
					sheet.write(row, 6, '0', contest_number_right)
					sheet.write(row, 7, move.debit, contest_number_right)
					sheet.write(row, 8, ', '.join(move.tax_ids.mapped('name')) or '', contest_left)
					dd += 1
					row += 1
			sheet.merge_range(row, 0, row, 7, u'Б. Экспортын борлуулалт', contest_center)
			row += 1
			for move in aml_ex:
				check = any(ch in move.move_id.line_ids.account_id.ids for ch in self.account_ids.ids)
				if check == False and self.include_account:
					sheet.write(row, 0, dd, contest_left)
					sheet.write(row, 1, move.date.strftime("%Y-%m-%d"), contest_left)
					sheet.write(row, 2, move.move_id.name, contest_left)
					sheet.write(row, 3, move.partner_id.name, contest_left)
					sheet.write(row, 4, move.partner_id.vat if move.partner_id.vat else '', contest_left)
					sheet.write(row, 5, move.debit, contest_number_right)
					sheet.write(row, 6, '0', contest_number_right)
					sheet.write(row, 7, move.debit, contest_number_right)
					sheet.write(row, 8, ', '.join(move.tax_ids.mapped('name')) or '', contest_left)
					dd += 1
					row += 1
			sheet.merge_range(row, 0, row, 7, u'В. Харилцагч дээр улс сонгогдоогүй борлуулалт', contest_center)
			row += 1
			for move in aml_un:
				check = any(ch in move.move_id.line_ids.account_id.ids for ch in self.account_ids.ids)
				if check == False and self.include_account:
					sheet.write(row, 0, dd, contest_left)
					sheet.write(row, 1, move.date.strftime("%Y-%m-%d"), contest_left)
					sheet.write(row, 2, move.move_id.name, contest_left)
					sheet.write(row, 3, move.partner_id.name, contest_left)
					sheet.write(row, 4, move.partner_id.vat if move.partner_id.vat else '', contest_left)
					sheet.write(row, 5, move.debit, contest_number_right)
					sheet.write(row, 6, '0', contest_number_right)
					sheet.write(row, 7, move.debit, contest_number_right)
					sheet.write(row, 8, ', '.join(move.tax_ids.mapped('name')) or '', contest_left)
					dd += 1
					row += 1
			if aml_un or aml_ex or aml_in:
				sheet.write_formula(row, 5, '{=SUM('+self._symbol(6, 5) +':'+ self._symbol(row-1, 5)+')}', contest_number_right)
				sheet.write_formula(row, 6, '{=SUM('+self._symbol(6, 6) +':'+ self._symbol(row-1, 6)+')}', contest_number_right)
				sheet.write_formula(row, 7, '{=SUM('+self._symbol(6, 7) +':'+ self._symbol(row-1, 7)+')}', contest_number_right)
		elif self.account_ids and not self.journal_ids and not self.include_account:
			domains_internal.append(('account_id','in',self.account_ids.ids))
			domains_external.append(('account_id','in',self.account_ids.ids))
			domains_undefined.append(('account_id','in',self.account_ids.ids))
			aml_in=self.env['account.move.line'].search(domains_internal)
			aml_ex=self.env['account.move.line'].search(domains_external)
			aml_un=self.env['account.move.line'].search(domains_undefined)
			dd = 1
			sheet.merge_range(row, 0, row, 7, u'А. Дотоодын борлуулалт', contest_center)
			row += 1
			for move in aml_in:
				sheet.write(row, 0, dd, contest_left)
				sheet.write(row, 1, move.date.strftime("%Y-%m-%d"), contest_left)
				sheet.write(row, 2, move.move_id.name, contest_left)
				sheet.write(row, 3, move.partner_id.name, contest_left)
				sheet.write(row, 4, move.partner_id.vat if move.partner_id.vat else '', contest_left)
				sheet.write(row, 5, sum(move.move_id.line_ids.mapped('debit')), contest_number_right)
				sheet.write(row, 6, move.debit, contest_number_right)
				sheet.write(row, 7, sum(move.move_id.line_ids.mapped('debit')) - move.debit, contest_number_right)
				dd += 1
				row += 1
			sheet.merge_range(row, 0, row, 7, u'Б. Экспортын борлуулалт', contest_center)
			row += 1
			for move in aml_ex:
				sheet.write(row, 0, dd, contest_left)
				sheet.write(row, 1, move.date.strftime("%Y-%m-%d"), contest_left)
				sheet.write(row, 2, move.move_id.name, contest_left)
				sheet.write(row, 3, move.partner_id.name, contest_left)
				sheet.write(row, 4, move.partner_id.vat if move.partner_id.vat else '', contest_left)
				sheet.write(row, 5, sum(move.move_id.line_ids.mapped('debit')), contest_number_right)
				sheet.write(row, 6, move.debit, contest_number_right)
				sheet.write(row, 7, sum(move.move_id.line_ids.mapped('debit')) - move.debit, contest_number_right)
				dd += 1
				row += 1
			sheet.merge_range(row, 0, row, 7, u'В. Харилцагч дээр улс сонгогдоогүй борлуулалт', contest_center)
			row += 1
			for move in aml_un:
				sheet.write(row, 0, dd, contest_left)
				sheet.write(row, 1, move.date.strftime("%Y-%m-%d"), contest_left)
				sheet.write(row, 2, move.move_id.name, contest_left)
				sheet.write(row, 3, move.partner_id.name, contest_left)
				sheet.write(row, 4, move.partner_id.vat if move.partner_id.vat else '', contest_left)
				sheet.write(row, 5, sum(move.move_id.line_ids.mapped('debit')), contest_number_right)
				sheet.write(row, 6, move.debit, contest_number_right)
				sheet.write(row, 7, sum(move.move_id.line_ids.mapped('debit')) - move.debit, contest_number_right)
				dd += 1
				row += 1
			if aml_un or aml_ex or aml_in:
				sheet.write_formula(row, 5, '{=SUM('+self._symbol(6, 5) +':'+ self._symbol(row-1, 5)+')}', contest_number_right)
				sheet.write_formula(row, 6, '{=SUM('+self._symbol(6, 6) +':'+ self._symbol(row-1, 6)+')}', contest_number_right)
				sheet.write_formula(row, 7, '{=SUM('+self._symbol(6, 7) +':'+ self._symbol(row-1, 7)+')}', contest_number_right)
		else:
			raise UserError('1. Журнал дангаар татах боломжгүй тул данс сонгоно уу')
############################################################
		workbook.close()
		out = base64.encodebytes(output.getvalue())
		excel_id = self.env['report.excel.output'].create({'data': out, 'name': file_name})

		return {
			'type': 'ir.actions.act_url',
			'url': "web/content/?model=report.excel.output&id=%d&filename_field=filename&download=true&field=data&filename=%s" % (excel_id.id, excel_id.name),
			'target': 'new',
		}

	def _symbol(self, row, col):
		return self._symbol_col(col) + str(row+1)
	def _symbol_col(self, col):
		excelCol = str()
		div = col+1
		while div:
			(div, mod) = divmod(div-1, 26)
			excelCol = chr(mod + 65) + excelCol
		return excelCol