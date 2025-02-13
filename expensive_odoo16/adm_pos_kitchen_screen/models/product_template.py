from odoo import models, fields, api
import logging
_logger = logging.getLogger(__name__)
from datetime import datetime

class ProductTemplate(models.Model):

    _inherit = "product.template"
    
    recipie = fields.Html(string="Recipie")