# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)

class power_workorder(models.Model):
    _inherit = 'power.workorder'

    def get_used_parts(self, ids):
        # headers = [u'Num',u'Parts name',u'Parts number',u'Qty',u'☑☒']
        headers = [u'Д/Д',u'БМ нэр',u'БМ дугаар',u'Тоо ширхэг']
        datas = []
        obj = self.env['power.workorder'].search([('id','=',ids)])
        i = 1
        if obj.stock_move_ids:
            for line in obj.stock_move_ids:
                temp = [str(i), unicode(line.product_id.name), unicode(line.product_id.default_code),str(line.product_uom_qty)]
                datas.append(temp)
                i += 1
        else:
            temp = ['| \n','| \n','| \n','| \n']
            datas.append(temp)
            datas.append(temp)
            datas.append(temp)
            datas.append(temp)
            datas.append(temp)
        res = {'header': headers, 'data':datas}
        _logger.info(u'-***********-WO--*************---get_used_parts--%s---\n'%unicode(res))
        return res

    # Захиалсан сэлбэг материал
    def get_ordered_parts(self, ids):
        headers = [u'Д/Д',u'БМ нэр',u'БМ дугаар',u'Тоо ширхэг']
        datas = []
        obj = self.env['power.workorder'].search([('id','=',ids)])
        i = 1
        if obj.product_expense_ids:
            for line in obj.product_expense_ids:
                temp = [str(i),str(line.product_id.name), line.product_id.default_code,str(line.product_qty)]
                datas.append(temp)
                i += 1
        else:
            temp = ['| \n','| \n','| \n','| \n']
            datas.append(temp)
            datas.append(temp)
            datas.append(temp)
            datas.append(temp)
            datas.append(temp)

        res = {'header': headers, 'data':datas}
        _logger.info(u'-***********-WO--*************---get_ordered_parts--%s---\n'%unicode(res))
        return res

    def get_brigad(self, ids):
        headers = [u'Нэр',u'Эхэлсэн Цаг']
        headers = [u'№',u'Код',u'Ажилтны нэр',u'Эхэлсэн цаг',u'Дууссан цаг',u'Зарцуулсан цаг']
        datas = []
        obj = self.env['power.workorder'].search([('id','=',ids)])
        i = 1
        if obj.brigad_ids:
            for line in obj.brigad_ids:
                ddd1 = u'%s'%(self.env['ir.qweb.field.float_time'].value_to_html(line.time_start, {}))
                ddd2 = u'%s'%(self.env['ir.qweb.field.float_time'].value_to_html(line.time_end, {}))
                ddd3 = u'%s'%(self.env['ir.qweb.field.float_time'].value_to_html(line.time_spent, {}))
                temp = [str(i),str(line.employee_id.identification_id) or '',str(line.employee_id.name) or '', ddd1, ddd2, ddd3]
                datas.append(temp)
                i += 1
        else:
            temp = ['| \n','| \n','| \n','| \n','| \n','| \n']
            datas.append(temp)
            datas.append(temp)
            datas.append(temp)
            datas.append(temp)
            datas.append(temp)
            datas.append(temp)
            datas.append(temp)
            datas.append(temp)
            datas.append(temp)
            datas.append(temp)
        res = {'header': headers, 'data':datas}
        return res

    def get_time_start(self, ids):
        return self.env['ir.qweb.field.float_time'].value_to_html(self.env['power.workorder'].search([('id','=',ids)]).time_start, {})
    def get_time_end(self, ids):
        return self.env['ir.qweb.field.float_time'].value_to_html(self.env['power.workorder'].search([('id','=',ids)]).time_end, {})
    def get_time_plan(self, ids):
        return self.env['ir.qweb.field.float_time'].value_to_html(self.env['power.workorder'].search([('id','=',ids)]).time_plan, {})
    def get_time_spent(self, ids):
        return self.env['ir.qweb.field.float_time'].value_to_html(self.env['power.workorder'].search([('id','=',ids)]).time_spent, {})
    def get_time_extend_hour(self, ids):
        return self.env['ir.qweb.field.float_time'].value_to_html(self.env['power.workorder'].search([('id','=',ids)]).time_extend_hour, {})