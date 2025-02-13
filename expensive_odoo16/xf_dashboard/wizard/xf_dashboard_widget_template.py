# -*- coding: utf-8 -*-
from lxml import etree

from odoo import fields, models
from odoo.tools.translate import encode


class XFDashboardWidgetTemplate(models.TransientModel):
    _name = 'xf.dashboard.widget.template'
    _description = 'Dashboard Widget Template'

    def get_default_arch(self):
        view = self.env.ref('xf_dashboard.default_widget_content')
        view_arch = etree.fromstring(encode(view.arch))
        items = view_arch.xpath('//div')
        if items:
            return etree.tostring(items[0])

    widget_id = fields.Many2one('xf.dashboard.widget', 'Widget')
    name = fields.Char('Name', required=True)
    xml_id = fields.Char('XML ID', required=True)
    arch_content = fields.Text('Content Architecture', required=True, default=get_default_arch)

    def create_template(self):
        # ir.ui.view
        external_xml_id = '{}.{}'.format(self._module, self.xml_id)
        view_vals = {
            'name': self.name,
            'type': 'qweb',
            'xml_id': external_xml_id,
            'key': external_xml_id,
            'arch_db': """<?xml version="1.0"?>\n<t name="{0}" t-name="{1}">{2}</t>""".format(self.name,
                                                                                              external_xml_id,
                                                                                              self.arch_content)
        }
        view = self.env['ir.ui.view'].create(view_vals)
        # ir.model.data
        model_data_vals = {
            'module': self._module,
            'name': self.xml_id,
            'noupdate': True,
            'model': 'ir.ui.view',
            'res_id': view.id
        }
        view.model_data_id = self.env['ir.model.data'].create(model_data_vals)

        template_field = self.env.context.get('template_field')
        if self.widget_id and template_field:
            setattr(self.widget_id, template_field, view.id)
        return True
