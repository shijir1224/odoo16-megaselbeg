# -*- encoding: utf-8 -*-
##############################################################################
from odoo import api, fields, models, _
from odoo.modules import get_module_resource
from datetime import datetime
import json
import openpyxl
from io import BytesIO
from operator import itemgetter
import time
import base64
from odoo.exceptions import UserError
"""
   Санхүүгийн тайлангийн тодруулга тайлан
"""


class AccountDisclosureReportMain(models.Model):
    _name = "account.disclosure.report.main"
    _description = u"Санхүүгийн тайлангийн тодруулга үндсэн тайлангийн тохиргоо"
    
    name = fields.Char(u'Нэр', required=True)
    company_id = fields.Many2one('res.company', u'Компани', required=True)

    report_table1_ids = fields.One2many('account.disclosure.report.table1', 'main_id', u'1.МӨНГӨ БА ТҮҮНТЭЙ АДИЛТГАХ ХӨРӨНГӨ')
    report_table2_ids = fields.One2many('account.disclosure.report.table2', 'main_id', u'2. ДАНСНЫ БОЛОН БУСАД АВЛАГА')
    report_table3_ids = fields.One2many('account.disclosure.report.table3', 'main_id', u'3. БУСАД САНХҮҮГИЙН ХӨРӨНГӨ"')
    report_table4_ids = fields.One2many('account.disclosure.report.table4', 'main_id', u'4. БАРАА МАТЕРИАЛ')
    report_table5_ids = fields.One2many('account.disclosure.report.table5', 'main_id', u'5. УРЬДЧИЛЖ ТӨЛСӨН ЗАРДАЛ/ТООЦОО')
    report_table6_1_ids = fields.One2many('account.disclosure.report.table6_1', 'main_id', u'6. ҮНДСЭН ХӨРӨНГӨ')
    report_table6_2_ids = fields.One2many('account.disclosure.report.table6_2', 'main_id', u'6. ҮНДСЭН ХӨРӨНГӨ')
    report_table7_1_ids = fields.One2many('account.disclosure.report.table7_1', 'main_id', u'7. БИЕТ БУС ХӨРӨНГӨ')
    report_table7_2_ids = fields.One2many('account.disclosure.report.table7_2', 'main_id', u'7. БИЕТ БУС ХӨРӨНГӨ')
    report_table8_1_ids = fields.One2many('account.disclosure.report.table8_1', 'main_id', u'8. ӨР ТӨЛБӨР')
    report_table8_2_ids = fields.One2many('account.disclosure.report.table8_2', 'main_id', u'8. ӨР ТӨЛБӨР')
    report_table8_3_ids = fields.One2many('account.disclosure.report.table8_3', 'main_id', u'8. ӨР ТӨЛБӨР')
    report_table8_4_ids = fields.One2many('account.disclosure.report.table8_4', 'main_id', u'8. ӨР ТӨЛБӨР')
    report_table8_5_ids = fields.One2many('account.disclosure.report.table8_5', 'main_id', u'8. ӨР ТӨЛБӨР')
    report_table9_1_ids = fields.One2many('account.disclosure.report.table9_1', 'main_id', u'9. БОРЛУУЛАЛТЫН ОРЛОГО БОЛОН БОРЛУУЛАЛТЫН ӨРТӨГ')
    report_table9_2_ids = fields.One2many('account.disclosure.report.table9_2', 'main_id', u'9. БОРЛУУЛАЛТЫН ОРЛОГО БОЛОН БОРЛУУЛАЛТЫН ӨРТӨГ')
    report_table9_3_ids = fields.One2many('account.disclosure.report.table9_3', 'main_id', u'9. БОРЛУУЛАЛТЫН ОРЛОГО БОЛОН БОРЛУУЛАЛТЫН ӨРТӨГ')
    report_table9_4_ids = fields.One2many('account.disclosure.report.table9_4', 'main_id', u'9. БОРЛУУЛАЛТЫН ОРЛОГО БОЛОН БОРЛУУЛАЛТЫН ӨРТӨГ')
    report_table9_5_ids = fields.One2many('account.disclosure.report.table9_5', 'main_id', u'9. БОРЛУУЛАЛТЫН ОРЛОГО БОЛОН БОРЛУУЛАЛТЫН ӨРТӨГ')
    report_table10_ids = fields.One2many('account.disclosure.report.table10', 'main_id', u'10. БУСАД ОРЛОГО, ОЛЗ (ГАРЗ), АШИГ (АЛДАГДАЛ)')
    report_table11_1_ids = fields.One2many('account.disclosure.report.table11_1', 'main_id', u'11. ЗАРДАЛ')
    report_table11_2_ids = fields.One2many('account.disclosure.report.table11_2', 'main_id', u'11. ЗАРДАЛ')
    report_table12_ids = fields.One2many('account.disclosure.report.table12', 'main_id', u'12. ОРЛОГЫН ТАТВАРЫН ЗАРДАЛ')
    
    @api.model
    def default_get(self, fields_list):
        res = super(AccountDisclosureReportMain, self).default_get(fields_list) 
        
        report_table1_list = []
        report_table2_list = []
        report_table4_list = []
        report_table5_list = []
        report_table6_1_list = []
        report_table6_2_list = []
        report_table7_1_list = []
        report_table7_2_list = []
        report_table8_1_list = []
        report_table8_2_list = []
        report_table8_3_list = []
        report_table8_4_list = []
        report_table9_1_list = []
        report_table9_2_list = []
        report_table9_3_list = []
        report_table9_4_list = []
        report_table9_5_list = []
        report_table11_1_list = []
        report_table11_2_list = []
        report_table12_list = []

        # 1 МӨНГӨ БА ТҮҮНТЭЙ АДИЛТГАХ ХӨРӨНГӨ
        report_table1_list.append((0, 0, {
            'main_id': self.id,
           'table1_1': u'Касс дахь мөнгө'}))
        report_table1_list.append((0, 0, {
            'main_id': self.id,
           'table1_1': u'Банкин дахь мөнгө'}))
        report_table1_list.append((0, 0, {
            'main_id': self.id,
           'table1_1': u'Мөнгө түүнтэй адилтгах хөрөнгө'}))
        
        # 2 ДАНСНЫ БОЛОН БУСАД АВЛАГА
        report_table2_list.append((0, 0, {
            'main_id': self.id,
           'table2_1': u'Дансны авлага'}))
        report_table2_list.append((0, 0, {
            'main_id': self.id,
           'table2_1': u'Найдваргүй авлагын хасагдуулга'}))
        report_table2_list.append((0, 0, {
            'main_id': self.id,
           'table2_1': u'ААНОАТ-ын авлага'}))
        report_table2_list.append((0, 0, {
            'main_id': self.id,
           'table2_1': u'НӨАТ-ын авлага'}))
        report_table2_list.append((0, 0, {
            'main_id': self.id,
           'table2_1': u'НДШ-ийн авлага'}))
        report_table2_list.append((0, 0, {
            'main_id': self.id,
           'table2_1': u'Холбоотой талаас авлага (эргэлтийн хөрөнгөнд хамаарах дүн)'}))
        report_table2_list.append((0, 0, {
            'main_id': self.id,
           'table2_1': u'Ажиллагчдаас авах авлага'}))
        report_table2_list.append((0, 0, {
            'main_id': self.id,
           'table2_1': u'Ногдол ашгийн авлага'}))
        report_table2_list.append((0, 0, {
            'main_id': self.id,
           'table2_1': u'Хүүний авлага'}))
        report_table2_list.append((0, 0, {
            'main_id': self.id,
           'table2_1': u'Богино хугацаат авлагын бичиг'}))
        report_table2_list.append((0, 0, {
            'main_id': self.id,
           'table2_1': u'Бусад талуудаас авах авлага'}))
        
        # 4 БАРАА МАТЕРИАЛ 
        report_table4_list.append((0, 0, {
            'main_id': self.id,
           'table4_1': u'Түүхий эд материал'}))
        report_table4_list.append((0, 0, {
            'main_id': self.id,
           'table4_1': u'Дуусаагүй үйлдвэрлэл'}))
        report_table4_list.append((0, 0, {
            'main_id': self.id,
           'table4_1': u'Бэлэн бүтээгдэхүүн'}))
        report_table4_list.append((0, 0, {
            'main_id': self.id,
           'table4_1': u'Бараа'}))
        report_table4_list.append((0, 0, {
            'main_id': self.id,
           'table4_1': u'Хангамжийн материал'}))
        
        # 5 УРЬДЧИЛЖ ТӨЛСӨН ЗАРДАЛ/ТООЦОО
        report_table5_list.append((0, 0, {
            'main_id': self.id,
           'table5_1': u'Урьдчилж төлсөн зардал'}))
        report_table5_list.append((0, 0, {
            'main_id': self.id,
           'table5_1': u'Урьдчилж төлсөн түрээс, даатгал'}))
        report_table5_list.append((0, 0, {
            'main_id': self.id,
           'table5_1': u'Бэлтгэн нийлүүлэгчид төлсөн урьдчилгаа төлбөр'}))
        
        # 6. ҮНДСЭН ХӨРӨНГӨ 
        # 6.1 Үндсэн хөрөнгө (өртөг)
        report_table6_1_list.append((0, 0, {
            'main_id': self.id,
           'table6_1_1': u'Газрын сайжруулалт'}))
        report_table6_1_list.append((0, 0, {
            'main_id': self.id,
           'table6_1_1': u'Барилга, байгууламж'}))
        report_table6_1_list.append((0, 0, {
            'main_id': self.id,
           'table6_1_1': u'Машин, тоног төхөөрөмж'}))
        report_table6_1_list.append((0, 0, {
            'main_id': self.id,
           'table6_1_1': u'Тээврийн хэрэгсэл'}))
        report_table6_1_list.append((0, 0, {
            'main_id': self.id,
           'table6_1_1': u'Тавилга эд хогшил'}))
        report_table6_1_list.append((0, 0, {
            'main_id': self.id,
           'table6_1_1': u'Компьютер, бусад хэрэгсэл'}))
        report_table6_1_list.append((0, 0, {
            'main_id': self.id,
           'table6_1_1': u'Бусад үндсэн хөрөнгө'}))

        # 6.2 Хуримтлагдсан элэгдэл
        report_table6_2_list.append((0, 0, {
            'main_id': self.id,
           'table6_2_1': u'Газрын сайжруулалт'}))
        report_table6_2_list.append((0, 0, {
            'main_id': self.id,
           'table6_2_1': u'Барилга, байгууламж'}))
        report_table6_2_list.append((0, 0, {
            'main_id': self.id,
           'table6_2_1': u'Машин, тоног төхөөрөмж'}))
        report_table6_2_list.append((0, 0, {
            'main_id': self.id,
           'table6_2_1': u'Тээврийн хэрэгсэл'}))
        report_table6_2_list.append((0, 0, {
            'main_id': self.id,
           'table6_2_1': u'Тавилга эд хогшил'}))
        report_table6_2_list.append((0, 0, {
            'main_id': self.id,
           'table6_2_1': u'Компьютер, бусад хэрэгсэл'}))
        report_table6_2_list.append((0, 0, {
            'main_id': self.id,
           'table6_2_1': u'Бусад үндсэн хөрөнгө'}))

        # 7. БИЕТ БУС ХӨРӨНГӨ
        # 7.1 Биет бус хөрөнгө (өртөг)
        report_table7_1_list.append((0, 0, {
            'main_id': self.id,
            'table7_1_1': u'Зохиогчийн эрх'}))
        report_table7_1_list.append((0, 0, {
            'main_id': self.id,
            'table7_1_1': u'Компьютерийн Программ хангамж'}))
        report_table7_1_list.append((0, 0, {
            'main_id': self.id,
            'table7_1_1': u'Патент'}))
        report_table7_1_list.append((0, 0, {
            'main_id': self.id,
            'table7_1_1': u'Барааны тэмдэг'}))
        report_table7_1_list.append((0, 0, {
            'main_id': self.id,
            'table7_1_1': u'Тусгай зөвшөөрөл'}))
        report_table7_1_list.append((0, 0, {
            'main_id': self.id,
            'table7_1_1': u'Газар эзэмших эрх'}))
        report_table7_1_list.append((0, 0, {
            'main_id': self.id,
            'table7_1_1': u'Бусад биет бус хөрөнгө'}))

        # 7.2 Хуримтлагдсан хорогдол
        report_table7_2_list.append((0, 0, {
            'main_id': self.id,
            'table7_2_1': u'Зохиогчийн эрх'}))
        report_table7_2_list.append((0, 0, {
            'main_id': self.id,
            'table7_2_1': u'Компьютерийн Программ хангамж'}))
        report_table7_2_list.append((0, 0, {
            'main_id': self.id,
            'table7_2_1': u'Патент'}))
        report_table7_2_list.append((0, 0, {
            'main_id': self.id,
            'table7_2_1': u'Барааны тэмдэг'}))
        report_table7_2_list.append((0, 0, {
            'main_id': self.id,
            'table7_2_1': u'Тусгай зөвшөөрөл'}))
        report_table7_2_list.append((0, 0, {
            'main_id': self.id,
            'table7_2_1': u'Газар эзэмших эрх'}))
        report_table7_2_list.append((0, 0, {
            'main_id': self.id,
            'table7_2_1': u'Бусад биет бус хөрөнгө'}))

        # 8. ӨР ТӨЛБӨР
        # 8.1. Дансны өглөг
        report_table8_1_list.append((0, 0, {
            'main_id': self.id,
            'table8_1_1': u'Дансны өглөг'}))

        # 8.2 Татварын өр
        report_table8_2_list.append((0, 0, {
            'main_id': self.id,
            'table8_2_1': u'ААНОАТ-ын өр'}))
        report_table8_2_list.append((0, 0, {
            'main_id': self.id,
            'table8_2_1': u'НӨАТ-ын өр'}))
        report_table8_2_list.append((0, 0, {
            'main_id': self.id,
            'table8_2_1': u'ХХОАТ-ын өр'}))
        report_table8_2_list.append((0, 0, {
            'main_id': self.id,
            'table8_2_1': u'Онцгой албан татварын өр'}))
        report_table8_2_list.append((0, 0, {
            'main_id': self.id,
            'table8_2_1': u'Бусад татварын өр'}))
        report_table8_2_list.append((0, 0, {
            'main_id': self.id,
            'table8_2_1': u'Татвар-1'}))

        # 8.3. Богино хугацаат зээл
        report_table8_3_list.append((0, 0, {
            'main_id': self.id,
            'table8_3_1': u'Богино хугацаат зээл'}))

        # 8.4. Богино хугацаат нөөц (өр төлбөр)
        report_table8_4_list.append((0, 0, {
            'main_id': self.id,
            'table8_4_1': u'Баталгаат засварын'}))
        report_table8_4_list.append((0, 0, {
            'main_id': self.id,
            'table8_4_1': u'Нөхөн сэргээлтийн'}))

        # 9. БОРЛУУЛАЛТЫН ОРЛОГО БОЛОН БОРЛУУЛАЛТЫН ӨРТӨГ
        report_table9_1_list.append((0, 0, {
            'main_id': self.id,
            'table9_1_1': u'Бараа, бүтээгдэхүүн борлуулсны орлого'}))
        report_table9_2_list.append((0, 0, {
            'main_id': self.id,
            'table9_2_1': u'Ажил, үйлчилгээ борлуулсны орлого'}))
        report_table9_3_list.append((0, 0, {
            'main_id': self.id,
            'table9_3_1': u'Борлуулалтын буцаалт, хөнгөлөлт, үнийн бууралт'}))
        report_table9_4_list.append((0, 0, {
            'main_id': self.id,
            'table9_4_1': u'Борлуулсан бараа, борлуулалтын өртөг'}))
        report_table9_5_list.append((0, 0, {
            'main_id': self.id,
            'table9_5_1': u'Борлуулсан ажил, үйлчилгээний өртөг'}))

        # 10. БУСАД ОРЛОГО, ОЛЗ (ГАРЗ), АШИГ (АЛДАГДАЛ)
        # 11.1. ЗАРДАЛ
        report_table11_1_list.append((0, 0, {
            'main_id': self.id,
            'table11_1_1': u'Ажиллагчдын цалингийн зардал'}))
        report_table11_1_list.append((0, 0, {
            'main_id': self.id,
            'table11_1_1': u'Аж ахуйн нэгжээс төлсөн НДШ-ийн зардал'}))
        report_table11_1_list.append((0, 0, {
            'main_id': self.id,
            'table11_1_1': u'Албан татвар, төлбөр, хураамжийн зардал '}))
        report_table11_1_list.append((0, 0, {
            'main_id': self.id,
            'table11_1_1': u'Томилолтын зардал'}))
        report_table11_1_list.append((0, 0, {
            'main_id': self.id,
            'table11_1_1': u'Бичиг хэргийн зардал'}))
        report_table11_1_list.append((0, 0, {
            'main_id': self.id,
            'table11_1_1': u'Шуудан холбооны зардал'}))
        report_table11_1_list.append((0, 0, {
            'main_id': self.id,
            'table11_1_1': u'Мэргэжлийн үйлчилгээний зардал'}))
        report_table11_1_list.append((0, 0, {
            'main_id': self.id,
            'table11_1_1': u'Сургалтын зардал'}))
        report_table11_1_list.append((0, 0, {
            'main_id': self.id,
            'table11_1_1': u'Сонин сэтгүүл захиалгын зардал'}))
        report_table11_1_list.append((0, 0, {
            'main_id': self.id,
            'table11_1_1': u'Даатгалын зардал'}))
        report_table11_1_list.append((0, 0, {
            'main_id': self.id,
            'table11_1_1': u'Ашиглалтын зардал'}))
        report_table11_1_list.append((0, 0, {
            'main_id': self.id,
            'table11_1_1': u'Засварын зардал'}))
        report_table11_1_list.append((0, 0, {
            'main_id': self.id,
            'table11_1_1': u'Элэгдэл, хорогдлын зардал'}))
        report_table11_1_list.append((0, 0, {
            'main_id': self.id,
            'table11_1_1': u'Түрээсийн зардал'}))
        report_table11_1_list.append((0, 0, {
            'main_id': self.id,
            'table11_1_1': u'Харуул хамгаалалтын зардал'}))
        report_table11_1_list.append((0, 0, {
            'main_id': self.id,
            'table11_1_1': u'Цэвэрлэгээ үйлчилгээний зардал'}))
        report_table11_1_list.append((0, 0, {
            'main_id': self.id,
            'table11_1_1': u'Тээврийн зардал'}))
        report_table11_1_list.append((0, 0, {
            'main_id': self.id,
            'table11_1_1': u'Шатахууны зардал'}))
        report_table11_1_list.append((0, 0, {
            'main_id': self.id,
            'table11_1_1': u'Хүлээн авалтын зардал'}))
        report_table11_1_list.append((0, 0, {
            'main_id': self.id,
            'table11_1_1': u'Зар сурталчилгааны зардал'}))
        report_table11_1_list.append((0, 0, {
            'main_id': self.id,
            'table11_1_1': u'Бусад'}))

        # 11.2. ЗАРДАЛ
        report_table11_2_list.append((0, 0, {
            'main_id': self.id,
            'table11_2_1': u'Алданги торгуулийн зардал'}))
        report_table11_2_list.append((0, 0, {
            'main_id': self.id,
            'table11_2_1': u'Хандивийн зардал'}))
        report_table11_2_list.append((0, 0, {
            'main_id': self.id,
            'table11_2_1': u'Найдваргүй авлагын зардал'}))
        report_table11_2_list.append((0, 0, {
            'main_id': self.id,
            'table11_2_1': u'Бусад'}))

        # 12. ОРЛОГЫН ТАТВАРЫН ЗАРДАЛ
        report_table12_list.append((0, 0, {
            'main_id': self.id,
            'table12_1': u'Тайлангийн үеийн орлогын татварын зардал'}))
        report_table12_list.append((0, 0, {
            'main_id': self.id,
            'table12_1': u'Хойшлогдсон татварын зардал /орлого/'}))

        res.update({
               'report_table1_ids':report_table1_list,
               'report_table2_ids':report_table2_list,
               'report_table4_ids':report_table4_list,
               'report_table5_ids':report_table5_list,
               'report_table6_1_ids':report_table6_1_list,
               'report_table6_2_ids': report_table6_2_list,
               'report_table7_1_ids':report_table7_1_list,
               'report_table7_2_ids': report_table7_2_list,
               'report_table8_1_ids': report_table8_1_list,
               'report_table8_2_ids': report_table8_2_list,
               'report_table8_3_ids': report_table8_3_list,
               'report_table8_4_ids': report_table8_4_list,
               'report_table9_1_ids': report_table9_1_list,
               'report_table9_2_ids': report_table9_2_list,
               'report_table9_3_ids': report_table9_3_list,
               'report_table9_4_ids': report_table9_4_list,
               'report_table9_5_ids': report_table9_5_list,
               'report_table11_1_ids': report_table11_1_list,
               'report_table11_2_ids': report_table11_2_list,
               'report_table12_ids': report_table12_list,
               })
        return res

