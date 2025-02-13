odoo.define('mw_timetable.HrTimetable', function (require) {
    "use strict";

var Widget= require('web.Widget');
var widgetRegistry = require('web.widget_registry');
var core = require('web.core');
var QWeb = core.qweb;
var data = require('web.data');

var HrTimetable = Widget.extend({
    template : "mw_timetable.HrTimetable",

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
        var ds = new data.DataSet(this, 'hr.timetable');
        ds.call('get_timesheet_js', [data_ids]).then(function(result) {
            if ( result!=undefined){      
                self.query_data = result;    
                self.timesheet_lines = result['line_ids'];
                self.time_line = result['time_line'];
                self.$el.html(QWeb.render("mw_timetable.HrTimetable", {widget: self}));
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
        var ds = new data.DataSet(this, 'hr.timetable');
        this.display_data(this.data);
        ds.call('get_timesheet_js', [data_ids]).then(function(result) {
            if ( result!=undefined){      
                self.query_data = result;    
                self.timesheet_lines = result['line_ids'];
                self.time_line = result['time_line'];
                self.$el.html(QWeb.render("mw_timetable.HrTimetable", {widget: self}));
                console.log("=======DRAW=====", self.timesheet_lines);
            }
        });
    },
});
widgetRegistry.add('hr_monthly_timesheet', HrTimetable);
return HrTimetable
});
