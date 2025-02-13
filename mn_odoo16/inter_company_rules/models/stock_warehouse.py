# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import Warning


class StockWarehouse(models.Model):

    _inherit = "stock.warehouse"

    is_main_for_branch = fields.Boolean('Салбарын үндсэн агуулах', default=False, help='Тухайн салбар уруу дотоод борлуулалт хийхэд үндсэн агуулахаар ашиглагдах бол үүнийг тэмдэглэнэ.')
