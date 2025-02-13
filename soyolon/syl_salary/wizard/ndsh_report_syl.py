# -*- coding: utf-8 -*-

import time
import xlsxwriter
from odoo.exceptions import UserError, AccessError
from io import BytesIO
import base64
from datetime import datetime, timedelta

from odoo import tools
from odoo import api, fields, models
from odoo.tools.misc import get_lang
class NdshReportSYL(models.TransientModel):
	_name = "ndsh.report.syl"
	_description = "ndsh report"

	salary_id= fields.Many2one('salary.order', 'Salary',  domain=[('type','=','final')])
	company_id= fields.Many2one('res.company', "Компани",required=True)
	year= fields.Char(method=True, store=True, type='char', string='Жил', size=8,required=True)
	month=fields.Selection([('1','1 сар'), ('2','2 сар'), ('3','3 сар'), ('4','4 сар'),
			('5','5 сар'), ('6','6 сар'), ('7','7 сар'), ('8','8 сар'), ('9','9 сар'),
			('90','10 сар'), ('91','11 сар'), ('92','12 сар')], u'Сар',required=True)
	date= fields.Date('Огноо')

	
	def export_report(self):
		ctx = dict(self._context)
		output = BytesIO()
		workbook = xlsxwriter.Workbook(output)

		sheet = workbook.add_worksheet(u'Sheet1')
		file_name = 'НДШ тайлан'

		h1 = workbook.add_format({'bold': 1})
		h1.set_font_size(12)

		theader = workbook.add_format({'bold': 1})
		theader.set_font_size(9)
		theader.set_text_wrap()
		theader.set_font('Times new roman')
		theader.set_align('center')
		theader.set_align('vcenter')
		theader.set_border(style=1)

		theader1 = workbook.add_format({'bold': 1})
		theader1.set_font_size(10)
		theader1.set_font('Times new roman')
		theader1.set_align('center')
		theader1.set_align('vcenter')

		theader2 = workbook.add_format({'bold': 1})
		theader2.set_font_size(9)
		theader2.set_font('Times new roman')
		theader2.set_align('right')
		theader2.set_align('vcenter')

		theader3 = workbook.add_format({'bold': 1})
		theader3.set_font_size(9)
		theader3.set_font('Times new roman')
		theader3.set_align('left')
		theader3.set_align('vcenter')

		header = workbook.add_format({'bold': 1})
		header.set_font_size(9)
		header.set_font('Times new roman')
		header.set_align('center')
		header.set_align('vcenter')
		header.set_border(style=1)
		header.set_bg_color('#A8C3F4')

		header_wrap = workbook.add_format({'bold': 1})
		header_wrap.set_text_wrap()
		header_wrap.set_font_size(9)
		header_wrap.set_align('center')
		header_wrap.set_align('vcenter')
		header_wrap.set_border(style=1)
		header_wrap.set_bg_color('#6495ED')

		footer = workbook.add_format({'bold': 1})
		footer.set_text_wrap()
		footer.set_font_size(9)
		footer.set_align('right')
		footer.set_align('vcenter')
		footer.set_border(style=1)
		footer.set_bg_color('#6495ED')
		footer.set_num_format('#,##0.00')

		contest_right = workbook.add_format()
		contest_right.set_text_wrap()
		contest_right.set_font_size(9)
		contest_right.set_font('Times new roman')
		contest_right.set_align('right')
		contest_right.set_align('vcenter')
		contest_right.set_border(style=1)
		contest_right.set_num_format('#,##0')


		contest_right_red = workbook.add_format()
		contest_right_red.set_text_wrap()
		contest_right_red.set_font_size(9)
		contest_right_red.set_font('Times new roman')
		contest_right_red.set_align('right')
		contest_right_red.set_align('vcenter')
		contest_right_red.set_font_color('red')
		contest_right_red.set_num_format('#,##0.00')

		contest_right_green = workbook.add_format()
		contest_right_green.set_text_wrap()
		contest_right_green.set_font_size(9)
		contest_right_green.set_align('right')
		contest_right_green.set_align('vcenter')
		contest_right_green.set_font_color('green')
		contest_right_green.set_num_format('#,##0.00')

		contest_left = workbook.add_format()
		contest_left.set_text_wrap()
		contest_left.set_font_size(9)
		contest_left.set_font('Times new roman')
		contest_left.set_align('left')
		contest_left.set_align('vcenter')
		contest_left.set_border(style=1)
		contest_left.set_num_format('#,##0.00')

		contest_left0 = workbook.add_format()
		contest_left0.set_font_size(9)
		contest_left0.set_align('left')
		contest_left0.set_align('vcenter')

		contest_center = workbook.add_format()
		contest_center.set_text_wrap()
		contest_center.set_font_size(9)
		contest_center.set_font('Times new roman')
		contest_center.set_align('center')
		contest_center.set_align('vcenter')
		contest_center.set_border(style=1)

		categ_name = workbook.add_format({'bold': 1})
		categ_name.set_font_size(9)
		categ_name.set_align('left')
		categ_name.set_align('vcenter')
		categ_name.set_border(style=1)
		categ_name.set_bg_color('#B9CFF7')

		categ_right = workbook.add_format({'bold': 1})
		categ_right.set_font_size(9)
		categ_right.set_align('right')
		categ_right.set_align('vcenter')
		categ_right.set_border(style=1)
		categ_right.set_bg_color('#B9CFF7')
		categ_right.set_num_format('#,##0.00')

		# GET warehouse loc ids
		rowx=0
		# sheet.write(rowx,0, 'ovog', theader),
		# sheet.write(rowx,1, 'name', theader),
		# sheet.write(rowx,2, 'register', theader),
		# sheet.write(rowx,3, 'nd_dugaar', theader),
		# sheet.write(rowx,4, 'emd_dugaar', theader),
		# sheet.write(rowx,5, 'undsen_nemegdel_tsalin', theader),
		# sheet.write(rowx,6, 'shagnalt_tsalin', theader),
		# sheet.write(rowx,7, 'busad_nemegdel_tsalin', theader),
		# sheet.write(rowx,8, 'hool_unaa', theader),
		# sheet.write(rowx,9, 'tulee_nuurs', theader),
		# sheet.write(rowx,10, 'niit', theader),		
		# sheet.write(rowx,11, 'daat_turul', theader),
		# sheet.write(rowx,12, 'hyazgaar', theader),
		# sheet.write(rowx,13, 'countryid', theader),
		# sheet.write(rowx,14, 'occ_code', theader),
		# sheet.write(rowx,15, 'loc_code', theader),
		# sheet.write(rowx,16, 'cellphone', theader),		
		# sheet.write(rowx,17, 'email', theader),

		sheet.write(rowx,0, 'Регистрийн дугаар', theader),
		sheet.write(rowx,1, 'Ургийн овог', theader),
		sheet.write(rowx,2, 'Эцэг/эхийн нэр', theader),
		sheet.write(rowx,3, 'Нэр', theader),
		sheet.write(rowx,4, 'Даатгуулагчийн төрөл', theader),
		sheet.write(rowx,5, 'Ажил мэргэжлийн ангилал', theader),
		sheet.write(rowx,6, 'Хөдөлмөрийн хөлс түүнтэй адилтгах орлого', theader),
		sheet.write(rowx,7, 'Үндсэн ба нэмэгдэл цалин', theader),
		sheet.write(rowx,8, 'Шагналт цалин', theader),
		sheet.write(rowx,9, 'Бусад нэмэгдэл цалин', theader),
		sheet.write(rowx,10, 'Хоол унааны хөлс', theader),		
		sheet.write(rowx,11, 'Түлээ нүүрсний үнийн хөнгөлөлт', theader),
		sheet.write(rowx,12, 'Иргэншил', theader),
		sheet.write(rowx,13, 'Харилцах утасны дугаар', theader),
		sheet.write(rowx,14, 'Цахим шуудангийн хаяг', theader),
		# sheet.write(rowx,15, 'Хэлтэс', theader),
		# sheet.write(rowx,16, 'НДШ', theader),
		# sheet.write(rowx,17, 'БНДШ хувь', theader),
		# sheet.write(rowx,18, 'БНДШ', theader),
		# sheet.write(rowx,19, 'Нийт НДШ', theader),
																	
		# rowx+=1
		
		sheet.set_column('A:A', 15)
		sheet.set_column('B:B', 15)
		sheet.set_column('C:C', 15)
		sheet.set_column('D:D', 15)
		sheet.set_column('G:G', 11)
		sheet.set_column('O:O', 25)
		sheet.set_column('P:P', 35)
		lang = self.env.user.lang or get_lang(self.env).code
		query="""SELECT 
			COALESCE(he.name->> '%s', he.name->>'en_US') as name,
			--he.name as name,
			he.last_name as last_name,
			he.family_name as family_name,
			he.passport_id as register,
			line.basic as wage,
			(select coalesce(sum(amount),0) from salary_order_line_line ll left join hr_allounce_deduction_category cat ON cat.id=ll.category_id where ll.order_line_id1=line.id and cat.code='TOOTS') as bodogdson,
			(select coalesce(sum(amount),0) from salary_order_line_line ll left join hr_allounce_deduction_category cat ON cat.id=ll.category_id where ll.order_line_id1=line.id and cat.code='SHI') as shi,
			(select coalesce(sum(amount),0) from salary_order_line_line ll left join hr_allounce_deduction_category cat ON cat.id=ll.category_id where ll.order_line_id1=line.id and cat.code='BSHI') as bshi,
			he.id as he_id,
			he.work_phone as work_phone,
			he.private_email as private_email,
			line.insured_type_id as insured_type_id,
			line.pitt_procent as pitt_procent
			FROM salary_order so
			LEFT JOIN salary_order_line line ON line.order_id=so.id
			LEFT JOIN hr_employee he ON he.id=line.employee_id
			WHERE so.year='%s' and so.month='%s' and so.type='final' and so.company_id=%s
			ORDER BY he.name"""%(lang,self.year,self.month,self.company_id.id)
		self.env.cr.execute(query)
		records = self.env.cr.dictfetchall()
		rowx+=1
		countryid=0
		code={}
		for record in records:
			cont_id = self.env['hr.contract'].search([('employee_id','=',record['he_id']),('active','=',True)],limit=1)
			employee_id = self.env['hr.employee'].search([('id','=',record['he_id'])],limit=1)
			insured_type_id = self.env['insured.type'].search([('id','=',record['insured_type_id'])],limit=1)
			# if record['bodogdson']>0:
			sheet.write(rowx, 0, record['register'],contest_left)
			sheet.write(rowx, 1,record['family_name'],contest_left)
			sheet.write(rowx, 2,record['last_name'],contest_left)
			sheet.write(rowx, 3,record['name'],contest_left)
			sheet.write(rowx, 4,cont_id.insured_type_id.code,contest_left)
			sheet.write(rowx, 5,employee_id.job_id.job_conf.name,contest_left)
			sheet.write(rowx, 6,record['bodogdson'],contest_left)
			sheet.write(rowx, 7,"0",contest_left)
			sheet.write(rowx, 8,"0",contest_left)
			sheet.write(rowx, 9,"0",contest_left)
			sheet.write(rowx, 10,"0",contest_left)
			sheet.write(rowx, 11,"0",contest_left)
			sheet.write(rowx, 12,employee_id.country_id.name,contest_left)
			sheet.write(rowx, 13,employee_id.work_phone,contest_right)
			sheet.write(rowx, 14,employee_id.work_email,contest_left)
			# sheet.write(rowx, 15,employee_id.department_id.name,contest_left)
			# sheet.write(rowx, 16,record['shi'],contest_left)
			# if insured_type_id.code=='40001' or insured_type_id.code=='02001':
			# 	sheet.write(rowx, 17,insured_type_id.o_shi_procent,contest_left)
			# else:
			# 	sheet.write(rowx, 17,insured_type_id.o_shi_procent+employee_id.job_id.job_conf.percent,contest_left)
			# sheet.write(rowx, 18,record['bshi'],contest_left)
			# sheet.write(rowx, 19,record['shi']+record['bshi'],contest_left)

			rowx+=1
			# sheet.write(rowx, 0, record['last_name'],contest_left)
			# sheet.write(rowx, 1,record['name'],contest_left)
			# sheet.write(rowx, 2,record['register'],contest_left)
			# sheet.write(rowx, 3,'0000000',contest_left)
			# sheet.write(rowx, 4,'0000000',contest_left)
			# sheet.write(rowx, 5,round(record['bodogdson']),contest_left)
			# sheet.write(rowx, 6,"0",contest_left)
			# sheet.write(rowx, 7,"0",contest_left)
			# sheet.write(rowx, 8,"0",contest_left)
			# sheet.write(rowx, 9,"0",contest_left)
			# sheet.write(rowx, 10,record['bodogdson'],contest_left)
			# sheet.write(rowx, 11,cont_id.insured_type_id.code,contest_left)
			# sheet.write(rowx, 12,"1",contest_left)
			# sheet.write(rowx, 13,'1',contest_right)
			# sheet.write(rowx, 14,'9621',contest_left)
			# sheet.write(rowx, 15,"1122",contest_left)
			# sheet.write(rowx, 16,record['work_phone'],contest_left)
			# sheet.write(rowx, 17,record['private_email'],contest_right)
			

		query1="""SELECT  it.code as code,
			it.id as it_id,
			COALESCE(he.name->> '%s', he.name->>'en_US') as name,
			--he.name as name,
			he.last_name as last_name,
			he.family_name as family_name,
			he.passport_id as register,
			hc.id as hc_id,
			he.id as he_id,
			he.work_phone as work_phone,
			he.private_email as private_email
			FROM hr_contract hc
			LEFT JOIN insured_type it ON hc.insured_type_id=it.id
			LEFT JOIN hr_employee he ON he.id=hc.employee_id
			WHERE it.code in ('06002','17002','21002','39012','39002','20002') 
				AND hc.active = True 
				AND he.company_id='%s'
			ORDER BY he.name"""%(lang,self.company_id.id)
		self.env.cr.execute(query1)
		recs = self.env.cr.dictfetchall()
		for rec in recs:
			employee_id = self.env['hr.employee'].search([('id','=',rec['he_id'])],limit=1)
			insured_type_id = self.env['insured.type'].search([('id','=',rec['it_id'])],limit=1)
			sheet.write(rowx, 0, rec['register'],contest_left)
			sheet.write(rowx, 1,rec['family_name'],contest_left)
			sheet.write(rowx, 2,rec['last_name'],contest_left)
			sheet.write(rowx, 3,rec['name'],contest_left)
			sheet.write(rowx, 4,insured_type_id.code,contest_left)
			sheet.write(rowx, 5,employee_id.job_id.job_conf.name,contest_left)
			sheet.write(rowx, 6,"660000",contest_left)
			sheet.write(rowx, 7,"0",contest_left)
			sheet.write(rowx, 8,"0",contest_left)
			sheet.write(rowx, 9,"0",contest_left)
			sheet.write(rowx, 10,"0",contest_left)
			sheet.write(rowx, 11,"0",contest_left)
			sheet.write(rowx, 12,employee_id.country_id.name,contest_left)
			sheet.write(rowx, 13,employee_id.work_phone,contest_right)
			sheet.write(rowx, 14,employee_id.work_email,contest_left)
			# sheet.write(rowx, 15,employee_id.department_id.name,contest_left)
			rowx+=1

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



