# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo import _, tools
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, time, timedelta, date
import collections
import time

class PartsMove(models.Model):
	_name = 'parts.move'
	_description = 'parts.move'
	_order = 'date_required desc'
	_rec_name = 'description'

	@api.model
	def _get_user(self):
		return self.env.user.id

	# Columns
	branch_id = fields.Many2one('res.branch', string=u'Салбар', required=True,
		states={'confirmed':[('readonly', True)]})
	company_id = fields.Many2one('res.company',string='Компани', readonly=True, default=lambda self: self.env.user.company_id)

	from_technic_id = fields.Many2one('technic.equipment', string=u'Шилжүүлэн авах техник', copy=True, required=False,
		states={'confirmed':[('readonly', True)]})
	to_technic_id = fields.Many2one('technic.equipment', string=u'Шилжүүлж тавих техник', required=False,
		states={'confirmed':[('readonly', True)]})
	date = fields.Datetime(string=u'Үүсгэсэн огноо', default=datetime.now(), readonly=True)
	date_required = fields.Date(string=u'Шилжсэн огноо', required=True,
		states={'confirmed':[('readonly', True)]})
	is_create_pr = fields.Boolean(string=u'PR үүсгэх эсэх', default=False,
		states={'confirmed':[('readonly', True)]})

	from_equipment_id = fields.Many2one('factory.equipment', string=u'Шилжүүлэн авах тоног төхөөрөмж', copy=True, required=True,
		states={'confirmed':[('readonly', True)]})
	to_equipment_id = fields.Many2one('factory.equipment', string=u'Шилжүүлж тавих тоног төхөөрөмж', required=True,
		states={'confirmed':[('readonly', True)]})
	repairman_id = fields.Many2one('hr.employee', string=u'Шилжүүлж тавьсан ажилтан', required=True,
		states={'confirmed':[('readonly', True)]})

	description = fields.Text(string=u'Тайлбар', required=True,
		states={'confirmed':[('readonly', True)]})

	line_ids = fields.One2many('parts.move.line', 'parent_id', string='Lines', copy=False,
		states={'manager': [('readonly', True)],'confirmed': [('readonly', True)]})

	user_id = fields.Many2one('res.users', string=u'Үүсгэсэн хэрэглэгч', default=_get_user, readonly=True)
	planner_id = fields.Many2one('res.users', string=u'Хуваарь гаргагч', readonly=True)
	manager_id = fields.Many2one('res.users', string=u'Менежер', readonly=True)
	# partsman_id = fields.Many2one('res.users', string=u'Сэлбэгийн мэргэжилтэн', readonly=True)
	request_id = fields.Many2one('purchase.request', string='PR №', readonly=True)
	attachment_ids = fields.Many2many('ir.attachment', string='Хавсралт')

	state = fields.Selection([
		('draft', u'Ноорог'),
		('confirmed', u'Засварын төлөвлөгч'),
		# ('master', u'Ээлжийн ахлах'),
		# ('manager', u'Засварын ахлах'),
		# ('confirmed', u'Баталсан'),
		],
		default='draft', string=u'Төлөв', tracking=True)

	def unlink(self):
		for s in self:
			if s.state != 'draft':
				raise UserError(_(u'Ноорог төлөвтэй бичлэгийг устгаж болно!'))
		return super(MaintenancePartsMove, self).unlink()

	# ===================================== Custom methods ------------------------------
	def action_to_draft(self):
		self.state = 'draft'

	def action_planner(self):
		self.planner_id = self.env.user.id
		self.state = 'confirmed'
		if self.to_equipment_id.id == self.from_equipment_id.id:
			raise UserError(_(u'2 ижил тоног төхөөрөмж сонгосон байна!'))
		self.action_to_create_pr()

	# PR үүсгэх
	def action_to_create_pr(self):
		if self.is_create_pr:
			if self.request_id:
				raise UserError(('%s дугаартай Худалдан авалтын хүсэлт үүссэн байна.' % self.request_id.name))
			p_request = self.env['purchase.request']
			p_req_line =self.env['purchase.request.line']

			emp = self.env['hr.employee'].search([('user_id','=',self.user_id.id)], limit=1)

			search_domain = [('model_id.model','=','purchase.request'),'|',('branch_ids','in',[self.user_id.branch_id.id]),('branch_ids','in',False)]
			flow_id = self.env['dynamic.flow'].search(search_domain, order='sequence', limit=1)
			flow_line_id = self.env['dynamic.flow.line'].search([('flow_id','=',flow_id.id)], order='sequence', limit=1)
			self.request_id = p_request.create(
				{'employee_id': emp.id if emp else False,
				'desc': self.description + self.from_equipment_id.name + ' техник дээр Сэлбэг шилжилтээр үүсгэв.',
				'flow_id': flow_id.id,
				'flow_line_id': flow_line_id.id,
				'date': date.today()
				})

			for item in self.line_ids:
				vals = {
					'request_id': self.request_id.id,
					'product_id': item.product_id.id,
					'equipment_id': self.from_equipment_id.id,
					'uom_id': item.uom_id.id,
					'qty': item.qty,
				}
				line_id = p_req_line.create(vals)
			flow_line_id = self.env['dynamic.flow.line'].search([('flow_id','=',flow_id.id),('state_type','=','sent')], order='sequence', limit=1)
			self.request_id.write({'flow_line_id': flow_line_id.id})
			# self.request_id.action_next_stage()
			return
			print('===========PR create=', self.request_id.name)
			return True

	def send_chat(self, group_name, text):
		# Chat илгээх
		res_model = self.env['ir.model.data'].search([
				('module','=','mw_technic_maintenance'),
				('name','=',group_name)])
		group = self.env['res.groups'].search([('id','in',res_model.mapped('res_id'))])
		partners = []
		for receiver in group.users:
			if receiver.partner_id:
				if self.env.user.partner_id.id != receiver.partner_id.id:
					partners.append(receiver.partner_id)
		# Manager батласан бол үүссэн PR чатаар мэдэгдэх
		if self.state == 'manager' and  self.is_create_pr == True:
			base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
			action_id = self.env['ir.model.data']._xmlid_lookup('mw_technic_maintenance.action_maintenance_parts_move')[2]
			# Сэлбэг шилжилт батлагдаж үүссэн PR илгээх
			# MSG илгээх
			html = u"""<span style='font-size:10pt; color:blue;'>%s %s <b><a target="_blank" href=%s/web#id=%s&view_type=form&model=purchase.request&action=%s>%s</a></b> Худалдан авалтын хүсэлт үүсэв!</span>""" % (self.description, text, base_url, self.request_id.id, action_id, self.request_id.name,)
		else:
			base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
			action_id = self.env['ir.model.data']._xmlid_lookup('mw_technic_maintenance.action_maintenance_parts_move')[2]
			# Сэлбэг шилжилт батлуулах
			# MSG илгээх
			html = u"""<span style='font-size:10pt; color:blue;'><b><a target="_blank" href=%s/web#id=%s&view_type=form&model=maintenance.parts.move&action=%s>%s</a></b> сэлбэг шилжүүлэлтийг батлана уу!, %s</span>""" % (base_url,self.id,action_id, self.description, text)
		# self.env.user.send_chat(html, partners)
		self.env.user.send_emails(partners=partners, body=html, attachment_ids=False)


class PartsMoveLine(models.Model):
	_name = 'parts.move.line'
	_description = 'parts.move.line'
	_order = 'product_id'
	# Columns
	parent_id = fields.Many2one('parts.move', string=u'Parent', ondelete='cascade')
	
	product_id = fields.Many2one('product.product', string=u'Сэлбэг/Parts', required=True,)
	uom_id = fields.Many2one(related="product_id.uom_id", string=u'Хэмжих нэгж', readonly=True)
	qty = fields.Integer(string=u'Тоо ширхэг', required=True,)
