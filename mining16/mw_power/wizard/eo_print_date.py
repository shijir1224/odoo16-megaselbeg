# -*- coding: utf-8 -*-

from odoo import api, models, fields
import xlrd, os
from tempfile import NamedTemporaryFile
import base64
import xlsxwriter
from io import BytesIO

from calendar import monthrange
from odoo.exceptions import UserError

class eo_print_wizard(models.TransientModel):
    _inherit = 'eo.print.wizard'
    
    def export_excel_date(self):
        objs = self.env['power.notes'].search([('date','>=',self.date_start),('date','<=',self.date_end)])
        if objs:
            output = BytesIO()
            workbook = xlsxwriter.Workbook(output)
            file_name = str(self.date_start)+'-'+str(self.date_end)+'.xlsx'

            h1 = workbook.add_format({'bold': 1})
            h1.set_font_size(12)

            header_wrap = workbook.add_format({'bold': 1})
            header_wrap.set_text_wrap()
            header_wrap.set_font_size(9)
            header_wrap.set_align('center')
            header_wrap.set_align('vcenter')
            header_wrap.set_border(style=1)
            header_wrap.set_bg_color('#E9A227')

            number_right = workbook.add_format()
            number_right.set_text_wrap()
            number_right.set_font_size(9)
            number_right.set_align('right')
            number_right.set_align('vcenter')
            number_right.set_border(style=1)

            contest_right = workbook.add_format()
            contest_right.set_text_wrap()
            contest_right.set_font_size(9)
            contest_right.set_align('right')
            contest_right.set_align('vcenter')
            contest_right.set_border(style=1)
            contest_right.set_num_format('#,##0.00')

            contest_left = workbook.add_format()
            contest_left.set_text_wrap()
            contest_left.set_font_size(9)
            contest_left.set_align('left')
            contest_left.set_align('vcenter')
            contest_left.set_border(style=1)

            contest_center = workbook.add_format()
            contest_center.set_text_wrap()
            contest_center.set_font_size(9)
            contest_center.set_align('center')
            contest_center.set_align('vcenter')
            contest_center.set_border(style=1)

            sub_total = workbook.add_format({'bold': 1})
            sub_total.set_text_wrap()
            sub_total.set_font_size(9)
            sub_total.set_align('center')
            sub_total.set_align('vcenter')
            sub_total.set_border(style=1)
            sub_total.set_bg_color('#c6e0b4')

            sub_total_sub = workbook.add_format()
            sub_total_sub.set_text_wrap()
            sub_total_sub.set_font_size(9)
            sub_total_sub.set_align('center')
            sub_total_sub.set_align('vcenter')
            sub_total_sub.set_border(style=1)
            sub_total_sub.set_bg_color('#c6e0b4')

            worksheet1 = workbook.add_worksheet(u'1.Тасралтын мэдээлэл')
            worksheet2 = workbook.add_worksheet(u'2.Гадны байгууллагын захиалгат таслалт /ААН-р хийгдсэн/')
            worksheet3 = workbook.add_worksheet(u'3.Төлөвлөгөөт таслалтын ажил /ААН-р хийгдсэн/')
            worksheet4 = workbook.add_worksheet(u'4.Дуудлагаар хийгдсэн ажил ')
            worksheet5 = workbook.add_worksheet(u'5.Өдөр тутмын шуурхайд төлөвлөгдсөн ажил')
            worksheet6 = workbook.add_worksheet(u'6.Экскаваторын зогсолт')
            
            row = 1
            worksheet1.merge_range(row, 0, row, 20, u"1.Тасралтын мэдээлэл", sub_total)
            row += 1
            col = 0
            worksheet1.merge_range(row, col, row+1, col, 'д/д', sub_total_sub)
            worksheet1.merge_range(row, col+1, row+1, col+1, 'Станц', sub_total_sub)
            worksheet1.merge_range(row, col+2, row+1, col+2, 'Хүчдлийн түвшин /В/', sub_total_sub)
            worksheet1.merge_range(row, col+3, row+1, col+3, 'Фидер', sub_total_sub)
            worksheet1.merge_range(row, col+4, row+1, col+4, 'Ажилласан хамгаалалт', sub_total_sub)
            worksheet1.merge_range(row, col+5, row+1, col+5, 'Тасарсан үеийн номинал гүйдэл /А/', sub_total_sub)
            worksheet1.merge_range(row, col+6, row+1, col+6, 'Огноо', sub_total_sub)
            col+=1
            worksheet1.merge_range(row, col+6, row+1, col+6, 'Ээлж', sub_total_sub)
            worksheet1.merge_range(row, col+7, row+1, col+7, 'Тасарсан хугацаа', sub_total_sub)
            worksheet1.merge_range(row, col+8, row+1, col+8, 'Залгасан хугацаа', sub_total_sub)
            worksheet1.merge_range(row, col+9, row+1, col+9, 'Тасралтын хугацаа /цаг/', sub_total_sub)
            worksheet1.merge_range(row, col+10, row+1, col+10, 'Дутуу эрчим хүч /кВт.ц/', sub_total_sub)
            worksheet1.merge_range(row, col+11, row+1, col+11, 'Тасралтын Ангилал', sub_total_sub)
            worksheet1.merge_range(row, col+12, row+1, col+12, 'Шалтгаан', sub_total_sub)
            worksheet1.merge_range(row, col+13, row+1, col+13, 'Авсан арга хэмжээ', sub_total_sub)
            worksheet1.merge_range(row, col+14, row+1, col+14, 'Ажилласан бригад', sub_total_sub)
            worksheet1.merge_range(row, col+15, row+1, col+15, 'Бүртгэгдсэн дис', sub_total_sub)
            worksheet1.merge_range(row, col+16, row, col+18, 'Ашигласан Бараа материал', sub_total_sub)
            worksheet1.write(row+1, col+16, 'марк', sub_total_sub)
            worksheet1.write(row+1, col+17, 'тоо хэмжээ', sub_total_sub)
            worksheet1.write(row+1, col+18, 'хэмжих нэгж', sub_total_sub)
            worksheet1.merge_range(row, col+19, row+1, col+19, 'Тайлбар', sub_total_sub)
            row += 2
            number = 1
            
            wos = objs.mapped('down_ids')
            for line in wos:
                col = 0
                worksheet1.write(row, col, number, contest_center)
                worksheet1.write(row, col+1, line.station_id.name or '', contest_center)
                worksheet1.write(row, col+2, line.level_id.name or '', contest_center)
                worksheet1.write(row, col+3, line.fider_id.name or '', contest_center)
                worksheet1.write(row, col+4, line.work_secure_id.name or '', contest_center)
                worksheet1.write(row, col+5, line.down_nominal or '', contest_center)
                worksheet1.write(row, col+6, str(line.notes_id.date) or '', contest_center)
                col+=1
                str_val = u'%s'%(dict(self.env['power.notes']._fields['shift'].selection).get(line.notes_id.shift) or '')
                worksheet1.write(row, col+6, str_val, contest_center)
                str_val = u'%s'%(self.env['ir.qweb.field.float_time'].value_to_html(line.down_time, {}) or '')
                worksheet1.write(row, col+7, str_val, contest_center)
                str_val = u'%s'%(self.env['ir.qweb.field.float_time'].value_to_html(line.plug_time, {}) or '')
                worksheet1.write(row, col+8, str_val, contest_center)
                str_val = u'%s'%(self.env['ir.qweb.field.float_time'].value_to_html(line.break_time, {}) or '')
                worksheet1.write(row, col+9, str_val, contest_center)
                worksheet1.write(row, col+10, line.incomplete_power or '', contest_center)
                worksheet1.write(row, col+11, line.down_type_id.name or '', contest_center)
                worksheet1.write(row, col+12, line.cause or '', contest_center)
                worksheet1.write(row, col+13, line.actions_taken or '', contest_center)
                worksheet1.write(row, col+14, ', '.join(line.work_user_ids.mapped('name')) or '', contest_center)
                worksheet1.write(row, col+15, str(line.notes_id.dispatcher_id.name) or '', contest_center)
                worksheet1.write(row, col+16, '', contest_center)
                worksheet1.write(row, col+17, '', contest_center)
                worksheet1.write(row, col+18, '', contest_center)
                worksheet1.write(row, col+19, line.description or '', contest_center)
                row += 1
                number += 1

            row = 1
            worksheet2.merge_range(row, 0, row, 17, u"2. Гадны байгууллагын захиалгат таслалт /ААН-р хийгдсэн/", sub_total)
            row += 1
            col = 0
            worksheet2.write(row, col, 'д/д', sub_total_sub)
            worksheet2.write(row, col+1, 'Захиалга өгсөн байгууллга, алба хэлтэс', sub_total_sub)
            worksheet2.write(row, col+2, 'ААН-ны Наряд шийдвэрийн дугаар', sub_total_sub)
            worksheet2.write(row, col+3, 'Захиалга өгсөн хүний нэр албан тушаал', sub_total_sub)
            worksheet2.write(row, col+4, 'Ангилал', sub_total_sub)
            worksheet2.write(row, col+5, 'Захиалгын утга', sub_total_sub)
            worksheet2.write(row, col+6, 'Захиалга баталсан албан тушаалтан', sub_total_sub)
            worksheet2.write(row, col+7, 'Огноо', sub_total_sub)
            col += 1
            worksheet2.write(row, col+7, 'Ээлж', sub_total_sub)
            worksheet2.write(row, col+8, 'Таслах үеийн ачаалал /А/', sub_total_sub)
            worksheet2.write(row, col+9, 'Тасалсан хугацаа', sub_total_sub)
            worksheet2.write(row, col+10, 'Залгасан хугацаа', sub_total_sub)
            worksheet2.write(row, col+11, 'Тасралтын хугацаа /цаг/', sub_total_sub)
            worksheet2.write(row, col+12, 'Дутуу эрчим хүч /кВт.ц/', sub_total_sub)
            worksheet2.write(row, col+13, 'Ажилласан баригад', sub_total_sub)
            worksheet2.write(row, col+14, 'Бүртгэсэн дис', sub_total_sub)
            worksheet2.write(row, col+15, 'Ашигласан Бараа материал', sub_total_sub)
            worksheet2.write(row, col+16, 'Тайлбар', sub_total_sub)
            row += 1
            number = 1
            
            wos = objs.mapped('down_order_ids')
            for line in wos:
                col = 0
                worksheet2.write(row, col, number, contest_center)
                worksheet2.write(row, col+1, line.down_partner_id.name or '', contest_center)
                worksheet2.write(row, col+2, line.aan_naryad or '', contest_center)
                worksheet2.write(row, col+3, line.partner_job_position or '', contest_center)
                worksheet2.write(row, col+4, '', contest_center)
                worksheet2.write(row, col+5, line.partner_notes or '', contest_center)
                worksheet2.write(row, col+6, line.confirm_user_id.name or '', contest_center)
                worksheet2.write(row, col+7, str(line.notes_order_id.date) or '', contest_center)
                col += 1
                str_val = u'%s'%(dict(self.env['power.notes']._fields['shift'].selection).get(line.notes_order_id.shift) or '')
                worksheet2.write(row, col+7, str_val, contest_center)
                worksheet2.write(row, col+8, line.down_nominal or '', contest_center)
                str_val = u'%s'%(self.env['ir.qweb.field.float_time'].value_to_html(line.down_time, {}) or '')
                worksheet2.write(row, col+9, str_val, contest_center)
                str_val = u'%s'%(self.env['ir.qweb.field.float_time'].value_to_html(line.plug_time, {}) or '')
                worksheet2.write(row, col+10, str_val, contest_center)
                str_val = u'%s'%(self.env['ir.qweb.field.float_time'].value_to_html(line.break_time, {}) or '')
                worksheet2.write(row, col+11, str_val, contest_center)
                worksheet2.write(row, col+12, line.incomplete_power or '', contest_center)
                worksheet2.write(row, col+13, ', '.join(line.work_user_ids.mapped('name')) or '', contest_center)
                worksheet2.write(row, col+14, str(line.notes_order_id.dispatcher_id.name) or '', contest_center)
                worksheet2.write(row, col+15, '', contest_center)
                worksheet2.write(row, col+16, line.description or '', contest_center)
                row += 1
                number += 1

            row = 1
            worksheet3.merge_range(row, 0, row, 19, u"3.Төлөвлөгөөт таслалтын ажил /ААН-р хийгдсэн/", sub_total)
            row += 1
            col = 0
            worksheet3.merge_range(row, col, row+1, col, 'д/д', sub_total_sub)
            worksheet3.merge_range(row, col+1, row+1, col+1, 'Ажлын ангилал', sub_total_sub)
            worksheet3.merge_range(row, col+2, row+1, col+2, 'Ажлын нэр', sub_total_sub)
            worksheet3.merge_range(row, col+3, row+1, col+3, 'ААНаряд шийдвэр дугаар', sub_total_sub)
            worksheet3.merge_range(row, col+4, row+1, col+4, 'Ажил гүйцэтгэгч', sub_total_sub)
            worksheet3.merge_range(row, col+5, row+1, col+5, 'Хүчдлийн түвшин /В/', sub_total_sub)
            worksheet3.merge_range(row, col+6, row+1, col+6, 'Огноо', sub_total_sub)
            col += 1
            worksheet3.merge_range(row, col+6, row+1, col+6, 'Ээлж', sub_total_sub)
            col += 1
            worksheet3.merge_range(row, col+6, row+1, col+6, 'Бүртгэсэн дис', sub_total_sub)
            worksheet3.merge_range(row, col+7, row, col+9, 'Төлөвлөгөөт', sub_total_sub)
            worksheet3.write(row+1, col+7, 'Эхлэх', sub_total_sub)
            worksheet3.write(row+1, col+8, 'Дуусах', sub_total_sub)
            worksheet3.write(row+1, col+9, 'нийт /цаг/', sub_total_sub)
            worksheet3.merge_range(row, col+10, row, col+12, 'Гүйцэтгэл', sub_total_sub)
            worksheet3.write(row+1, col+10, 'Эхлэх', sub_total_sub)
            worksheet3.write(row+1, col+11, 'Дуусах', sub_total_sub)
            worksheet3.write(row+1, col+12, 'нийт /цаг/', sub_total_sub)
            worksheet3.merge_range(row, col+13, row+1, col+13, 'Төлөвлөгөө гүйцэтгэлийн зөрүү /цаг/', sub_total_sub)
            worksheet3.merge_range(row, col+14, row, col+16, 'Ашигласан Бараа материал', sub_total_sub)
            worksheet3.write(row+1, col+14, 'марк', sub_total_sub)
            worksheet3.write(row+1, col+15, 'тоо хэмжээ', sub_total_sub)
            worksheet3.write(row+1, col+16, 'хэмжих нэгж', sub_total_sub)
            worksheet3.merge_range(row, col+17, row+1, col+17, 'Тайлбар', sub_total_sub)
            row += 2
            number = 1
            wos = objs.mapped('down_plan_ids')
            for line in wos:
                col = 0
                worksheet3.write(row, col, number, contest_center)
                worksheet3.write(row, col+1, line.work_type_id.name or '', contest_center)
                worksheet3.write(row, col+2, line.work_name or '', contest_center)
                worksheet3.write(row, col+3, line.aan_naryad or '', contest_center)
                worksheet3.write(row, col+4, line.work_user_id.name or '', contest_center)
                worksheet3.write(row, col+5, line.level_id.name or '', contest_center)
                worksheet3.write(row, col+6, str(line.notes_plan_id.date) or '', contest_center)
                col += 1
                str_val = u'%s'%(dict(self.env['power.notes']._fields['shift'].selection).get(line.notes_plan_id.shift) or '')
                worksheet3.write(row, col+6, str_val, contest_center)
                col += 1
                worksheet3.write(row, col+6, str(line.notes_plan_id.dispatcher_id.name) or '', contest_center)
                str_val = u'%s'%(self.env['ir.qweb.field.float_time'].value_to_html(line.down_time_plan, {}) or '')
                worksheet3.write(row, col+7, str_val, contest_center)
                str_val = u'%s'%(self.env['ir.qweb.field.float_time'].value_to_html(line.plug_time_plan, {}) or '')
                worksheet3.write(row, col+8, str_val, contest_center)
                str_val = u'%s'%(self.env['ir.qweb.field.float_time'].value_to_html(line.break_time_plan, {}) or '')
                worksheet3.write(row, col+9, str_val, contest_center)
                str_val = u'%s'%(self.env['ir.qweb.field.float_time'].value_to_html(line.down_time, {}) or '')
                worksheet3.write(row, col+10, str_val, contest_center)
                str_val = u'%s'%(self.env['ir.qweb.field.float_time'].value_to_html(line.plug_time, {}) or '')
                worksheet3.write(row, col+11, str_val, contest_center)
                str_val = u'%s'%(self.env['ir.qweb.field.float_time'].value_to_html(line.break_time, {}) or '')
                worksheet3.write(row, col+12, str_val, contest_center)
                diff_time = line.break_time_plan - line.break_time
                str_val = u'%s'%(self.env['ir.qweb.field.float_time'].value_to_html(diff_time, {}) or '')
                worksheet3.write(row, col+13, str_val, contest_center)
                worksheet3.write(row, col+14, '', contest_center)
                worksheet3.write(row, col+15, '', contest_center)
                worksheet3.write(row, col+16, '', contest_center)
                worksheet3.write(row, col+17, line.description or '', contest_center)
                row += 1
                number += 1

            row = 1
            worksheet4.merge_range(row, 0, row, 17, u"4.Дуудлагаар хийгдсэн ажил", sub_total)
            row += 1
            col = 0
            worksheet4.merge_range(row, col, row+1, col, 'д/д', sub_total_sub)
            worksheet4.merge_range(row, col+1, row+1, col+1, 'Хүчдэлийн түвшин /В/', sub_total_sub)
            worksheet4.merge_range(row, col+2, row+1, col+2, 'Дуудлага өгсөн хэлтэс', sub_total_sub)
            worksheet4.merge_range(row, col+3, row+1, col+3, 'Дуудлага өгсөн хүний нэр', sub_total_sub)
            worksheet4.merge_range(row, col+4, row+1, col+4, 'Дуудлага авсан диспетчер', sub_total_sub)
            worksheet4.merge_range(row, col+5, row+1, col+5, 'Дуудлага ангилал', sub_total_sub)
            worksheet4.merge_range(row, col+6, row+1, col+6, 'Дуудлагын агуулга', sub_total_sub)
            col += 1
            worksheet4.merge_range(row, col+6, row+1, col+6, 'Огноо', sub_total_sub)
            col += 1
            worksheet4.merge_range(row, col+6, row+1, col+6, 'Ээлж', sub_total_sub)
            worksheet4.merge_range(row, col+7, row+1, col+7, 'Дуудлага бүртгэж авсан цаг', sub_total_sub)
            worksheet4.merge_range(row, col+8, row+1, col+8, 'Дуудлага барагдуулсан цаг', sub_total_sub)
            worksheet4.merge_range(row, col+9, row+1, col+9, 'Дуудлага барагдуулсан хугацаа', sub_total_sub)
            worksheet4.merge_range(row, col+10, row+1, col+10, 'Дуудлагаар авсан арга хэмжээ', sub_total_sub)
            worksheet4.merge_range(row, col+11, row+1, col+11, 'Дуудлага барагдуулсан монтёр', sub_total_sub)
            worksheet4.merge_range(row, col+12, row, col+14, 'Ашигласан Бараа материал', sub_total_sub)
            worksheet4.write(row+1, col+12, 'марк', sub_total_sub)
            worksheet4.write(row+1, col+13, 'тоо хэмжээ', sub_total_sub)
            worksheet4.write(row+1, col+14, 'хэмжих нэгж', sub_total_sub)
            worksheet4.merge_range(row, col+15, row+1, col+15, 'Тайлбар', sub_total_sub)
            row += 2
            number = 1
            
            wos = objs.mapped('down_call_ids')
            for line in wos:
                col = 0
                worksheet4.write(row, col, number, contest_center)
                worksheet4.write(row, col+1, line.level_id.name or '', contest_center)
                worksheet4.write(row, col+2, line.call_department_id.name or '', contest_center)
                worksheet4.write(row, col+3, line.call_partner_name or '', contest_center)
                worksheet4.write(row, col+4, line.notes_call_id.dispatcher_id.name or '', contest_center)
                worksheet4.write(row, col+5, line.call_type_id.name or '', contest_center)
                worksheet4.write(row, col+6, line.call_notes or '', contest_center)
                col += 1
                worksheet4.write(row, col+6, (line.notes_call_id.date) or '', contest_center)
                col += 1
                str_val = u'%s'%(dict(self.env['power.notes']._fields['shift'].selection).get(line.notes_call_id.shift) or '')
                worksheet4.write(row, col+6, str_val, contest_center)
                str_val = u'%s'%(self.env['ir.qweb.field.float_time'].value_to_html(line.call_time_start, {}) or '')
                worksheet4.write(row, col+7, str_val, contest_center)
                str_val = u'%s'%(self.env['ir.qweb.field.float_time'].value_to_html(line.call_time_end, {}) or '')
                worksheet4.write(row, col+8, str_val, contest_center)
                str_val = u'%s'%(self.env['ir.qweb.field.float_time'].value_to_html(line.call_fix_time, {}) or '')
                worksheet4.write(row, col+9, str_val, contest_center)
                worksheet4.write(row, col+10, line.call_taken or '', contest_center)
                worksheet4.write(row, col+11, line.call_taken_user_id.name or '', contest_center)
                worksheet4.write(row, col+12, '', contest_center)
                worksheet4.write(row, col+13, '', contest_center)
                worksheet4.write(row, col+14, '', contest_center)
                worksheet4.write(row, col+15, line.description or '', contest_center)
                row += 1
                number += 1

            row = 1
            worksheet5.merge_range(row, 0, row, 14, u"5.Өдөр тутмын шуурхайд төлөвлөгдсөн ажил", sub_total)
            row += 1
            col = 0
            worksheet5.merge_range(row, col, row+1, col, 'д/д', sub_total_sub)
            worksheet5.merge_range(row, col+1, row+1, col+1, 'Ажлын ангилал', sub_total_sub)
            worksheet5.merge_range(row, col+2, row+1, col+2, 'Ажлын нэр', sub_total_sub)
            worksheet5.merge_range(row, col+3, row+1, col+3, 'Ажил гүйцэтгэгч', sub_total_sub)
            col += 1
            worksheet5.merge_range(row, col+3, row+1, col+3, 'Огноо', sub_total_sub)
            col += 1
            worksheet5.merge_range(row, col+3, row+1, col+3, 'Ээлж', sub_total_sub)
            col += 1
            worksheet5.merge_range(row, col+3, row+1, col+3, 'Бүртгэсэн дис', sub_total_sub)
            worksheet5.merge_range(row, col+4, row+1, col+4, 'Эхлэх', sub_total_sub)
            worksheet5.merge_range(row, col+5, row+1, col+5, 'Дуусах', sub_total_sub)
            worksheet5.merge_range(row, col+6, row+1, col+6, 'хугацаа /цаг/', sub_total_sub)
            worksheet5.merge_range(row, col+7, row+1, col+7, 'Ажлын хувь /0-100%/', sub_total_sub)
            worksheet5.merge_range(row, col+8, row, col+10, 'Ашигласан Бараа материал', sub_total_sub)
            worksheet5.write(row+1, col+8, 'марк', sub_total_sub)
            worksheet5.write(row+1, col+9, 'тоо хэмжээ', sub_total_sub)
            worksheet5.write(row+1, col+10, 'хэмжих нэгж', sub_total_sub)
            worksheet5.merge_range(row, col+11, row+1, col+11, 'Тайлбар', sub_total_sub)
            row += 2
            number = 1
            wos = objs.mapped('down_daily_ids')
            for line in wos:
                col = 0
                worksheet5.write(row, col, number, contest_center)
                worksheet5.write(row, col+1, line.daily_work_type_id.name or '', contest_center)
                worksheet5.write(row, col+2, line.work_name or '', contest_center)
                worksheet5.write(row, col+3, line.work_user_id.name or '', contest_center)
                col += 1
                worksheet5.write(row, col+3, (line.notes_daily_id.date) or '', contest_center)
                col += 1
                str_val = u'%s'%(dict(self.env['power.notes']._fields['shift'].selection).get(line.notes_daily_id.shift) or '')
                worksheet5.write(row, col+3, str_val or '', contest_center)
                col += 1
                worksheet5.write(row, col+3, (line.notes_daily_id.dispatcher_id.name) or '', contest_center)
                str_val = u'%s'%(self.env['ir.qweb.field.float_time'].value_to_html(line.start_time, {}) or '')
                worksheet5.write(row, col+4, str_val, contest_center)
                str_val = u'%s'%(self.env['ir.qweb.field.float_time'].value_to_html(line.end_time, {}) or '')
                worksheet5.write(row, col+5, str_val, contest_center)
                str_val = u'%s'%(self.env['ir.qweb.field.float_time'].value_to_html(line.diff_time, {}) or '')
                worksheet5.write(row, col+6, str_val, contest_center)
                worksheet5.write(row, col+7, line.work_actual or '', contest_center)
                worksheet5.write(row, col+8, '', contest_center)
                worksheet5.write(row, col+9, '', contest_center)
                worksheet5.write(row, col+10, '', contest_center)
                worksheet5.write(row, col+11, line.description or '', contest_center)
                row += 1
                number += 1
            
            row = 1
            worksheet6.merge_range(row, 0, row, 10, u"6.Экскаваторын зогсолт", sub_total)
            row += 1
            col = 0
            worksheet6.write(row, col, 'д/д', sub_total_sub)
            worksheet6.write(row, col+1, 'Эзэмшил', sub_total_sub)
            worksheet6.write(row, col+2, 'Экскаваторууд', sub_total_sub)
            worksheet6.write(row, col+3, 'Чадал', sub_total_sub)
            col += 1
            worksheet6.write(row, col+3, 'Огноо', sub_total_sub)
            col += 1
            worksheet6.write(row, col+3, 'Ээлж', sub_total_sub)
            col += 1
            worksheet6.write(row, col+3, 'Бүртгэсэн дис', sub_total_sub)
            worksheet6.write(row, col+4, 'Зогссон цаг /цаг/', sub_total_sub)
            worksheet6.write(row, col+5, 'Ажилласан цаг /цаг/', sub_total_sub)
            worksheet6.write(row, col+6, 'Зогссон хугацаа /цаг/', sub_total_sub)
            worksheet6.write(row, col+7, 'Цахилгаантай холбоотой зогсолтын шалтгаан', sub_total_sub)
            
            row += 1
            number = 1
            wos = objs.mapped('portable_ids')
            for line in wos:
                col = 0
                worksheet6.write(row, col, number, contest_center)
                str_val = u'%s'%(line.power_technic_id.technic_id.partner_id.name or '')
                worksheet6.write(row, col+1, str_val or '', contest_center)
                worksheet6.write(row, col+2, line.power_technic_id.name or '', contest_center)
                str_val = u'%s'%(int(line.power_technic_id.technic_id.technic_setting_id.engine_capacity) or '')
                worksheet6.write(row, col+3, str_val or '', contest_center)
                col += 1
                worksheet6.write(row, col+3, (line.notes_id.date) or '', contest_center)
                col += 1
                str_val = u'%s'%(dict(self.env['power.notes']._fields['shift'].selection).get(line.notes_id.shift) or '')
                worksheet6.write(row, col+3, str_val, contest_center)
                col += 1
                worksheet6.write(row, col+3, (line.notes_id.dispatcher_id.name) or '', contest_center)
                str_val = u'%s'%(self.env['ir.qweb.field.float_time'].value_to_html(line.start_time, {}) or '')
                worksheet6.write(row, col+4, str_val, contest_center)
                str_val = u'%s'%(self.env['ir.qweb.field.float_time'].value_to_html(line.end_time, {}) or '')
                worksheet6.write(row, col+5, str_val, contest_center)
                str_val = u'%s'%(self.env['ir.qweb.field.float_time'].value_to_html(line.diff_time, {}) or '')
                worksheet6.write(row, col+6, str_val, contest_center)
                worksheet6.write(row, col+7, line.description or '', contest_center)
                row += 1
                number += 1
            # =============================
            workbook.close()
            out = base64.encodestring(output.getvalue())
            excel_id = self.env['report.excel.output'].create({'data': out, 'name': file_name})

            return {
                 'type' : 'ir.actions.act_url',
                 'url': "web/content/?model=report.excel.output&id=%d&filename_field=filename&download=true&field=data&filename=%s"%(excel_id.id,excel_id.name),
                 'target': 'new',
            }
        else:
            raise UserError(u'Бичлэг олдсонгүй!')


    