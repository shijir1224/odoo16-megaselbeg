# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

import logging
_logger = logging.getLogger(__name__)
from odoo.exceptions import AccessError, UserError, ValidationError
from xlsxwriter.utility import xl_rowcol_to_cell
import xlsxwriter
from io import BytesIO
import base64
import xlrd
from tempfile import NamedTemporaryFile
import os

class ReceivablePayable(models.Model):
	_name = "receivable.payable"
	_inherit = ['mail.thread']
	_description = "receivable.payable"

	def unlink(self):
		for obj in self:
			if obj.state != 'draft':
				raise UserError(_('Ноорог төлөвтэй биш бол устгах боломжгүй.'))
		return super(ReceivablePayable, self).unlink()

	@api.depends('year','month')
	def _name_write(self):
		for obj in self:
			if obj.month=='90':
				month = '10'
			elif obj.month=='91':
				month = '11'
			elif obj.month=='92':
				month = '12'
			else:
				month = obj.month

			if obj.year and obj.month:
				obj.name=obj.year+' ' + u'оны'+' '+month+' ' + u'сарын авлага'
			else:
				obj.name=''

	name= fields.Char(string=u'Нэр', index=True, readonly=True, compute=_name_write)
	year= fields.Char(method=True, store=True, type='char', string='Жил', size=8,required=True)
	month=fields.Selection([('1','1 сар'), ('2','2 сар'), ('3','3 сар'), ('4','4 сар'),
			('5','5 сар'), ('6','6 сар'), ('7','7 сар'), ('8','8 сар'), ('9','9 сар'),
			('90','10 сар'), ('91','11 сар'), ('92','12 сар')], u'Сар',required=True)
	work_location_id = fields.Many2one('hr.work.location', 'Ажлын байршил')
	line_ids= fields.One2many('receivable.payable.line', 'parent_id', 'Lines')
	company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id)
	state= fields.Selection([('draft','Draft'),
				 ('done',u'done')], 'Status',readonly=True, default = 'draft', tracking=True, copy=False)
	data = fields.Binary('Exsel file')
	file_fname = fields.Char(string='File name')
	
	def done_action(self):
		for line in self.line_ids:
			line.write({'state': 'done'})
		return self.write({'state': 'done'})

	def draft_action(self):
		for line in self.line_ids:
			line.write({'state': 'draft'})
		return self.write({'state': 'draft'})

	def receivable_payable_line(self):
		line_pool =  self.env['receivable.payable.line']
		if self.line_ids:
			self.line_ids.unlink()
		for obj in self:
			employee_lines=self.env['hr.employee'].search([('employee_type','in',('employee','trainee','contractor')),('work_location_id','=',self.work_location_id.id)])
			for employee in employee_lines:
				partner=self.env['res.partner'].search([('id','=',employee.partner_id.id)])
				if partner:
					line_data_id = line_pool.create({
						'department_id' : employee.department_id.id,
						'job_id' : employee.job_id.id,
						'employee_id' : employee.id,
						'receivable_payable' : partner.receivable_payable,
						'parent_id': obj.id,
					})

	def action_import_line(self):
		receivable_line_pool =  self.env['receivable.payable.line']
		if self.line_ids:
			self.line_ids.unlink()
		fileobj = NamedTemporaryFile('w+b')
		fileobj.write(base64.decodebytes(self.data))
		fileobj.seek(0)
		if not os.path.isfile(fileobj.name):
			raise osv.except_osv(u'Aldaa')
		book = xlrd.open_workbook(fileobj.name)
		
		try :
			sheet = book.sheet_by_index(0)
		except:
			raise osv.except_osv(u'Aldaa')
		nrows = sheet.nrows
		
		rowi = 0
		data = []
		r=0
		for item in range(2,nrows):

			row = sheet.row(item)
			default_code = row[0].value
			talon = row[3].value
			evaluation = row[4].value
			
			employee_ids = self.env['hr.employee'].search([('identification_id','=',default_code)])
			if employee_ids:
				receivable_line_id = receivable_line_pool.create({'employee_id':employee_ids.id,
							'parent_id': self.id,
							'department_id': employee_ids.department_id.id,
							'job_id': employee_ids.job_id.id,
							'receivable_payable':evaluation,
							})
			else:
				raise UserError(_('%s дугаартай ажилтны мэдээлэл байхгүй байна.')%(default_code))

	def print_receivable_payable(self,context={}):
		output = BytesIO()
		workbook = xlsxwriter.Workbook(output)
		
		sheet = workbook.add_worksheet(u'Авлага')

		file_name = 'Авлага'

		h1 = workbook.add_format({'bold': 1})
		h1.set_font_size(12)

		theader = workbook.add_format({'bold': 1})
		theader.set_font_size(9)
		theader.set_text_wrap()
		theader.set_font('Times new roman')
		theader.set_align('center')
		theader.set_align('vcenter')
		theader.set_border(style=1)
		theader.set_bg_color('#c4d79b')


		theader1 = workbook.add_format({'bold': 1})
		theader1.set_font_size(10)
		theader1.set_text_wrap()
		theader1.set_font('Times new roman')
		theader1.set_align('center')
		theader1.set_align('vcenter')

		contest_left = workbook.add_format()
		contest_left.set_text_wrap()
		contest_left.set_font_size(9)
		contest_left.set_font('Times new roman')
		contest_left.set_align('left')
		contest_left.set_align('vcenter')
		contest_left.set_border(style=1)

		rowx=0
		save_row=3
		
		# sheet.merge_range(rowx+1,0,rowx+1,10, self.year +u'  ОНЫ  '+ self.month+u' -Р САРЫН ТЭТГЭМЖ', theader1),
		
		rowx=3
		sheet.merge_range(rowx,1,rowx+3,1, u'№', theader),
		sheet.merge_range(rowx,2,rowx+3,2, u'Ажилтны код', theader),
		sheet.merge_range(rowx,3,rowx+3,3, u'Овог', theader),
		sheet.merge_range(rowx,4,rowx+3,4, u'Нэр', theader),
		sheet.merge_range(rowx,5,rowx+3,5, u'Хэлтэс', theader),
		sheet.merge_range(rowx,6,rowx+3,6, u'Албан тушаал', theader),
		sheet.merge_range(rowx,7,rowx+3,7, u'Авлага', theader),	
		
		sheet.freeze_panes(7, 6)
		rowx+=4
		
		sheet.set_column('A:A', 1)
		sheet.set_column('B:B', 4)
		sheet.set_column('C:C', 7)
		sheet.set_column('D:D', 12)
		sheet.set_column('E:E', 12)
		sheet.set_column('F:F', 20)
		sheet.set_column('G:G', 30)
		sheet.set_column('H:U', 10)
		n=1
		des=''
		status=''
		for data in self.line_ids:

			sheet.write(rowx, 1, n,contest_left)
			sheet.write(rowx, 2, data.employee_id.identification_id,contest_left)
			sheet.write(rowx, 3, data.employee_id.name,contest_left)
			sheet.write(rowx, 4, data.employee_id.last_name,contest_left)
			sheet.write(rowx, 5, data.employee_id.department_id.name,contest_left)
			sheet.write(rowx, 6, data.employee_id.job_id.name,contest_left)
			sheet.write(rowx, 7, data.receivable_payable,contest_left)

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

class ReceivablePayableLine(models.Model):
	_name = "receivable.payable.line"
	_description = "receivable payable line"

	parent_id=fields.Many2one('receivable.payable', 'Parent',ondelete='cascade')
	employee_id= fields.Many2one('hr.employee', 'Employee', required=True)
	department_id = fields.Many2one('hr.department','Хэлтэс')
	job_id = fields.Many2one('hr.job','Албан тушаал')
	receivable_payable= fields.Float('Авлага', digits=(3, 2))
	state= fields.Selection([('draft','Draft'),
				 ('done',u'done')], 'Status',readonly=True, default = 'draft', tracking=True, copy=False)

