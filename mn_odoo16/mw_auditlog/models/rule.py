# Copyright 2015 ABF OSIELL <https://osiell.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, modules, _
from odoo import tools

class AuditlogRule(models.Model):
    _inherit = 'auditlog.rule'
    
    def get_tuple_str(self, tup):
        first_number = str(tup[0])
        tup = tup[1].encode("utf-8")
        tup = tup.decode('utf-8')
        number_s = '('+first_number+', '+tup+')'
        return number_s

    def get_unicode(self, number):
        try:
            if type(number) in [list]:
                s_number = '['
                for item in number:
                    if type(item) in [tuple]:
                        ddd = ', '+self.get_tuple_str(item)
                        s_number += ddd
                    else:
                        s_number += ', '+str(item)
                number = s_number+']'
            elif type(number) in [tuple]:
                number = self.get_tuple_str(number)
            else:
                number = number.encode("utf-8")
                number = number.decode('utf-8')
        except Exception as e:
            return number
        return number

    def _prepare_log_line_vals_on_read(self, log, field, read_values):
        res = super(AuditlogRule, self)._prepare_log_line_vals_on_read(log, field, read_values)
        res['old_value'] = self.get_unicode(res['old_value'])
        res['old_value_text'] = self.get_unicode(res['old_value_text'])
        return res

    def _prepare_log_line_vals_on_write(self, log, field, old_values, new_values):
        res = super(AuditlogRule, self)._prepare_log_line_vals_on_write(log, field, old_values, new_values)
        res['old_value'] = self.get_unicode(res['old_value'])
        res['old_value_text'] = self.get_unicode(res['old_value_text'])
        res['new_value'] = self.get_unicode(res['new_value'])
        res['new_value_text'] = self.get_unicode(res['new_value_text'])
        return res

    def _prepare_log_line_vals_on_create(self, log, field, new_values):
        res = super(AuditlogRule, self)._prepare_log_line_vals_on_create(log, field, new_values)
        res['new_value'] = self.get_unicode(res['new_value'])
        res['new_value_text'] = self.get_unicode(res['new_value_text'])
        return res


class auditlog_log_report(models.Model):
    _name = "auditlog.log.report"
    _description = "auditlog log report"
    _auto = False

    create_date = fields.Datetime('Create date', readonly=True)
    name = fields.Char("Resource Name", readonly=True)
    model_id = fields.Many2one('ir.model', string="Model", readonly=True)
    res_id = fields.Integer("Resource ID", readonly=True)
    user_id = fields.Many2one('res.users', string="User", readonly=True)
    method = fields.Char("Method", readonly=True)
    http_session_id = fields.Many2one('auditlog.http.session', string="Session", readonly=True)
    http_request_id = fields.Many2one('auditlog.http.request', string="HTTP Request", readonly=True)
    log_type = fields.Selection([('full', "Full log"),('fast', "Fast log"),], string="Type", readonly=True)
    
    field_id = fields.Many2one('ir.model.fields', string="Field", readonly=True)
    log_id = fields.Many2one('auditlog.log', string="Log", readonly=True)
    old_value = fields.Text("Old Value", readonly=True)
    new_value = fields.Text("New Value", readonly=True)
    old_value_text = fields.Text("Old value Text", readonly=True)
    new_value_text = fields.Text("New value Text", readonly=True)
    
    # field_name = fields.Char("Technical name", related='field_id.name')
    # field_description = fields.Char("Description", related='field_id.field_description')

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE or REPLACE VIEW %s as (
            SELECT  
                al_l.id,
                al.name,
                al.model_id,
                al.res_id,
                al.user_id,
                al.method,
                al.http_session_id,
                al.http_request_id,
                al.log_type,
                al_l.create_date,
                al_l.field_id,
                al_l.log_id,
                al_l.old_value,
                al_l.new_value,
                al_l.old_value_text,
                al_l.new_value_text

                from auditlog_log_line al_l
                left join  auditlog_log al on (al_l.log_id=al.id)

        )""" % self._table)