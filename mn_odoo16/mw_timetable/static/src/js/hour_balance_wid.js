odoo.define('mw_timetable.HourBalanceDynamic', function (require) {
"use strict";

var core = require('web.core');
var QWeb = core.qweb;
var Widget = require('web.Widget');
var widget_registry = require('web.widget_registry');
console.log('aaaaaaaaa3333 ');
var HourBalanceDynamic = Widget.extend({
    template: 'mw_timetable.HourBalanceDynamic',

    
    init: function (parent, params) {
	    console.log('aaaaaaaaa00 ');
        this.data = params.data;
        this.fields = params.fields;
        this._updateData();
        this._super(parent);
    },
        
    _updateData: function() {
        console.log('aaaaaaaaa ');
        var self = this;
        var get_data = this.data;
        var data_ids = get_data.id;
        var ds = new data.DataSet(this, 'hour.balance.dynamic');
        ds.call('get_balance_dynamic_js', [data_ids]).then(function(result) {
            if ( result!=undefined){      
                self.query_data = result;    
                self.balance_lines = result['line_ids'];
                self.conf_line = result['conf_line'];
                self.sum_foot = result['sum_foot'];
                self.sum_day_to_work = result['sum_day_to_work'];
                self.sum_hour_to_work = result['sum_hour_to_work'];
                self.$el.html(QWeb.render("mw_timetable.HourBalanceDynamic", {widget: self}));
                console.log("=======DRAW=====", self.balance_lines);
            }
        });
    },
    
    start: function () {
        this._render();
        return this._super.apply(this, arguments) 
    },

    _render: function () {
        console.log('aaaaaaaaa ');
        var self = this;
        var get_data = this.data;
        var data_ids = get_data.id;
        var ds = new data.DataSet(this, 'hour.balance.dynamic');
        ds.call('get_balance_dynamic_js', [data_ids]).then(function(result) {
            if ( result!=undefined){      
                self.query_data = result;    
                self.balance_lines = result['line_ids'];
                self.conf_line = result['conf_line'];
                self.sum_foot = result['sum_foot'];
                self.sum_day_to_work = result['sum_day_to_work'];
                self.sum_hour_to_work = result['sum_hour_to_work'];
                self.$el.html(QWeb.render("mw_timetable.HourBalanceDynamic", {widget: self}));
                
            }
        });
    },    
});

widget_registry.add('hr_dynamic_balance', HourBalanceDynamic);

return HourBalanceDynamic;
});
