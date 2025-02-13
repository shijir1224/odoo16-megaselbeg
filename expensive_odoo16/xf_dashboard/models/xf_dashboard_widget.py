# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.tools.safe_eval import safe_eval


class XFDashboardWidget(models.Model):
    _name = 'xf.dashboard.widget'
    _description = 'Dashboard Widget'
    _order = 'sequence asc'

    active = fields.Boolean('Active', default=True)
    sequence = fields.Integer('Sequence', default=10)
    name = fields.Char('Name', required=True, translate=True)
    res_model = fields.Char(string='Model',
                            help="Model name on which the method to be called is located, e.g. 'res.partner'.")
    function = fields.Char(string='Method', help="Name of the method to be called when this job is processed.")
    kwargs = fields.Text(string='Arguments', help="kwargs to be passed to the method, e.g. {'limit':5}.", default="{}")
    allowed_keywords = fields.Char('Allowed Keywords', compute='_compute_allowed_keywords')
    container_template_id = fields.Many2one('ir.ui.view', string='Container Template', required=True,
                                            default=lambda self: self.env.ref('xf_dashboard.default_widget_container'))
    container_template = fields.Char('Container Template XML ID', related='container_template_id.xml_id', readonly=True)
    content_template_id = fields.Many2one('ir.ui.view', string='Content Template', required=True,
                                          default=lambda self: self.env.ref('xf_dashboard.default_widget_content'))
    content_template = fields.Char('Content Template XML ID', related='content_template_id.xml_id', readonly=True)

    view_more_action_id = fields.Many2one('ir.actions.act_window', string='View More Action',
                                          help='Window Action to be called on click to "View More" link')
    view_more_action = fields.Char('View More Action XML ID', related='view_more_action_id.xml_id', readonly=True)
    read_more_action_id = fields.Many2one('ir.actions.act_window', string='Read More Action',
                                          help='Window Action to be called on click to "Read More" link or item card')
    read_more_action = fields.Char('Read More Action XML ID', related='read_more_action_id.xml_id', readonly=True)

    custom_class = fields.Char('Custom CSS Class')

    col_selection = [(str(n), str(n)) for n in range(1, 13)]
    row_id = fields.Many2one('xf.dashboard.row', 'Row', required=True)
    column_id = fields.Many2one('xf.dashboard.column', 'Column', domain="[('row_id', '=', row_id)]")
    min_height = fields.Integer('Min Height', default=0)
    max_height = fields.Integer('Max Height', default=0)
    hide_no_content = fields.Boolean('Hide if No Content', help='Do not show widget if no content')
    show_view_more = fields.Boolean('Show "View More" Link', help='Show/Hide "View More" if widget has such link',
                                    default=True)
    show_title = fields.Boolean('Show Title', help='Show/Hide Widget Title', default=True)
    col_sm = fields.Selection(string='Col SM', selection=col_selection, required=True, default='6')
    col_md = fields.Selection(string='Col MD', selection=col_selection, required=True, default='6')
    col_lg = fields.Selection(string='Col LG', selection=col_selection, required=True, default='6')
    col_xl = fields.Selection(string='Col XL', selection=col_selection, required=True, default='6')

    def _domain_variables(self):
        return {
            'uid': self.env.user.id,
            'today': fields.Date.today(),
            'now': fields.Datetime.now(),
        }

    def _compute_allowed_keywords(self):
        domain_variables = self._domain_variables()
        for widget in self:
            widget.allowed_keywords = ', '.join(domain_variables.keys())

    @api.constrains('res_model', 'function', 'kwargs')
    def _check_function(self):
        for widget in self:
            if not widget.res_model or not widget.function:
                continue
            if widget.res_model not in self.env:
                raise ValidationError('Incorrect model name')
            res_model = self.env[widget.res_model]
            if not hasattr(res_model, widget.function) or not callable(getattr(res_model, widget.function)):
                raise ValidationError('Incorrect method name for the widget model {}'.format(widget.res_model))
            try:
                kwargs = safe_eval(widget.kwargs, self._domain_variables())
                if not isinstance(kwargs, dict):
                    raise ValidationError('Invalid arguments')
            except Exception:
                raise ValidationError('Invalid arguments')

    @api.model
    def get_widgets_by_row(self):
        column_fields_to_read = (
            'col_xl', 'col_lg', 'col_md', 'col_sm',
        )
        fields_to_read = [
            'display_name', 'custom_class',
            'col_xl', 'col_lg', 'col_md', 'col_sm',
            'min_height', 'max_height',
            'show_title', 'show_view_more', 'hide_no_content',
            'container_template', 'content_template',
            'view_more_action', 'read_more_action',
        ]
        rows = self.env['xf.dashboard.row'].search([('widgets', '!=', False)])
        response = []
        for row in rows:
            row_data = {'columns': [], 'widgets': []}
            if row.columns:
                for column in row.columns:
                    column_data = column.read(column_fields_to_read)[0]
                    column_data['widgets'] = column.widgets.read(fields_to_read)
                    row_data['columns'].append(column_data)
            else:
                row_data['widgets'] = row.widgets.read(fields_to_read)
            response.append(row_data)
        return response

    @api.model
    def get_widgets_templates(self):
        widgets = self.search([])
        container_templates = widgets.mapped('container_template')
        content_templates = widgets.mapped('content_template')
        return list(set(container_templates + content_templates))

    @api.model
    def get_widgets_data(self):
        widgets = self.search([])
        response = {}
        for widget in widgets:
            if not widget.res_model or not widget.function or widget.res_model not in self.env:
                continue
            res_model = self.env[widget.res_model]
            if hasattr(res_model, widget.function):
                widget_function = getattr(res_model, widget.function)
                if callable(widget_function):
                    kwargs = safe_eval(widget.kwargs, self._domain_variables())
                    response[widget.id] = widget_function(**kwargs)

        return response

    def action_open_new_template_wizard(self):
        wizard = self.env.ref('xf_dashboard.xf_dashboard_widget_template_wizard')
        return {
            'name': _('Dashboard Widget Template'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'xf.dashboard.widget.template',
            'views': [(wizard.id, 'form')],
            'view_id': wizard.id,
            'target': 'new',
            'context': {
                'template_field': self.env.context.get('template_field'),
                'default_widget_id': self.id,
            },
        }

    def get_hello_widget_data(self):
        return self.env.user.read(['name'])[0]

    def get_logo_widget_data(self):
        return {'logo_src': '/web/binary/company_logo'}
