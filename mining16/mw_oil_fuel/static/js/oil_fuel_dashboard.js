odoo.define('mw_oil_fuel.oil_fuel_dashboard', function (require) {
    "use strict";

    var Widget= require('web.Widget');
    var widgetRegistry = require('web.widget_registry');
    var data = require('web.data');
    var FieldManagerMixin = require('web.FieldManagerMixin');

    var core = require('web.core');
    var QWeb = core.qweb;

    var FuelProdDashboardWidget = Widget.extend(FieldManagerMixin, {
        template : "mw_oil_fuel.FuelProdDashboardWidget",
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
                var technic_ids = dataPoint.data.technic_ids;
                console.log('technic_ids---- ',technic_ids);
                if (technic_ids){
                    technic_ids = technic_ids.res_ids;
                }
                var technic_setting_id = dataPoint.data.technic_setting_id;
                if (technic_setting_id){
                    technic_setting_id = technic_setting_id.data.id
                }
                self.get_locations(group_by, date_from, date_to, technic_ids, technic_setting_id);
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
                var technic_ids = dataPoint.data.technic_ids;
                if (technic_ids){
                    technic_ids = technic_ids.res_ids;
                }
                var technic_setting_id = dataPoint.data.technic_setting_id;
                if (technic_setting_id){
                    technic_setting_id = technic_setting_id.data.id
                }
                self.get_locations(group_by, date_from, date_to, technic_ids, technic_setting_id);
            }
        },
        get_locations: function(group_by, date_from, date_to, technic_ids, technic_setting_id){
            var self = this;
            var ds = new data.DataSet(this, 'oil.fuel.dashboard');
            console.log('mining blast 333');
            ds.call('get_fuel_prod_datas', ['oil.fuel.dashboard', group_by, date_from, date_to, technic_ids, technic_setting_id, 'shift'])
                .then(function (res) {
                 self.display_data(res);
                 
            });
        },
        display_data_draw: function(data, get_type) {
            var datas = data[0];
            if (datas && datas['data_series']){
                var technic_name = datas['technic_name'];
                var gr_by = datas['gr_by'];
                var min = datas['fuel_idle']['min'];
                var mid = datas['fuel_idle']['mid'];
                var max = datas['fuel_idle']['max'];
                var series = [];
                if (get_type=='shift' || get_type=='production_shift'){
                    series = [{
                                name: 'Өдөр түлш',
                                color: 'rgba(165,120,217,1)',
                                data: datas['data_series']['series_day_fuel'],
                                pointPadding: 0.3,
                                pointPlacement: -0.2,
                                dataLabels: {
                                    enabled: true,
                                    align: 'left',
                                    format: '{point.y:.1f}', // one decimal
                                    style: {
                                        fontSize: '8px',
                                        fontFamily: 'Verdana, sans-serif'
                                    }
                                }
                            }
                            ]
                    if (get_type=='shift'){
                        series.push({
                                name: 'Өдөр ресс',
                                color: 'rgba(248,199,63,1)',
                                data: datas['data_series']['series_day_res'],
                                pointPadding: 0.4,
                                pointPlacement: -0.2,
                                yAxis: 1,
                                dataLabels: {
                                    enabled: true,
                                    color: '#FFFFFF',
                                    align: 'left',
                                    format: '{point.y:.0f}', // one decimal
                                    style: {
                                        fontSize: '8px',
                                        fontFamily: 'Verdana, sans-serif'
                                    }
                                }
                            })
                    }else if (get_type=='production_shift'){
                        series.push({
                                name: 'Өдөр бүтээл',
                                color: 'rgba(23,164,45)',
                                data: datas['data_series']['series_day_prod'],
                                pointPadding: 0.4,
                                pointPlacement: -0.2,
                                yAxis: 1,
                                dataLabels: {
                                    enabled: true,
                                    color: '#FFFFFF',
                                    align: 'left',
                                    format: '{point.y:.0f}', // one decimal
                                    style: {
                                        fontSize: '8px',
                                        fontFamily: 'Verdana, sans-serif'
                                    }
                                }
                            })
                    }
                    series.push({
                                name: 'Шөнө түлш',
                                color: 'rgba(165,170,217,1)',
                                data: datas['data_series']['series_night_fuel'],
                                pointPadding: 0.3,
                                pointPlacement: 0.2,
                                dataLabels: {
                                    enabled: true,
                                    align: 'left',
                                    format: '{point.y:.1f}', // one decimal
                                    style: {
                                        fontSize: '8px',
                                        fontFamily: 'Verdana, sans-serif'
                                    }
                                }
                            })

                    if (get_type=='shift'){
                        series.push({
                                name: 'Шөнө ресс',
                                color: 'rgba(248,161,63,1)',
                                data: datas['data_series']['series_night_res'],
                                pointPadding: 0.4,
                                pointPlacement: 0.2,
                                yAxis: 1,
                                dataLabels: {
                                    enabled: true,
                                    color: '#FFFFFF',
                                    align: 'left',
                                    format: '{point.y:.0f}', // one decimal
                                    style: {
                                        fontSize: '8px',
                                        fontFamily: 'Verdana, sans-serif'
                                    }
                                }
                            })
                    }else if (get_type=='production_shift'){
                        series.push({
                                name: 'Шөнө бүтээл',
                                color: 'rgba(23,234,45)',
                                data: datas['data_series']['series_night_prod'],
                                pointPadding: 0.4,
                                pointPlacement: 0.2,
                                yAxis: 1,
                                dataLabels: {
                                    enabled: true,
                                    color: '#FFFFFF',
                                    align: 'left',
                                    format: '{point.y:.0f}', // one decimal
                                    style: {
                                        fontSize: '8px',
                                        fontFamily: 'Verdana, sans-serif'
                                    }
                                }
                            })
                    }
                }else{
                    series = [{
                                name: 'Өдөр түлш',
                                color: 'rgba(165,120,217,1)',
                                data: datas['data_series']['series_date_fuel'],
                                pointPadding: 0.3,
                                pointPlacement: -0.2,
                                dataLabels: {
                                    enabled: true,
                                    align: 'left',
                                    format: '{point.y:.1f}', // one decimal
                                    // x: 10, // 10 pixels down from the top
                                    style: {
                                        fontSize: '8px',
                                        fontFamily: 'Verdana, sans-serif'
                                    }
                                }
                            }
                            ]
                    if (get_type=='date'){
                        series.push({
                                name: 'Өдөр ресс',
                                color: 'rgba(248,199,63,1)',
                                data: datas['data_series']['series_date_res'],
                                pointPadding: 0.4,
                                pointPlacement: -0.2,
                                yAxis: 1,
                                dataLabels: {
                                    enabled: true,
                                    color: '#FFFFFF',
                                    align: 'left',
                                    format: '{point.y:.0f}', // one decimal
                                    // x: -10, // 10 pixels down from the top
                                    style: {
                                        fontSize: '8px',
                                        fontFamily: 'Verdana, sans-serif'
                                    }
                                }
                            })
                    }else if (get_type=='production_date'){
                        series.push( {
                                name: 'Өдөр бүтээл',
                                color: 'rgba(23,234,45)',
                                data: datas['data_series']['series_date_prod'],
                                pointPadding: 0.4,
                                pointPlacement: -0.2,
                                yAxis: 1,
                                dataLabels: {
                                    enabled: true,
                                    color: '#FFFFFF',
                                    align: 'left',
                                    format: '{point.y:.0f}', // one decimal
                                    // x: -10, // 10 pixels down from the top
                                    style: {
                                        fontSize: '8px',
                                        fontFamily: 'Verdana, sans-serif'
                                    }
                                }
                            })
                    }
                }
                
                var options ={
                            chart: {
                                type: 'column'
                            },
                            title: {
                                text: technic_name
                            },
                            subtitle: {
                                                text: 'Өдөр Шөнийн Ээлжээр Түлш зарцуулалт Рессийн тоо '+gr_by
                                            },
                            xAxis: {
                                categories: datas['categ_names']
                            },
                            yAxis: [{
                                min: 0,
                                title: {
                                    text: 'Түлш зарцуулалт'
                                },
                                plotLines: [
                                                    {
                                                        value: min,
                                                        color: 'green',
                                                        dashStyle: 'shortdash',
                                                        width: 2,
                                                        label: {
                                                            text: 'Fuel low idle'
                                                        }
                                                    },
                                                    {
                                                        value: mid,
                                                        color: 'orange',
                                                        dashStyle: 'shortdash',
                                                        width: 2,
                                                        label: {
                                                            text: 'Fuel medium idle'
                                                        }
                                                    },
                                                    {
                                                        value: max,
                                                        color: 'red',
                                                        dashStyle: 'shortdash',
                                                        width: 2,
                                                        label: {
                                                            text: 'Fuel high idle'
                                                        }
                                                    }
                                                    ]
                            }, {
                                title: {
                                    text: 'Явсан ресс'
                                },
                                opposite: true
                            }],
                            legend: {
                                shadow: false
                            },
                            tooltip: {
                                shared: true,
                                valueDecimals: 2
                            },
                            plotOptions: {
                                column: {
                                    grouping: false,
                                    shadow: false,
                                    borderWidth: 0
                                }
                            },
                            series: series
                        }

                                try{
                                    if (get_type=='shift'){
                                        $('#fuel_prod_dashboard').highcharts(options);
                                    }else if (get_type=='date'){
                                        $('#fuel_prod_day_dashboard').highcharts(options);
                                    }else if (get_type=='production_date'){
                                        $('#fuel_with_prod_day').highcharts(options);
                                    }else if (get_type=='production_shift'){
                                        $('#fuel_with_prod_shift').highcharts(options);
                                    }
                                    
                                }catch(err) {
                                   console.log(err.message);
                                }
                }
        },
        display_data: function(data) {
            var self = this;
            console.log("=======DRAW=====", data);
            self.$el.html(QWeb.render("mw_oil_fuel.FuelProdDashboardWidget", {widget: self}));
            
            self.display_data_draw(data, 'shift');
            self.display_data_draw(data, 'date');
            self.display_data_draw(data, 'production_date');
            self.display_data_draw(data, 'production_shift');
        },
    });
    widgetRegistry.add(
        'fuel_prod_dashboard', FuelProdDashboardWidget
    );

});
