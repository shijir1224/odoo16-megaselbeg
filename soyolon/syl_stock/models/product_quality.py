from odoo import api, fields, models

class StockQualityNotification(models.Model):
	_name = 'stock.quality.notification'
	_description = 'Шаардлага хангаагүй барааны мэдэгдэл хүлээн авах'

	user_ids = fields.Many2many('res.users', string='Мэдэгдэл хүлээн авах хэрэглэгчид', required=True)