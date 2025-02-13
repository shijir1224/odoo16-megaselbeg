from odoo import  api, fields, models, _
from datetime import datetime, timedelta
from io import BytesIO
from tempfile import NamedTemporaryFile
import base64
import xlsxwriter
import os,xlrd
from odoo.exceptions import UserError

class HseHazardReport(models.Model):
	_inherit = "hse.hazard.report"

	def action_to_back(self):
		if self.state =='repaired':
			self.write({'state':'to_assign'})