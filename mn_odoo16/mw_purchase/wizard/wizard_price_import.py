# -*- coding: utf-8 -*-
from odoo import fields, models
from odoo.exceptions import UserError
from tempfile import NamedTemporaryFile
import xlrd, os
import base64
import xlrd

class PriceListImportFromExcel(models.TransientModel):
	_name = 'price.import.from.excel'
	_description = "price import from excel"

	name = fields.Char(u'Name', required=True,)
	excel_data = fields.Binary(string='Excel file', required=True)
	solution = fields.Char(u'nrows')

	def import_from_excel(self):
		fileobj = NamedTemporaryFile('w+b')
		fileobj.write(base64.decodebytes(self.excel_data))
		fileobj.seek(0)
		if not os.path.isfile(fileobj.name):
			raise UserError(u'Importing error.\nCheck excel file!')
		book = xlrd.open_workbook(fileobj.name)
		try:
			sheet = book.sheet_by_index(0)
		except:
			raise UserError(u'Wrong Sheet number.')

		nrows = sheet.nrows
		count = 0 
		for r in range(1,nrows):
			row = sheet.row(r)
			if row[0].value and row[1].value and row[2].value and row[3].value and row[4].value:
				partner_name = str(row[0].value)
				try:
					tmpl_default_code = str(int(row[1].value))
				except ValueError:
					tmpl_default_code = str(row[1].value)
				try:
					default_code = str(int(row[2].value))
				except ValueError:
					default_code = str(row[2].value)
				currency = str(row[3].value)
				price = row[4].value

				product_supp = self.env['product.supplierinfo']
				product_template = False
				product_obj = self.env['product.product'].search([('default_code','=',tmpl_default_code)], limit=1)
				product_product_obj = self.env['product.product'].search([('default_code','=',default_code)], limit=1)
				if product_obj:
					product_template = product_obj.product_tmpl_id
				
				currency_obj = self.env['res.currency'].search([('name','=',currency)])
				partner_obj = self.env['res.partner'].search([('name','=',partner_name)])
				if product_template and product_product_obj and currency_obj and partner_obj:
					ppp = product_supp.search(['|',('product_tmpl_id','=',product_template.id),('product_id','=',product_product_obj.id),('currency_id','=',currency_obj.id),('name','=',partner_obj.id)], limit=1)
					if ppp and ppp.product_id:
						ppp.price = price
					elif ppp and not ppp.product_id:
						ppp.product_id = product_product_obj.id
						ppp.price = price
					else:
						product_supp.create({
							'name': partner_obj.id,
							'product_tmpl_id': product_template.id,
							'product_id': product_product_obj.id,
							'currency_id': currency_obj.id,
							'price': price
						})
					count +=1
			self.solution = "%s бараа импортлосноос %s бараа импортлогдов." %(nrows, count)
			action = self.env.ref('mw_purchase.action_import_result_view')
			result = action.read()[0]
			res = self.env.ref('mw_purchase.wizard_import_result_view', False)
			result['views'] = [(res and res.id or False, 'form')]
			result['res_id'] = self.id
		return True
