# -*- coding: utf-8 -*-

import xlsxwriter
from io import BytesIO
import base64
from odoo import api, fields, models

class EvalConsReport(models.TransientModel):
	_name = "eval.cons.report"
	_description = "Eval cons report"

	year = fields.Char('Жил')

	def export_report(self):
		ctx = dict(self._context)
		output = BytesIO()
		workbook = xlsxwriter.Workbook(output)

		sheet = workbook.add_worksheet(u'Evaluation report')

		file_name = 'Гүйцэтгэлийн нэгтгэл'

		h1 = workbook.add_format({'bold': 1})
		h1.set_font_size(12)

		contest_left = workbook.add_format({'bold': 1})
		contest_left.set_text_wrap()
		contest_left.set_font_size(11)
		contest_left.set_font('Times new roman')
		contest_left.set_align('left')
		contest_left.set_align('vcenter')
		contest_left.set_border(style=1)

		theader = workbook.add_format({'bold': 1})
		theader.set_font_size(11)
		theader.set_font('Times new roman')
		theader.set_align('left')
		theader.set_align('vcenter')
		

		fooder = workbook.add_format({'bold': 1})
		fooder.set_font_size(10)
		fooder.set_text_wrap()
		fooder.set_font('Times new roman')
		fooder.set_align('center')
		fooder.set_align('vcenter')
		fooder.set_border(style=1)

		contest_center = workbook.add_format()
		contest_center.set_text_wrap()
		contest_center.set_font_size(9)
		contest_center.set_font('Times new roman')
		contest_center.set_align('center')
		contest_center.set_align('vcenter')
		contest_center.set_border(style=1)
		contest_center.set_num_format('#,##0')
		
		sheet.set_column('A:B', 15)
		rowx=0
		sheet.merge_range(0,2,0,10, u'БАТЛАВ. ҮЙЛ АЖИЛЛАГАА ХАРИУЦСАН ЗАХИРАЛ													 Т.БАТЦЭЦЭГ', theader),
		sheet.merge_range(2,2,2,13, u'Гүйцэтгэлийн урамшууллын тайлан', theader),
		rowx=3

		sheet.merge_range(rowx,0,rowx,1,u'Огноо/Ажилтны тоо', contest_left),
		sheet.write(rowx+1,0,u'Үнэлгээ', contest_left),
		sheet.write(rowx+2,0,u'100%-аас их', contest_left),
		sheet.write(rowx+3,0,u'90%-аас 100%', contest_left),
		sheet.write(rowx+4,0,u'80%-иас 90%', contest_left),
		sheet.write(rowx+5,0,u'80%-иас бага', contest_left),
		sheet.merge_range(rowx+7,0,rowx+7,1,u'Туршилтын ажилтан', contest_left),
		sheet.merge_range(rowx+8,0,rowx+8,1,u'Гүйцэтгэлийн урамшуулал авсан', contest_left),
		sheet.merge_range(rowx+9,0,rowx+9,1,u'Гүйцэтгэлийн хувь', contest_left),
		sheet.merge_range(rowx+10,0,rowx+10,1,u'Хэлтсийн гүйцэтгэлийн үнэлгээ', contest_left),
		sheet.write(rowx+1,1,u'Үнэлгээний тайлбар', contest_left),
		sheet.write(rowx+2,1,u'Хүлээлтээс давсан буюу өндөр гүйцэтгэл', contest_left),
		sheet.write(rowx+3,1,u'Хангалттай буюу сайн гүйцэтгэл', contest_left),
		sheet.write(rowx+4,1,u'Сайжруулах шаардлагатай гүйцэтгэл', contest_left),
		sheet.write(rowx+5,1,u'Хангалтгүй муу гүйцэтгэл', contest_left),
		sheet.merge_range(rowx,2,rowx+1,2,u'1 сар', contest_left),
		sheet.merge_range(rowx,3,rowx+1,3,u'2 сар', contest_left),
		sheet.merge_range(rowx,4,rowx+1,4,u'3 сар', contest_left),
		sheet.merge_range(rowx,5,rowx+1,5,u'4 сар', contest_left),
		sheet.merge_range(rowx,6,rowx+1,6,u'5 сар', contest_left),
		sheet.merge_range(rowx,7,rowx+1,7,u'6 сар', contest_left),
		sheet.merge_range(rowx,8,rowx+1,8,u'7 сар', contest_left),
		sheet.merge_range(rowx,9,rowx+1,9,u'8 сар', contest_left),
		sheet.merge_range(rowx,10,rowx+1,10,u'9 сар', contest_left),
		sheet.merge_range(rowx,11,rowx+1,11,u'10 сар', contest_left),
		sheet.merge_range(rowx,12,rowx+1,12,u'11 сар', contest_left),
		sheet.merge_range(rowx,13,rowx+1,13,u'12 сар', contest_left),
		rowx+=1
		i=1
		col=2
		while i<=12:
			trainee=0
			score_100=0
			score_90=0
			score_80=0
			score_70=0
			score_list=[]
			con_line = self.env['hr.evaluation.cons.line'].search([('year','=',self.year),('month','=',i)])
			
			for ll in con_line:
				if ll.total_score > 100:
					score_100 +=1
				if ll.total_score <= 100 and ll.total_score > 90:
					score_90 +=1
				if ll.total_score <= 90 and ll.total_score > 80:
					score_80 +=1
				if ll.total_score <= 80:
					score_70 +=1	
				if ll.employee_id.employee_type =='trainee':
					trainee+=1
			score_list.append(score_100)	
			score_list.append(score_90)		
			score_list.append(score_80)		
			score_list.append(score_70)		
			rowx=5
			for item in score_list:
				sheet.write(rowx,col,item,contest_center)
				rowx+=1
			sheet.write(10,col,trainee,contest_center)
			con_plan = self.env['hr.evaluation.plan'].search([('year','=',self.year),('month','=',i)])
			rowl=14
			for lp in con_plan:
				sheet.merge_range(rowl,0,rowl,1,lp.department_id.name,contest_center)
				sheet.write(rowl,col,lp.kpi_team,contest_center)
				rowl+=1
			i+=1
			col+=1
			
		colx=13
		l=2
		while l <= colx:
			sheet.write_formula(9, l, '{=SUM('+self._symbol(5, l) + ': '+ self._symbol(8, l)+')}', fooder)
			sheet.write_formula(11, l,'{=SUM('+self._symbol(5, l) + ': '+ self._symbol(7, l)+')}', fooder)
			sheet.write_formula(12, l, '=' + self._symbol(11, l) + '*100/' + self._symbol(9, l), fooder)
			l+=1
			
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
