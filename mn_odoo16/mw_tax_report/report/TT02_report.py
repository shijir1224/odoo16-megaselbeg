# -*- coding: utf-8 -*-
from odoo import fields, models, _
import time
from io import BytesIO
import xlsxwriter
import base64
from odoo.exceptions import UserError
from xlsxwriter.utility import xl_rowcol_to_cell

class MwTaxReportTt02(models.TransientModel):
	_name = 'mw.tax.report.tt02'
	_description = "ААНОАТ-ын тайлан /ТТ-02/"

	date_start = fields.Date(string=u'Эхлэх огноо', required=True, default=time.strftime('%Y-%m-01'))
	date_end = fields.Date(string=u'Дуусах огноо', required=True, default=fields.Date.context_today)

	def action_mw_tax_report_tt02_export(self):
		if self.date_start <= self.date_end:
			output = BytesIO()
			workbook = xlsxwriter.Workbook(output)
			file_name = 'ААНОАТ-ын тайлан /ТТ-02/ ('+self.date_start.strftime("%m.%d.%Y")+'-'+self.date_end.strftime("%m.%d.%Y")+').xlsx'

			# гарчиг цагаан
			header = workbook.add_format({'bold': 1})
			header.set_font_size(16)
			header.set_font('Times new roman')
			header.set_align('center')
			header.set_align('vcenter')

			company_name = workbook.add_format()
			company_name.set_font_size(9)
			company_name.set_font('Times new roman')
			company_name.set_align('left')
			company_name.set_align('vcenter')


			company_author = workbook.add_format()
			company_author.set_font_size(12)
			company_author.set_font('Times new roman')
			company_author.set_align('left')
			company_author.set_align('vcenter')

			contest_header_center = workbook.add_format({'bold': 1})
			contest_header_center.set_text_wrap()
			contest_header_center.set_font_size(12)
			contest_header_center.set_font('Times new roman')
			contest_header_center.set_align('center')
			contest_header_center.set_align('vcenter')
			contest_header_center.set_border(style=1)

			contest_light_left = workbook.add_format({'bold': 1})
			contest_light_left.set_font_size(12)
			contest_light_left.set_font('Times new roman')
			contest_light_left.set_align('left')
			contest_light_left.set_align('vcenter')
			contest_light_left.set_border(style=1)

			contest_light_left_no_bold = workbook.add_format()
			contest_light_left_no_bold.set_font_size(12)
			contest_light_left_no_bold.set_font('Times new roman')
			contest_light_left_no_bold.set_align('left')
			contest_light_left_no_bold.set_align('vcenter')
			contest_light_left_no_bold.set_border(style=1)

			contest_light_left_small = workbook.add_format()
			contest_light_left_small.set_text_wrap()
			contest_light_left_small.set_font_size(11)
			contest_light_left_small.set_font('Times new roman')
			contest_light_left_small.set_align('left')
			contest_light_left_small.set_align('vcenter')
			contest_light_left_small.set_border(style=1)
			contest_light_left_small.set_indent(1)


			contest_light_left_small_3 = workbook.add_format()
			contest_light_left_small_3.set_text_wrap()
			contest_light_left_small_3.set_font_size(11)
			contest_light_left_small_3.set_font('Times new roman')
			contest_light_left_small_3.set_align('left')
			contest_light_left_small_3.set_align('vcenter')
			contest_light_left_small_3.set_border(style=1)
			contest_light_left_small_3.set_indent(3)


			contest_signature = workbook.add_format()
			contest_signature.set_text_wrap()
			contest_signature.set_font_size(12)
			contest_signature.set_font('Times new roman')
			contest_signature.set_align('left')
			contest_signature.set_align('vcenter')
			contest_signature.set_indent(15)

			contest_signature1 = workbook.add_format()
			contest_signature1.set_text_wrap()
			contest_signature1.set_font_size(12)
			contest_signature1.set_font('Times new roman')
			contest_signature1.set_align('left')
			contest_signature1.set_align('vcenter')


			contest_light_green_center = workbook.add_format()
			contest_light_green_center.set_font_size(12)
			contest_light_green_center.set_font('Times new roman')
			contest_light_green_center.set_align('center')
			contest_light_green_center.set_align('vcenter')
			contest_light_green_center.set_border(style=1)
			contest_light_green_center.set_bg_color('#e2f0d9')

			contest_left = workbook.add_format()
			contest_left.set_font_size(9)
			contest_left.set_font('Times new roman')
			contest_left.set_align('left')
			contest_left.set_align('vcenter')
			contest_left.set_border(style=1)

			contest_center = workbook.add_format()
			contest_center.set_font_size(9)
			contest_center.set_font('Times new roman')
			contest_center.set_align('center')
			contest_center.set_align('vcenter')
			contest_center.set_border(style=1)

			contest_grey = workbook.add_format()
			contest_grey.set_font_size(9)
			contest_grey.set_font('Times new roman')
			contest_grey.set_align('center')
			contest_grey.set_align('vcenter')
			contest_grey.set_border(style=1)
			contest_grey.set_bg_color('#e7e6e6')


			sheet = workbook.add_worksheet(u'TT /02/')
			sheet.merge_range(2, 0, 2, 3, u'АЖ АХУЙН НЭГЖИЙН ОРЛОГЫН АЛБАН ТАТВАРЫН ТАЙЛАН', header)
			sheet.write(4, 0, u"%s оны %s сарын %s өдөр" %(time.strftime('%Y'),time.strftime('%m'),time.strftime('%d')), company_name)

			sheet.set_column('A:A', 80)
			sheet.set_column('B:B', 15)
			sheet.set_column('C:C', 20)
			sheet.set_column('D:K', 15)


			# HEADER
			row = 5
			sheet.write(row, 0, u'Үзүүлэлтүүд', contest_header_center)
			sheet.write(row, 1, u'Мөр', contest_header_center)
			sheet.write(row, 2, u'Дүн', contest_header_center)
			row = 6
			sheet.write(row, 0, u'I', contest_header_center)
			sheet.write(row, 1, u'II', contest_header_center)
			sheet.write(row, 2, u'III', contest_header_center)
			row = 7
			sheet.merge_range(row, 0, row, 2, u'А. Нийтлэг хувь хэмжээгээр ногдуулах албан татварын тооцоолол', contest_light_left)
			sheet.write(8, 0, u'1. Нийт орлогын дүн', contest_light_left)
			sheet.write(8, 1, u'1', contest_header_center)
			sheet.write(8, 2, u'', contest_header_center)
			sheet.write(9, 0, u'1.1 Татвараас чөлөөлөгдөх орлого', contest_light_left_small)
			sheet.write(9, 1, u'2', contest_header_center)
			sheet.write(9, 2, u'', contest_header_center)
			sheet.write(10, 0, u'1.2 Тусгай хэмжээгаар татвар ногдох орлого', contest_light_left_small)
			sheet.write(10, 1, u'3', contest_header_center)
			sheet.write(10, 2, u'', contest_header_center)
			sheet.write(11, 0, u'1.3 Бусад орлогын дүн', contest_light_left_small)
			sheet.write(11, 1, u'4', contest_header_center)
			sheet.write(11, 2, u'', contest_header_center)
			sheet.write(12, 0, u'1.4 Нийтлэг хувь хэмжээгээр татвар ногдох орлого', contest_light_left_small)
			sheet.write(12, 1, u'5', contest_header_center)
			sheet.write(12, 2, u'', contest_header_center)
			sheet.write(13, 0, u'Бараа, ажил, үйлчилгээний борлуулалтын орлого', contest_light_left_small_3)
			sheet.write(13, 1, u'6', contest_header_center)
			sheet.write(13, 2, u'', contest_header_center)
			sheet.write(14, 0, u'Төлбөрт таавар, бооцоот тоглоом, эд мөнгөний хонжворт сугалааны үйл ажиллагааны орлого', contest_light_left_small_3)
			sheet.write(14, 1, u'7', contest_header_center)
			sheet.write(14, 2, u'', contest_header_center)
			sheet.write(15, 0, u'Техникийн, удирдлагын, зөвлөхийн болон бусад үйлчилгээний орлого', contest_light_left_small_3)
			sheet.write(15, 1, u'8', contest_header_center)
			sheet.write(15, 2, u'', contest_header_center)
			sheet.write(16, 0, u'Үнэ төлбөргүйгээр бусдаас авсан бараа, ажил, үйлчилгээний орлого', contest_light_left_small_3)
			sheet.write(16, 1, u'9', contest_header_center)
			sheet.write(16, 2, u'', contest_header_center)
			sheet.write(17, 0, u'Үл хөдлөх эд хөрөнгө ашиглуулсан болон түрээслүүлсний орлого', contest_light_left_small_3)
			sheet.write(17, 1, u'10', contest_header_center)
			sheet.write(17, 2, u'', contest_header_center)
			sheet.write(18, 0, u'Хөдлөх хөрөнгө ашиглуулсан болон түрээслүүлсний орлого', contest_light_left_small_3)
			sheet.write(18, 1, u'11', contest_header_center)
			sheet.write(18, 2, u'', contest_header_center)
			sheet.write(19, 0, u'Хувьцаа, үнэт цаас, санхүүгийн бусад хэрэгсэл борлуулсны орлого', contest_light_left_small_3)
			sheet.write(19, 1, u'12', contest_header_center)
			sheet.write(19, 2, u'', contest_header_center)
			sheet.write(20, 0, u'Бусад биет бус хөрөнгө болон хөдлөх эд хөрөнгө борлуулсан, шилжүүлсны орлого', contest_light_left_small_3)
			sheet.write(20, 1, u'13', contest_header_center)
			sheet.write(20, 2, u'', contest_header_center)
			sheet.write(21, 0, u'Гэрээгээр хүлээсэн үүргээ биелүүлээгүй этгээдээс авсан хүү, анз /торгууль, алданга/, хохирлын нөхөн төлбөрийн орлого', contest_light_left_small_3)
			sheet.write(21, 1, u'14', contest_header_center)
			sheet.write(21, 2, u'', contest_header_center)
			sheet.write(22, 0, u'Гадаад валютын ханшийн зөрүүгийн бодит орлого', contest_light_left_small_3)
			sheet.write(22, 1, u'15', contest_header_center)
			sheet.write(22, 2, u'', contest_header_center)
			sheet.write(23, 0, u'Албан татвар ногдох', contest_light_left_small_3)
			sheet.write(23, 1, u'16', contest_header_center)
			sheet.write(23, 2, u'', contest_header_center)
			sheet.write(24, 0, u'2. Нийт зардлын дүн', contest_light_left)
			sheet.write(24, 1, u'17', contest_header_center)
			sheet.write(24, 2, u'', contest_header_center)
			sheet.write(25, 0, u'2.1 Борлуулалтын өртөг', contest_light_left_small)
			sheet.write(25, 1, u'18', contest_header_center)
			sheet.write(25, 2, u'', contest_header_center)
			sheet.write(26, 0, u'2.2 Удирдлагын болон борлуулалтын үйл ажиллагааны зардал', contest_light_left_small)
			sheet.write(26, 1, u'19', contest_header_center)
			sheet.write(26, 2, u'', contest_header_center)
			sheet.write(27, 0, u'2.3 Үндсэн үйл ажиллагааны зардал', contest_light_left_small)
			sheet.write(27, 1, u'20', contest_header_center)
			sheet.write(27, 2, u'', contest_header_center)
			sheet.write(28, 0, u'3. Татвар төлөхийн өмнөх ашиг, алдагдал', contest_light_left)
			sheet.write(28, 1, u'21', contest_header_center)
			sheet.write(28, 2, u'', contest_header_center)
			sheet.write(29, 0, u'4. Татвар төлөхийн өмнөх ашиг, алдагдалыг нэмэгдүүлэх дүн', contest_light_left_no_bold)
			sheet.write(29, 1, u'22', contest_header_center)
			sheet.write(29, 2, u'', contest_header_center)
			sheet.write(30, 0, u'5. Татвар төлөхийн өмнөх ашиг, алдагдалыг бууруулах дүн', contest_light_left_no_bold)
			sheet.write(30, 1, u'23', contest_header_center)
			sheet.write(30, 2, u'', contest_header_center)
			sheet.write(31, 0, u'6. Татвар ногдуулах орлого', contest_light_left_no_bold)
			sheet.write(31, 1, u'24', contest_header_center)
			sheet.write(31, 2, u'', contest_header_center)
			sheet.write(32, 0, u'7. Сайн дурын даатгалын хураамжийн хэтрэлт', contest_light_left_no_bold)
			sheet.write(32, 1, u'25', contest_header_center)
			sheet.write(32, 2, u'', contest_header_center)
			sheet.write(33, 0, u'8. Зохицуулагдсан татвар ногдуулах орлогын дүн', contest_light_left_no_bold)
			sheet.write(33, 1, u'26', contest_header_center)
			sheet.write(33, 2, u'', contest_header_center)
			sheet.write(34, 0, u'9. Өмнөх жилүүдийн татварын тайлангаар гарсан татварын албаар баталгаажуулсан алдагдлаас тайлант хугацаанд шилжүүлсэн дүн', contest_light_left_no_bold)
			sheet.write(34, 1, u'27', contest_header_center)
			sheet.write(34, 2, u'', contest_header_center)
			sheet.write(35, 0, u'10. Нийтлэг хувь хэмжээгээр татвар ногдуулах орлого', contest_light_left_no_bold)
			sheet.write(35, 1, u'28', contest_header_center)
			sheet.write(35, 2, u'', contest_header_center)
			sheet.write(36, 0, u'11. Ногдуулсан албан татвар', contest_light_left_no_bold)
			sheet.write(36, 1, u'29', contest_header_center)
			sheet.write(36, 2, u'', contest_header_center)
			sheet.write(37, 0, u'12. Хуулийн 22.5-д заасны дагуу хөнгөлөгдөх татвар', contest_light_left_no_bold)
			sheet.write(37, 1, u'30', contest_header_center)
			sheet.write(37, 2, u'', contest_header_center)
			sheet.write(38, 0, u'13. НИЙТЛЭГ ХУВЬ ХЭМЖЭЭГЭЭР НОГДУУЛСАН ТӨЛБӨЛ ЗОХИХ АЛБАН ТАТВАР', contest_light_left_no_bold)
			sheet.write(38, 1, u'31', contest_header_center)
			sheet.write(38, 2, u'', contest_header_center)
			sheet.merge_range(39, 0, 39, 2, u'Б. Тусгай хувь хэмжээгээр ногдуулах албан татварын тооцоолол:', contest_light_left)
			sheet.write(40, 0, u'14. Тусгай хувь хэмжээгээр татвар ногдох ', contest_light_left)
			sheet.write(40, 1, u'32', contest_header_center)
			sheet.write(40, 2, u'', contest_header_center)
			sheet.write(41, 0, u'15. Төрийн байгууллагаас олгосон эрх борлуулсан, шилжүүлсний орлого', contest_light_left_no_bold)
			sheet.write(41, 1, u'33', contest_header_center)
			sheet.write(41, 2, u'', contest_header_center)
			sheet.write(42, 0, u'Төрийн байгууллагаас эрх олгосон тохиолдолд эрх авахтай холбогдон төрийн байгууллагад төлсөн баримтаар нотлогдох төлбөр, хураамж', contest_light_left_small_3)
			sheet.write(42, 1, u'34', contest_header_center)
			sheet.write(42, 2, u'', contest_header_center)
			sheet.write(43, 0, u'Бусдаас худалдаж, шилжүүлж авсан тохиолдолд хэлцлийн дагуу худалдах, шилжүүлэн авахад төлсөн, шилжүүлсэн баримтаар нотлогдох төлбөр', contest_light_left_small_3)
			sheet.write(43, 1, u'35', contest_header_center)
			sheet.write(43, 2, u'', contest_header_center)
			sheet.write(44, 0, u'Татвар ногдуулах орлого', contest_light_left_small_3)
			sheet.write(44, 1, u'36', contest_header_center)
			sheet.write(44, 2, u'', contest_header_center)
			sheet.write(45, 0, u'Эрх борлуулсан, шилжүүлсний орлогод ногдох татвар', contest_light_left_small_3)
			sheet.write(45, 1, u'37', contest_header_center)
			sheet.write(45, 2, u'', contest_header_center)
			sheet.write(46, 0, u'16. Эрхийн шимтгэлийн орлого', contest_light_left_no_bold)
			sheet.write(46, 1, u'38', contest_header_center)
			sheet.write(46, 2, u'', contest_header_center)
			sheet.write(47, 0, u'17. Ногдол ашгийн орлого', contest_light_left_no_bold)
			sheet.write(47, 1, u'39', contest_header_center)
			sheet.write(47, 2, u'', contest_header_center)
			sheet.write(48, 0, u'18. Байгаль орчинд нөлөөлөх байдлын үнэлгээний тухай хуулийн 9.11, Газрын тосны тухай хуулийн 11.1.4, 12.5-д заасны дагуу буцаан олгосон мөнгөн хөрөнгө', contest_light_left_no_bold)
			sheet.write(48, 1, u'40', contest_header_center)
			sheet.write(48, 2, u'', contest_header_center)
			sheet.write(49, 0, u'19. Даатгалын нөхөн төлбөрийн орлого', contest_light_left_no_bold)
			sheet.write(49, 1, u'41', contest_header_center)
			sheet.write(49, 2, u'', contest_header_center)
			sheet.write(50, 0, u'20. Хүүгийн орлого', contest_light_left_no_bold)
			sheet.write(50, 1, u'42', contest_header_center)
			sheet.write(50, 2, u'', contest_header_center)
			sheet.write(51, 0, u'Ногдуулсан татвар', contest_light_left_small_3)
			sheet.write(51, 1, u'43', contest_header_center)
			sheet.write(51, 2, u'', contest_header_center)
			sheet.write(52, 0, u'21. Монгол улсын арилжааны банкны гадаад, дотоодын эх үүсвэрээс татсан зээл, өрийн хэрэгслийн хүүгийн орлого', contest_light_left_no_bold)
			sheet.write(52, 1, u'44', contest_header_center)
			sheet.write(52, 2, u'', contest_header_center)
			sheet.write(53, 0, u'22. Ашигт малтмал, цацраг идэвхт ашигт малтмал, газрын тосны хайгуулын болон ашиглалтын тусгай зөвшөөрөл эзэмшдэггүй / Үүнд энэ хуулийн 4.1.12, 30.1-д заасан этгээд мөн хамаарна./ Монгол Улсад байрладаг албан татвар төлөгчийн гадаад, дотоодын үнэт цаасны анхдагч болон хоёрдогч зах зээлд нээлттэй арилжаалах өрийн хэрэгсэл, нэгж эрх худалдан авсан албан татвар төлөгчийн хүүгийн орлого', contest_light_left_no_bold)
			sheet.write(53, 1, u'45', contest_header_center)
			sheet.write(53, 2, u'', contest_header_center)
			sheet.write(54, 0, u'Ногдуулсан татвар', contest_light_left_small_3)
			sheet.write(54, 1, u'46', contest_header_center)
			sheet.write(54, 2, u'', contest_header_center)
			sheet.write(55, 0, u'23. Үл хөдлөх эд хөрөнгө борлуулсан, шилжүүлсний орлого', contest_light_left_no_bold)
			sheet.write(55, 1, u'47', contest_header_center)
			sheet.write(55, 2, u'', contest_header_center)
			sheet.write(56, 0, u'Ногдуулсан татвар', contest_light_left_small_3)
			sheet.write(56, 1, u'48', contest_header_center)
			sheet.write(56, 2, u'', contest_header_center)
			sheet.write(57, 0, u'24. Төлбөрт таавар, бооцоот тоглоом, эд мөнгөний хонжворт сугалаанаас хожсон орлого', contest_light_left_no_bold)
			sheet.write(57, 1, u'49', contest_header_center)
			sheet.write(57, 2, u'', contest_header_center)
			sheet.write(58, 0, u'Ногдуулсан татвар', contest_light_left_small_3)
			sheet.write(58, 1, u'50', contest_header_center)
			sheet.write(58, 2, u'', contest_header_center)
			sheet.write(59, 0, u'25. ТУСГАЙ ХХУВЬ ХЭМЖЭЭГЭЭР НОГДУУЛСАН АЛБАН ТАТВАР', contest_light_left_no_bold)
			sheet.write(59, 1, u'51', contest_header_center)
			sheet.write(59, 2, u'', contest_header_center)
			sheet.merge_range(60, 0, 60, 2, u'В. Албан татвар ногдуулах тооцоолол:', contest_light_left)
			sheet.write(60, 0, u'26. Хуулийн дагуу бусдад суутгуулсан албан татвар', contest_light_left_no_bold)
			sheet.write(60, 1, u'52', contest_header_center)
			sheet.write(60, 2, u'', contest_header_center)
			sheet.write(61, 0, u'27. Төлбөл зохих албан татвараас хасагдах гадаад улсад ногдуулан төлсөн албан татвар', contest_light_left_no_bold)
			sheet.write(61, 1, u'53', contest_header_center)
			sheet.write(61, 2, u'', contest_header_center)
			sheet.write(62, 0, u'28. НИЙТ ТӨЛБӨЛ ЗОХИХ ТАТВАРЫН ДҮН', contest_light_left)
			sheet.write(62, 1, u'54', contest_header_center)
			sheet.write(62, 2, u'', contest_header_center)
			sheet.write(63, 0, u'29. Хуулийн 22.1-т заасны дагуу албан татварын хөнгөлөн буцаан авахаар тооцсон дүн', contest_light_left_no_bold)
			sheet.write(63, 1, u'55', contest_header_center)
			sheet.write(63, 2, u'', contest_header_center)
			sheet.write(65, 0, u'Тайланг үнэн зөв гаргасан:', contest_signature)
			sheet.merge_range(65, 1, 65, 2, u'Тайланг хүлээн авсан:', contest_signature1)
			sheet.write(67, 0, u'Захирал /дарга/.................', contest_signature)
			sheet.merge_range(67, 1, 67, 2, u'Татварын улсын байцаагч.................', contest_signature1)
			sheet.write(69, 0, u'Ерөнхий нягтлан бодогч.................', contest_signature)
			sheet.write(71, 0, u'Итгэмжлэгдсэн нягтлан бодогч............./.................', contest_signature)

			#### Хавсралт 1
			sheet1 = workbook.add_worksheet(u'ХМ-02(1)')
			sheet1.merge_range(2, 0, 2, 2, u'Албан татвараас чөлөөлөгдөх орлогын мэдээ /ХМ-02(1)/', header)

			sheet1.set_column('A:A', 5)
			sheet1.set_column('B:B', 80)
			sheet1.set_column('C:C', 15)
			sheet1.set_column('D:K', 15)


			# HEADER
			row = 5
			sheet1.write(row, 0, u'Д/Д', contest_header_center)
			sheet1.write(row, 1, u'Чөлөөлөгдөх төрөл', contest_header_center)
			sheet1.write(row, 2, u'Нийт орлого', contest_header_center)


			#### Хавсралт 2
			sheet2 = workbook.add_worksheet(u'ХМ-02(2)')
			sheet2.merge_range(2, 0, 2, 4, u'Нийтлэг хувь хэмжээгээр албан татвар ногдох орлогын мэдээ /ХМ-02(2)/', header)

			sheet2.set_column('A:A', 5)
			sheet2.set_column('B:B', 80)
			sheet2.set_column('C:C', 15)
			sheet2.set_column('D:K', 15)


			# HEADER
			row = 5
			sheet2.write(row, 0, u'Д/Д', contest_header_center)
			sheet2.write(row, 1, u'Борлуулалтын орлогын төрөл', contest_header_center)
			sheet2.write(row, 2, u'Монгол Улсад болон Монгол Улсаас эх үүсвэртэй олсон орлого', contest_header_center)
			sheet2.write(row, 3, u'Гадаад улсад олсон орлого', contest_header_center)
			sheet2.write(row, 4, u'Нийт орлого', contest_header_center)

			#### Хавсралт 2
			sheet3 = workbook.add_worksheet(u'ХМ-02(3)')
			sheet3.merge_range(2, 0, 2, 2, u'Нийт зардал, өртгийн мэдээ /ХМ-02(3)/', header)

			sheet3.set_column('A:A', 5)
			sheet3.set_column('B:B', 80)
			sheet3.set_column('C:C', 15)
			sheet3.set_column('D:K', 15)


			# HEADER
			row = 5
			sheet3.merge_range(row, 0, row, 2, u'А.Нийт зардлын хувиарлалт', company_author)
			row = 6
			sheet3.write(row, 0, u'Д/Д', contest_header_center)
			sheet3.write(row, 1, u'Үзүүлэлтүүд', contest_header_center)
			sheet3.write(row, 2, u'Нийт зардал', contest_header_center)




			workbook.close()
			out = base64.encodebytes(output.getvalue())
			excel_id = self.env['report.excel.output'].create(
				{'data': out, 'name': file_name})

			return {
				'type': 'ir.actions.act_url',
				'url': "web/content/?model=report.excel.output&id=%d&filename_field=filename&download=true&field=data&filename=%s" % (excel_id.id, excel_id.name),
				'target': 'new',
			}
		else:
			raise UserError(_(u'Бичлэг олдсонгүй!'))

	def _symbol(self, row, col):
		return self._symbol_col(col) + str(row+1)

	def _symbol_col(self, col):
		excelCol = str()
		div = col+1
		while div:
			(div, mod) = divmod(div-1, 26)
			excelCol = chr(mod + 65) + excelCol
		return excelCol
