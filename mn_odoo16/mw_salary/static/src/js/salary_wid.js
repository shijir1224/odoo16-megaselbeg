odoo.define('mw_salary.SalaryOrder', function (require) {
"use strict";

var core = require('web.core');
var QWeb = core.qweb;
var Widget = require('web.Widget');
var widget_registry = require('web.widget_registry');
var SalaryOrder = Widget.extend({
    template: 'mw_salary.SalaryOrder',

    
    init: function (parent, params) {
        this.data = params.data;
        this.fields = params.fields;
        this._updateData();
        this._super(parent);
    },

    _updateData: function() {
        var self = this;
        var get_data = this.data;
        var data_ids = get_data.id;
        var ds = new data.DataSet(this, 'salary.order');
        ds.call('get_salary_js', [data_ids]).then(function(result) {
            if ( result!=undefined){      
                self.query_data = result;    
                self.balance_lines = result['line_ids'];
                self.conf_line = result['conf_line'];
                self.sum_foot = result['sum_foot'];
                self.sum_day_to_work = result['sum_day_to_work'];
                self.sum_hour_to_work = result['sum_hour_to_work'];
                self.$el.html(QWeb.render("mw_salary.SalaryOrder", {widget: self}));
                console.log("=======DRAW=====", self.balance_lines);
            }
        });
    },
    
    start: function () {
        this._render();
        return this._super.apply(this, arguments) 
    },

    _render: function () {
        var self = this;
        var get_data = this.data;
        var data_ids = get_data.id;
        var ds = new data.DataSet(this, 'salary.order');
        ds.call('get_salary_js', [data_ids]).then(function(result) {
            if ( result!=undefined){      
                self.query_data = result;    
                self.balance_lines = result['line_ids'];
                self.conf_line = result['conf_line'];
                self.sum_foot = result['sum_foot'];
                self.sum_day_to_work = result['sum_day_to_work'];
                self.sum_hour_to_work = result['sum_hour_to_work'];
                self.$el.html(QWeb.render("mw_salary.SalaryOrder", {widget: self}));
                
            }
        });
    },    
});

widget_registry.add('hr_salary_order', SalaryOrder);

return SalaryOrder;
});
