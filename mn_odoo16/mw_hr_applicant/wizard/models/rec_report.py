# # -*- coding: utf-8 -*-
# import base64
# try:
#     # Python 2 support
#     from base64 import encodestring
# except ImportError:
#     # Python 3.9.0+ support
#     from base64 import encodebytes as encodestring
# import time
# import xlsxwriter
# from odoo.exceptions import UserError, AccessError
# from io import BytesIO
# import base64
# from datetime import datetime, timedelta

# from odoo import tools
# from odoo import api, fields, models
# DATE_FORMAT = "%Y-%m-%d"

# class ApplicantReport(models.TransientModel):
#     _name = "applicant.report"
#     _descriptin = "Applicant report" 

#     start_date = fields.Date('Эхлэх огноо')
#     end_date = fields.Date('Дуусах огноо')
#     company_id = fields.Many2one('res.company',string='Компани')
#     sector_id = fields.Many2one('hr.department',string='Сектор')
#     department_id = fields.Many2one('hr.department',string='Хэлтэс')

#     def export_report(self):
#         ctx = dict(self._context)
#         output = BytesIO()
#         workbook = xlsxwriter.Workbook(output)

#         sheet = workbook.add_worksheet(u'СШ тайлан')

#         file_name = 'СШ тайлан'

#         h1 = workbook.add_format({'bold': 1})
#         h1.set_font_size(12)

#         theader = workbook.add_format({'bold': 1})
#         theader.set_font_size(9)
#         theader.set_text_wrap()
#         theader.set_font('Times new roman')
#         theader.set_align('center')
#         theader.set_align('vcenter')
#         theader.set_border(style=1)
#         theader.set_bg_color('#BEC5D1')

#         theader3 = workbook.add_format({'bold': 1})
#         theader3.set_font_size(11)
#         theader3.set_font('Times new roman')
#         theader3.set_align('left')
#         theader3.set_align('vcenter')

#         contest_date_center = workbook.add_format({'num_format': 'YYYY-MM-DD'})
#         contest_date_center.set_text_wrap()
#         contest_date_center.set_font_size(9)
#         contest_date_center.set_border(style=1)
#         contest_date_center.set_align('vcenter')


#         contest_left = workbook.add_format()
#         contest_left.set_text_wrap()
#         contest_left.set_font_size(9)
#         contest_left.set_font('Times new roman')
#         contest_left.set_align('left')
#         contest_left.set_align('vcenter')
#         contest_left.set_border(style=1)

#         contest_center = workbook.add_format()
#         contest_center.set_text_wrap(True)
#         contest_center.set_font_size(9)
#         contest_center.set_font('Times new roman')
#         contest_center.set_align('center')
#         contest_center.set_align('vcenter')
#         contest_center.set_border(style=1)
#         contest_center.set_num_format('#,##0')

#         rowx=3
#         sheet.merge_range(1,1,1,5, u'Бүрдүүлэлтийн шинжилгээ', theader3),

#         sheet.merge_range(rowx,1,rowx+1,1, u'№', theader),
#         sheet.merge_range(rowx,2,rowx+1,2, u'Компани', theader),
#         sheet.merge_range(rowx,3,rowx+1,3, u'Алба / нэгж', theader),
#         sheet.merge_range(rowx,4,rowx+1,4, u'Албан тушаал', theader),
#         sheet.merge_range(rowx,5,rowx+1,5, u'Батлагдсан орон тоо', theader),
#         sheet.merge_range(rowx,6,rowx+1,6, u'Бүртгэлтэй орон тоо', theader),
#         sheet.merge_range(rowx,7,rowx+1,7, u'Сул орон тоо', theader),
#         sheet.merge_range(rowx,8,rowx+1,8, u'Хангалтын хувь', theader),
#         sheet.merge_range(rowx,9,rowx+1,9, u'Овог', theader),
#         sheet.merge_range(rowx,10,rowx+1,10, u'Ажилтны нэр', theader),
#         sheet.merge_range(rowx,11,rowx+1,11, u'Регистр', theader),
#         sheet.merge_range(rowx,12,rowx+1,12, u'Ажилд орсон огноо', theader),
#         sheet.merge_range(rowx,13,rowx+1,13, u'Ажилтны төлөв', theader),
#         sheet.merge_range(rowx,14,rowx+1,14, u'СШ хийсэн ХН мэргэжилтэн', theader),
#         sheet.merge_range(rowx,15,rowx+1,15, u'ХН-ийн захиалга өгсөн огноо', theader),
#         sheet.merge_range(rowx,16,rowx+1,16, u'Бүрдүүлэлт хийгдсэн огноо', theader),
#         sheet.merge_range(rowx,17,rowx+1,17, u'Бүрдүүлэлт хийгдэхэд шаардагдсан хугацаа', theader),
        
        
#         rowx+=2
        
#         sheet.set_column('A:A', 2)
#         sheet.set_column('B:B', 5)
#         sheet.set_column('C:C', 15)
#         sheet.set_column('D:D', 10)
#         sheet.set_column('E:E', 13)
#         sheet.set_column('F:F', 13)
#         sheet.set_column('G:G', 15)
#         sheet.set_column('H:H', 8)
#         sheet.set_column('I:I', 10)
#         sheet.set_column('J:J', 9)
#         sheet.set_column('K:K', 10)
#         sheet.set_column('L:L', 10)
#         sheet.set_column('M:M', 15)
#         sheet.set_column('N:N', 25)
#         sheet.set_column('O:O', 15)
#         sheet.set_column('P:P', 15)
#         sheet.set_column('R:R', 20)
#         sheet.set_column('Q:Q', 15)

