# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)

class res_partner(models.Model):
	_inherit = 'res.partner'
	
	tin_type = fields.Selection([('company','Company'),('person','Person'),('none','none')], default='person', string='Tin type')
	payment_type = fields.Selection([
		('cash','Бэлэн'),
		('loan','Зээлээр'),
		('on_site','Байршуулах'),
		('cash_bank','Сардаа тэглэх')], default='cash')
	group_name = fields.Char('Group name' )
	is_mobile_active = fields.Boolean(u'Утсанд харагдах?', default=False)
	decrease_payment_amount = fields.Boolean(u'Хөнгөлөлтийн %-аа хасч шилжүүлдэг эсэх', default=False)
	driver_id = fields.Many2one('res.users', string='Driver', )
	print_type = fields.Selection([('type1','Үнийн хүснэгтээр'),('type2','Үндсэн үнээр хувь харагдуулах'),('type3','Эцсийн үнээр')], 'Хэвлэх төрөл')
	
	def name_get(self):
		res = []
		for partner in self:
			name = partner.name or ''

			if partner.company_name or partner.parent_id:
				if not name and partner.type in ['invoice', 'delivery', 'other']:
					name = dict(self.fields_get(['type'])['type']['selection'])[partner.type]
				if not partner.is_company:
					name = "%s, %s" % (partner.commercial_company_name or partner.parent_id.name, name)
			if self._context.get('show_address_only'):
				name = partner._display_address(without_company=True)
			if self._context.get('show_address'):
				name = name + "\n" + partner._display_address(without_company=True)
			name = name.replace('\n\n', '\n')
			name = name.replace('\n\n', '\n')
			if self._context.get('show_email') and partner.email:
				name = "%s <%s>" % (name, partner.email)
			if self._context.get('html_format'):
				name = name.replace('\n', '<br/>')
			if partner.group_name:
				name = partner.name+' ' + partner.group_name
			res.append((partner.id, name))
		return res
	
