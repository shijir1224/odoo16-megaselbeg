from odoo import models, fields, api
import logging
_logger = logging.getLogger(__name__)
from datetime import datetime

class ProductProduct(models.Model):

    _inherit = "product.product"
    
    avg_completion_time = fields.Integer(string="Avg completion time")
    recipie = fields.Html(related="product_tmpl_id.recipie", string="Recipie")