# -*- coding: utf-8 -*-
from odoo import fields, _
from odoo.models import TransientModel
from odoo.exceptions import ValidationError, UserError

class PurchaseRequestLineUserSet(TransientModel):
	_name = 'purchase.request.line.user.set'
	_description = 'Purchase Order Create'

	user_id = fields.Many2one('res.users', string='Оноох хангамжийн ажилтан', required=True)

	def action_done(self):
		obj = self.env['purchase.request.line'].browse(self._context['active_ids'])

		# if obj.filtered(lambda r: r.po_line_ids):
		# 	raise ValidationError(_('ХА захиалга үүссэн байна!'))
		if obj.filtered(lambda r: r.request_id.state_type != 'done'):
			raise UserError('Батлагдаагүй хүсэлт дээр ажилтан оноох боломжгүй!!!')
		if obj.filtered(lambda r: r.po_diff_qty <= 0):
			raise ValidationError(_('Бүх тоо хэмжээгээр ХА захиалга үүссэн байна!'))

		html = u'<i style="color: red">%s</i> ажилтанд <br/><b>Худалдан авалтын хүсэлт оноогдлоо </b><br/>' % (
			self.user_id.name)
		base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
		action_id = self.env.ref('mw_purchase_request.action_purchase_request_view').id

		for item in obj:
			item.user_id = self.user_id.id
			html += u"""<b><a target="_blank"  href=%s/web#id=%s&form&model=purchase.request.line&action=%s>%s</a></b>,""" % (
				base_url, item.id, action_id, item.name)

		self.env['dynamic.flow.line'].send_chat(html, self.user_id.partner_id)

		for item in obj.sudo().mapped('request_id.partner_id'):
			self.env['dynamic.flow.line'].send_chat(html, item)
		return True
