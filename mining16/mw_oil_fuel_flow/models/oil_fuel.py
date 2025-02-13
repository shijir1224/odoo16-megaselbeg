# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo import _, tools
from odoo.exceptions import UserError, ValidationError, Warning
from datetime import date, datetime, timedelta
import collections
from calendar import monthrange
from io import BytesIO
import base64
import xlsxwriter
from tempfile import NamedTemporaryFile
import os,xlrd
from odoo.osv import expression

import logging
_logger = logging.getLogger(__name__)

class dynamic_flow_history(models.Model):
	_inherit = 'dynamic.flow.history'

	oil_id = fields.Many2one('oil.fuel', 'Oil fuel', ondelete='cascade', index=True)


class oil_fuel(models.Model):
	_inherit = 'oil.fuel'

	def flow_find(self, domain=[], order='sequence'):
		search_domain = []
		if self.flow_id:
			search_domain.append(('flow_id','=',self.flow_id.id))
		search_domain.append(('flow_id.model_id.model','=','oil.fuel'))
		search_domain += ['|',('flow_id.branch_ids','in', self.env.user.branch_id.id),('flow_id.branch_ids','in', False)]
		return self.env['dynamic.flow.line'].search(search_domain, order=order, limit=1).id


	def _get_dynamic_flow_line_id(self):
		return self.flow_find()

	def _get_default_flow_id(self):
		search_domain = []
		search_domain.append(('model_id.model','=','oil.fuel'))
		search_domain += ['|',('branch_ids','in', self.env.user.branch_id.id),('branch_ids','in', False)]
		if self.env.context.get('type') == 'fuel':
			search_domain.append(('description','=','fuel'))
		if self.env.context.get('type') == 'oil':
			search_domain.append(('description','=','oil'))
		if self.env.context.get('type') == 'fuel_in':
			search_domain.append(('description','=','fuel_in'))
		print(search_domain)
		return self.env['dynamic.flow'].search(search_domain, order='sequence', limit=1).id


	flow_id = fields.Many2one('dynamic.flow', string='Урсгал тохиргоо',tracking=True, default=_get_default_flow_id, copy=True, domain="[('model_id.model', '=', 'oil.fuel')]")
	flow_line_id = fields.Many2one('dynamic.flow.line', string='Тохиргооны мөр', tracking=True, index=True, default=_get_dynamic_flow_line_id, copy=False, domain="[('flow_id', '=', flow_id),('flow_id.model_id.model', '=', 'oil.fuel')]", readonly=True)
	back_flow_line_id = fields.Many2one('dynamic.flow.line', string='Өмнөх урсгал тохиргоо', compute='_compute_flow_line_id', readonly=True)
	next_flow_line_id = fields.Many2one('dynamic.flow.line', string='Дараах урсгал тохиргоо', compute='_compute_flow_line_id', readonly=True)
	state_type = fields.Selection(related='flow_line_id.state_type', string='Урсгалын Төлөв', readonly=True, store=True)
	history_flow_ids = fields.One2many('dynamic.flow.history','oil_id', string='Түүх', readonly=True)
	visible_flow_line_ids = fields.Many2many('dynamic.flow.line',string='Харагдах мөрүүд', compute='_compute_visible_flow_line_ids', readonly=True)
	confirm_user_ids = fields.Many2many('res.users', string="Батлах хэрэглэгчид", compute="_compute_user_ids")
	count_users = fields.Integer(string="Count users", compute="_compute_user_ids", store=True)

	@api.depends('flow_line_id', 'flow_id.line_ids')
	def _compute_user_ids(self):
		for item in self:
			temp_users = []
			for w in item.flow_id.line_ids:
				temp = []
				try:
					temp = w._get_flow_users(item.branch_id, item.sudo().create_uid.department_id if item.sudo().create_uid else False, item.sudo().create_uid).ids
				except:
					pass
				temp_users += temp
			item.confirm_user_ids = temp_users
			item.count_users = len(item.confirm_user_ids)

	@api.depends('flow_id','visible_flow_line_ids', 'flow_line_id')
	def _compute_flow_line_id(self):
		for item in self:
			item.next_flow_line_id = item._get_next_flow_line(self.visible_flow_line_ids)
			item.back_flow_line_id = item._get_back_flow_line(self.visible_flow_line_ids)
 
	def _get_next_flow_line(self, flow_line_ids=False):
		if self.id:
			if flow_line_ids:
				next_flow_line_id = self.env['dynamic.flow.line'].search([
					('flow_id','=',self.flow_id.id),
					('id','!=',self.flow_line_id.id),
					('sequence','>',self.flow_line_id.sequence),
					('sequence','in',flow_line_ids.mapped('sequence')),
					('state_type','not in',['cancel']),
					], limit=1, order='sequence')
				return next_flow_line_id
			else:
				next_flow_line_id = self.env['dynamic.flow.line'].search([
					('flow_id','=',self.flow_id.id),
					('id','!=',self.flow_line_id.id),
					('sequence','>',self.flow_line_id.sequence),
					('state_type','not in',['cancel']),
					], limit=1, order='sequence')
				return next_flow_line_id
		else:
			return False

	def _get_back_flow_line(self, flow_line_ids=False):
		if self.id:
			if flow_line_ids:
				back_flow_line_id = self.env['dynamic.flow.line'].search([
					('flow_id','=',self.flow_id.id),
					('id','!=',self.flow_line_id.id),
					('sequence','<',self.flow_line_id.sequence),
					('sequence','in',flow_line_ids.mapped('sequence')),
					('state_type','not in',['cancel']),
					], limit=1, order='sequence desc')
				return back_flow_line_id
			else:
				back_flow_line_id = self.env['dynamic.flow.line'].search([
				('flow_id','=',self.flow_id.id),
				('id','!=',self.flow_line_id.id),
				('sequence','<',self.flow_line_id.sequence),
				('state_type','not in',['cancel']),
				], limit=1, order="sequence desc")
			return back_flow_line_id
		return False

	@api.onchange('flow_id')
	def _onchange_flow_id(self):
		if self.flow_id:
			if self.flow_id:
				self.write({'flow_line_id': self.flow_find(())})
		else:
			self.flow_line_id = False

	@api.depends('flow_id.line_ids', 'flow_id.is_amount')
	def _compute_visible_flow_line_ids(self):
		for item in self:
			if item.flow_id:
				if item.flow_id.is_amount:
					flow_line_ids = []
					for fl in item.flow_id.line_ids:
						if fl.state_type in ['draft','cancel']:
							flow_line_ids.append(fl.id)
						elif fl.amount_price_min==0 and fl.amount_price_max==0:
							flow_line_ids.append(fl.id)
						elif fl.amount_price_min<=item.amount_mnt and fl.amount_price_max>=item.amount_mnt:
							flow_line_ids.append(fl.id)
					item.visible_flow_line_ids = flow_line_ids
				else:
					item.visible_flow_line_ids = self.env['dynamic.flow.line'].search([('flow_id', '=', item.flow_id.id),('flow_id.model_id.model', '=', 'oil.fuel')])
			else:
				item.visible_flow_line_ids = []

	def action_next_stage(self):
		next_flow_line_id = self.flow_line_id._get_next_flow_line()
		user_id = self.env.user
		for lines in self.line_ids:
			if lines.technic_id and lines.moto_hour< lines.before_moto_hour:
				raise UserError(u'Одоогийн мото цаг өмнөх мото цагаас бага байна !!! %s'%lines.technic_id.name)
			if lines.technic_id and lines.current_km < lines.before_km:
				raise UserError(u'Одоогийн явсан км өмнөх явсан км-с бага байна !!! %s'%lines.technic_id.name)
		if next_flow_line_id:
			print(next_flow_line_id.stage_id.name)
			if next_flow_line_id._get_check_ok_flow(False, user_id.department_id, user_id):
				self.flow_line_id = next_flow_line_id
				self.env['dynamic.flow.history'].create_history(next_flow_line_id, 'oil_id', self)
				if self.next_flow_line_id:
					send_users = self.next_flow_line_id._get_flow_users(False, user_id.department_id, user_id)
					hmtl = "%s Түлшний зарлагын баримтыг хянан уу!" % (self.name)
					if send_users:
						self.env.user.send_chat(hmtl,send_users.mapped('partner_id'))
			else:
				con_user = next_flow_line_id._get_flow_users(False, False)
				confirm_usernames = ''
				if con_user:
					confirm_usernames = ', '.join(con_user.mapped('display_name'))
				raise UserError(u'Та батлах хэрэглэгч биш байна\n Батлах хэрэглэгчид %s'%confirm_usernames)
			if self.flow_line_id.state_type=='done':
				self.action_done()
			self.env['dynamic.flow.history'].done_activity('purchase.request', self.id)

	def action_back_stage(self):
		user_id = self.env.user
		back_flow_line_id = self.flow_line_id._get_back_flow_line()
		next_flow_line_id = self.flow_line_id._get_next_flow_line()
		if back_flow_line_id:
			if back_flow_line_id._get_check_ok_flow(False, user_id.department_id, user_id):
				self.flow_line_id = back_flow_line_id
				self.env['dynamic.flow.history'].create_history(back_flow_line_id, 'oil_id', self)
				hmtl = "%s Түлшний зарлагын баримт буцаагдлаа" % (self.name)
				self.env.user.send_chat(hmtl,user_id.mapped('partner_id'))
			else:
				raise UserError(_('You are not back user'))
				
	def action_cancel_stage(self):
		user_id = self.env.user
		flow_line_id = self.flow_line_id._get_cancel_flow_line()
		if flow_line_id._get_check_ok_flow(False, user_id.department_id, user_id):
			self.flow_line_id = flow_line_id
			self.state = 'cancel'
			self.env['dynamic.flow.history'].create_history(flow_line_id, 'oil_id', self)
		else:
			raise UserError(_('You are not cancel user'))

	def action_draft_stage(self):
		flow_line_id = self.flow_line_id._get_draft_flow_line()
		if flow_line_id._get_check_ok_flow():
			self.flow_line_id = flow_line_id
			self.state = 'draft'
			self.env['dynamic.flow.history'].create_history(flow_line_id, 'oil_id', self)
		else:
			raise UserError(_('You are not draft user'))
	
	def action_import_technic(self):
		if self.state_type == 'draft':
			tech_ids = self.env['technic.equipment'].search([('branch_id','=',self.branch_id.id)])
			line_obj = self.env['oil.fuel.line']
			for item in tech_ids:
				line_obj.create({
					'parent_id': self.id,
					'technic_id': item.id,
					})