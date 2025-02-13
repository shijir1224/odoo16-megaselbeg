import logging
from odoo import models, fields, api

class HrJob(models.Model):
	_inherit = "hr.job"

	job_conf = fields.Many2one('job.code.conf.mn',string='Ажил мэргэжлийн код')
    
class JobCodeConfMn(models.Model):
    _name = 'job.code.conf.mn'

    basic_group = fields.Char(string='Үндсэн бүлэг')
    basic_group_code = fields.Integer(string='Код /Үндсэн бүлэг/')
    sub_group = fields.Char(string='Дэд бүлэг')
    sub_group_code = fields.Integer(string='Код /Дэд бүлэг/')
    small_group = fields.Char(string='Бага бүлэг')
    small_group_code = fields.Integer(string='Код /Бага бүлэг/')
    negj_group = fields.Char(string='Нэгж бүлэг')
    negj_group_code = fields.Integer(string='Код /Нэгж бүлэг/')
    job_name = fields.Char(string='Ажил мэргэжил')
    percent = fields.Float(string='ҮО-ын хувь')
    name = fields.Char(string='Код')
    desc = fields.Char(string='Тайлбар')
    job = fields.Char(string='Компанийн нэршил /ажил, албан тушаал/')