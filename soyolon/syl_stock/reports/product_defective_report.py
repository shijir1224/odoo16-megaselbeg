import io
from odoo import api, fields, models, tools, _
from io import BytesIO
import base64
import xlsxwriter
from odoo.exceptions import UserError
from datetime import date
import pandas as pd

class ProductDefectiveReport(models.Model):
  # ДОГОЛДОЛТОЙ БАРАА МАТЕРИАЛЫН ТАЙЛАН
  _name = 'product.defective.report'
  _description = 'Defective products report'
  
  company_id = fields.Many2one('res.company', string='Company', default= lambda self: self.env.company.id)
  department_id = fields.Many2one('res.branch', string='Department')
  branch_ids = fields.Many2many('res.branch', string='Department', required='1')
  user_id = fields.Many2one('res.users', string='User', default= lambda self: self.env.user.id)
  date = fields.Date(string='Date', default=fields.Date.today())
  sdate = fields.Date(string='Start date', required='1')
  edate = fields.Date(string='End date', required='1')
  
  # Тайлан шүүлт
  @api.onchange('branch_ids','edate')
  def domain_branch_id(self):
    if self.branch_ids and self.sdate and self.edate:
      scrap_ids = self.env['stock.scrap'].search([('state','=','done')])
      sdate = self.sdate
      edate = self.edate
      if scrap_ids:
        for scrap_id in scrap_ids:
          scrap_id.report_branch = False
          for branch_id in self.branch_ids:
            branch = self.env['res.branch'].search([('name','=',branch_id.name)])
            if scrap_id.parent_id.branch_id == branch:
              scr_date = (scrap_id.date_done).date()
              if scr_date >= sdate:
                if scr_date <= edate:
                  scrap_id.report_branch = True
               
  # Тайланг татах
  def get_defective_reports(self):
    language = self.env.user.lang
    if language == 'mn_MN':
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
      main_format.set_num_format('#,##0.00')
      header_format = workbook.add_format()
      header_format.set_valign('vcenter')
      header_format.set_text_wrap()
      header_format.set_font_size(10)
      header_format.set_font('Times new roman')
      header_format.set_align('center')
      header_format.set_border(1)
      header_format.set_border_color('black')
      header_format.set_num_format('#,##0.00')
      footer_format = workbook.add_format()
      footer_format.set_valign('vcenter')
      footer_format.set_text_wrap()
      footer_format.set_font_size(10)
      footer_format.set_font('Times new roman')
      footer_format.set_align('left')
      footer_format.set_border(2) 
      footer_format.set_border_color('black')
      footer_format.set_num_format('#,##0.00')
      main_table_format = workbook.add_format()
      main_table_format.set_font_color('white')
      main_table_format.set_font_size(10)
      main_table_format.set_font('Times new roman')
      main_table_format.set_align('center')
      main_table_format.set_bg_color('#1B2E8B')
      main_table_format.set_num_format('#,##0.00')
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
      sheet.write(0,16, 'СБХ АШБ№', main_format)
      sheet.write(0,17, '', main_format)
      sheet.merge_range("A5:R5",'ДОГОЛДОЛТОЙ БАРАА МАТЕРИАЛЫН ТАЙЛАН',main_table_format)
      sheet.write(6,0, 'Байгууллагын нэр: '+ u'%s' %(self.company_id.name), main_format)
      sheet.write(7,0, 'Хэлтэс, нэгж: '+ u'%s' %(self.department_id.name), main_format)
      sheet.write("O8:R8", 'Тайлант хугацаа: ' + u'%s' %(self.sdate) + '-' + u'%s' %(self.edate),main_format)
      sheet.merge_range("A10:A11", 'Д/д',header_format)
      sheet.merge_range("B10:B11", 'PO дугаар',header_format)
      sheet.merge_range("C10:C11", 'Тээврийн хэрэгслийн дугаар',header_format)
      sheet.merge_range("D10:D11", 'Хариуцсан худалдан авалтын ажилтан',header_format)
      sheet.merge_range("E10:E11", 'Орлогын огноо',header_format)
      sheet.merge_range("F10:F11", 'Бэлтгэн нийлүүлэгч',header_format)
      sheet.merge_range("G10:G11", 'Барааны код',header_format)
      sheet.merge_range("H10:H11", 'Барааны нэр',header_format)
      sheet.merge_range("I10:I11", 'Хэмжих нэгж',header_format)
      sheet.merge_range("J10:J11", 'Анх худ.н авсан үнэ/НӨАТ-гүй',header_format)
      sheet.merge_range("K10:K11", 'Нэгж өртөг',header_format)
      sheet.merge_range("L10:M10", 'Татан авалт',header_format)
      sheet.write(10,11, 'Тоо ширхэг',header_format)
      sheet.write(10,12, 'Нийт өртөг',header_format)
      sheet.merge_range("N10:O10", 'Доголдол',header_format)
      sheet.write(10,13, 'Тоо ширхэг',header_format)
      sheet.write(10,14, 'Нийт өртөг',header_format)
      sheet.merge_range("P10:P11", 'Тайлбар',header_format)
      sheet.merge_range("Q10:R10", 'Шийдвэрлэсэн эсэх',header_format)
      sheet.write(10,16, 'Тийм',header_format)
      sheet.write(10,17, 'Үгүй',header_format)
      sheet.set_column(0,17, 10)
      sheet.set_row(9, 20)
      sheet.set_row(10, 20)
      row = 11
      number = 1
      # Body
      scrap_ids = self.env['stock.scrap'].search([('state','=','done')])
      price = 0.0
      unit_cost = 0.0
      po_qty = 0.0
      po_cost = 0.0
      def_qty = 0.0
      def_cost = 0.0
      for scrap_id in scrap_ids:
        if scrap_id.report_branch == True:
          price += scrap_id.price
          unit_cost += scrap_id.unit_cost
          po_qty += scrap_id.po_qty
          po_cost += scrap_id.po_cost
          def_qty += scrap_id.def_qty
          def_cost += scrap_id.def_cost
          sheet.write(row,0, number, num_format)
          sheet.write(row,1, u'%s' %(scrap_id.po_number.name or ''),header_format)
          sheet.write(row,2, u'%s' %(scrap_id.vehicle_number or ''),header_format)
          sheet.write(row,3, u'%s' %(scrap_id.po_manager.name or ''),header_format)
          if scrap_id.income_date:
            sheet.write(row,4, u'%s' %((scrap_id.income_date).date() or ''),header_format)
          else:
            sheet.write(row,4, (''),header_format)
          sheet.write(row,5, u'%s' %(scrap_id.supplier.name or ''),header_format)
          sheet.write(row,6, u'%s' %(scrap_id.product_code or ''),header_format)
          sheet.write(row,7, u'%s' %(scrap_id.product_name.name or ''),header_format)
          sheet.write(row,8, u'%s' %(scrap_id.uom_id.name or ''),header_format)
          sheet.write(row,9, scrap_id.price,header_format)
          sheet.write(row,10, scrap_id.unit_cost,header_format)
          sheet.write(row,11, scrap_id.po_qty,header_format)
          sheet.write(row,12, scrap_id.po_cost,header_format)
          sheet.write(row,13, scrap_id.def_qty,header_format)
          sheet.write(row,14, scrap_id.def_cost,header_format)
          sheet.write(row,15, u'%s' %(scrap_id.descriptions or ''),header_format)
          sheet.write(row,16, '',header_format)
          sheet.write(row,17, '',header_format)
          row += 1
          number += 1
      # Footer
      for i in range(18):
        title = ''
        if i == 5:
          title = 'НИЙТ ДҮН'
        elif i == 9:
          title = price
        elif i == 10:
          title = unit_cost
        elif i == 11:
          title = po_qty
        elif i == 12:
          title = po_cost
        elif i == 13:
          title = def_qty
        elif i == 14:
          title = def_cost
        sheet.write(row, i, title, header_format)
      row += 3
      sheet.write(row,5,'Тайлан гаргасан: ' + u'%s' %(self.user_id.name), main_format)
      row += 2
      sheet.write(row,5,'Тайлантай танилцсан: ', main_format)
      workbook.close()
      out=base64.encodebytes(output.getvalue())
      excel_id=self.env['report.excel.output'].create(
				{'data': out, 'name': 'Доголдолтой бараа материалын тайлан'})
      return {
				 'type': 'ir.actions.act_url',
				 'url': "web/content/?model=report.excel.output&id=%d&filename_field=filename&download=true&field=data&filename=%s" % (excel_id.id, excel_id.name),
				 'target': 'new',
			}



  