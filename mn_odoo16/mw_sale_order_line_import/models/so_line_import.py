# -*- coding: utf-8 -*-
from odoo import fields, models, _
from io import BytesIO
import base64
import xlsxwriter
from tempfile import NamedTemporaryFile
import os,xlrd
from odoo.exceptions import UserError

class SaleOrderLineImport(models.Model):
    _inherit = 'sale.order'

    import_data = fields.Binary('Import excel', copy=False)

    def action_export(self):
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet(u'Гүйцэтгэл')

        header = workbook.add_format({'bold': 1})
        header.set_font_size(9)
        header.set_align('center')
        header.set_align('vcenter')
        header.set_border(style=1)
        header.set_bg_color('#9ad808')
        header.set_text_wrap()
        header.set_font_name('Arial')

        header_wrap = workbook.add_format({'bold': 1})
        header_wrap.set_text_wrap()
        header_wrap.set_font_size(11)
        header_wrap.set_align('center')
        header_wrap.set_align('vcenter')
        header_wrap.set_border(style=1)

        contest_center = workbook.add_format()
        contest_center.set_text_wrap()
        contest_center.set_font_size(9)
        contest_center.set_align('center')
        contest_center.set_align('vcenter')
        contest_center.set_border(style=1)
        contest_center.set_font_name('Arial')

        cell_format2 = workbook.add_format({
            'border': 1,
            'align': 'right',
            'font_size':9,
            'font_name': 'Arial',
            # 'text_wrap':1,
            'num_format':'#,####0'
        })

        row = 0
        last_col = 3
        worksheet.merge_range(row, 0, row, last_col, u'"'+self.name+'"'+u' Борлуулалт', header_wrap)

        row += 1
        worksheet.merge_range(row, 0, row, last_col, u'Борлуулалт импортлох загвар', contest_center)

        row += 1

        worksheet.write(row, 0, u"Бараа", header)
        worksheet.write(row, 1, u"Техник", header)
        worksheet.write(row, 2, u"Тоо хэмжээ", header)
        worksheet.write(row, 3, u"Expected date", header)
        for item in self.order_line:
            row+=1
            worksheet.write(row, 0, u'%s' %(item.product_id.default_code), cell_format2)
            if hasattr(item, 'technic_id'):
                worksheet.write(row, 1, u'%s' %(item.technic_id.vin_number), cell_format2)
            else:
                worksheet.write(row, 1, u'', cell_format2)
            worksheet.write(row, 2, item.product_uom_qty, cell_format2)
            worksheet.write(row, 3, u'%s' %(item.expected_date if item.expected_date else ''), cell_format2)

        workbook.close()

        out = base64.encodebytes(output.getvalue())
        file_name = self.name+'.xlsx'
        excel_id = self.env['report.excel.output'].create({'data': out, 'name': file_name})
        return {
             'type' : 'ir.actions.act_url',
             'url': "web/content/?model=report.excel.output&id=" + str(excel_id.id) + "&filename_field=filename&download=true&field=data&filename=" + excel_id.name,
             'target': 'new',
        }

    def action_import_line(self):
        fileobj = NamedTemporaryFile('w+b')
        fileobj.write(base64.decodebytes(self.import_data))
        fileobj.seek(0)
        if not os.path.isfile(fileobj.name):
            raise UserError(u'Алдаа',u'Мэдээллийн файлыг уншихад алдаа гарлаа.\nЗөв файл эсэхийг шалгаад дахин оролдоно уу!')
        book = xlrd.open_workbook(fileobj.name)
        
        try :
            sheet = book.sheet_by_index(0)
        except:
            raise UserError(u'Алдаа', u'Sheet -ны дугаар буруу байна.')
        nrows = sheet.nrows
        
        rowi = 2
        data = []
        r=3
        line_obj = self.env['sale.order.line']
        for item in range(r,nrows):
            row = sheet.row(item)
            try:
                default_code = str(int(row[0].value))
            except ValueError:
                default_code = str(row[0].value)
            technic_id = False
            if row[1].value:
                vin_number = row[1].value
                technic_id = self.env['technic.equipment'].search([('vin_number','=',vin_number)], limit=1)
            product_qty = row[2].value
            expected_date = row[3].value
            product_id = self.env['product.product'].search([('default_code','=',default_code)], limit=1)

            if product_id:
                obj = line_obj.create({
                    'order_id': self.id,
                    'name': product_id.name_get()[0][1],
                    'product_id': product_id.id,
                    'product_uom': product_id.uom_id.id,
                    'product_uom_qty': product_qty,
                    # 'technic_id': technic_id.id if hasattr(line_obj, 'technic_id') else False,
                    'expected_date': expected_date if expected_date else False
                })
                if hasattr(obj, 'technic_id') and technic_id:
                    obj.technic_id = technic_id.id
            else:
            	raise UserError(default_code+' кодтой бараа олдсонгүй!!!')
            