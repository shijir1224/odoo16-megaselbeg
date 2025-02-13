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
    _name = 'eo.print.wizard'
    _descriptoin = 'eo print wizard'

    date = fields.Date('Огноо', default=fields.Date.context_today)
    type = fields.Selection([('day','Өдрийн'),('day_from','Өдрийн хооронд')], default='day')
    date_start = fields.Date('Эхлэх Огноо', default=fields.Date.context_today)
    date_end = fields.Date('Дуусах Огноо', default=fields.Date.context_today)

    def export_excel(self):
        day_obj = self.env['power.notes'].search([('date','=',self.date),('shift','=','day')])
        night_obj = self.env['power.notes'].search([('date','=',self.date),('shift','=','night')])
        if night_obj and day_obj:
            output = BytesIO()
            workbook = xlsxwriter.Workbook(output)
            file_name = str(self.date)+'.xlsx'

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

            worksheet = workbook.add_worksheet(u'Sheet1')

            # worksheet.set_zoom(80)
            # worksheet.write(0,2, u"Сэлбэг хүлээсэн WORKORDER", h1)

            # TABLE HEADER
            row = 1
            # worksheet.set_row(1, 30)
            # worksheet.write(row, 0, u'№', header_wrap)
            # worksheet.set_column(0, 0, 3)
            # worksheet.write(row, 1, u'Date', header_wrap)
            # worksheet.set_column(2, 2, 10)
            # worksheet.write(row, 2, u'Work Order', header_wrap)
            # worksheet.set_column(2, 2, 12)
            # worksheet.write(row, 3, u'Equipment', header_wrap)
            # worksheet.set_column(3, 3, 28)
            # worksheet.write(row, 4, u'Equipment description', header_wrap)
            # worksheet.write(row, 5, u'Type', header_wrap)
            # worksheet.set_column(5, 5, 10)
            # worksheet.write(row, 6, u'Ээлж', header_wrap)
            # worksheet.set_column(6, 6, 8)
            # worksheet.write(row, 7, u'Description', header_wrap)
            # worksheet.set_column(7, 7, 90)
            # worksheet.write(row, 8, u'Status', header_wrap)
            # worksheet.set_column(8, 8, 8)
            # worksheet.write(row, 9, u'Shift Foreman', header_wrap)
            # worksheet.set_column(9, 9, 15)

            row = 1
            worksheet.merge_range(row, 0, row, 17, u"Цахилгааны хэлтэс/%s/"%(str(self.date)), sub_total)
            row += 2
            
            worksheet.merge_range(row, 0, row+3, 0, u"Ээлжинд диспетчер техникч", contest_center)
            col = 1
            str_val = dict(self.env['power.notes']._fields['shift'].selection).get(day_obj.shift)
            worksheet.merge_range(row, col, row+1, col, str_val, contest_center)
            str_val = dict(self.env['power.notes']._fields['shift'].selection).get(night_obj.shift)
            worksheet.merge_range(row+2, col, row+3, col, str_val, contest_center)
            col = 2
            str_val = day_obj.dispatcher_id.name
            worksheet.merge_range(row, col, row+1, col, str_val, contest_center)
            str_val = night_obj.dispatcher_id.name
            worksheet.merge_range(row+2, col, row+3, col, str_val, contest_center)

            col = 4
            worksheet.merge_range(row, col, row+3, col, u"Ээлжинд мастер", contest_center)
            col = 5
            str_val = dict(self.env['power.notes']._fields['shift'].selection).get(day_obj.shift)
            worksheet.merge_range(row, col, row+1, col, str_val, contest_center)
            str_val = dict(self.env['power.notes']._fields['shift'].selection).get(night_obj.shift)
            worksheet.merge_range(row+2, col, row+3, col, str_val, contest_center)
            col = 6
            str_val = day_obj.master_id.name
            worksheet.merge_range(row, col, row+1, col, str_val, contest_center)
            str_val = night_obj.master_id.name
            worksheet.merge_range(row+2, col, row+3, col, str_val, contest_center)

            col = 8
            str_val = 'Шуурхай ажиллагааны бригад'
            worksheet.merge_range(row, col, row+1, col, str_val, contest_center)
            str_val = dict(self.env['power.notes']._fields['shift'].selection).get(day_obj.shift)
            worksheet.write(row, col+1, str_val, contest_center)
            str_val = ', '.join(day_obj.brigad_ids.mapped('name'))
            worksheet.merge_range(row, col+2, row, col+6, str_val, contest_center)
            str_val = dict(self.env['power.notes']._fields['shift'].selection).get(night_obj.shift)
            worksheet.write(row+1, col+1, str_val, contest_center)
            str_val = ', '.join(night_obj.brigad_ids.mapped('name'))
            worksheet.merge_range(row+1, col+2, row+1, col+6, str_val, contest_center)
            
            str_val = 'Засварын бригад'
            worksheet.merge_range(row+2, col, row+3, col, str_val, contest_center)
            str_val = dict(self.env['power.notes']._fields['shift'].selection).get(day_obj.shift)
            worksheet.write(row+2, col+1, str_val, contest_center)
            str_val = ', '.join(day_obj.maintenance_ids.mapped('name'))
            worksheet.merge_range(row+2, col+2, row+2, col+6, str_val, contest_center)
            str_val = dict(self.env['power.notes']._fields['shift'].selection).get(night_obj.shift)
            worksheet.write(row+3, col+1, str_val, contest_center)
            str_val = ', '.join(night_obj.maintenance_ids.mapped('name'))
            worksheet.merge_range(row+3, col+2, row+3, col+6, str_val, contest_center)
            str_val = 'Нийт %s ажилтан'%(len(night_obj.maintenance_ids)+len(day_obj.maintenance_ids)+len(night_obj.brigad_ids)+len(day_obj.brigad_ids))
            worksheet.merge_range(row, col+7, row+3, col+7, str_val, contest_center)
            row += 5
            worksheet.merge_range(row, 0, row, 19, u"1.Тасралтын мэдээлэл", sub_total)
            row += 1
            col = 0
            worksheet.merge_range(row, col, row+1, col, 'д/д', sub_total_sub)
            worksheet.merge_range(row, col+1, row+1, col+1, 'Станц', sub_total_sub)
            worksheet.merge_range(row, col+2, row+1, col+2, 'Хүчдлийн түвшин /В/', sub_total_sub)
            worksheet.merge_range(row, col+3, row+1, col+3, 'Фидер', sub_total_sub)
            worksheet.merge_range(row, col+4, row+1, col+4, 'Ажилласан хамгаалалт', sub_total_sub)
            worksheet.merge_range(row, col+5, row+1, col+5, 'Тасарсан үеийн номинал гүйдэл /А/', sub_total_sub)
            worksheet.merge_range(row, col+6, row+1, col+6, 'Огноо', sub_total_sub)
            worksheet.merge_range(row, col+7, row+1, col+7, 'Тасарсан хугацаа', sub_total_sub)
            worksheet.merge_range(row, col+8, row+1, col+8, 'Залгасан хугацаа', sub_total_sub)
            worksheet.merge_range(row, col+9, row+1, col+9, 'Тасралтын хугацаа /мин/', sub_total_sub)
            worksheet.merge_range(row, col+10, row+1, col+10, 'Дутуу эрчим хүч /кВт.ц/', sub_total_sub)
            worksheet.merge_range(row, col+11, row+1, col+11, 'Тасралтын Ангилал', sub_total_sub)
            worksheet.merge_range(row, col+12, row+1, col+12, 'Шалтгаан', sub_total_sub)
            worksheet.merge_range(row, col+13, row+1, col+13, 'Авсан арга хэмжээ', sub_total_sub)
            worksheet.merge_range(row, col+14, row+1, col+14, 'Ажилласан бригад', sub_total_sub)
            worksheet.merge_range(row, col+15, row+1, col+15, 'Бүртгэгдсэн дис', sub_total_sub)
            worksheet.merge_range(row, col+16, row, col+18, 'Ашигласан Бараа материал', sub_total_sub)
            worksheet.write(row+1, col+16, 'марк', sub_total_sub)
            worksheet.write(row+1, col+17, 'тоо хэмжээ', sub_total_sub)
            worksheet.write(row+1, col+18, 'хэмжих нэгж', sub_total_sub)
            worksheet.merge_range(row, col+19, row+1, col+19, 'Тайлбар', sub_total_sub)
            row += 2
            number = 1
            wos = night_obj.down_ids+day_obj.down_ids
            for line in wos:
                worksheet.write(row, col, number, contest_center)
                worksheet.write(row, col+1, line.station_id.name or '', contest_center)
                worksheet.write(row, col+2, line.level_id.name or '', contest_center)
                worksheet.write(row, col+3, line.fider_id.name or '', contest_center)
                worksheet.write(row, col+4, line.work_secure_id.name or '', contest_center)
                worksheet.write(row, col+5, line.down_nominal or '', contest_center)
                worksheet.write(row, col+6, str(line.notes_id.date) or '', contest_center)
                str_val = u'%s'%(self.env['ir.qweb.field.float_time'].value_to_html(line.down_time, {}) or '')
                worksheet.write(row, col+7, str_val, contest_center)
                str_val = u'%s'%(self.env['ir.qweb.field.float_time'].value_to_html(line.plug_time, {}) or '')
                worksheet.write(row, col+8, str_val, contest_center)
                str_val = u'%s'%(line.break_time*60)
                worksheet.write(row, col+9, str_val, contest_center)
                worksheet.write(row, col+10, line.incomplete_power or '', contest_center)
                worksheet.write(row, col+11, line.down_type_id.name or '', contest_center)
                worksheet.write(row, col+12, line.cause or '', contest_center)
                worksheet.write(row, col+13, line.actions_taken or '', contest_center)
                worksheet.write(row, col+14, ', '.join(line.work_user_ids.mapped('name')) or '', contest_center)
                worksheet.write(row, col+15, str(line.notes_id.dispatcher_id.name) or '', contest_center)
                worksheet.write(row, col+16, '', contest_center)
                worksheet.write(row, col+17, '', contest_center)
                worksheet.write(row, col+18, '', contest_center)
                worksheet.write(row, col+19, line.description or '', contest_center)
                row += 1
                number += 1
            row += 1
            worksheet.merge_range(row, 0, row, 16, u"2.Гадны байгууллагын захиалгат таслалт /ААН-р хийгдсэн/", sub_total)
            row += 1
            col = 0
            worksheet.write(row, col, 'д/д', sub_total_sub)
            worksheet.write(row, col+1, 'Захиалга өгсөн байгууллга, алба хэлтэс', sub_total_sub)
            worksheet.write(row, col+2, 'ААН-ны Наряд шийдвэрийн дугаар', sub_total_sub)
            worksheet.write(row, col+3, 'Захиалга өгсөн хүний нэр албан тушаал', sub_total_sub)
            worksheet.write(row, col+4, 'Ангилал', sub_total_sub)
            worksheet.write(row, col+5, 'Захиалгын утга', sub_total_sub)
            worksheet.write(row, col+6, 'Захиалга баталсан албан тушаалтан', sub_total_sub)
            worksheet.write(row, col+7, 'Огноо', sub_total_sub)
            worksheet.write(row, col+8, 'Таслах үеийн ачаалал /А/', sub_total_sub)
            worksheet.write(row, col+9, 'Тасалсан хугацаа', sub_total_sub)
            worksheet.write(row, col+10, 'Залгасан хугацаа', sub_total_sub)
            worksheet.write(row, col+11, 'Тасралтын хугацаа /мин/', sub_total_sub)
            worksheet.write(row, col+12, 'Дутуу эрчим хүч /кВт.ц/', sub_total_sub)
            worksheet.write(row, col+13, 'Ажилласан баригад', sub_total_sub)
            worksheet.write(row, col+14, 'Бүртгэсэн дис', sub_total_sub)
            worksheet.write(row, col+15, 'Ашигласан Бараа материал', sub_total_sub)
            worksheet.write(row, col+16, 'Тайлбар', sub_total_sub)
            row += 1
            number = 1
            wos = night_obj.down_order_ids+day_obj.down_order_ids
            for line in wos:
                worksheet.write(row, col, number, contest_center)
                worksheet.write(row, col+1, line.down_partner_id.name or '', contest_center)
                worksheet.write(row, col+2, line.aan_naryad or '', contest_center)
                worksheet.write(row, col+3, line.partner_job_position or '', contest_center)
                worksheet.write(row, col+4, '', contest_center)
                worksheet.write(row, col+5, line.partner_notes or '', contest_center)
                worksheet.write(row, col+6, line.confirm_user_id.name or '', contest_center)
                worksheet.write(row, col+7, str(line.notes_order_id.date) or '', contest_center)
                worksheet.write(row, col+8, line.down_nominal or '', contest_center)
                str_val = u'%s'%(self.env['ir.qweb.field.float_time'].value_to_html(line.down_time, {}) or '')
                worksheet.write(row, col+9, str_val, contest_center)
                str_val = u'%s'%(self.env['ir.qweb.field.float_time'].value_to_html(line.plug_time, {}) or '')
                worksheet.write(row, col+10, str_val, contest_center)
                str_val = u'%s'%(line.break_time*60)
                worksheet.write(row, col+11, str_val, contest_center)
                worksheet.write(row, col+12, line.incomplete_power or '', contest_center)
                worksheet.write(row, col+13, ', '.join(line.work_user_ids.mapped('name')) or '', contest_center)
                worksheet.write(row, col+14, str(line.notes_order_id.dispatcher_id.name) or '', contest_center)
                worksheet.write(row, col+15, '', contest_center)
                worksheet.write(row, col+16, line.description or '', contest_center)
                row += 1
                number += 1

            row += 1
            worksheet.merge_range(row, 0, row, 17, u"3.Төлөвлөгөөт таслалтын ажил /ААН-р хийгдсэн/", sub_total)
            row += 1
            col = 0
            worksheet.merge_range(row, col, row+1, col, 'д/д', sub_total_sub)
            worksheet.merge_range(row, col+1, row+1, col+1, 'Ажлын ангилал', sub_total_sub)
            worksheet.merge_range(row, col+2, row+1, col+2, 'Ажлын нэр', sub_total_sub)
            worksheet.merge_range(row, col+3, row+1, col+3, 'ААНаряд шийдвэр дугаар', sub_total_sub)
            worksheet.merge_range(row, col+4, row+1, col+4, 'Ажил гүйцэтгэгч', sub_total_sub)
            worksheet.merge_range(row, col+5, row+1, col+5, 'Хүчдлийн түвшин /В/', sub_total_sub)
            worksheet.merge_range(row, col+6, row+1, col+6, 'Огноо', sub_total_sub)
            worksheet.merge_range(row, col+7, row, col+9, 'Төлөвлөгөөт', sub_total_sub)
            worksheet.write(row+1, col+7, 'Эхлэх', sub_total_sub)
            worksheet.write(row+1, col+8, 'Дуусах', sub_total_sub)
            worksheet.write(row+1, col+9, 'нийт /мин/', sub_total_sub)
            worksheet.merge_range(row, col+10, row, col+12, 'Гүйцэтгэл', sub_total_sub)
            worksheet.write(row+1, col+10, 'Эхлэх', sub_total_sub)
            worksheet.write(row+1, col+11, 'Дуусах', sub_total_sub)
            worksheet.write(row+1, col+12, 'нийт /мин/', sub_total_sub)
            worksheet.merge_range(row, col+13, row+1, col+13, 'Төлөвлөгөө гүйцэтгэлийн зөрүү /мин/', sub_total_sub)
            worksheet.merge_range(row, col+14, row, col+16, 'Ашигласан Бараа материал', sub_total_sub)
            worksheet.write(row+1, col+14, 'марк', sub_total_sub)
            worksheet.write(row+1, col+15, 'тоо хэмжээ', sub_total_sub)
            worksheet.write(row+1, col+16, 'хэмжих нэгж', sub_total_sub)
            worksheet.merge_range(row, col+17, row+1, col+17, 'Тайлбар', sub_total_sub)
            row += 2
            number = 1
            wos = night_obj.down_plan_ids+day_obj.down_plan_ids
            for line in wos:
                worksheet.write(row, col, number, contest_center)
                worksheet.write(row, col+1, line.work_type_id.name or '', contest_center)
                worksheet.write(row, col+2, line.work_name or '', contest_center)
                worksheet.write(row, col+3, line.aan_naryad or '', contest_center)
                worksheet.write(row, col+4, line.work_user_id.name or '', contest_center)
                worksheet.write(row, col+5, line.level_id.name or '', contest_center)
                worksheet.write(row, col+6, str(line.notes_plan_id.date) or '', contest_center)
                str_val = u'%s'%(self.env['ir.qweb.field.float_time'].value_to_html(line.down_time_plan, {}) or '')
                worksheet.write(row, col+7, str_val, contest_center)
                str_val = u'%s'%(self.env['ir.qweb.field.float_time'].value_to_html(line.plug_time_plan, {}) or '')
                worksheet.write(row, col+8, str_val, contest_center)
                str_val = u'%s'%(line.break_time_plan*60)
                worksheet.write(row, col+9, str_val, contest_center)
                str_val = u'%s'%(self.env['ir.qweb.field.float_time'].value_to_html(line.down_time, {}) or '')
                worksheet.write(row, col+10, str_val, contest_center)
                str_val = u'%s'%(self.env['ir.qweb.field.float_time'].value_to_html(line.plug_time, {}) or '')
                worksheet.write(row, col+11, str_val, contest_center)
                str_val = u'%s'%(line.break_time*60)
                worksheet.write(row, col+12, str_val, contest_center)
                diff_time = line.break_time_plan - line.break_time
                str_val = u'%s'%(diff_time*60)
                worksheet.write(row, col+13, str_val, contest_center)
                worksheet.write(row, col+14, '', contest_center)
                worksheet.write(row, col+15, '', contest_center)
                worksheet.write(row, col+16, '', contest_center)
                worksheet.write(row, col+17, line.description or '', contest_center)
                row += 1
                number += 1

            row += 1
            worksheet.merge_range(row, 0, row, 15, u"4.Дуудлагаар хийгдсэн ажил", sub_total)
            row += 1
            col = 0
            worksheet.merge_range(row, col, row+1, col, 'д/д', sub_total_sub)
            worksheet.merge_range(row, col+1, row+1, col+1, 'Хүчдэлийн түвшин /В/', sub_total_sub)
            worksheet.merge_range(row, col+2, row+1, col+2, 'Дуудлага өгсөн хэлтэс', sub_total_sub)
            worksheet.merge_range(row, col+3, row+1, col+3, 'Дуудлага өгсөн хүний нэр', sub_total_sub)
            worksheet.merge_range(row, col+4, row+1, col+4, 'Дуудлага авсан диспетчер', sub_total_sub)
            worksheet.merge_range(row, col+5, row+1, col+5, 'Дуудлага ангилал', sub_total_sub)
            worksheet.merge_range(row, col+6, row+1, col+6, 'Дуудлагын агуулга', sub_total_sub)
            worksheet.merge_range(row, col+7, row+1, col+7, 'Дуудлага бүртгэж авсан цаг', sub_total_sub)
            worksheet.merge_range(row, col+8, row+1, col+8, 'Дуудлага барагдуулсан цаг', sub_total_sub)
            worksheet.merge_range(row, col+9, row+1, col+9, 'Дуудлага барагдуулсан хугацаа', sub_total_sub)
            worksheet.merge_range(row, col+10, row+1, col+10, 'Дуудлагаар авсан арга хэмжээ', sub_total_sub)
            worksheet.merge_range(row, col+11, row+1, col+11, 'Дуудлага барагдуулсан монтёр', sub_total_sub)
            worksheet.merge_range(row, col+12, row, col+14, 'Ашигласан Бараа материал', sub_total_sub)
            worksheet.write(row+1, col+12, 'марк', sub_total_sub)
            worksheet.write(row+1, col+13, 'тоо хэмжээ', sub_total_sub)
            worksheet.write(row+1, col+14, 'хэмжих нэгж', sub_total_sub)
            worksheet.merge_range(row, col+15, row+1, col+15, 'Тайлбар', sub_total_sub)
            row += 2
            number = 1
            wos = night_obj.down_call_ids+day_obj.down_call_ids
            for line in wos:
                worksheet.write(row, col, number, contest_center)
                worksheet.write(row, col+1, line.level_id.name or '', contest_center)
                worksheet.write(row, col+2, line.call_department_id.name or '', contest_center)
                worksheet.write(row, col+3, line.call_partner_name or '', contest_center)
                worksheet.write(row, col+4, line.notes_call_id.dispatcher_id.name or '', contest_center)
                worksheet.write(row, col+5, line.call_type_id.name or '', contest_center)
                worksheet.write(row, col+6, line.call_notes or '', contest_center)
                str_val = u'%s'%(self.env['ir.qweb.field.float_time'].value_to_html(line.call_time_start, {}) or '')
                worksheet.write(row, col+7, str_val, contest_center)
                str_val = u'%s'%(self.env['ir.qweb.field.float_time'].value_to_html(line.call_time_end, {}) or '')
                worksheet.write(row, col+8, str_val, contest_center)
                str_val = u'%s'%(self.env['ir.qweb.field.float_time'].value_to_html(line.call_fix_time, {}) or '')
                worksheet.write(row, col+9, str_val, contest_center)
                worksheet.write(row, col+10, line.call_taken or '', contest_center)
                worksheet.write(row, col+11, line.call_taken_user_id.name or '', contest_center)
                worksheet.write(row, col+12, '', contest_center)
                worksheet.write(row, col+13, '', contest_center)
                worksheet.write(row, col+14, '', contest_center)
                worksheet.write(row, col+15, line.description or '', contest_center)
                row += 1
                number += 1

            row += 1
            worksheet.merge_range(row, 0, row, 11, u"5.Өдөр тутмын шуурхайд төлөвлөгдсөн ажил", sub_total)
            row += 1
            col = 0
            worksheet.merge_range(row, col, row+1, col, 'д/д', sub_total_sub)
            worksheet.merge_range(row, col+1, row+1, col+1, 'Ажлын ангилал', sub_total_sub)
            worksheet.merge_range(row, col+2, row+1, col+2, 'Ажлын нэр', sub_total_sub)
            worksheet.merge_range(row, col+3, row+1, col+3, 'Ажил гүйцэтгэгч', sub_total_sub)
            worksheet.merge_range(row, col+4, row+1, col+4, 'Эхлэх', sub_total_sub)
            worksheet.merge_range(row, col+5, row+1, col+5, 'Дуусах', sub_total_sub)
            worksheet.merge_range(row, col+6, row+1, col+6, 'хугацаа /мин/', sub_total_sub)
            worksheet.merge_range(row, col+7, row+1, col+7, 'Ажлын хувь /0-100%/', sub_total_sub)
            worksheet.merge_range(row, col+8, row, col+10, 'Ашигласан Бараа материал', sub_total_sub)
            worksheet.write(row+1, col+8, 'марк', sub_total_sub)
            worksheet.write(row+1, col+9, 'тоо хэмжээ', sub_total_sub)
            worksheet.write(row+1, col+10, 'хэмжих нэгж', sub_total_sub)
            worksheet.merge_range(row, col+11, row+1, col+11, 'Тайлбар', sub_total_sub)
            row += 2
            number = 1
            wos = night_obj.down_daily_ids+day_obj.down_daily_ids
            for line in wos:
                worksheet.write(row, col, number, contest_center)
                worksheet.write(row, col+1, line.daily_work_type_id.name or '', contest_center)
                worksheet.write(row, col+2, line.work_name or '', contest_center)
                worksheet.write(row, col+3, line.work_user_id.name or '', contest_center)
                str_val = u'%s'%(self.env['ir.qweb.field.float_time'].value_to_html(line.start_time, {}) or '')
                worksheet.write(row, col+4, str_val, contest_center)
                str_val = u'%s'%(self.env['ir.qweb.field.float_time'].value_to_html(line.end_time, {}) or '')
                worksheet.write(row, col+5, str_val, contest_center)
                str_val = u'%s'%(line.diff_time*60)
                worksheet.write(row, col+6, str_val, contest_center)
                worksheet.write(row, col+7, line.work_actual or '', contest_center)
                worksheet.write(row, col+8, '', contest_center)
                worksheet.write(row, col+9, '', contest_center)
                worksheet.write(row, col+10, '', contest_center)
                worksheet.write(row, col+11, line.description or '', contest_center)
                row += 1
                number += 1
            
            row += 1
            worksheet.merge_range(row, 0, row, 7, u"6.Экскаваторын зогсолт", sub_total)
            row += 1
            col = 0
            worksheet.write(row, col, 'д/д', sub_total_sub)
            worksheet.write(row, col+1, 'Эзэмшил', sub_total_sub)
            worksheet.write(row, col+2, 'Экскаваторууд', sub_total_sub)
            worksheet.write(row, col+3, 'Чадал', sub_total_sub)
            worksheet.write(row, col+4, 'Зогссон цаг /цаг/', sub_total_sub)
            worksheet.write(row, col+5, 'Ажилласан цаг /цаг/', sub_total_sub)
            worksheet.write(row, col+6, 'Зогссон хугацаа /мин/', sub_total_sub)
            worksheet.write(row, col+7, 'Цахилгаантай холбоотой зогсолтын шалтгаан', sub_total_sub)
            
            row += 1
            number = 1
            wos = night_obj.portable_ids+day_obj.portable_ids
            for line in wos:
                worksheet.write(row, col, number, contest_center)
                str_val = u'%s'%(line.power_technic_id.technic_id.partner_id.name or '')
                worksheet.write(row, col+1, str_val or '', contest_center)
                worksheet.write(row, col+2, line.power_technic_id.name or '', contest_center)
                str_val = u'%s'%(int(line.power_technic_id.technic_id.technic_setting_id.engine_capacity) or '')
                worksheet.write(row, col+3, str_val or '', contest_center)
                str_val = u'%s'%(self.env['ir.qweb.field.float_time'].value_to_html(line.start_time, {}) or '')
                worksheet.write(row, col+4, str_val, contest_center)
                str_val = u'%s'%(self.env['ir.qweb.field.float_time'].value_to_html(line.end_time, {}) or '')
                worksheet.write(row, col+5, str_val, contest_center)
                str_val = u'%s'%(line.diff_time)
                worksheet.write(row, col+6, str_val, contest_center)
                worksheet.write(row, col+7, line.description or '', contest_center)
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


    