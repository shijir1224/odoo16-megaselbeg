# -*- coding: utf-8 -*-
from odoo import models, fields, api


class View(models.Model):
    _inherit = 'ir.ui.view'

    def unlink(self):
        self.reset_container_template()
        self.reset_content_template()
        return super(View, self).unlink()

    def reset_container_template(self):
        for view in self:
            # search widgets which use template that will be deleted
            widgets = self.env['xf.dashboard.widget'].search([('container_template_id', '=', view.id)])
            if widgets:
                # if found, deactivate widgets and reset container template
                widgets.write({
                    'active': False,
                    'container_template_id': self.env.ref('xf_dashboard.default_widget_container').id
                })

    def reset_content_template(self):
        for view in self:
            # search widgets which use template that will be deleted
            widgets = self.env['xf.dashboard.widget'].search([('content_template_id', '=', view.id)])
            if widgets:
                # if found, deactivate widgets and reset content template
                widgets.write({
                    'active': False,
                    'content_template_id': self.env.ref('xf_dashboard.default_widget_content').id
                })

    @api.model
    def read_template(self, xml_id):
        template_id = self._get_view_id(xml_id)
        return self.sudo()._read_template(template_id)
