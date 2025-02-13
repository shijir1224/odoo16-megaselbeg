# -*- coding: utf-8 -*-

import xlsxwriter
from io import BytesIO
import base64
from odoo import api, fields, models

class EvalPlanReport(models.TransientModel):
	_name = "eval.plan.report"
	_description = "Eval plan report"

	company_id= fields.Many2one('res.company', "Компани", default=lambda self: self.env.user.company_id, required=True)
	# start_date = fields.Date('Эхлэх огноо', required=True)
	# end_date = fields.Date('Дуусах огноо', required=True)
	year = fields.Char('Жил')
	month = fields.Char('Сар')
	department_id = fields.Many2one('hr.department',string='Хэлтэс')

	def export_report(self):
		ctx = dict(self._context)
		output = BytesIO()
		workbook = xlsxwriter.Workbook(output)

		sheet = workbook.add_worksheet(u'Evaluation report')

		file_name = 'Гүйцэтгэлийн нэгтгэл'

		h1 = workbook.add_format({'bold': 1})
		h1.set_font_size(12)

		theader = workbook.add_format({'bold': 1})
		theader.set_font_size(8)
		theader.set_text_wrap()
		theader.set_font('Times new roman')
		theader.set_align('center')
		theader.set_align('vcenter')
		theader.set_border(style=1)
		theader.set_bg_color('#98FB98')

		contest_left = workbook.add_format({'num_format': '#,##0.00'})
		contest_left.set_text_wrap()
		contest_left.set_font_size(11)
		contest_left.set_font('Times new roman')
		contest_left.set_align('left')
		contest_left.set_align('vcenter')
		contest_left.set_border(style=1)
		contest_left.set_num_format('#,##0.00')

		contest_left1 = workbook.add_format({'num_format': '#,##0.00'})
		contest_left1.set_text_wrap()
		contest_left1.set_font_size(11)
		contest_left1.set_font('Times new roman')
		contest_left1.set_align('right')
		contest_left1.set_border(style=1)
		contest_left1.set_num_format('#,##0.00')

		theader3 = workbook.add_format({'bold': 1})
		theader3.set_font_size(11)
		theader3.set_font('Times new roman')
		theader3.set_align('left')
		theader3.set_align('vcenter')

		contest_center_date = workbook.add_format()
		contest_center_date.set_text_wrap()
		contest_center_date.set_font_size(9)
		contest_center_date.set_font('Times new roman')
		contest_center_date.set_align('center')
		contest_center_date.set_align('vcenter')
		contest_center_date.set_border(style=1)
		contest_center_date.set_num_format('dd/mm/yy')

		contest_center = workbook.add_format()
		contest_center.set_text_wrap()
		contest_center.set_font_size(9)
		contest_center.set_font('Times new roman')
		contest_center.set_align('center')
		contest_center.set_align('vcenter')
		contest_center.set_border(style=1)
		contest_center.set_num_format('#,##0')

		contest_center_t = workbook.add_format()
		contest_center_t.set_text_wrap()
		contest_center_t.set_font_size(9)
		contest_center_t.set_font('Times new roman')
		contest_center_t.set_align('center')
		contest_center_t.set_align('vcenter')
		contest_center_t.set_border(style=1)

		rowx=0
		sheet.merge_range(0,2,0,10, u'БАТЛАВ. ҮЙЛ АЖИЛЛАГАА ХАРИУЦСАН ЗАХИРАЛ                                                     Т.БАТЦЭЦЭГ', theader3),
		sheet.merge_range(2,2,2,13, u'ЗАХИРГАА-ХҮНИЙ НӨӨЦИЙН ХЭЛТСИЙН %s ОНЫ %s-Р САРЫН ГҮЙЦЭТГЭЛИЙН ҮНЭЛГЭЭ'%(self.year,self.month), theader3),
		rowx=3

		sheet.merge_range(rowx,0,rowx+1,0,u'№', contest_left1),
		sheet.merge_range(rowx,1,rowx+1,1,u'Овог', contest_left1),
		sheet.merge_range(rowx,2,rowx+1,2,u'Нэр', contest_left1),
		sheet.merge_range(rowx,3,rowx+1,3,u'Ажилтны код', contest_left1),
		sheet.merge_range(rowx,4,rowx+1,4,u'Албан тушаал', contest_left1),
		sheet.merge_range(rowx,5,rowx+1,5,u'Өөрийн үнэлгээ %', contest_left1),
		sheet.merge_range(rowx,6,rowx+1,6,u'Удирдлагын үнэлгээ %', contest_left1),
		# sheet.merge_range(rowx,7,rowx,8,u' сар', contest_left1),
		# sheet.write(rowx+1, 7, u'Өөрийн үнэлгээ %', contest_left1),
		# sheet.write(rowx+1, 8, u'Удирдлагын үнэлгээ %', contest_left1),
		# sheet.merge_range(rowx,9,rowx,10,u'сар', contest_left1),
		# sheet.write(rowx+1, 9, u'Өөрийн үнэлгээ %', contest_left1),
		# sheet.write(rowx+1, 10, u'Удирдлагын үнэлгээ %', contest_left1),
		# sheet.merge_range(rowx,11,rowx,12,u'улирал', contest_left1),
		# sheet.write(rowx+1, 11, u'Өөрийн үнэлгээ %', contest_left1),
		# sheet.write(rowx+1, 12, u'Удирдлагын үнэлгээ %', contest_left1),
		sheet.merge_range(rowx,7,rowx,8,u'Төлөвлөгөөт ажлын гүйцэтгэл', contest_left1),
		sheet.write(rowx+1, 7, u'Үнэлгээ', contest_left1),
		sheet.write(rowx+1, 8, u'Эзлэх хувь', contest_left1),
		sheet.merge_range(rowx,9,rowx,10,u'Багийн гүйцэтгэл', contest_left1),
		sheet.write(rowx+1, 9, u'Үнэлгээ', contest_left1),
		sheet.write(rowx+1, 10, u'Эзлэх хувь', contest_left1),
		sheet.merge_range(rowx,11,rowx+1,11,u'Явцын үнэлгээний хувь', contest_left1),
		# sheet.merge_range(rowx,12,rowx+1,12,u'Улирлын үнэлгээ', contest_left1),
		sheet.merge_range(rowx,12,rowx+1,12,u'Урамшуулал олгох %', contest_left1),
		sheet.merge_range(rowx,13,rowx+1,13,u'Тайлбар', contest_center),

		sheet.merge_range(21,4,21,4, u'ТУРШИЛТЫН хугацаанд гүйцэтгэлээс хамаарсан урамшууллыг олгохгүй.',contest_left1)

		rowx+=1

		sheet.set_column('A:A', 5)
		sheet.set_column('B:C', 12)
		sheet.set_column('D:D', 12)
		sheet.set_column('E:E', 25)
		sheet.set_column('G:G', 15)
		sheet.set_column('U:U', 35)
		sheet.set_column('L:M', 13)
		sheet.set_column('N:N', 30)


		query="""SELECT
			hr.name as hr_name,
			hr.last_name as last_name,
			hr.identification_id as ident_id,
			hd.name as hd_name,
			hj.id as hj_id,
			el.score as score,
			el.sum_amount as sum_amount,
			el.year as year,
			el.month as month,
			el.description_employee as description,
			el.id as el_id
			FROM hr_evaluation he
			LEFT JOIN hr_evaluation_line el ON el.parent_id=he.id
			LEFT JOIN hr_employee hr ON hr.id=el.employee_id
			LEFT JOIN hr_department hd ON hd.id=hr.department_id
			LEFT JOIN hr_job hj ON hj.id=hr.job_id
			WHERE hr.company_id=%s and he.year='%s' and he.month='%s'"""%(self.company_id.id,self.year,self.month)
		self.env.cr.execute(query)
		records = self.env.cr.dictfetchall()
		rowx=5
		n=1
		for record in records:
			line_pool = self.env['hr.evaluation.line.line'].search([('line_parent_id','=',record['el_id'])])
			hj_name = self.env['hr.job'].search([('id','=',record['hj_id'])]).name
			own_score = self.env['hr.evaluation.line'].search([('id','=',record['el_id'])]).own_score
			sheet.write(rowx, 0,n,contest_center)
			sheet.write(rowx, 1,record['last_name'],contest_left1)
			sheet.write(rowx, 2,record['hr_name'],contest_left1)
			sheet.write(rowx, 3,record['ident_id'],contest_left1)
			sheet.write(rowx, 4,hj_name,contest_left1)
			sheet.write(rowx, 5,own_score,contest_left1)
			sheet.write(rowx, 6,record['score'],contest_left1)
			sheet.write(rowx, 7,record['score'],contest_left1)
			sheet.write(rowx, 8,record['score']*0.7,contest_left1)
			sheet.write(rowx, 9,record['score'],contest_left1)
			sheet.write(rowx, 10,record['score']*0.3,contest_left1)
			sheet.write(rowx, 11,record['score'],contest_left1)
			sheet.write(rowx, 12,record['sum_amount'],contest_left1)
			sheet.write(rowx, 13,record['description'],contest_left)
			rowx+=1
			n+=1


		workbook.close()
		out = base64.encodebytes(output.getvalue())
		excel_id = self.env['report.excel.output'].create({'data': out, 'name': file_name+'.xlsx'})
		return {
			'name': 'Export Result',
			'view_mode': 'form',
			'res_model': 'report.excel.output',
			'view_id': False,
			'type' : 'ir.actions.act_url',
			'url': "web/content/?model=report.excel.output&id=" + str(excel_id.id) + "&filename_field=filename&download=true&field=data&filename=" + excel_id.name,
			'target': 'new',
			'nodestroy': True,
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
	


class EvalDepartmentReport(models.TransientModel):
	_name = "eval.department.report"
	_description = "Eval plan report"

	year = fields.Char('Жил')
	month = fields.Char('Сар')

	def export_report(self):
		ctx = dict(self._context)
		output = BytesIO()
		workbook = xlsxwriter.Workbook(output)

		sheet = workbook.add_worksheet(u'Evaluation report')

		file_name = 'Хэлтсүүдийн сарын нэгтгэл'

		h1 = workbook.add_format({'bold': 1})
		h1.set_font_size(12)

		theader = workbook.add_format({'bold': 1})
		theader.set_font_size(8)
		theader.set_text_wrap()
		theader.set_font('Times new roman')
		theader.set_align('center')
		theader.set_align('vcenter')
		theader.set_border(style=1)
		theader.set_bg_color('#98FB98')


		contest_left1 = workbook.add_format({'num_format': '#,##0'})
		contest_left1.set_text_wrap()
		contest_left1.set_font_size(11)
		contest_left1.set_font('Times new roman')
		contest_left1.set_align('right')
		contest_left1.set_border(style=1)
		contest_left1.set_num_format('#,##0')

		contest_left = workbook.add_format({})
		contest_left.set_text_wrap()
		contest_left.set_font_size(11)
		contest_left.set_font('Times new roman')
		contest_left.set_align('right')
		contest_left.set_border(style=1)


	

		sheet.merge_range(3, 1, 3, 8, u'%s ОНЫ %s-р САРЫН ХЭЛТСҮҮДИЙН НЭГТГЭЛ'%(self.year,self.month), h1)
		
		rowx=6
		sheet.merge_range(rowx,0,rowx+1,0,u'№', theader),
		sheet.merge_range(rowx,1,rowx+1,1,u'Хэлтэс', theader),
		sheet.merge_range(rowx,2,rowx+1,2,u'Өдөр тутмын ажлын гүйцэтгэл', theader),
		sheet.merge_range(rowx,3,rowx+1,3,u'Төлөвлөгөөт ажлын үнэлгээний дүн', theader),
		sheet.merge_range(rowx,4,rowx+1,4,u'Багийн гүйцэтгэлийн үнэлгээний дүн', theader),

		rowx+=1

		sheet.set_column('A:A', 5)
		sheet.set_column('B:B', 14)
		

		query="""SELECT
			he.kpi_daily_head as kpi_daily_head,
			he.kpi_head as kpi_head,
			he.kpi_team as kpi_team,
			hd.name as hd_name
			FROM hr_evaluation_plan he
			LEFT JOIN hr_department hd ON hd.id=he.department_id
			WHERE he.year='%s' and he.month='%s'"""%(self.year,self.month)
		self.env.cr.execute(query)
		records = self.env.cr.dictfetchall()
		rowx=8
		n=1
		for record in records:
			sheet.write(rowx, 0,n,contest_left)
			sheet.write(rowx, 1,record['hd_name'],contest_left1)
			sheet.write(rowx, 2,record['kpi_daily_head'],contest_left1)
			sheet.write(rowx, 3,record['kpi_head'],contest_left1)
			sheet.write(rowx, 4,record['kpi_team'],contest_left1)
			rowx+=1
			n+=1


		workbook.close()
		out = base64.encodebytes(output.getvalue())
		excel_id = self.env['report.excel.output'].create({'data': out, 'name': file_name+'.xlsx'})
		return {
			'name': 'Export Result',
			'view_mode': 'form',
			'res_model': 'report.excel.output',
			'view_id': False,
			'type' : 'ir.actions.act_url',
			'url': "web/content/?model=report.excel.output&id=" + str(excel_id.id) + "&filename_field=filename&download=true&field=data&filename=" + excel_id.name,
			'target': 'new',
			'nodestroy': True,
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
