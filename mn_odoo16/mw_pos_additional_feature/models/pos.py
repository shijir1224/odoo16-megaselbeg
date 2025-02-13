from odoo import api, fields, models, _

class PosConfig(models.Model):
	_inherit = "pos.config"

	pos_user_ids = fields.Many2many('res.users', 'pos_config_res_user_rel', 'pos_config_id', 'user_id', string='Пос Харагдах Хэрэглэгч')