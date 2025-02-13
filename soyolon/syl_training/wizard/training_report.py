# -*- coding: utf-8 -*-

import xlsxwriter
from io import BytesIO
import base64
from odoo import api, fields, models

class TrainingRegReport(models.TransientModel):
	_name = "training.reg.report"
	_description = "Training Reg Report"

	company_id= fields.Many2one('res.company', "Компани", default=lambda self: self.env.user.company_id, required=True)
	year = fields.Char('Жил')
	month = fields.Char('Сар')
	

	def export_report(self):
		ctx = dict(self._context)
		output = BytesIO()
		workbook = xlsxwriter.Workbook(output)

		sheet = workbook.add_worksheet(u'Сургалт хөгжлийн тайлан')

		file_name = 'Сургалт хөгжлийн тайлан'

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
		contest_left.set_bg_color('#7090d2')
		

		contest_left1 = workbook.add_format({'num_format': '#,##0.00'})
		contest_left1.set_text_wrap()
		contest_left1.set_font_size(11)
		contest_left1.set_font('Times new roman')
		contest_left1.set_align('left')
		contest_left1.set_align('vcenter')
		contest_left1.set_border(style=1)
		contest_left1.set_num_format('#,##0.00')
		contest_left1.set_bg_color('#7fb4ea')

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
		contest_center_date.set_num_format('yy-mm-dd')

		contest_center = workbook.add_format()
		contest_center.set_text_wrap()
		contest_center.set_font_size(9)
		contest_center.set_font('Times new roman')
		contest_center.set_align('center')
		contest_center.set_align('vcenter')
		contest_center.set_border(style=1)
		contest_center.set_num_format('#,##0')
		

		contest_center_head = workbook.add_format({'bold': 1})
		contest_center_head.set_text_wrap()
		contest_center_head.set_font_size(9)
		contest_center_head.set_font('Times new roman')
		contest_center_head.set_align('center')
		contest_center_head.set_align('vcenter')
		contest_center_head.set_border(style=1)
		contest_center_head.set_num_format('#,##0')
		contest_center_head.set_bg_color('#7fb4ea')


		rowx=0
		sheet.merge_range(2,2,2,13, u'%s ОНЫ СУРГАЛТ ХӨГЖЛИЙН ТАЙЛАН'%(self.year), theader3),
		rowx=3

		sheet.merge_range(rowx,0,rowx+1,0,u'№', contest_left),
		sheet.merge_range(rowx,1,rowx+1,1,u'Төлөвлөгөөт сургалт', contest_left),
		sheet.merge_range(rowx,2,rowx+1,2,u'Сургалтын төрөл', contest_left),
		sheet.merge_range(rowx,3,rowx+1,3,u'Сургалт явуулах байгууллага буюу дотоот сургагч багш', contest_left),
		sheet.merge_range(rowx,4,rowx+1,4,u'Сургалтанд хамрагдах ажилтан', contest_left),
		sheet.merge_range(rowx,5,rowx+1,5,u'Сургалтын цаг/хүн', contest_left),
		sheet.merge_range(rowx,6,rowx+1,6,u'Нэгж үнэ', contest_left),
		sheet.merge_range(rowx,7,rowx+1,7,u'Сургалтын төсөв/өртөг/', contest_left),
		sheet.merge_range(rowx,8,rowx+1,8,u'Тайлбар', contest_left),
		sheet.merge_range(rowx,9,rowx+1,9,u'Сургалтыг зохион байгуулах газар', contest_left),
		sheet.merge_range(rowx,10,rowx+1,10,u'Сургалт зохион байгуулах хариуцах ажилтан', contest_left),
		sheet.merge_range(rowx,11,rowx,19,u'Гүйцэтгэл', contest_center_head),
		sheet.write(rowx+1, 11, u'Хэзээ зохион байгуулагдсан', contest_center_head),
		sheet.write(rowx+1, 12, u'Төсвийн зарцуулалт', contest_center_head),
		sheet.write(rowx+1, 13, u'Сургалтын цаг', contest_center_head),
		sheet.write(rowx+1, 14, u'Нийт хамрагдсан ажилтны тоо', contest_center_head),
		sheet.write(rowx+1, 15, u'Оролцогч овог', contest_center_head),
		sheet.write(rowx+1, 16, u'Оролцогч нэр', contest_center_head),
		sheet.write(rowx+1, 17, u'Сургалтын ирц %', contest_center_head),
		sheet.write(rowx+1, 18, u'Дараагийн үнэлгээний %', contest_center_head),
		sheet.write(rowx+1, 19, u'Тайлбар', contest_center_head),
		
		rowx+=2

		sheet.set_column('A:A', 5)
		sheet.set_column('B:C', 12)
		sheet.set_column('D:D', 12)
		sheet.set_column('E:E', 25)
		sheet.set_column('G:G', 15)
		sheet.set_column('U:U', 35)
		sheet.set_column('L:M', 13)
		sheet.set_column('N:N', 30)

		query="""SELECT
			tr.id as tr_id,
			tt.name as name,
			tpl.id as tpl_id,
			tpl.teacher as teacher,
			tpl.employee_count as employee_count,
			tpl.emp_time as emp_time,
			tpl.each_amount as each_amount,
			tpl.budget as budget,
			tpl.desc as desc,
			tpl.tr_date as tr_date,
			tr.start_date as start_date,
			tr.cost as cost,
			tr.time as time,
			tr.study_employee_count as study_employee_count,
			trl.score as score,
			trl.attendance as attendance,
			trl.reason as reason,
			hd.name as hd_name
			FROM training_plan_line tpl
			LEFT JOIN training_registration tr ON tpl.id = tr.plan_line_id
			LEFT JOIN training_registration_line trl ON trl.parent_id = tr.id
			LEFT JOIN training_plan trp ON trp.id = tpl.parent_id
			LEFT JOIN hr_department hd ON hd.id=tpl.department_id
			LEFT JOIN training_register tt ON tt.id = tpl.name_id
			WHERE trp.company_id=%s and trp.year='%s'"""%(self.company_id.id,self.year)
		self.env.cr.execute(query)
		records = self.env.cr.dictfetchall()
		n=1
		for record in records:
			if record['tr_id']:
				query2="""SELECT
					trl.score as score,
					trl.attendance as attendance,
					trl.reason as reason,
					hr.name as hr_name,
					hr.last_name as last_name
					FROM training_registration_line trl
					LEFT JOIN hr_employee hr ON hr.id = trl.t_employee_id
					WHERE trl.parent_id=%s"""%(record['tr_id'])
				self.env.cr.execute(query2)
				lines = self.env.cr.dictfetchall()
				t=0
				rowl = rowx
				types=''
				tpl = self.env['training.plan.line'].search([('id','=',record['tpl_id'])],limit=1)
				for line in lines:
					sheet.write(rowl, 15,line['last_name'],contest_center)
					sheet.write(rowl, 16,line['hr_name'],contest_center)
					sheet.write(rowl, 17,line['score'],contest_center)
					sheet.write(rowl, 18,line['attendance'],contest_center)
					sheet.write(rowl, 19,line['reason'],contest_center)
					rowl+=1
					t+=1
				if t<=1:
					sheet.write(rowx, 0,n,contest_center)
					sheet.write(rowx, 1,record['name'],contest_center)
					sheet.write(rowx, 2, dict(tpl._fields['req_type'].selection).get(tpl.req_type),contest_center)
					sheet.write(rowx, 3,record['teacher'],contest_center)
					sheet.write(rowx, 4,record['employee_count'],contest_center)
					sheet.write(rowx, 5,record['emp_time'],contest_center)
					sheet.write(rowx, 6,record['each_amount'],contest_center)
					sheet.write(rowx, 7,record['budget'],contest_center)
					sheet.write(rowx, 8,record['desc'],contest_center_date )
					sheet.write(rowx, 9,'',contest_center)
					sheet.write(rowx, 10,'',contest_center)
					sheet.write(rowx, 11,record['start_date'],contest_center_date)
					sheet.write(rowx, 12,record['cost'],contest_center)
					sheet.write(rowx, 13,record['time'],contest_center)
					sheet.write(rowx, 14,record['study_employee_count'],contest_center)
				else:
					sheet.merge_range(rowx, 0, rowx+t-1, 0, n, contest_center)
					sheet.merge_range(rowx, 1, rowx+t-1, 1,record['name'], contest_center)
					sheet.merge_range(rowx, 2, rowx+t-1, 2, dict(tpl._fields['req_type'].selection).get(tpl.req_type), contest_center)
					sheet.merge_range(rowx, 3,rowx+t-1, 3,record['teacher'],contest_center)
					sheet.merge_range(rowx, 4,rowx+t-1, 4,record['employee_count'],contest_center)
					sheet.merge_range(rowx, 5,rowx+t-1, 5,record['emp_time'],contest_center)
					sheet.merge_range(rowx, 6,rowx+t-1, 6,record['each_amount'],contest_center)
					sheet.merge_range(rowx, 7,rowx+t-1, 7,record['budget'],contest_center)
					sheet.merge_range(rowx, 8,rowx+t-1, 8,record['desc'],contest_center_date )
					sheet.merge_range(rowx, 9,rowx+t-1, 9,'',contest_center)
					sheet.merge_range(rowx, 10,rowx+t-1, 10,'',contest_center)
					sheet.merge_range(rowx, 11,rowx+t-1, 11,record['start_date'],contest_center_date)
					sheet.merge_range(rowx, 12,rowx+t-1, 12,record['cost'],contest_center)
					sheet.merge_range(rowx, 13,rowx+t-1, 13,record['time'],contest_center)
					sheet.merge_range(rowx, 14,rowx+t-1, 14,record['study_employee_count'],contest_center)
				rowx+=t
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
