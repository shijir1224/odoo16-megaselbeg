from urllib.parse import uses_fragment
from odoo import  api, fields, models, _
from datetime import date, datetime, timedelta
from odoo.exceptions import UserError, ValidationError,Warning


class hse_product(models.Model):
	_name ='hse.product'
	_description = 'Hse product'
	_inherit = ["mail.thread", "mail.activity.mixin"]
   
	name = fields.Char(string='Нэр')
	english_name = fields.Char('Англи нэр',)
	china_name = fields.Char('Хятад нэр',)
	code = fields.Char('Код')
	type = fields.Char('Ангилал')
	uom_id = fields.Many2one('uom.uom', string='Хэмжих нэгж')
	end_date = fields.Date('Дуусах хугацаа',  default=fields.Date.context_today)
	company_id = fields.Many2one('res.company', string=u'Компани', readonly=True, default=lambda self: self.env.user.company_id)