# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, tools, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import date, datetime, timedelta
from io import BytesIO
import base64
import xlsxwriter
from xlsxwriter.utility import xl_rowcol_to_cell
from tempfile import NamedTemporaryFile
import os,xlrd

class miningSurveyorMeasurementImport(models.TransientModel):
    _name = 'mining.surveyor.measurement.import'
    _decribtion = 'Mining Surveyor Measurement import'
    
    desc = fields.Text(string='Тайлбар' , readonly=True, default='Файл бэлдэх Экселийн ХОЁР ДАХЬ мөрөөс эхлэнэ 1.Техник , 2.Эхлэх Огноо, 3.Дуусах Огноо , 4.Салбар , 5.Материал , 6.Тоо хэмжээ')
    import_data_ids = fields.Many2many('ir.attachment', string='Импортлох эксел')
    
    def action_import(self):
        if not self.import_data_ids:
            raise UserError('Оруулах эксэлээ UPLOAD хийнэ үү ')

        fileobj = NamedTemporaryFile('w+')
        import_data = self.import_data_ids[0].datas
        fileobj.write(base64.decodestring(import_data))
        fileobj.seek(0)
        if not os.path.isfile(fileobj.name):
            raise osv.except_osv(u'Алдаа',u'Мэдээллийн файлыг уншихад алдаа гарлаа.\nЗөв файл эсэхийг шалгаад дахин оролдоно уу!')
        book = xlrd.open_workbook(fileobj.name)
        
        try :
            sheet = book.sheet_by_index(0)
        except:
            raise osv.except_osv(u'Алдаа', u'Sheet -ны дугаар буруу байна.')
        nrows = sheet.nrows
        
        rowi = 1
        m_obj = self.env['mining.surveyor.measurement']
        for item in range(rowi,nrows):
            row = sheet.row(item)
            technic_name = row[0].value
            start = row[1].value
            end = row[2].value
            branch = row[3].value
            material = row[4].value
            qty = row[5].value
            tech_id = self.env['technic.equipment'].search(['|',('park_number','=',technic_name),('name','=',technic_name)], limit=1)
            mater_id = self.env['mining.material'].search([('name','=',material)], limit=1)
            branch_id = self.env['res.branch'].search([('name','=',branch)], limit=1)
            print('tech_id',tech_id,'mater_id',mater_id,'branch_id',branch_id)
            if tech_id and mater_id and branch_id:
                m_id = m_obj.create({
                    'date_start': start,
                    'date_end': end,
                    'excavator_id': tech_id.id,
                    'branch_id': branch_id.id,
                    'line_ids': [(0, 0, {
                        'material_id': mater_id.id,
                        'amount_by_measurement': qty,
                        'is_production': True,
                    })]
                    })
                m_id.confirm()
            else:
            	raise UserError(u'%s  техникийн нэрээ оруулна уу'%(technic_name))
