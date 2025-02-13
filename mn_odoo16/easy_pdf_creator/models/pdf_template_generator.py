# -*- coding: utf-8 -*-

from odoo import api, fields, models, modules, SUPERUSER_ID
from odoo import _, tools
from odoo.exceptions import UserError
import time
from io import BytesIO
import base64
try:
    # Python 2 support
    from base64 import encodestring
except ImportError:
    # Python 3.9.0+ support
    import base64 

import pdfkit
import re
import pytz
from datetime import datetime, timedelta
from markupsafe import Markup
import logging
_logger = logging.getLogger(__name__)

class ReportPdfOutput(models.TransientModel):
	_name = 'report.pdf.output'
	_description = "Report PDF Output"

	name = fields.Char('Filename', readonly=True)
	data = fields.Binary('File', readonly=True, required=True)
	date = fields.Datetime(default=lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'))

class PdfTemplateGenerator(models.Model):
	_name = 'pdf.template.generator'
	_description = 'PDF template generator'
	_order = 'name'

	# Columns
	company_id = fields.Many2one('res.company', string="Компани", 
		help="Хэрэглэгчийн default компаниар загвар хэвлэх үед ашиглана уу")
	name = fields.Char(string='Template name', required=True, help="You can use when search template configuration by this name")
	model_id = fields.Many2one('ir.model', string="Model name", help="Your model name")
	template_text = fields.Html('Template', required=True, help=u'PDF template body')

	margin_top = fields.Integer('Margin top', required=True, default=10)
	margin_left = fields.Integer('Margin left', required=True, default=10)
	margin_right = fields.Integer('Margin right', required=True, default=10)
	margin_bottom = fields.Integer('Margin bottom', required=True, default=10)

	auto_page_number = fields.Boolean('Auto page number',  default=False)
	disable_smart_shrinking = fields.Boolean('Disable smart shrinking', default=False)

	lang_id = fields.Many2one('res.lang', string="Language", )

	paper_size = fields.Selection([
						('A4', 'A4'),
						('Letter', 'Letter'),
						('A5', 'A5'),
						('A6', 'A6'),
						('A7', 'A7'),
						('A8', 'A8'),
						('A9', 'A9'),
						('A10', 'A10'),
						('custom', 'Custom'),
						],
		default='A4', required=True, string='Paper size')
	page_width = fields.Integer('Page width', default=60)
	page_height = fields.Integer('Page height', default=40)
	orientation = fields.Selection([
						('Portrait', 'Portrait'),
						('Landscape', 'Landscape')],
		default='Portrait', required=True, string='Orientation')

	# _sql_constraints = [('name_uniq', 'unique(name)', 'Must be unique name!')]

	def search_default_template(self, res_model, context=None):
		template = self.env['pdf.template.generator'].search(
			[('name','=','default'),
			 ('model_id.model','=',res_model),
			 ('company_id','=',self.env.user.company_id.id)], limit=1)
		if template:
			return template.id
		template = self.env['pdf.template.generator'].search(
			[('name','=','default'),
			 ('model_id.model','=',res_model)], order='id', limit=1)
		if template:
			return template.id
		else:
			return False

	# Get binary DATA
	def get_template_data(self, ids):
		html = self.template_text
		html = self._set_function_horizontal_pattern(html, ids)
		html = self._set_function_vertical_pattern(html, ids)
		html = self._set_function_simple_pattern(html, ids)
		html = self._set_one2many_pattern(html, ids)
		# Images
		html = self._set_image_field_urls_pattern(html, ids)
		html = self._set_image_field_with_size_pattern(html, ids)
		html = self._set_image_field_pattern(html, ids)
		html = self._set_out_img_src_pattern(html, ids)
		html = self._set_img_src_pattern(html, ids)

		html = self._set_many2one_pattern(html, ids)

		html = self._set_simple_pattern(html, ids)
		html = self._set_static_pattern(html)
		html = self.encode_for_xml(html, 'ascii')

		options = {
			'margin-top': str(self.margin_top)+'mm',
			'margin-right': str(self.margin_right)+'mm',
			'margin-bottom': str(self.margin_bottom)+'mm',
			'margin-left': str(self.margin_left)+'mm',
			'encoding': "UTF-8",
			'header-spacing': 5,
			'orientation': self.orientation,
		}
		if self.auto_page_number:
			options['footer-right'] = '[page]/[topage]'
		if self.paper_size=='custom':
			options['page-width'] = str(self.page_width)+'mm'
			options['page-height'] = str(self.page_height)+'mm'
		else:
			options['page-size'] = self.paper_size
		if self.disable_smart_shrinking:
			options['disable-smart-shrinking'] = ''

		path = modules.get_module_resource('easy_pdf_creator', 'static/css/froala_style.css')
		path2 = modules.get_module_resource('easy_pdf_creator', 'static/css/base.css')
		output = BytesIO(pdfkit.from_string(html.decode('utf-8'),False,options=options, css=[path,path2]))
		out = base64.encodebytes(output.getvalue())

		return out

	def get_template_data_html(self, ids):
		html = self.template_text
		html = self._set_function_horizontal_pattern(html, ids)
		html = self._set_function_vertical_pattern(html, ids)
		html = self._set_function_simple_pattern(html, ids)
		html = self._set_one2many_pattern(html, ids)
		# Images
		html = self._set_image_field_urls_pattern(html, ids)
		html = self._set_image_field_with_size_pattern(html, ids)
		html = self._set_image_field_pattern(html, ids)
		html = self._set_out_img_src_pattern(html, ids)
		html = self._set_img_src_pattern(html, ids)

		html = self._set_many2one_pattern(html, ids)
		html = self._set_simple_pattern(html, ids)
		html = self._set_static_pattern(html)
		# html = self.encode_for_xml(html, 'ascii')
		return html

	def print_template_html_set(self, html, ids):
		html = self._set_function_horizontal_pattern(html, ids)
		html = self._set_function_vertical_pattern(html, ids)
		html = self._set_function_simple_pattern(html, ids)
		html = self._set_one2many_pattern(html, ids)
		# Images
		html = self._set_image_field_urls_pattern(html, ids)
		html = self._set_image_field_with_size_pattern(html, ids)
		html = self._set_image_field_pattern(html, ids)
		html = self._set_out_img_src_pattern(html, ids)
		html = self._set_img_src_pattern(html, ids)

		html = self._set_many2one_pattern(html, ids)
		html = self._set_simple_pattern(html, ids)
		html = self._set_static_pattern(html)
		html = self.encode_for_xml(html, 'ascii')
		return html

	# Direct print PDF
	def print_template_html(self, html, options=False, file_name=False):
		res_html = self.encode_for_xml(html, 'ascii')
		res_html = html or ''
		if not options:
			options = {
				'margin-top': str(self.margin_top)+'mm',
				'margin-right': str(self.margin_right)+'mm',
				'margin-bottom': str(self.margin_bottom)+'mm',
				'margin-left': str(self.margin_left)+'mm',
				'encoding': "UTF-8",
				'header-spacing': 5,
				'orientation': self.orientation,
			}
			if self.auto_page_number:
				options['footer-right'] = '[page]/[topage]'
			if self.paper_size=='custom':
				options['page-width'] = str(self.page_width)+'mm'
				options['page-height'] = str(self.page_height)+'mm'
			else:
				options['page-size'] = self.paper_size
			if self.disable_smart_shrinking:
				options['disable-smart-shrinking'] = ''

		path = modules.get_module_resource('easy_pdf_creator', 'static/css/froala_style.css')
		path2 = modules.get_module_resource('easy_pdf_creator', 'static/css/base.css')
		output = BytesIO(pdfkit.from_string(res_html,False,options=options, css=[path,path2]))
		out = base64.encodebytes(output.getvalue())
		file_name = self.name+'.pdf' if not file_name else file_name
		res_id = self.env['report.pdf.output'].create({'data': out, 'name': file_name})
		return {
			'target': 'new',
			'type' : 'ir.actions.act_url',
			'url': "web/content/?model=report.pdf.output&id=" + str(res_id.id) + "&filename_field=filename&field=data&filename=" + file_name,
		}


	# Direct print PDF
	def print_template(self, ids):
		html = self.template_text or ''
		html = self._set_function_horizontal_pattern(html, ids)
		html = self._set_function_vertical_pattern(html, ids)
		html = self._set_function_simple_pattern(html, ids)
		html = self._set_one2many_pattern(html, ids)
		# Images
		html = self._set_image_field_urls_pattern(html, ids)
		html = self._set_image_field_with_size_pattern(html, ids)
		html = self._set_image_field_pattern(html, ids)
		html = self._set_out_img_src_pattern(html, ids)
		html = self._set_img_src_pattern(html, ids)

		html = self._set_many2one_pattern(html, ids)
		html = self._set_simple_pattern(html, ids)
		html = self._set_static_pattern(html)
		html = self.encode_for_xml(html, 'ascii')

		options = {
			'margin-top': str(self.margin_top)+'mm',
			'margin-right': str(self.margin_right)+'mm',
			'margin-bottom': str(self.margin_bottom)+'mm',
			'margin-left': str(self.margin_left)+'mm',
			'encoding': "UTF-8",
			'header-spacing': 5,
			'orientation': self.orientation,
		}
		if self.auto_page_number:
			options['footer-right'] = '[page]/[topage]'
		if self.paper_size=='custom':
			options['page-width'] = str(self.page_width)+'mm'
			options['page-height'] = str(self.page_height)+'mm'
		else:
			options['page-size'] = self.paper_size
		if self.disable_smart_shrinking:
			options['disable-smart-shrinking'] = ''

		path = modules.get_module_resource('easy_pdf_creator', 'static/css/froala_style.css')
		path2 = modules.get_module_resource('easy_pdf_creator', 'static/css/base.css')
		output = BytesIO(pdfkit.from_string(html.decode('utf-8'),False,options=options, css=[path,path2]))
		out = base64.encodebytes(output.getvalue())
		file_name = self.name+'.pdf'
		res_id = self.env['report.pdf.output'].create({'data': out, 'name': file_name})
		return {
			'target': 'new',
			'type' : 'ir.actions.act_url',
			'url': "web/content/?model=report.pdf.output&id=" + str(res_id.id) + "&filename_field=filename&field=data&filename=" + file_name,
		}

	# Fixed size on image
	def _set_image_field_with_size_pattern(self, text, ids):
		match = re.findall(r'{image_field:[\w.-]+:[0-9]+:[0-9]+}', text)
		obj = self.env[ self.env.context.get('model_id_model',self.model_id.model) ].sudo().search([('id','=',ids)])

		array_match = []
		for item in match:
			s_item = item.replace('{','')
			s_item = s_item.replace('}','')
			array_match.append(s_item)

		for patern_name in array_match:
			pttrn_name = '{'+patern_name+'}'
			related_fields = patern_name.split(':')
			field_name = related_fields[1]
			width = related_fields[2]
			height = related_fields[3]
			data = '???'

			pic = self.env['ir.attachment'].sudo().search([
				('res_model','=',self.env.context.get('model_id_model',self.model_id.model)),
				('res_field','=',field_name),
				('res_id','=',ids),
				], limit=1)
			if pic:
				pic_url = pic._full_path(pic.store_fname)
				data = '''<img border="1" name="'''+field_name+'''"
					width="'''+width+'''" height="'''+height+'''"
					src="'''+pic_url+'''">'''

			# text = text.replace(pttrn_name,data)
			text = text.replace(pttrn_name, Markup(data))
		return text

	# No sized image
	def _set_image_field_pattern(self, text, ids):
		match = re.findall(r'{image_field:[\w.-]+}', text)
		obj = self.env[ self.env.context.get('model_id_model',self.model_id.model) ].sudo().search([('id','=',ids)])

		array_match = []
		for item in match:
			s_item = item.replace('{','')
			s_item = s_item.replace('}','')
			array_match.append(s_item)

		for patern_name in array_match:
			pttrn_name = '{'+patern_name+'}'
			related_fields = patern_name.split(':')
			field_name = related_fields[1]
			data = '???'

			pic = self.env['ir.attachment'].sudo().search([
				('res_model','=',self.env.context.get('model_id_model',self.model_id.model)),
				('res_field','=',field_name),
				('res_id','=',ids),
				], limit=1)
			if pic:
				pic_url = pic._full_path(pic.store_fname)
				data = '''<img border="1" name="'''+field_name+'''"
					src="'''+pic_url+'''">'''

			# text = text.replace(pttrn_name,data)
			text = text.replace(pttrn_name, Markup(data))
		return text

	# Print image by URLs
	# You can set many image's url
	# Data format
	# Ex: ['img.domain.mn/uploads/20160626/6f6bfbfa73e662c1505ab5858a14c3c2.jpg', 'img.domain.mn/uploads/order_note/20170928/74594d9c9904a50374b71b4bcc4d83e7.jpg', 'img.domain.mn/uploads/order_note/20170928/3195fdb649288984ae092ceff1fc6372.png']
	def _set_image_field_urls_pattern(self, text, ids):
		match = re.findall(r'{image_field_urls:[\w.-]+}', text)
		obj = self.env[ self.env.context.get('model_id_model',self.model_id.model) ].sudo().search([('id','=',ids)])

		array_match = []
		for item in match:
			s_item = item.replace('{','')
			s_item = s_item.replace('}','')
			array_match.append(s_item)

		for patern_name in array_match:
			pttrn_name = '{'+patern_name+'}'
			related_fields = patern_name.split(':')
			field_name = related_fields[1]
			images = ""
			urls = obj.sudo().read([field_name])[0][field_name] if obj.sudo().read([field_name])[0][field_name] else ''
			if urls:
				urls = urls.replace('[','')
				urls = urls.replace(']','')
				urls = urls.replace("'",'')
				urls = urls.replace("'",'')
				urls = urls.replace(" ",'')
				urls = urls.strip()
				urls = urls.split(',')
				for url in urls:
					img = '''<img border="1" name="'''+field_name+'''"
						src="http://'''+url+'''"><br>'''
					images += img
			# text = text.replace(pttrn_name,images)
			text = text.replace(pttrn_name, Markup(images))
		return text

	# Local image on template
	def _set_out_img_src_pattern(self, text, ids):
		match = re.findall(r'/web/image/[0-9]+', text)
		for patern_name in match:
			pic_id = patern_name.split('/')[3]
			pic = self.env['ir.attachment'].sudo().search([('id','=',pic_id)], limit=1)
			# text = text.replace(patern_name, pic._full_path(pic.store_fname))
			text = text.replace(patern_name, Markup(pic._full_path(pic.store_fname)))
		return text

	# Default WEB images
	def _set_img_src_pattern(self, text, ids):
		match = re.findall(r'/website/static/src/img/library', text)

		base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
		if not base_url:
			raise UserError(u'Base URL тохиргоо хийгдээгүй байна! (ir.config_parameter:web.base.url)')

		array_match = []
		for item in match:
			array_match.append(item)

		for patern_name in array_match:
			text = text.replace(patern_name, Markup(base_url+patern_name))
			
		return text

	# Simple function
	def _set_function_simple_pattern(self, text, ids):
		match = re.findall(r'{function_simple:[\w.-]+}', text)
		obj = self.env[ self.env.context.get('model_id_model',self.model_id.model) ].sudo().search([('id','=',ids)])
		array_match = []
		for item in match:
			s_item = item.replace('{','')
			s_item = s_item.replace('}','')
			array_match.append(s_item)

		for patern_name in array_match:
			pttrn_name = '{'+patern_name+'}'
			related_fields = patern_name.split(':')

			model = self.env[ self.env.context.get('model_id_model',self.model_id.model) ]
			method_name = related_fields[1]
			data =  getattr(model, method_name)(ids)
			if type(data) in [float, int]:
				data = "{:,}".format(data)
			_logger.info(u'-***********-_set_function_simple_pattern--*************-----%s---\n'%(pttrn_name))
			# _logger.info(u'-***********-_set_function_simple_pattern data--*************-----%s---\n'%(data))
			if data:
				text = text.replace(pttrn_name,Markup(data))
				# text = text.replace(patern_name, Markup(data))
			else:
				text = text.replace(pttrn_name,Markup(''))
		return text

	# Draw table by data
	# Call function then return DATA
	# Data format
	# return {'header':['col1','col2'],'data':[[112323,435345.5],[23.4,56]]}
	# horizontal print line
	def _set_function_horizontal_pattern(self, text, ids):
		match = re.findall(r'{function_horizontal:[\w.-]+:[\w.-]+:[\w.-]+}', text)
		obj = self.env[ self.env.context.get('model_id_model',self.model_id.model) ].sudo().search([('id','=',ids)])
		array_match = []
		for item in match:
			s_item = item.replace('{','')
			s_item = s_item.replace('}','')
			array_match.append(s_item)

		for patern_name in array_match:
			related_fields = patern_name.split(':')

			header_css_name = related_fields[2]
			cell_css_name = related_fields[3]

			pttrn_name = '{'+patern_name+'}'

			_logger.info(u'-***********-_set_function_horizontal_pattern--*************-----%s---\n'%(pttrn_name))

			model = self.env[ self.env.context.get('model_id_model',self.model_id.model) ]
			method_name = related_fields[1]
			data =  getattr(model, method_name)(ids)
			if data:
				table_lines = '<table style="border: 1px solid #000000;width:100%;border-collapse: collapse; font-size: inherit;">'
				# Table ийн толгой зурах
				table_header = ''
				for th in data['header']:
					table_header += '<td style="border: 1px solid #000000;padding:1px; page-break-before:always; page-break-inside:avoid;" class="'+header_css_name+'">'+th+'</td>'
				table_lines += table_header

				for line in data['data']:
					row = '<tr>'
					for td in line:
						if td:
							if isinstance(td,datetime):
								td = datetime.strftime(td,'%Y-%m-%d %H:%M:%S')
							row += '<td style="border: 1px solid #000000;padding:1px; page-break-before:always; page-break-inside:avoid;" class="'+cell_css_name+'">'+ td +'</td>'
						else:
							row += '<td style="border: 1px solid #000000;padding:1px; page-break-before:always; page-break-inside:avoid;" class="'+cell_css_name+'"> </td>'
					table_lines += row +'</tr>'
				table_lines += '</table>'

				text = text.replace(pttrn_name, Markup(table_lines))
			else:
				text = text.replace(pttrn_name, Markup(""))
				# Bayasaa haav
				# text = text.replace(pttrn_name, "-Empty-")
		return text

	# Vertical print line
	def _set_function_vertical_pattern(self, text, ids):
		match = re.findall(r'{function_vertical:[\w.-]+:[\w.-]+:[\w.-]+}', text)
		obj = self.env[ self.env.context.get('model_id_model',self.model_id.model) ].sudo().search([('id','=',ids)])
		array_match = []
		for item in match:
			s_item = item.replace('{','')
			s_item = s_item.replace('}','')
			array_match.append(s_item)

		for patern_name in array_match:
			related_fields = patern_name.split(':')

			header_css_name = related_fields[2]
			cell_css_name = related_fields[3]

			pttrn_name = '{'+patern_name+'}'

			model = self.env[ self.env.context.get('model_id_model',self.model_id.model) ]
			method_name = related_fields[1]
			data =  getattr(model, method_name)(ids)
			if data:
				table_lines = '<table style="border: 1px solid #000000;width:100%;border-collapse: collapse; ">'
				# Босоо хэвлэх
				headers = data['header']
				datas = data['data']
				i = 0
				for th in headers:
					new_row = '<tr><td style="border: 1px solid #000000;padding:1px;" class="'+header_css_name+'">'+th+'</td>'
					for td in datas:
						if i < len(td):
							# print '===========td', i, td[i]
							new_row += '<td style="border: 1px solid #000000;padding:1px;" class="'+cell_css_name+'">'+ td[i] +'</td>'
					new_row += '</tr>'
					table_lines += new_row
					i += 1
				table_lines += '</table>'

				text = text.replace(pttrn_name, Markup(table_lines))
			else:
				text = text.replace(pttrn_name, Markup(""))
				# Bayasaa haav
				# text = text.replace(pttrn_name, "-Empty-")
		return text

	# Simple fields, many2one, datetime
	def _set_simple_pattern(self, text, ids):
		data = self.env[ self.env.context.get('model_id_model',self.model_id.model) ].sudo().fields_get()
		match = re.findall(r'{\w+}', text)
		obj = self.env[ self.env.context.get('model_id_model',self.model_id.model) ].sudo().search([('id','=',ids)])

		array_match = []
		for item in match:
			s_item = item.replace('{','')
			s_item = s_item.replace('}','')
			array_match.append(s_item)

		for field_name in array_match:
			field = '{'+field_name+'}'
			if field_name in data:
				value = ''
				if str(data[field_name]['type'])=='many2one':
					value = obj.sudo().read([field_name])[0][field_name][1] if obj.sudo().read([field_name])[0][field_name] else ''
				elif str(data[field_name]['type'])=='date':
					value = str(obj.sudo().read([field_name])[0][field_name]) if obj.sudo().read([field_name])[0][field_name] else ''
					value = value
				elif str(data[field_name]['type'])=='datetime':
					value = str(obj.sudo().read([field_name])[0][field_name]) if obj.sudo().read([field_name])[0][field_name] else ''

					tz = self.env['res.users'].sudo().browse(SUPERUSER_ID).tz or 'Asia/Ulaanbaatar'
					timezone = pytz.timezone(tz)
					f_date = ''
					if value:
						f_date = datetime.strptime(value[:19], '%Y-%m-%d %H:%M:%S')
						f_date += timedelta(hours=self._get_tz())
						f_date = datetime.strftime(f_date, '%Y-%m-%d %H:%M:%S')

					value = f_date
				elif str(data[field_name]['type'])=='selection':
					if obj.sudo().read([field_name])[0][field_name]:
						try:
							value1 = obj.sudo().read([field_name])[0][field_name]
							if type(value1) in [float, int]:
								value = "{:,}".format(value1)
							else:
								value = str(value1)
						except ValueError:
							value=str(obj.sudo().read([field_name])[0][field_name].encode('utf-8'))
					# String олох
					if value:
						for ss in data[field_name]['selection']:
							if value == ss[0]:
								value = ss[1]
					# _logger.info(u'-***********-CHECK--*************-----%s %s---\n'%(field_name,value))
				else:
					if obj.sudo().read([field_name])[0][field_name]:
						try:
							value1 = obj.sudo().read([field_name])[0][field_name]
							if type(value1) in [float, int]:
								value = "{:,}".format(value1)
							else:
								value = str(value1)
						except ValueError:
							value=str(obj.sudo().read([field_name])[0][field_name].encode('utf-8'))
					else:
						value = ''
				try:
					text = text.replace(field,Markup(value))
				except ValueError:
					text = text.replace(field,Markup(value.decode('utf-8')))
			else:
				text = text.replace(field,Markup(''))
		return text

	def _get_tz(self):
		return 8

	def _set_static_pattern(self, text):
		match = re.findall(r'now_date_print', text)
		m_date = fields.Datetime.now()
		tz = self.env.user.tz or 'Asia/Ulaanbaatar'
		timezone = pytz.timezone(tz)
		m_date = m_date.replace(tzinfo=pytz.timezone('UTC')).astimezone(timezone)
		# print (dddd)
		if match:
			f_date = datetime.strftime(m_date, '%Y-%m-%d')
			text = text.replace('now_date_print',Markup(f_date))
		match = re.findall(r'now_datetime_print', text)
		if match:
			f_date = datetime.strftime(m_date, '%Y-%m-%d %H:%M:%S')
			text = text.replace('now_datetime_print',Markup(f_date))
		return text
	# Many2one field's field
	def _set_many2one_pattern(self, text, ids):
		field_names = self.env[ self.env.context.get('model_id_model',self.model_id.model) ].sudo().fields_get()
		match = re.findall(r'{[\w.-]+:[\w.-]+}', text)
		obj = self.env[ self.env.context.get('model_id_model',self.model_id.model) ].sudo().search([('id','=',ids)])

		array_match = []
		for item in match:
			s_item = item.replace('{','')
			s_item = s_item.replace('}','')
			array_match.append(s_item)

		for patern_name in array_match:
			pttrn_name = '{'+patern_name+'}'
			related_fields = patern_name.split(':')
			field_name = related_fields[0]
			field_name2 = related_fields[1]
			if field_name in field_names:
				value = ''
				if str(field_names[field_name]['type'])=='many2one' and obj.sudo().read([field_name])[0][field_name]:
					_logger.info(u'-***********-_set_many2one_pattern--*************-----%s---\n'%(field_name))
					sub_obj_id = obj.sudo().read([field_name])[0][field_name][0]
					sub_obj = self.env[ field_names[field_name]['relation'] ].sudo().search([('id','=',sub_obj_id)])
					value = sub_obj.sudo().read([field_name2])[0][field_name2] if sub_obj.sudo().read([field_name2])[0][field_name2] else u' '
					if type(value) in [float, int]:
						value = "{:,}".format(value)
					else:
						value = value
				# text = text.replace(pttrn_name,value)
				text = text.replace(pttrn_name, Markup(value))
			else:
				text = text.replace(pttrn_name,Markup(''))
		return text

	# One2many field's data into table
	def _set_one2many_pattern(self, text, ids):
		field_names = self.env[ self.env.context.get('model_id_model',self.model_id.model) ].sudo().fields_get()
		match = re.findall(r'{[\w.-]+:{[\w,]+}:[\w.-]+:[\w.-]+}', text)
		obj = self.env[ self.env.context.get('model_id_model',self.model_id.model) ].sudo().search([('id','=',ids)])

		array_match = []
		for item in match:
			s_item = item.replace('{','')
			s_item = s_item.replace('}','')
			array_match.append(s_item)

		for patern_name in array_match:
			related_fields = patern_name.split(':')
			field_name = related_fields[0]
			one2many_fields = related_fields[1].split(',')

			header_css_name = related_fields[2]
			cell_css_name = related_fields[3]

			pttrn_name = '{'+field_name+':{'+related_fields[1]+'}:'+header_css_name+':'+cell_css_name+'}'

			#print '---------',header_css_name, cell_css_name
			if field_name in field_names:
				value = ''
				if str(field_names[field_name]['type'])=='one2many':
					o2m_ids = obj.sudo().read([field_name])[0][field_name]
					o2m_field_names = self.env[ field_names[field_name]['relation'] ].sudo().fields_get()

					data = False

					table_lines = '<table style="border:1px solid #dddddd;border-collapse: collapse;width:100%;font-size: 11pt;">'
					# Table ийн толгой зурах
					table_header = ''
					for fn in one2many_fields:
						table_header += '<th style="border:1px solid #dddddd;text-align: center;" class="'+header_css_name+'">'+o2m_field_names[fn]['string']+'</th>'
					table_lines += table_header

					for o2m_id in o2m_ids:
						row = '<tr style="border: 1px solid #dddddd;padding:1px">'
						o2m_obj = self.env[ field_names[field_name]['relation'] ].sudo().search([('id','=',o2m_id)])
						data = o2m_obj.sudo().read(one2many_fields)[0]

						for fn in one2many_fields:
							td = '<td style="border: 1px solid #dddddd;padding:1px" class="'+cell_css_name+'">'
							if type(data[fn]) is tuple:
								td += data[fn][1]
							elif type(data[fn]) in [float, int]:
								td += "{:,}".format(data[fn])
							else:
								td += str(data[fn])
							row += td + '</td>'
						table_lines += row + '</tr>'
					table_lines += '</table>'

				text = text.replace(pttrn_name, Markup(table_lines))
			else:
				text = text.replace(pttrn_name,Markup(''))
		return text

	def encode_for_xml(self, unicode_data, encoding='ascii'):
		try:
			return unicode_data.encode(encoding, 'xmlcharrefreplace')
		except ValueError:
			return self._xmlcharref_encode(unicode_data, encoding)

	def _xmlcharref_encode(self, unicode_data, encoding):
		chars = []
		for char in unicode_data:
			try:
				chars.append(char.encode(encoding, 'strict'))
			except UnicodeError:
				chars.append('&#%i;' % ord(char))
		return ''.join(chars)
