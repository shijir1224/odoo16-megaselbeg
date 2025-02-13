# pylint: disable=missing-docstring
# Copyright 2016 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, exceptions, fields, models
from datetime import datetime
from dateutil.relativedelta import relativedelta

_intervalTypes = {
	'days': lambda interval: relativedelta(days=interval),
	'hours': lambda interval: relativedelta(hours=interval),
	'weeks': lambda interval: relativedelta(days=7*interval),
	'months': lambda interval: relativedelta(months=interval),
	'minutes': lambda interval: relativedelta(minutes=interval),
}

DEFAULT_MESSAGE = "Default message"

SUCCESS = "success"
DANGER = "danger"
WARNING = "warning"
INFO = "info"
DEFAULT = "default"

class ResUsers(models.Model):
	_inherit = "res.users"

	def _notify_channel(
		self,
		type_message=DEFAULT,
		message=DEFAULT_MESSAGE,
		title=None,
		sticky=False,
		mw_not_id=False,
	):
		if not self.env.user._is_admin() and any(
			user.id != self.env.uid for user in self
		):
			raise exceptions.UserError(
				_("Sending a notification to another user is forbidden.")
			)
		channel_name_field = "notify_{}_channel_name".format(type_message)
		bus_message = {
			"type": type_message,
			"message": message,
			"title": title,
			"sticky": sticky,
			"mw_not_id": mw_not_id,
		}
		notifications = [
			(record[channel_name_field], bus_message) for record in self
		]
		self.env["bus.bus"]._sendmany(notifications)

class mw_notify(models.Model):
	_name = 'mw.notify'
	_inherit = 'mail.thread'
	_description = 'mw notify'
	
	@api.model
	def default_get(self, fields):
		def_context = self.env.context
		defaults = super(mw_notify, self).default_get(fields)
		res_id = False
		model_model = False
		try:
			res_id = def_context['params']['id']
			model_model = def_context['params']['model']
		except Exception as e:
			pass
		if res_id:
			defaults['res_id'] = res_id
		if model_model:
			defaults['model_model'] = model_model
		return defaults

	name = fields.Char('Гарчиг')
	desc = fields.Text('Тайлбар')
	res_id = fields.Integer('Res ID')
	model_model = fields.Char(readonly=True)
	active = fields.Boolean('Мэдэгдэл хүргэх', default=True, tracking=True)
	user_ids = fields.Many2many('res.users', 'mw_notify_user_rel', 'nof_id', 'user_id', string='Мэдэгдэл очих ажилтанууд')
	sticky = fields.Boolean('X-тэй байх', default=False, tracking=True)
	type = fields.Selection([
		('success','SUCCESS'),
		('danger','DANGER'),
		('warning','WARNING'),
		('info','INFO'),
		('default','DEFAULT'),
		], default='info', string='Төрөл', tracking=True)
	interval_number = fields.Integer(default=1, string='Давтамж', tracking=True)
	interval_type = fields.Selection([('minutes', 'Minutes'),
									  ('hours', 'Hours'),
									  ('days', 'Days'),
									  ('weeks', 'Weeks'),
									  ('months', 'Months')], string='Давтамжийн төрөл', default='hours', tracking=True)
	nextcall = fields.Datetime(string='Дараагийн дуудах', required=True, default=fields.Datetime.now, readonly=True, tracking=True)
	lastcall = fields.Datetime(string='Сүүлийн дуудсан', readonly=True, tracking=True)

	def showed(self, res_id):
		self.env['mw.notify'].browse(res_id).active = False
		return True

	def check_notify_hand(self):
		self.check_notify()

	def def_search(self):
		return self.env['mw.notify'].search([('res_id','!=',False), ('model_model','!=',False)])

	def send_notify(self):
		item = self
		for user in item.user_ids:
			mw_not_id = {
				'mw_id': self.id,
				'mw_res_id': self.res_id,
				'mw_model_model': self.model_model
			}
			user._notify_channel(item.type, item.desc+'<div id="mw_not"></div>', item.name, sticky=item.sticky, mw_not_id=mw_not_id)
		item.lastcall = datetime.now()
		nemegdeh = _intervalTypes[item['interval_type']](item['interval_number'])
		lastcall = item.lastcall + nemegdeh
		item.nextcall = lastcall
		
	@api.model
	def check_notify(self):
		pass
		not_ids = self.def_search()
		for item in not_ids:
			now = datetime.now()
			if now >= item.nextcall:
				item.send_notify()
