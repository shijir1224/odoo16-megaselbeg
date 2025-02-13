# -*- coding: utf-8 -*-
from odoo import fields, models, _

class PurchaseOrderAttach(models.Model):
	_name = 'purchase.order.attach'
	_description = 'Purchase order attach'

	type = fields.Char('Attachment type')
	data = fields.Many2many('ir.attachment', string='Insert file')
	checked = fields.Boolean('Checked')
	po_attach_id = fields.Many2one('purchase.order', string='Purchase order')

class PurchaseOrderInheritAttach(models.Model):
	_inherit = "purchase.order"

	def _get_mail_thread_data_attachments(self):
		self.ensure_one()
		res = super()._get_mail_thread_data_attachments()
		# thread.check_items
		item_ids = self.check_items
		item_ids = self.env['ir.attachment'].search([('res_id', 'in', item_ids.ids), ('res_model', '=', 'purchase.order.attach')], order='id desc')
		return res | item_ids

	def _get_attachments(self):
		res = []
		items = ['Гэрээ','Нэхэмжлэх','И-баримт','Зарлагын баримт','Харьцуулсан баримт','ХА хүсэлтийн баримт']
		for item in items:
			dct = {
				'type': item,
				'checked': False,
			}
			res.append(dct)
		return res

	check_items = fields.One2many('purchase.order.attach','po_attach_id',default =_get_attachments)
