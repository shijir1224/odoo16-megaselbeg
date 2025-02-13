odoo.define('xf_dashboard', function (require) {
    "use strict";

    const core = require('web.core');
    const AbstractAction = require('web.AbstractAction');
    const config = require('web.config');
    const QWeb = core.qweb;
    const XFDashboardWidget = require('xf_dashboard_widget');


    const XFDashboard = AbstractAction.extend({
        template: 'XFDashboardMain',

        widget_rows: {},

        init: function (parent, data) {
            this.parent = parent;
            this.has_been_loaded = $.Deferred();
            this.widget_rows = {};
            return this._super.apply(this, arguments);
        },

        willStart: function () {
            return $.when(
                this._super.apply(this, arguments),
                this.load_widgets_templates(),
                this.load_widgets_by_row(),
            );
        },

        load_widgets_templates: function () {
            const self = this;
            return this._rpc({
                model: 'xf.dashboard.widget',
                method: 'get_widgets_templates'
            }).then(function (qweb_templates) {
                qweb_templates.forEach(function (qweb_template_xml_id) {
                    self._rpc({
                        model: 'ir.ui.view',
                        method: 'read_template',
                        args: [qweb_template_xml_id]
                    }).then(function (xml) {
                        QWeb.add_template('<templates>' + xml + '</templates>');
                    });
                });
            });
        },

        load_widgets_by_row: function () {
            const self = this;
            return this._rpc({
                model: 'xf.dashboard.widget',
                method: 'get_widgets_by_row',
            }).then(function (response) {
                self.widget_rows = response;
            });
        },

        start: function () {
            const self = this;
            $(window).on('resize', this.do_sync_height);
            return this._super.apply(arguments).then(function () {
                self.load().done(function () {
                    self.do_sync_height();
                });
            });
        },

        destroy: function () {
            $(window).off('resize', this.do_sync_height);
            this._super.apply(this, arguments);
        },

        do_sync_height: function () {
            let $widgets = this.$el.find('.o_xf_dashboard_widgets .row > .o_xf_dashboard_widget');
            let content_block = '.o_xf_dashboard_widget_content';
            $widgets.each(function () {
                let $widget = $(this);
                let $widget_siblings = $widget.siblings();
                // reset height
                $widget.find(content_block).height('auto');
                $widget_siblings.each(function () {
                    $(this).find(content_block).height('auto');
                });
                if (config.device.size_class >= config.device.SIZES.MD) {
                    // set height
                    let content_heights = [$widget.find(content_block).height()];
                    $widget_siblings.each(function () {
                        content_heights.push($(this).find(content_block).height())
                    });
                    let max_height = Math.max.apply(null, content_heights);
                    $widget.find(content_block).height(max_height);
                    $widget_siblings.each(function () {
                        $(this).find(content_block).height(max_height);
                    });
                }
            });
        },

        do_update_widgets: function () {
            this.$el.find('.o_xf_dashboard_widgets').replaceWith(
                QWeb.render("XFDashboardWidgets", {'widget_rows': this.widget_rows})
            );
        },

        load: function () {
            const self = this;
            this._rpc({
                model: 'xf.dashboard.widget',
                method: 'get_widgets_data'
            }).then(function (data) {
                // Load each widget
                let all_widgets_defs = [self.do_update_widgets()];

                _.each(self.widget_rows, function (row) {
                    _.each(row['columns'], function (column) {
                        _.each(column['widgets'], function (widget) {
                            const widget_def = self.insert_widget(widget, data);
                            if (widget_def) {
                                all_widgets_defs.push(widget_def);
                            }
                        });
                    });
                    _.each(row['widgets'], function (widget) {
                        const widget_def = self.insert_widget(widget, data);
                        if (widget_def) {
                            all_widgets_defs.push(widget_def);
                        }
                    });
                });

                // Resolve has_been_loaded when all dashboards defs are resolved
                $.when.apply($, all_widgets_defs).then(function () {
                    self.has_been_loaded.resolve();
                });
            });


            return self.has_been_loaded;
        },

        insert_widget: function (widget_record, data) {
            let widget_data = data[widget_record['id']];
            let visible = true;
            if (widget_record['hide_no_content'] && widget_data.length === 0) {
                visible = false;
            }
            let $widget_container = this.$('#o_xf_dashboard_widget_' + widget_record['id'] + ' .o_xf_dashboard_widget_container');
            let $widget = new XFDashboardWidget(this, widget_record, widget_data);
            if (visible) {
                return $widget.replace($widget_container);
            } else {
                return this.$('#o_xf_dashboard_widget_' + widget_record['id']).hide();
            }
        },

        do_show: function () {
            this.parent.do_push_state({});
            return this._super();
        },

    });


    core.action_registry.add('xf_dashboard.main', XFDashboard);

    return XFDashboard;

});
