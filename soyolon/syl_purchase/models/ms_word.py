from odoo import  models
from odoo.addons.populating_ms_word_template.models.mailmerge import MailMerge
from datetime import datetime, date
from io import BytesIO
from zipfile import ZipFile, ZIP_DEFLATED
from lxml import etree
import tempfile
from docx import Document
from docx.table import Table
import base64

class IrActionsReport(models.Model):
	_inherit = 'ir.actions.report'

	def export_doc_by_template(self, file_template_data=None, suffix='.docx', file_name_export='export1', datas={}):
		simple_merge = {}
		populating_tables = {}
		file_template = self._convert_binary_to_doc(file_template_data=file_template_data,suffix='.docx')
		document = MailMerge(file_template.name)
		fields = document.get_merge_fields()

		for field in fields:
			childs = field.split('.')
			if len(childs) == 1:
				value = getattr(datas, childs[0], '')
				if isinstance(value, datetime):
					value = self._convert_datetime_usertz_to_utctz(value)
				elif isinstance(value, date):
					value = value.strftime(self.env['res.lang'].search([('code', '=', self.env.user.lang)], limit=1).date_format)
				elif isinstance(value, bool):
					if value == False:
						value = ''
					else:
						value = str(value)
				elif isinstance(value, bytes):
					value = childs[0]
				else:
					if isinstance(value, int) or isinstance(value, float):
						value = self.format_number(value)
					else:
						value = str(value)
				simple_merge[field] = value
			else:
				print ('childschildschilds ',childs)
				if childs[0] == 'line' and len(childs)>1 and childs[1] == 'user_sign':
					print ('datas ',datas)
					childs.remove(childs[0])
					childs.remove(childs[0])
					key = childs[0]
					print ('key ',key)
					data_array = getattr(datas, key)
					childs.remove(key)
					tmp_val = []
					value_field = {}
					numerical_order = 0

					field_if = field.split('.IF.')

					for data in data_array:
						data_check = data
						if len(field_if) > 1:
							condition = field_if[1].split('=')
							if len(condition):
								childs_check = condition[0].split('.')
								value = condition[1]
							else:
								childs_check = field_if[1].split('.')
								value = True

							for child in childs_check:
								data_check = getattr(data_check, child)
							if isinstance(data_check, bool):
								value = bool(value)

							if data_check != value:
								continue

						for child in childs:
							if child == 'IF':
								break
							if child == 'numerical_order':
								data = numerical_order + 1
								numerical_order = data
							elif child == "float_time":
								hour, minute = divmod(data * 60, 60)
								x_tmp = "%02d:%02d" % (hour, minute)
								data = x_tmp
							else:
								image_value = data.id
								data = getattr(data, child)
							if isinstance(data, bytes):
								image_value = str(image_value) + "." + field
								break

						if isinstance(data, (float, int)) == False and data == False:
							data = ''
						elif isinstance(data, bool):
							data = ''
						elif isinstance(data, datetime):
							data = self._convert_datetime_usertz_to_utctz(data)
						elif isinstance(data, date):
							data = data.strftime(
								self.env['res.lang'].search([('code', '=', self.env.user.lang)], limit=1).date_format)
						elif isinstance(data, bytes):
							data = image_value
						else:
							if isinstance(data, int) or isinstance(data, float):
								data = self.format_number(data)
							else:
								data = str(data)
						tmp_val.append(data)

					value_field[field] = tmp_val
					if key in populating_tables:
						populating_tables[key].append(value_field)
					else:
						tmp_value = []
						tmp_value.append(value_field)
						populating_tables[key] = tmp_value
				elif childs[1] == 'user_sign' and len(childs)==2:
					key = childs[0]
					data_array = getattr(datas, key)
					childs.remove(key)
					tmp_val = []
					value_field = {}
					numerical_order = 0

					field_if = field.split('.IF.')

					for data in data_array:
						data_check = data
						if len(field_if) > 1:
							condition = field_if[1].split('=')
							if len(condition):
								childs_check = condition[0].split('.')
								value = condition[1]
							else:
								childs_check = field_if[1].split('.')
								value = True

							for child in childs_check:
								data_check = getattr(data_check, child)
							if isinstance(data_check, bool):
								value = bool(value)

							if data_check != value:
								continue

						for child in childs:
							if child == 'IF':
								break
							if child == 'numerical_order':
								data = numerical_order + 1
								numerical_order = data
							elif child == "float_time":
								hour, minute = divmod(data * 60, 60)
								x_tmp = "%02d:%02d" % (hour, minute)
								data = x_tmp
							else:
								image_value = data.id
								# digital_signature
								data = getattr(data, 'digital_signature')
							if isinstance(data, bytes):
								image_value = str(image_value) + "." + field
								break

						if isinstance(data, (float, int)) == False and data == False:
							data = ''
						elif isinstance(data, bool):
							data = ''
						elif isinstance(data, datetime):
							data = self._convert_datetime_usertz_to_utctz(data)
						elif isinstance(data, date):
							data = data.strftime(
								self.env['res.lang'].search([('code', '=', self.env.user.lang)], limit=1).date_format)
						elif isinstance(data, bytes):
							data = image_value
						else:
							if isinstance(data, int) or isinstance(data, float):
								data = self.format_number(data)
							else:
								data = str(data)
						tmp_val.append(data)

					value_field[field] = tmp_val
					if key in populating_tables:
						populating_tables[key].append(value_field)
					else:
						tmp_value = []
						tmp_value.append(value_field)
						populating_tables[key] = tmp_value
				elif childs[0] == 'line':
					childs.remove(childs[0])
					key = childs[0]
					data_array = getattr(datas, key)
					childs.remove(key)
					tmp_val = []
					value_field = {}
					numerical_order = 0

					field_if = field.split('.IF.')

					for data in data_array:
						data_check = data
						if len(field_if) > 1:
							condition = field_if[1].split('=')
							if len(condition):
								childs_check = condition[0].split('.')
								value = condition[1]
							else:
								childs_check = field_if[1].split('.')
								value = True

							for child in childs_check:
								data_check = getattr(data_check, child)
							if isinstance(data_check, bool):
								value = bool(value)

							if data_check != value:
								continue

						for child in childs:
							if child == 'IF':
								break
							if child == 'numerical_order':
								data = numerical_order + 1
								numerical_order = data
							elif child == "float_time":
								hour, minute = divmod(data * 60, 60)
								x_tmp = "%02d:%02d" % (hour, minute)
								data = x_tmp
							else:
								image_value = data.id
								data = getattr(data, child)
							if isinstance(data, bytes):
								image_value = str(image_value) + "." + field
								break

						if isinstance(data, (float, int)) == False and data == False:
							data = ''
						elif isinstance(data, bool):
							data = ''
						elif isinstance(data, datetime):
							data = self._convert_datetime_usertz_to_utctz(data)
						elif isinstance(data, date):
							data = data.strftime(
								self.env['res.lang'].search([('code', '=', self.env.user.lang)], limit=1).date_format)
						elif isinstance(data, bytes):
							data = image_value
						else:
							if isinstance(data, int) or isinstance(data, float):
								data = self.format_number(data)
							else:
								data = str(data)
						tmp_val.append(data)

					value_field[field] = tmp_val
					if key in populating_tables:
						populating_tables[key].append(value_field)
					else:
						tmp_value = []
						tmp_value.append(value_field)
						populating_tables[key] = tmp_value


				elif childs[0] == 'line_fix':
					childs.remove(childs[0])
					key = childs[0]
					data_array = getattr(datas, key)
					childs.remove(key)
					key = childs[0]
					for data in data_array:
						data_key = getattr(data, key)
						if data_key.id == int(childs[1]):
							if childs[2] != 'label':
								value = getattr(data, childs[2])
								if data._name == 'tests' and data.parameter_characteristic_id.unit_id.id != False:
									unit = data.parameter_characteristic_id.unit_id.name
									value = value + ' ' + unit
								if isinstance(data, datetime):
									value = self._convert_datetime_usertz_to_utctz(value)
								elif isinstance(value, date):
									value = value.strftime(self.env['res.lang'].search([('code', '=', self.env.user.lang)],
																					   limit=1).date_format)
								elif isinstance(value, bool):
									if value == False:
										value = ''
									else:
										value = str(value)
								elif isinstance(value, str):
									value = str(value)

								elif isinstance(value, bytes):
									value = str(data.id) + "." + field
								elif isinstance(value, object):
									if len(value) > 1:
										value_str = ''
										length = 1
										for val in value:
											if len(value) == length:
												value_str += getattr(val, 'name')
											else:
												value_str += getattr(val, 'name') + ', '
												length += 1
										value = value_str
									else:
										value = getattr(value, 'name')
								else:
									if isinstance(value, int) or isinstance(value, float):
										value = self.format_number(value)
									else:
										value = str(value)
								if field in simple_merge:
									if len(childs) == 4 and childs[3] == 'merge':
										pass
									else:
										simple_merge[field] = simple_merge[field] + '           ' + value
								else:
									simple_merge[field] = value
							else:
								if data._name == 'tests':
									values = data.parameter_id.get_field_translations('name')
									for v in values[0]:
										if len(childs) < 4:
											if v['lang'] == self.env.lang:
												value = v['value']
										else:
											if childs[3] == v['lang']:
												value = v['value']
									simple_merge[field] = value

				else:
					if len(childs) <= 0:
						continue
					tmp_logic = childs[len(childs)-1]
					if tmp_logic == 'sum':
						data_array = getattr(datas, childs[0])
						sum = 0
						if len(childs) == 3:
							for data in data_array:
								value = getattr(data, childs[1])
								sum += value
							simple_merge[field] = self.format_number(sum)
						elif len(childs) == 4:
							data_array = getattr(data_array, childs[1])
							for data in data_array:
								value = getattr(data, childs[2])
								sum += value
							simple_merge[field] = self.format_number(sum)
						else:
							simple_merge[field] = 0
					elif tmp_logic == 'count':
						data_array = getattr(datas, childs[0])
						count = len(data_array)
						simple_merge[field] = self.format_number(count)
					elif tmp_logic == 'sum_number2word':
						data_array = getattr(datas, childs[0])
						sum = 0

						for data in data_array:
							value = getattr(data, childs[1])
							sum += value
						num_to_char = self.num2word(sum)
						simple_merge[field] = num_to_char
					elif tmp_logic == 'width':
						simple_merge[field] = field
					else:
						data = datas
						for child in childs:
							data = getattr(data,child)
						try:
							simple_merge[field] = self.format_number(data)
						except Exception:
							simple_merge[field] = str(data)

		document.merge(**simple_merge)
		for key in populating_tables:
			value = populating_tables[key]
			list = []
			anchor = ''
			number = 0
			if number == 0:
				for k in value[0]:
					val = value[0][k]
					number = len(val)
					break
			for i in range(number):
				dict = {}
				for val in value:
					for k in val:
						v = val[k]
						dict[k] = v[i]
						if anchor == '':
							anchor = k
						break
				list.append(dict)
			document.merge_rows(anchor, list)
		for field in document.get_merge_fields():
			document.merge(**{field: ''})
		mem_zip = BytesIO()
		with ZipFile(mem_zip, 'w', ZIP_DEFLATED) as output:
			for zi in document.zip.filelist:
				if zi in document.parts:
					xml = etree.tostring(document.parts[zi].getroot())
					output.writestr(zi.filename, xml)
				elif zi == document._settings_info:
					xml = etree.tostring(document.settings.getroot())
					output.writestr(zi.filename, xml)
				else:
					output.writestr(zi.filename, document.zip.read(zi))

		tempfile_docx = tempfile.NamedTemporaryFile(suffix='docx')
		with open(tempfile_docx.name, "wb+") as f:
			f.write(mem_zip.getbuffer())
		f.close()
		doc = Document(tempfile_docx.name)
		for block in self._iter_block_items(doc):
			if isinstance(block, Table):
				self._replace_table_cell_with_image(block, datas, fields)
			else:
				self._match_and_replace(block, datas, fields)
		doc.save(tempfile_docx.name)

		with open(tempfile_docx.name, 'rb') as docx_file:
			docx_binary_value = docx_file.read()
		if self.type_export == 'docx':
			return docx_binary_value
		else:
			# return self.convert_docx_to_pdf(docx_binary_value)
			file = self.convert_docx_to_pdf(docx_binary_value)
			if self.model == 'purchase.order':
				att_id = self.env['ir.attachment'].sudo().create({
						'name': datas.name + ": " + datetime.strftime(datetime.now(),'%H-%M-%S') + '.pdf',
						'res_model':self.model,
						'res_id': datas.id,
						'type':'binary',
						'datas': base64.encodebytes(self.convert_docx_to_pdf(docx_binary_value)),
						'mimetype':'application/pdf',
						'index_content':'pdf',
					})
			
			elif self.model == 'sale.order':
				att_id = self.env['ir.attachment'].sudo().create({
					'name': datas.name + ": " + datetime.strftime(datetime.now(),'%H-%M-%S') + '.pdf',
					'res_model':self.model,
					'res_id': datas.id,
					'type':'binary',
					'datas': base64.encodebytes(self.convert_docx_to_pdf(docx_binary_value)),
					'mimetype':'application/pdf',
					'index_content':'pdf',
				})
			return file