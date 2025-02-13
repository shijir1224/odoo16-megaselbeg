odoo.define('mw_mining.mining_blast_dash', function (require) {
    "use strict";

    var Widget= require('web.Widget');
    var widgetRegistry = require('web.widget_registry');
    var data = require('web.data');
    var FieldManagerMixin = require('web.FieldManagerMixin');

    var core = require('web.core');
    var QWeb = core.qweb;

    var MiningBlastWidget = Widget.extend(FieldManagerMixin, {
        template : "mw_mining.MiningBlastWidget",
        init: function (parent, dataPoint) {
            this._super.apply(this, arguments);
            this.data = dataPoint.data;
            	// $("head").append('<script type="text/javascript" src="mw_mining/static/libs/drilldown.js"></script>');
	            // $("head").append('<script type="text/javascript" src="mw_mining/static/libs/exporting.js"></script>');
	            // $("head").append('<script type="text/javascript" src="mw_mining/static/libs/export-data.js"></script>');
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
            ds.call('get_blast_plan_datas', ['mining.dashboard', group_by, date_from, date_to])
                .then(function (res) {
                    self.display_data(res);
            });
       	},
        // start: function() {
        //     var self = this;
        //     var ds = new data.DataSet(this, 'mining.dashboard');
        //     console.log('mining blast 333');
        //     ds.call('get_blast_plan_datas', ['mining.dashboard'])
        //         .done(function (res) {
        //             self.display_data(res);
        //     });
        // },
        display_data: function(data) {
            var self = this;
            var self = this;
            console.log("=======DRAW=====", data);
            self.$el.html(QWeb.render("mw_mining.MiningBlastWidget", {widget: self}));
            var datas = data[0]
            // DATA zurax
            // WO timesheet
            console.log('datas',datas);
            if (datas['data_series']){
                var options = {
    chart: {
        type: 'column'
    },
    title: {
        text: 'Салбарын төлөвлөгөө гүйцэтгэл'
    },
    // subtitle: {
    //     text: 'Source: WorldClimate.com'
    // },
    xAxis: {
        // categories: datas['categories'],
        // crosshair: true,
        type: 'category',
    },
    yAxis: {
        min: 0,
        title: {
            text: 'м3'
        }
    },
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
        column: {
            pointPadding: 0.2,
            borderWidth: 0
        }
    },
    series: datas['data_series'],
    "drilldown": {
        "series": datas['data_series_drilldown']
    }
    // series: [{
    //     name: 'Мастер Төлөвлөгөө',
    //     data: [48.9, 38.8, 39.3, 41.4, 47.0, 48.3, 59.0, 59.6, 52.4, 65.2, 59.3, 51.2]

    // },
    // {
    //     name: 'Төлөвлөгөө',
    //     data: [49.9, 71.5, 106.4, 129.2, 144.0, 176.0, 135.6, 148.5, 216.4, 194.1, 95.6, 54.4]

    // }, {
    //     name: 'Гүйцэтгэл',
    //     data: [83.6, 78.8, 98.5, 93.4, 106.0, 84.5, 105.0, 104.3, 91.2, 83.5, 106.6, 92.3]

    // }]
}



//                 var options ={
//     chart: {
//         type: 'column'
//     },
//     title: {
//         text: 'Browser market shares. January, 2018'
//     },
//     subtitle: {
//         text: 'Click the columns to view versions. Source: <a href="http://statcounter.com" target="_blank">statcounter.com</a>'
//     },
//     // xAxis: {
//     //     type: 'category'
//     // },
//     xAxis: {
//         categories: [
//             'Jan',
//             'Feb',
//             'Mar',
//             'Apr',
//             'May',
//             'Jun',
//             'Jul',
//             'Aug',
//             'Sep',
//             'Oct',
//             'Nov',
//             'Dec'
//         ],
//         crosshair: true
//     },
//     yAxis: {
//         title: {
//             text: 'Total percent market share'
//         }

//     },
//     legend: {
//         enabled: false
//     },
//     plotOptions: {
//         series: {
//             borderWidth: 0,
//             dataLabels: {
//                 enabled: true,
//                 format: '{point.y:.1f}%'
//             }
//         }
//     },

//     tooltip: {
//         headerFormat: '<span style="font-size:11px">{series.name}</span><br>',
//         pointFormat: '<span style="color:{point.color}">{point.name}</span>: <b>{point.y:.2f}%</b> of total<br/>'
//     },

//     "series": [
//         {
//             "name": "Browsers",
//             "colorByPoint": true,
//             "data": [
//                 {
//                     "name": "Chrome",
//                     "y": 62.74,
//                     "drilldown": "Chrome"
//                 },
//                 {
//                     "name": "Firefox",
//                     "y": 10.57,
//                     "drilldown": "Firefox"
//                 },
//                 {
//                     "name": "Internet Explorer",
//                     "y": 7.23,
//                     "drilldown": "Internet Explorer"
//                 },
//                 {
//                     "name": "Safari",
//                     "y": 5.58,
//                     "drilldown": "Safari"
//                 },
//                 {
//                     "name": "Edge",
//                     "y": 4.02,
//                     "drilldown": "Edge"
//                 },
//                 {
//                     "name": "Opera",
//                     "y": 1.92,
//                     "drilldown": "Opera"
//                 },
//                 {
//                     "name": "Other",
//                     "y": 7.62,
//                     "drilldown": null
//                 }
//             ]
//         },
//         {
//             "name": "Browsers11",
//             "colorByPoint": true,
//             "data": [
//                 {
//                     "name": "Chrome11",
//                     "y": 62.74,
//                     "drilldown": "Chrome11"
//                 },
//                 {
//                     "name": "Firefox11",
//                     "y": 10.57,
//                     "drilldown": "Firefox11"
//                 },
//                 {
//                     "name": "Internet Explorer11",
//                     "y": 7.23,
//                     "drilldown": "Internet Explorer11"
//                 },
//                 {
//                     "name": "Safari11",
//                     "y": 5.58,
//                     "drilldown": "Safari11"
//                 },
//                 {
//                     "name": "Edge11",
//                     "y": 4.02,
//                     "drilldown": "Edge11"
//                 },
//                 {
//                     "name": "Opera11",
//                     "y": 1.92,
//                     "drilldown": "Opera11"
//                 },
//                 {
//                     "name": "Other11",
//                     "y": 7.62,
//                     "drilldown": null
//                 }
//             ]
//         }

//     ],
//     "drilldown": {
//         "series": [
//         {
//                 "name": "Chrome11",
//                 "id": "Chrome11",
//                 "data": [
//                     [
//                         "v65.0",
//                         0.2
//                     ],
//                     [
//                         "v64.0",
//                         1.5
//                     ],
//                     [
//                         "v63.0",
//                         56.02
//                     ],
//                     [
//                         "v62.0",
//                         0.4
//                     ],
//                     [
//                         "v61.0",
//                         0.88
//                     ],
//                     [
//                         "v60.0",
//                         0.56
//                     ],
//                     [
//                         "v59.0",
//                         0.45
//                     ],
//                     [
//                         "v58.0",
//                         0.49
//                     ],
//                     [
//                         "v57.0",
//                         0.32
//                     ],
//                     [
//                         "v56.0",
//                         0.29
//                     ],
//                     [
//                         "v55.0",
//                         0.79
//                     ],
//                     [
//                         "v54.0",
//                         0.18
//                     ],
//                     [
//                         "v51.0",
//                         0.13
//                     ],
//                     [
//                         "v49.0",
//                         2.16
//                     ],
//                     [
//                         "v48.0",
//                         0.13
//                     ],
//                     [
//                         "v47.0",
//                         0.11
//                     ],
//                     [
//                         "v43.0",
//                         0.17
//                     ],
//                     [
//                         "v29.0",
//                         0.26
//                     ]
//                 ]
//             },
//             {
//                 "name": "Chrome",
//                 "id": "Chrome",
//                 "data": [
//                     [
//                         "v65.0",
//                         0.1
//                     ],
//                     [
//                         "v64.0",
//                         1.3
//                     ],
//                     [
//                         "v63.0",
//                         53.02
//                     ],
//                     [
//                         "v62.0",
//                         1.4
//                     ],
//                     [
//                         "v61.0",
//                         0.88
//                     ],
//                     [
//                         "v60.0",
//                         0.56
//                     ],
//                     [
//                         "v59.0",
//                         0.45
//                     ],
//                     [
//                         "v58.0",
//                         0.49
//                     ],
//                     [
//                         "v57.0",
//                         0.32
//                     ],
//                     [
//                         "v56.0",
//                         0.29
//                     ],
//                     [
//                         "v55.0",
//                         0.79
//                     ],
//                     [
//                         "v54.0",
//                         0.18
//                     ],
//                     [
//                         "v51.0",
//                         0.13
//                     ],
//                     [
//                         "v49.0",
//                         2.16
//                     ],
//                     [
//                         "v48.0",
//                         0.13
//                     ],
//                     [
//                         "v47.0",
//                         0.11
//                     ],
//                     [
//                         "v43.0",
//                         0.17
//                     ],
//                     [
//                         "v29.0",
//                         0.26
//                     ]
//                 ]
//             },
//             {
//                 "name": "Firefox",
//                 "id": "Firefox",
//                 "data": [
//                     [
//                         "v58.0",
//                         1.02
//                     ],
//                     [
//                         "v57.0",
//                         7.36
//                     ],
//                     [
//                         "v56.0",
//                         0.35
//                     ],
//                     [
//                         "v55.0",
//                         0.11
//                     ],
//                     [
//                         "v54.0",
//                         0.1
//                     ],
//                     [
//                         "v52.0",
//                         0.95
//                     ],
//                     [
//                         "v51.0",
//                         0.15
//                     ],
//                     [
//                         "v50.0",
//                         0.1
//                     ],
//                     [
//                         "v48.0",
//                         0.31
//                     ],
//                     [
//                         "v47.0",
//                         0.12
//                     ]
//                 ]
//             },
//             {
//                 "name": "Internet Explorer",
//                 "id": "Internet Explorer",
//                 "data": [
//                     [
//                         "v11.0",
//                         6.2
//                     ],
//                     [
//                         "v10.0",
//                         0.29
//                     ],
//                     [
//                         "v9.0",
//                         0.27
//                     ],
//                     [
//                         "v8.0",
//                         0.47
//                     ]
//                 ]
//             },
//             {
//                 "name": "Safari",
//                 "id": "Safari",
//                 "data": [
//                     [
//                         "v11.0",
//                         3.39
//                     ],
//                     [
//                         "v10.1",
//                         0.96
//                     ],
//                     [
//                         "v10.0",
//                         0.36
//                     ],
//                     [
//                         "v9.1",
//                         0.54
//                     ],
//                     [
//                         "v9.0",
//                         0.13
//                     ],
//                     [
//                         "v5.1",
//                         0.2
//                     ]
//                 ]
//             },
//             {
//                 "name": "Edge",
//                 "id": "Edge",
//                 "data": [
//                     [
//                         "v16",
//                         2.6
//                     ],
//                     [
//                         "v15",
//                         0.92
//                     ],
//                     [
//                         "v14",
//                         0.4
//                     ],
//                     [
//                         "v13",
//                         0.1
//                     ]
//                 ]
//             },
//             {
//                 "name": "Opera",
//                 "id": "Opera",
//                 "data": [
//                     [
//                         "v50.0",
//                         0.96
//                     ],
//                     [
//                         "v49.0",
//                         0.82
//                     ],
//                     [
//                         "v12.1",
//                         0.14
//                     ]
//                 ]
//             }
//         ]
//     }
// }
                // var options = {
                //     chart: {
                //     type: 'line'
                // },
                // title: {
                //     text: 'Blast volume'
                // },
                // subtitle: {
                //     text: "Mera blast project's"
                // },
                // xAxis: {
                //     categories: datas['categories']
                // },
                // yAxis: {
                //     title: {
                //         text: 'Blast volume'
                //     }
                // },
                // plotOptions: {
                //     line: {
                //         dataLabels: {
                //             enabled: true
                //         },
                //         enableMouseTracking: false
                //     }
                // },
                // series: datas['data_series']
                // }

                            try{
                                $('#mining_blast').highcharts(options);
                            }catch(err) {
                               console.log(err.message);
                            }
            }
            else {
                $('#mining_blast').remove();
            }
        },
    });
    widgetRegistry.add(
        'mining_blast_plan', MiningBlastWidget
    );

});
