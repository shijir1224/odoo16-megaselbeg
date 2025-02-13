odoo.define('xf_dashboard_widget', function (require) {
    "use strict";

    const core = require('web.core');
    const AbstractAction = require('web.AbstractAction');
    const QWeb = core.qweb;

    return AbstractAction.extend({
        template: false,
        content_template: false,
        view_more_action: false,
        read_more_action: false,
        events: {
            'click .o_view_more': 'do_view_more',
            'click .o_read_more': 'do_read_more',
            'click .o_open_form': 'do_open_form',
            'click [data-action]': 'do_custom_action',
        },

        init: function (parent, widget_record, widget_data) {
            this.parent = parent;
            // data
            this.widget_record = widget_record;
            this.widget_data = widget_data;
            // actions
            this.view_more_action = widget_record['view_more_action']
            this.read_more_action = widget_record['read_more_action']
            // templates
            this.template = widget_record['container_template'];
            this.content_template = widget_record['content_template'];

            return this._super.apply(this, arguments);
        },

        do_update_content: function () {
            let $widget_content = this.$('.o_xf_dashboard_widget_content')
            $widget_content.html(QWeb.render(this.content_template, {
                'widget_record': this.widget_record,
                'data': this.widget_data
            }));
            let min_height = $widget_content.parents('.o_xf_dashboard_widget').data('content-min_height');
            if (min_height) {
                $widget_content.css('min-height', min_height);
            }
            let max_height = $widget_content.parents('.o_xf_dashboard_widget').data('content-max_height');
            if (max_height) {
                $widget_content.css('max-height', max_height);
            }
        },

        do_view_more: function (e) {
            if (this.view_more_action) {
                e.preventDefault();
                this.do_action(this.view_more_action);
            }
        },

        do_read_more: function (e) {
            const self = this;
            let res_id = Number(e.currentTarget.dataset['id']);
            if (this.read_more_action && res_id) {
                e.preventDefault();
                this._rpc({
                    route: "/web/action/load",
                    params: {
                        action_id: this.read_more_action,
                    },
                }).then(function (result) {
                    result.res_id = res_id;
                    self.do_action(result);
                });
            }
        },

        do_open_form: function (e) {
            let res_model = e.currentTarget.dataset['res_model'];
            let res_id = Number(e.currentTarget.dataset['id']);
            if (res_model && res_id) {
                e.preventDefault();
                this.do_action({
                    type: 'ir.actions.act_window',
                    res_model: res_model,
                    res_id: res_id,
                    views: [[false, 'form']],
                });
            }
        },

        do_custom_action: function (e) {
            let action_xml_id = e.currentTarget.dataset['action'];
            if (action_xml_id) {
                e.preventDefault();
                this.do_action(action_xml_id);
            }
        },

        start: function () {
            const self = this;
            return self._super.apply(this, arguments).then(function () {
                return self.do_update_content();
            });
        },

    });

});
