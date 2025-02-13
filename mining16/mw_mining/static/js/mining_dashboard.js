odoo.define('mw_mining.mining_dashboard', function (require) {
    "use strict";

    var Widget= require('web.Widget');
    var widgetRegistry = require('web.widget_registry');
    var data = require('web.data');
    var FieldManagerMixin = require('web.FieldManagerMixin');

    var core = require('web.core');
    var QWeb = core.qweb;

    var MiningDashboardWidget = Widget.extend(FieldManagerMixin, {
        template : "mw_mining.MiningDashboardWidget",
        init: function (parent, dataPoint) {
            this._super.apply(this, arguments);
            this.data = dataPoint.data;
        },
         start: function() {
            var self = this;
            var dataPoint = this;
            console.log('dataPoint.data',dataPoint.data);
            if(dataPoint.data.group_by && dataPoint.data.date_from && dataPoint.data.date_to){
                var group_by = dataPoint.data.group_by;
                var date_from = dataPoint.data.date_from;
                var date_to = dataPoint.data.date_to;
                
                self.get_locations(group_by, date_from, date_to);
            }
            return this._super();
        },
        updateState: function (dataPoint) {
			var self = this;
			console.log('dataPoint.data',dataPoint.data);
			if(dataPoint.data.group_by && dataPoint.data.date_from && dataPoint.data.date_to){
				var group_by = dataPoint.data.group_by;
				var date_from = dataPoint.data.date_from;
				var date_to = dataPoint.data.date_to;
				
				self.get_locations(group_by, date_from, date_to);
			}
       	},
       	get_locations: function(group_by, date_from, date_to){
       		var self = this;
            var ds = new data.DataSet(this, 'mining.dashboard');
            console.log('mining blast 333');
            ds.call('get_mining_plan_datas', ['mining.dashboard', group_by, date_from, date_to])
                .then(function (res) {
                    self.display_data(res);
            });
       	},
       
        display_data: function(data) {
            var self = this;
            var self = this;
            console.log("=======DRAW=====", data);
            self.$el.html(QWeb.render("mw_mining.MiningDashboardWidget", {widget: self}));
            var datas = data[0]
//             // DATA zurax
//             // WO timesheet
            console.log('datas',datas);
            if (datas){
                console.log("datas['data_series_drilldown']",datas['data_series_drilldown']);
                var options = {
    chart: {
        type: 'column'
    },
    title: {
        text: 'Уулын ажлын төлөвлөгөө гүйцэтгэл'
    },
    // subtitle: {
    //     text: 'Source: WorldClimate.com'
    // },
    xAxis: {
        // categories: datas['categories'],
        // crosshair: true,
        type: 'category',
    },
    yAxis: [{ // Secondary yAxis
        title: {
            text: 'Өссөн дүн',
            
        },
        labels: {
            format: '{value} м3',
            
        },
        opposite: true
    },{ // Primary yAxis
        labels: {
            format: '{value} м3',
            
        },
        title: {
            text: 'Уулын цул',
            style: {
                color: Highcharts.getOptions().colors[1]
            }
        }
    }],
    
    tooltip: {
        headerFormat: '<span style="font-size:10px">{point.key}</span><table>',
        pointFormat: '<tr><td style="color:{series.color};padding:0">{series.name}: </td>' +
            '<td style="padding:0"><b>{point.y:,.0f} м3</b></td></tr>',
        footerFormat: '</table>',
        // valueDecimals: 2,
        shared: true,
        useHTML: true
    },
    plotOptions: {
        series: {
            borderWidth: 0,
            dataLabels: {
                enabled: true,
                format: '{point.y:.0f}',
                // /1000,
                // Highcharts.numberFormat(this.y/1000, 1, ',', '.'),
                // ; '{point.y:.1f}%',
                // format: Highcharts.numberFormat('{point.y:.1f}', 0, ',', '.'),
                style: {
                    fontSize: '6px',
                    fontFamily: 'Verdana, sans-serif'
                }
            }
        }
    },
    // plotOptions: {
    //     column: {
    //         pointPadding: 0,
    //         borderWidth: 0
    //     }
    // },
    series: datas['data_series'],
    "drilldown": {
        "series": datas['data_series_drilldown']
    }
    
}


                            try{
                                $('#mining_dashboard').highcharts(options);
                            }catch(err) {
                               console.log(err.message);
                            }
            }
            else {
                $('#mining_dashboard').remove();
            }
        },
    });
    widgetRegistry.add(
        'mining_dashboard_plan', MiningDashboardWidget
    );

});
