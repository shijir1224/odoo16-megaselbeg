
import xlsxwriter
from io import BytesIO
import base64
try:
	# Python 2 support
	from base64 import encodestring
except ImportError:
	# Python 3.9.0+ support
	from base64 import encodebytes as encodestring
from odoo import  models, _



class HourBalanceDynamic(models.Model):
	_inherit = "hour.balance.dynamic"

	def print_dyn_hour_balance(self,context={}):
		output = BytesIO()
		workbook = xlsxwriter.Workbook(output)
		
		file_name = 'Цагийн баланс'

		# CELL styles тодорхойлж байна
		h1 = workbook.add_format({'bold': 1})
		h1.set_font_size(11)
		h1.set_font('Times new roman')
		h1.set_align('center')
		h1.set_align('vcenter')

		left_h1 = workbook.add_format({'bold': 1})
		left_h1.set_font_size(10)
		left_h1.set_font('Times new roman')
		left_h1.set_align('left')

		h2 = workbook.add_format()
		h2.set_font_size(11)
		h2.set_font('Times new roman')
		h2.set_align('left')

		theader = workbook.add_format({'bold': 1})
		theader.set_font_size(10)
		theader.set_text_wrap()
		theader.set_font('Times new roman')
		theader.set_align('center')
		theader.set_align('vcenter')
		theader.set_border(style=1)
		theader.set_bg_color('#c4d79b')

		content_right = workbook.add_format()
		content_right.set_text_wrap()
		content_right.set_font('Times new roman')
		content_right.set_font_size(9)
		content_right.set_border(style=1)
		content_right.set_align('right')

		content_left = workbook.add_format({'num_format': '#,##0.00'})
		content_left.set_text_wrap()
		content_left.set_font('Times new roman')
		content_left.set_font_size(9)
		content_left.set_border(style=1)
		content_left.set_align('left')
		content_left.set_num_format('#,##0.00')
		
		content_left_n = workbook.add_format({})
		content_left_n.set_text_wrap()
		content_left_n.set_font('Times new roman')
		content_left_n.set_font_size(9)
		content_left_n.set_border(style=1)
		content_left_n.set_align('left')
		
		content_left_h = workbook.add_format({})
		content_left_h.set_text_wrap()
		content_left_h.set_font('Times new roman')
		content_left_h.set_font_size(11)
		content_left_h.set_align('left')
		
		center = workbook.add_format({'num_format': '#,##0.00'})
		center.set_text_wrap()
		center.set_font('Times new roman')
		center.set_font_size(9)	 
		center.set_align('right')
		center.set_border(style=1)

		center_att = workbook.add_format({'num_format': '#,##0.0'})
		center_att.set_text_wrap()
		center_att.set_font('Times new roman')
		center_att.set_font_size(9)	 
		center_att.set_align('right')
		center_att.set_border(style=1)

		

		fooder = workbook.add_format({'num_format': '#,##0.0','bold': 1})
		fooder.set_font_size(10)
		fooder.set_text_wrap()
		fooder.set_font('Times new roman')
		fooder.set_align('center')
		fooder.set_align('vcenter')
		fooder.set_border(style=1)
		fooder.set_bg_color('#c4d79b')
		sheet = workbook.add_worksheet(u'Төлөвлөгөө')
		month_code=0
		
		if self.month=='90':
			month_code=10
		if self.month=='91':
			month_code=11
		if self.month=='92':
			month_code=12 
		else:
			month_code=self.month

		sheet.merge_range(0, 1, 0, 9, u'БАТЛАВ. ЗАХИРГАА-ХҮНИЙ НӨӨЦИЙН ЗАХИРАЛ ...............................'' %s' '.' '%s' %(self.confirm_emp_id.last_name[:1],self.confirm_emp_id.name), h1)			
		sheet.merge_range(4, 1, 4, 9, u'%s ЦАГИЙН БҮРТГЭЛ %s ОНЫ %s-р САР '%(self.department_id.name,self.year,month_code), h1)

		rowx=5
		save_row=9
		sheet.merge_range(rowx, 0,rowx+2,0, u'Д/д', theader),
		sheet.merge_range(rowx,1,rowx+2,1, u'Код', theader),
		sheet.merge_range(rowx,2,rowx+2,2, u'Регитер', theader),
		sheet.merge_range(rowx,3,rowx+2,3, u'Овог', theader),
		sheet.merge_range(rowx,4,rowx+2,4, u'Нэр', theader),
		sheet.merge_range(rowx,5,rowx+2,5, u'Албан тушаал', theader),
		sheet.merge_range(rowx,6,rowx+2,6, u'АЗ өдөр', theader),
		sheet.merge_range(rowx,7,rowx+2,7, u'АЗ цаг', theader),
		sheet.merge_range(rowx,8,rowx+2,8, u'Ирцийн хувь', theader),
		sheet.merge_range(rowx,9,rowx+2,9, u'Тайлбар', theader),
	
		
		sheet.freeze_panes(8, 5)

		sheet.set_column('A:A', 4)
		sheet.set_column('B:B', 7)
		sheet.set_column('C:C', 15)
		sheet.set_column('D:D', 15)
		sheet.set_column('E:E', 20)
		sheet.set_column('F:BB', 10)

		confs = self.env['hour.balance.dynamic.configuration'].search([('company_id','=',self.company_id.id),('work_location_id','in',(self.work_location_id.id,False))])

		col=10
		for c in confs:
			sheet.merge_range(rowx,col,rowx+2,col, c.name, theader),
			col+=1
		n=1
		rowx+=3
		desc=''
		for data in self.balance_line_ids:
			if data.description:
				desc = data.description
			else:
				desc =''
			sheet.write(rowx, 0, n,content_left_n)
			sheet.write(rowx, 1, data.employee_id.identification_id,content_left)
			sheet.write(rowx, 2, data.employee_id.passport_id,content_left)
			sheet.write(rowx, 3,data.employee_id.last_name,content_left)
			sheet.write(rowx, 4,data.employee_id.name,content_left)
			sheet.write(rowx, 5,data.employee_id.job_id.name,content_left)
			sheet.write(rowx, 6,data.day_to_work_month,center_att)
			sheet.write(rowx, 7,data.hour_to_work_month,center_att)
			sheet.write(rowx, 8,data.att_procent,center_att)
			sheet.write(rowx, 9,desc,center_att)
			
			colx=10
			for line in data.balance_line_line_ids:
				sheet.write(rowx, colx,line.hour,center)
				colx+=1
		
			rowx+=1
			n+=1
			
		rowj = rowx
		sheet.merge_range(rowx, 0, rowx, 5, u'НИЙТ', fooder)
		l=6
		while l <= colx:
			sheet.write_formula(rowx, l, '{=SUM('+self._symbol(save_row-1, l) +':'+ self._symbol(rowx-1, l)+')}', fooder)
			l+=1
			
		
		sheet.merge_range(rowj+4,5,rowj+4,20,'Цагийн бүртгэл нэгтгэсэн:' + '.....................................................' ' %s '		   ' %s' '.' '%s' %(self.employee_id.job_id.name,self.employee_id.last_name[:1],self.employee_id.name), content_left_h),
	

		sheet.merge_range(rowj+6,5,rowj+6,20,'Цагийн бүртгэл хянасан:' + '.....................................................' ' %s '		   ' %s' '.' '%s' %(self.h_emp_id.job_id.name,self.h_emp_id.last_name[:1],self.h_emp_id.name), content_left_h),
	
		
		
		workbook.close()
		out = encodestring(output.getvalue())
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