#         query_har = """SELECT 
# 			hj.no_of_recruitment as no_of_recruitment,
# 			hj.no_of_employee as no_of_employee,
#             har.request_date as request_date,
#             rc.name as res_company_id,
#             hj.id as job,
#             hd.name as department_id,
#             har.id as har_id
# 			FROM hr_applicant_request har 
#             LEFT JOIN res_company rc ON rc.id=har.res_company_id
#             LEFT JOIN hr_job hj ON hj.id=har.job_id
#             LEFT JOIN hr_department hd ON hd.id=har.request_department_id
#             WHERE har.request_date >='%s' and har.request_date <='%s' and  hj.active = 'true' and har.res_company_id = '%s'
# 			ORDER BY har.request_date
#             """ % (self.start_date, self.end_date,self.company_id.id)
#         self.env.cr.execute(query_har)
#         records = self.env.cr.dictfetchall()
#         n =1
#         for rec in records:
#             query_he = """
#                 SELECT 
#                 he.last_name as last_name,
#                 he.name as name,
#                 he.passport_id as passport_id,
#                 he.engagement_in_company as engagement_in_company,
#                 he.id as he_id
#                 FROM hr_employee he
#                 LEFT JOIN hr_job hj ON hj.id=he.job_id
#                 WHERE he.job_id=%s and he.employee_type != 'resigned' """ % (rec['job'])
#             self.env.cr.execute(query_he)
#             recs = self.env.cr.dictfetchall()
#             t = 0
#             for r in recs:
#                 hr_id = self.env['hr.employee'].sudo().browse(int(r['he_id']))
#                 rowl = rowx
#                 rowl += t
#                 sheet.write(rowl, 9, r['last_name'], contest_center)
#                 sheet.write(rowl, 10, r['name'],contest_center)
#                 sheet.write(rowl, 11, r['passport_id'], contest_center)
#                 sheet.write(rowl, 12, r['engagement_in_company'], contest_date_center)
#                 sheet.write(rowl, 13, dict(hr_id._fields['employee_type'].selection).get(hr_id.employee_type), contest_center)
#                 t += 1

#             job_name = self.env['hr.job'].sudo().search([('id','=',rec['job'])]).name
#             if rec['no_of_recruitment'] or rec['no_of_employee']:
#                 expected_emp = rec['no_of_recruitment']-rec['no_of_employee']
#             else:
#                 raise UserError(("Бүх албан тушаал дээр бүтэц орон тоог оруулж батлана уу"))
#             if t <= 1:
#                 sheet.write(rowx, 1, n, contest_center)
#                 sheet.write(rowx, 2, rec['res_company_id'], contest_center)
#                 sheet.write(rowx, 3, rec['department_id'], contest_center)
#                 sheet.write(rowx, 4, job_name, contest_center)
#                 sheet.write(rowx, 5, rec['no_of_recruitment'],contest_center)
#                 sheet.write(rowx, 6, rec['no_of_employee'], contest_center)
#                 sheet.write(rowx, 7, expected_emp, contest_center)
#                 sheet.write(rowx, 8, str(rec['no_of_employee']*100/rec['no_of_recruitment'])+ '%', contest_center)
#                 sheet.write(rowx, 15, rec['request_date'],contest_date_center)
                
#             else:
#                 sheet.merge_range(rowx, 1, rowx+t-1,1,n, contest_center)
#                 sheet.merge_range(rowx, 2, rowx+t-1,2,rec['res_company_id'], contest_center)
#                 sheet.merge_range(rowx, 3, rowx+t-1,3,rec['department_id'], contest_center)
#                 sheet.merge_range(rowx, 4, rowx+t-1,4,job_name, contest_center)
#                 sheet.merge_range(rowx, 5, rowx+t-1,5,rec['no_of_recruitment'],contest_center)
#                 sheet.merge_range(rowx, 6, rowx+t-1,6,rec['no_of_employee'], contest_center)
#                 sheet.merge_range(rowx, 7, rowx+t-1,7,expected_emp, contest_center)
#                 sheet.merge_range(rowx, 8, rowx+t-1,8,str(rec['no_of_employee']*100/rec['no_of_recruitment'])+ '%', contest_center)
#                 sheet.merge_range(rowx, 15, rowx+t-1,15,rec['request_date'],contest_date_center)

#             rowx+=t
#             n +=1
#         workbook.close()
#         out = encodestring(output.getvalue())
#         excel_id = self.env['report.excel.output'].create(
#             {'data': out, 'name': file_name+'.xlsx'})
#         return {
#             'name': 'Export Result',
#             'view_mode': 'form',
#             'res_model': 'report.excel.output',
#             'view_id': False,
#             'type': 'ir.actions.act_url',
#             'url': "web/content/?model=report.excel.output&id=" + str(excel_id.id) + "&filename_field=filename&downlodr=true&field=data&filename=" + excel_id.name,
#             'target': 'new',
#             'nodestroy': True,
#         }
    
#     def _symbol(self, row, col):
#         return self._symbol_col(col) + str(row+1)

#     def _symbol_col(self, col):
#         excelCol = str()
#         div = col+1
#         while div:
#             (div, mod) = divmod(div-1, 26)
#             excelCol = chr(mod + 65) + excelCol
#         return excelCol