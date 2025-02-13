odoo.define('pos_kitchen.kitchen_kanban', function (require) {
    "use strict";
    
    var AbstractAction = require('web.AbstractAction');
    var core = require('web.core');
    var session = require('web.session');
    var QWeb = core.qweb;
    var KitchenKanban = AbstractAction.extend({
        template: 'kitchen_template',
        events: {
            'click .start_order_line': '_onStartOrEndOrderLine',
            'click .end_order_line': '_onStartOrEndOrderLine',
            'click .show_receipie': '_onShowReceipie',
            'click .recipie_container .icon-close': '_onHideRecipie',
            'click .show_note': '_onShowNote',
            'click .note_container .icon-close': '_onHideNote',
            'click .options_header': '_onShowHideRecipie',
            'click .pending-orders-filter': '_onFilterPendingOrders',
            'click .in-progress-orders-filter': '_onFilterInProgressOrders',
            'click .done-orders-filter': '_onFilterDoneOrders',
            'click .pause-play-refresh': '_onPausePlayRefresh',
        },
        auto_refresh: true,
        show_pending_orders: true,
        show_in_progress_orders: true,
        show_done_orders: true,
        category_ids: [],
        pos_config_ids: [],
        
        init: function(parent, action) {
            this._super(parent, action);
        },
        start: function() {
            var self = this;
            this._rpc({
                model: 'res.users',
                method: 'search_read',
                args: [[['id', '=', session.uid]], ['kitchen_category_ids']],
                args: [[['id', '=', session.uid]], ['kitchen_category_ids', 'pos_config_ids']],
            }).then(function (data) {
                self.category_ids = data[0].kitchen_category_ids;
                self.pos_config_ids = data[0].pos_config_ids;
                if (self.category_ids.length === 0 || self.pos_config_ids.length === 0) {
                    self.$('.setup_container').show();
                }
                self.load_data();
            });
            setInterval(function() {
                self.load_data();
            }, 30000);
        },
        load_data: function () {
            var self = this;
            if (!self.auto_refresh) {
                return;
            }
            if ($('.kitchen_container').length === 0) {
                self.$('.kanban_view').html(QWeb.render('kitchen_kanban', {}));
            }
            var today = new Date();
            var dd = String(today.getDate()).padStart(2, '0');
            var mm = String(today.getMonth() + 1).padStart(2, '0');
            var yyyy = today.getFullYear();
    
            today = yyyy + '-' + mm + '-' + dd;
            var fields = ['id', 'kitchen_state', 'name', 'start_date', 'user_id', 'pos_reference', 'table_id', 'create_date', 'customer_count'];
            self._rpc({
                model: 'pos.order.line',
                method: 'search_read',
                args: [[
                    ['create_date', '>=', today],
                    ['product_id.pos_categ_id.id', 'in', self.category_ids],
                    ['order_id.session_id.config_id.id', 'in', self.pos_config_ids]],
                    ['kitchen_state', 'full_product_name', 'qty', 'order_id', 'product_id', 'avg_completion_time', 'customer_note']
                ],
            }).then(function(lines) {
                self._rpc({
                    model: 'pos.order',
                    method: 'search_read',
                    args: [[['create_date', '>=', today], ['kitchen_state', '=', ['pending', 'in_progress', 'done']]], fields],
                }).then(function(orders) {
                    orders.forEach(function(order) {
                        order.user_id = order.user_id && order.user_id.length > 0 ? order.user_id[1] : '';
                        order.table_id = order.table_id && order.table_id.length > 0 ? order.table_id[1] : '';
                        order.create_date = self.convertDateToLocale(new Date(order.create_date));
                    });
                    if (self.show_pending_orders) {
                        self.getPendingOrders(lines, orders);
                    }
                    if (self.show_in_progress_orders) {
                        self.getInProgressOrders(lines, orders);
                    }
                    if (self.show_done_orders) {
                        self.getDoneOrders(lines, orders);
                    }
                });
            });
        },

        /*getPosCategories: function() {
            this._rpc({
                model: 'pos.category',
                method: 'search_read',
                args: [[['parent_id', '=', false], ['show_in_kitchen', '=', true]], ['name']],
            }).then(function (data) {
                console.warn(data);
                data.forEach((item) =>  {
                    $('#categories_selector').append($('<option>', { 
                        value: item['id'],
                        text : item['name'] 
                    }));
                });
            });
        },*/

        convertDateToLocale: function(date) {
            var newDate = new Date(date.getTime()+date.getTimezoneOffset()*60*1000);
            var offset = date.getTimezoneOffset() / 60;
            var hours = date.getHours();
            newDate.setHours(hours - offset);
            return newDate.toLocaleString();
        },
        
        _onShowReceipie: function (ev) {
            var product = $(ev.currentTarget).data( "product").split(',')[0];
            this._rpc({
                model: 'product.product',
                method: 'search_read',
                args: [[['id', '=', product]], ['name', 'recipie', 'image_512']],
            }).then(function (data) {
                if (!data[0]['recipie']) {
                    data[0]['recipie'] = '';
                }
                var html_data = '<div class="icon-close-container"><span class="icon-close"><i class="fa fa-close"></i></span></div>';
                html_data += '<h5> <i class="fa fa-file-text-o"/> ' + data[0]['name'] +  ' Recipie</h5>';
                html_data += '<div class="recipie_wrapper">';
                if (data[0]['image_512'] !== false) {
                    html_data += '<p class="product_image"><img src="data:image/png;base64, ' + data[0]['image_512'] + '" /></p>';
                }
                html_data += '<div class="recipie_description">' + data[0]['recipie'] + '</div>';
                html_data += '</div>';
                self.$('.recipie_container').html(html_data);
                self.$('.recipie_container').show();
            });
            
        },

        _onHideRecipie: function (ev) {
            this.$('.recipie_container').hide();
        },
        
        _onShowNote: function (ev) {
            var note = $(ev.currentTarget).data( "note");
            var product = $(ev.currentTarget).data( "product").split(',')[1];
            var html_data = '<div class="icon-close-container"><span class="icon-close"><i class="fa fa-close"></i></span></div>';
            html_data += '<h5> <i class="fa fa-sticky-note"/> ' + product +  ' Notes</h5>';
            html_data += '<div class="note_wrapper">';
            html_data += '<div class="recipie_description">' + note + '</div>';
            html_data += '</div>';
            self.$('.note_container').html(html_data);
            self.$('.note_container').show();
            
        },

        _onHideNote: function (ev) {
            this.$('.note_container').hide();
        },

        _onPausePlayRefresh: function (ev) {
            this.$('.pause-play-refresh').toggle();
            this.auto_refresh = !this.auto_refresh;
        },

        _onFilterPendingOrders: function (ev) {
            this.$('.pending-orders-filter').toggleClass('active');
            this.$('.kitchen_grid.pending').toggle();
            this.show_pending_orders = !this.show_pending_orders;
        },

        _onFilterInProgressOrders: function (ev) {
            this.$('.in-progress-orders-filter').toggleClass('active');
            this.$('.kitchen_grid.in_progress').toggle();
            this.show_in_progress_orders = !this.show_in_progress_orders;
        },

        _onFilterDoneOrders: function (ev) {
            self.$('.done-orders-filter').toggleClass('active');
            self.$('.kitchen_grid.done').toggle();
            this.show_done_orders = !this.show_done_orders;
        },

        _onShowHideRecipie: function (ev) {
            self.$('.options_body').toggle();
            self.$('.options_header .chevron-icons i').toggle();
        },
    
        _onStartOrEndOrderLine: function (ev) {
            var today = new Date();
            var date = today.getFullYear()+'-'+String(today.getMonth()+1).padStart(2, '0') + '-'+String(today.getDate()).padStart(2, '0');
            var time = String(today.getHours()).padStart(2, '0') + ":" + String(today.getMinutes()).padStart(2, '0') + ":" + String(today.getSeconds()).padStart(2, '0');
            var dateTime = date+' '+time;
            var self = this;
            ev.stopPropagation();
            var values = {}
            var id = $(ev.currentTarget).parent().data( "id");
            values[$(ev.currentTarget).data( "type") === 'start' ? 'start_date' : 'end_date'] = dateTime;
            
            this._rpc({
                model: 'pos.order.line',
                method: 'write',
                args: [[id], values],
            }).then(function () {
                self.load_data();
            });
        },
    
        getPendingOrders: function(lines, orders) {
            orders = this.getOrdersWithLines(orders, lines);
            orders = orders.filter((order) => {
                return order.lines.filter((line) => line.kitchen_state === 'in_progress' || line.kitchen_state === 'done').length === 0;
            });
            this.$('.kitchen_grid.pending .content').html(QWeb.render('kitchen_orders', {
                orders: orders
            }));
        },
    
        getInProgressOrders: function(lines, orders) {
            orders = this.getOrdersWithLines(orders, lines);
            orders = orders.filter((order) => {
                const in_progress_lines = order.lines.filter((line) => line.kitchen_state === 'in_progress');
                const pending_lines = order.lines.filter((line) => line.kitchen_state === 'pending');
                const done_lines = order.lines.filter((line) => line.kitchen_state === 'done');
                return (in_progress_lines.length > 0) || (pending_lines.length > 0 && done_lines.length > 0);
            });
            this.$('.kitchen_grid.in_progress .content').html(QWeb.render('kitchen_orders', {
                orders: orders
            }));
        },
    
        
    
        getDoneOrders: function(lines, orders) {
            orders = this.getOrdersWithLines(orders, lines);
            orders = orders.filter((order) => {
                return order.lines.filter((line) => line.kitchen_state !== 'done').length === 0;
            });
            this.$('.kitchen_grid.done .content').html(QWeb.render('kitchen_orders', {
                orders: orders
            }));
        },
    
        getOrdersWithLines: function(orders, lines) {
            orders.forEach(function(order) {
                order.lines = lines.filter((line) => line.order_id[0] === order.id);
            });
            orders = orders.filter((order) => order.lines.length > 0);
            return orders;
        }
    });
    core.action_registry.add("kitchen_kanban", KitchenKanban);
    });