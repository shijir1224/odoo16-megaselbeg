import io
from odoo import api, fields, models, tools, _
from io import BytesIO
import base64
import xlsxwriter
from odoo.exceptions import UserError
from datetime import date
import pandas as pd

class ProductStandartCostLocationReport(models.Model):
  #НОРМ, ЗАРЦУУЛАЛТЫН ХАРЬЦУУЛАЛТЫН ТАЙЛАН
  _name = 'standart.cost.location.report'
  _description = 'Standart and Cost of products by location report'
  
  company_id = fields.Many2one('res.company', string='Company', default= lambda self: self.env.company.id)
  types = fields.Selection([('location','Location'),('Types','Types')], string='Report type', default='location', required='1')
  department_ids = fields.Many2many('hr.department', string='Department')
  location_id = fields.Many2one('res.branch',string='Location')
  location_ids = fields.Many2many('res.branch', string='Location')
  types_id = fields.Many2one('stock.norm.types', string='Product types')
  user_id = fields.Many2one('res.users', string='User', default= lambda self: self.env.user.id)
  date = fields.Date(string='Date', default=fields.Date.today())
  sdate = fields.Date(string='Start date', required='1')
  edate = fields.Date(string='End date', required='1')
  job_ids = fields.Many2many('hr.job', string='Job position')

  # Тайлан шүүх
  @api.onchange('location_ids','department_ids','edate')
  def get_norm_lines(self):
    for i in self:
      norm_ids = self.env['stock.product.other.expense.line'].search([('parent_id.state_type','=','done'),('parent_id.norm_type','=','branch')])
      for norm_id in norm_ids:
        norm_id.check_location = False
        if norm_id.norm_id:
          for branch in i.location_ids:
            if i.department_ids:
              branchs = self.env['res.branch'].search([('name','=',branch.name)])
              for b in branchs:
                for department in i.department_ids:
                  departments = self.env['hr.department'].search([('name','=',department.name)])
                  for d in departments:
                    if b == norm_id.branch_id and d == norm_id.department_id:
                      if i.sdate and i.edate:
                        if norm_id.parent_id.date_required >= i.sdate:
                          if norm_id.parent_id.date_required <= i.edate:
                            norm_id.check_location = True
            else:
              if i.sdate and i.edate:
                if norm_id.parent_id.date_required >= i.sdate:
                  if norm_id.parent_id.date_required <= i.edate:
                    branchs = self.env['res.branch'].search([('name','=', branch.name)])
                    for b in branchs:
                      if norm_id.branch_id == b:

                        norm_id.check_location = True

  # Тайлан шүүх
  @api.onchange('job_ids','edate')
  def get_expense_lines(self):
    for i in self:
      expense_ids = self.env['stock.product.other.expense.line'].search([('parent_id.state_type','=','done'),('parent_id.norm_type','=','department')])
      for expense_id in expense_ids:
        expense_id.check_types = False
        if expense_id.norm_id:
          for job_id in i.job_ids:
            if expense_id.job_position.name == job_id.name:
              if i.sdate and i.edate:
                if expense_id.parent_id.date_required >= i.sdate:
                  if expense_id.parent_id.date_required <= i.edate:
                    expense_id.check_types = True

  # Тайланг татах
  def get_standart_cost_location_reports(self):
    language = self.env.user.lang
    if language == 'mn_MN':
      # Тайлан байршилаар
      if self.types == 'location':
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        num_format = workbook.add_format()
        num_format.set_valign('vcenter')
        num_format.set_text_wrap()
        num_format.set_font_size(10)
        num_format.set_font('Times new roman')
        num_format.set_align('center')
        num_format.set_border(1)
        num_format.set_border_color('black')
        main_format = workbook.add_format()
        main_format.set_font_size(10)
        main_format.set_font('Times new roman')
        main_format.set_align('left')
        header_format = workbook.add_format()
        header_format.set_valign('vcenter')
        header_format.set_text_wrap()
        header_format.set_font_size(10)
        header_format.set_font('Times new roman')
        header_format.set_align('center')
        header_format.set_border(1)
        header_format.set_border_color('black')
        footer_format = workbook.add_format()
        footer_format.set_valign('vcenter')
        footer_format.set_text_wrap()
        footer_format.set_font_size(10)
        footer_format.set_font('Times new roman')
        footer_format.set_align('left')
        footer_format.set_border(2) 
        footer_format.set_border_color('black')
        main_table_format = workbook.add_format()
        main_table_format.set_font_color('white')
        main_table_format.set_font_size(10)
        main_table_format.set_font('Times new roman')
        main_table_format.set_align('center')
        main_table_format.set_bg_color('#1B2E8B')
        workbook.add_format({})
        sheet = workbook.add_worksheet("Тайлан")
        # Header
        image = io.BytesIO(base64.b64decode(self.company_id.logo))
        image_width = 140.0
        image_height = 182.0
        cell_width = 64.0
        cell_height = 60.0
        x_scale = cell_width/image_width
        y_scale = cell_height/image_height
        sheet.insert_image('A1', "image.png", {'image_data': image,'x_scale': x_scale, 'y_scale': y_scale})
        sheet.write(0,12, 'СБХ АШБ№', main_format)
        sheet.write(0,13, '', main_format)
        sheet.merge_range("A5:N5",'Норм зарцуулалтын харьцуулалтын тайлан',main_table_format)
        sheet.write(6,0, 'Байгууллагын нэр: '+ u'%s' %(self.company_id.name), main_format)
        # sheet.write(7,0, 'Байршил: '+ u'%s' %(self.location_id.name), main_format)
        sheet.write("L8:N8", 'Тайлант хугацаа: ' + u'%s' %(self.sdate) + '-' + u'%s' %(self.edate), main_format)
        sheet.merge_range("A10:A11", 'Д/д',header_format)
        sheet.merge_range("B10:B11",'Байршил', header_format)
        sheet.merge_range("C10:C11",'Хэлтэс', header_format)
        sheet.merge_range("D10:D11", 'Барааны код',header_format)
        sheet.merge_range("E10:E11", 'Барааны нэр',header_format)
        sheet.merge_range("F10:F11", 'Хэмжих нэгж',header_format)
        sheet.merge_range("G10:G11", 'Нэгж өртөг',header_format)
        sheet.merge_range("H10:I10", 'Норм',header_format)
        sheet.write(10,7, 'Тоо ширхэг',header_format)
        sheet.write(10,8, 'Нийт өртөг',header_format)
        sheet.merge_range("J10:K10", 'Зарцуулалт',header_format)
        sheet.write(10,9, 'Тоо ширхэг',header_format)
        sheet.write(10,10, 'Нийт өртөг',header_format)
        sheet.merge_range("L10:M10", 'Хэтрэлт, хэмнэлт',header_format)
        sheet.write(10,11, 'Тоо ширхэг',header_format)
        sheet.write(10,12, 'Нийт өртөг',header_format)
        sheet.merge_range("N10:N11",'Шалтгаан',header_format)
        sheet.set_column(0,19, 10)
        sheet.set_row(9, 20)
        sheet.set_row(10, 20)
        row = 11
        number = 1
        # Body
        norm_ids = self.env['stock.product.other.expense.line'].search([('parent_id.state_type','=','done'),('parent_id.norm_type','=','branch')])
        unit_cost = 0.0
        no_qty = 0.0
        no_cost = 0.0
        spe_qty = 0.0
        spe_cost = 0.0
        ext_qty = 0.0
        ext_cost = 0.0
        for norm_id in norm_ids:
          if norm_id.check_location == True:
            unit_cost += norm_id.unit_cost
            no_qty += norm_id.no_qty
            no_cost += norm_id.no_cost
            spe_qty += norm_id.spe_qty
            spe_cost += norm_id.spe_cost
            ext_qty += norm_id.ext_qty
            ext_cost += norm_id.ext_cost
            sheet.write(row,0,  u'%s' %(number or ''),num_format)
            sheet.write(row,1,  u'%s' %(norm_id.branch_id.name or ''),header_format)
            sheet.write(row,2,  u'%s' %(norm_id.department_id.name or ''),header_format)
            sheet.write(row,3,  u'%s' %(norm_id.product_id.default_code or ''),header_format)
            sheet.write(row,4,  u'%s' %(norm_id.product_id.name or ''),header_format)
            sheet.write(row,5,  u'%s' %(norm_id.uom_id.name or ''),header_format)
            sheet.write(row,6, norm_id.unit_cost, header_format)
            sheet.write(row,7, norm_id.no_qty,header_format)
            sheet.write(row,8, norm_id.no_cost,header_format)
            sheet.write(row,9, norm_id.spe_qty,header_format)
            sheet.write(row,10, norm_id.spe_cost,header_format)
            sheet.write(row,11, norm_id.ext_qty,header_format)
            sheet.write(row,12, norm_id.ext_cost,header_format)
            sheet.write(row,13,u'%s' %(norm_id.reason or ''),header_format)
            row += 1
            number += 1
        # Footer
        for i in range(14):
          title = ''
          if i == 3:
            title = 'НИЙТ ДҮН'
          elif i== 6:
            title = unit_cost
          elif i == 7:
            title = no_qty
          elif i == 8:
            title = no_cost
          elif i == 9:
            title = spe_qty
          elif i == 10:
            title = spe_cost
          elif i == 11:
            title = ext_qty
          elif i == 12:
            title = ext_cost
          sheet.write(row, i, title, header_format)
        row += 3
        sheet.write(row,3,'Тайлан гаргасан: ' + u'%s' %(self.user_id.name), main_format)
        row += 2
        sheet.write(row,3,'Тайлантай танилцсан: ', main_format)
        workbook.close()
        out=base64.encodebytes(output.getvalue())
        excel_id=self.env['report.excel.output'].create(
			  	{'data': out, 'name': 'Норм зарцуулалтын харьцуулалтын тайлан'})
        return {
			  	 'type': 'ir.actions.act_url',
			  	 'url': "web/content/?model=report.excel.output&id=%d&filename_field=filename&download=true&field=data&filename=%s" % (excel_id.id, excel_id.name),
			  	 'target': 'new',
			  }
      # Тайлан барааны төрлөөр
      else:
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        num_format = workbook.add_format()
        num_format.set_valign('vcenter')
        num_format.set_text_wrap()
        num_format.set_font_size(10)
        num_format.set_font('Times new roman')
        num_format.set_align('center')
        num_format.set_border(1)
        num_format.set_border_color('black')
        main_format = workbook.add_format()
        main_format.set_font_size(10)
        main_format.set_font('Times new roman')
        main_format.set_align('left')
        header_format = workbook.add_format()
        header_format.set_valign('vcenter')
        header_format.set_text_wrap()
        header_format.set_font_size(10)
        header_format.set_font('Times new roman')
        header_format.set_align('center')
        header_format.set_border(1)
        header_format.set_border_color('black')
        footer_format = workbook.add_format()
        footer_format.set_valign('vcenter')
        footer_format.set_text_wrap()
        footer_format.set_font_size(10)
        footer_format.set_font('Times new roman')
        footer_format.set_align('left')
        footer_format.set_border(2) 
        footer_format.set_border_color('black')
        main_table_format = workbook.add_format()
        main_table_format.set_font_color('white')
        main_table_format.set_font_size(10)
        main_table_format.set_font('Times new roman')
        main_table_format.set_align('center')
        main_table_format.set_bg_color('#1B2E8B')
        workbook.add_format({})
        sheet = workbook.add_worksheet("Тайлан")
        # Header
        image = io.BytesIO(base64.b64decode(self.company_id.logo))
        image_width = 140.0
        image_height = 182.0
        cell_width = 64.0
        cell_height = 60.0
        x_scale = cell_width/image_width
        y_scale = cell_height/image_height
        sheet.insert_image('A1', "image.png", {'image_data': image,'x_scale': x_scale, 'y_scale': y_scale})
        sheet.write(0,12, 'СБХ АШБ№', main_format)
        sheet.write(0,13, '', main_format)
        sheet.merge_range("A5:N5",'Норм зарцуулалтын харьцуулалтын тайлан',main_table_format)
        sheet.write(6,0, 'Байгууллагын нэр: '+ u'%s' %(self.company_id.name), main_format)
        # sheet.write(7,0, 'Барааны төрөл: '+ u'%s' %(self.types_id.name), main_format)
        sheet.write("L8:N8", 'Тайлант хугацаа: ' + u'%s' %(self.sdate) + '-' + u'%s' %(self.edate), main_format)
        sheet.merge_range("A10:A11", 'Д/д',header_format)
        sheet.merge_range("B10:B11", 'Албан тушаал',header_format)
        sheet.merge_range("C10:C11", 'Ажилтны нэр',header_format)
        sheet.merge_range("D10:D11", 'Барааны код',header_format)
        sheet.merge_range("E10:E11", 'Барааны нэр',header_format)
        sheet.merge_range("F10:F11", 'Хэмжих нэгж',header_format)
        sheet.merge_range("G10:G11", 'Нэгж өртөг',header_format)
        sheet.merge_range("H10:I10", 'Норм',header_format)
        sheet.write(10,7, 'Тоо ширхэг',header_format)
        sheet.write(10,8, 'Нийт өртөг',header_format)
        sheet.merge_range("J10:K10", 'Зарцуулалт',header_format)
        sheet.write(10,9, 'Тоо ширхэг',header_format)
        sheet.write(10,10, 'Нийт өртөг',header_format)
        sheet.merge_range("L10:M10", 'Хэтрэлт, хэмнэлт',header_format)
        sheet.write(10,11, 'Тоо ширхэг',header_format)
        sheet.write(10,12, 'Нийт өртөг',header_format)
        sheet.merge_range("N10:N11",'Шалтгаан',header_format)
        sheet.set_column(0,17, 10)
        sheet.set_row(9, 20)
        sheet.set_row(10, 20)
        row = 11
        number = 1
        # Body
        expense_ids = self.env['stock.product.other.expense.line'].search([('parent_id.state_type','=','done'),('parent_id.norm_type','=','department')])
        unit_cost = 0.0
        no_qty = 0.0
        no_cost = 0.0
        spe_qty = 0.0
        spe_cost = 0.0
        ext_qty = 0.0
        ext_cost = 0.0
        for expense_id in expense_ids:
          if expense_id.check_types == True:
            unit_cost += expense_id.unit_cost
            no_qty += expense_id.no_qty
            no_cost += expense_id.no_cost
            spe_qty += expense_id.spe_qty
            spe_cost += expense_id.spe_cost
            ext_qty += expense_id.ext_qty
            ext_cost += expense_id.ext_cost
            sheet.write(row,0,  u'%s' %(number or ''),num_format)
            sheet.write(row,1,  u'%s' %(expense_id.job_position.name or ''),header_format)
            sheet.write(row,2,  u'%s' %(expense_id.partner_id.name or ''),header_format)
            sheet.write(row,3,  u'%s' %(expense_id.product_id.default_code or ''),header_format)
            sheet.write(row,4,  u'%s' %(expense_id.product_id.name or ''),header_format)
            sheet.write(row,5,  u'%s' %(expense_id.uom_id.name or ''),header_format)
            sheet.write(row,6, expense_id.unit_cost, header_format)
            sheet.write(row,7, expense_id.no_qty,header_format)
            sheet.write(row,8, expense_id.no_cost,header_format)
            sheet.write(row,9, expense_id.spe_qty,header_format)
            sheet.write(row,10, expense_id.spe_cost,header_format)
            sheet.write(row,11, expense_id.ext_qty,header_format)
            sheet.write(row,12, expense_id.ext_cost,header_format)
            sheet.write(row,13,u'%s' %(expense_id.reason or ''),header_format)
            row += 1
            number += 1
        # Footer
        for i in range(14):
          title = ''
          if i == 3:
            title = 'НИЙТ ДҮН'
          elif i == 6:
            title = unit_cost
          elif i == 7:
            title = no_qty
          elif i == 8:
            title = no_cost
          elif i == 9:
            title = spe_qty
          elif i == 10:
            title = spe_cost
          elif i == 11:
            title = ext_qty
          elif i == 12:
            title = ext_cost
          sheet.write(row, i, title, header_format)
        row += 3
        sheet.write(row,3,'Тайлан гаргасан: ' + u'%s' %(self.user_id.name), main_format)
        row += 2
        sheet.write(row,3,'Тайлантай танилцсан: ', main_format)
        workbook.close()
        out=base64.encodebytes(output.getvalue())
        excel_id=self.env['report.excel.output'].create(
			  	{'data': out, 'name': 'Норм зарцуулалтын харьцуулалтын тайлан'})
        return {
			  	 'type': 'ir.actions.act_url',
			  	 'url': "web/content/?model=report.excel.output&id=%d&filename_field=filename&download=true&field=data&filename=%s" % (excel_id.id, excel_id.name),
			  	 'target': 'new',
			  }