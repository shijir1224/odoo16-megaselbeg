# -*- coding: utf-8 -*-
from odoo import models, fields

class EnvironmentMeasurement(models.Model):
    _name = 'environment.measurement'
    _description = 'Environment Measurement'

    department_id = fields.Many2one('hr.department', string='Хэлтэс, нэгж', required=True)
    branch_id = fields.Many2one('res.branch', string='Дэд ангилал')
    registration_ids = fields.One2many('environment.registration', 'measurement_id', string='Бүртгэлүүд')
    date = fields.Date(string='Date', required=True)


class EnvironmentRegistration(models.Model):
    _name = 'environment.registration'
    _description = 'Environment Registration'

    department = fields.Char(string='Department', required=True)
    subsection = fields.Char(string='Subsection')
    wind_speed = fields.Float(string='Салхины хурд')
    temperature = fields.Float(string='Орчны температур')
    noise_level = fields.Float(string='Дуу чимээ')
    lighting = fields.Float(string='Гэрэлтүүлэг')
    humidity = fields.Float(string='Харьцангуй чийгшил')
    air_composition = fields.Char(string='Агаарын найрлага')
    measurement_id = fields.Many2one('environment.measurement', string='Measurement Reference', ondelete='cascade')