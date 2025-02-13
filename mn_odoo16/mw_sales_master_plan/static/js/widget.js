odoo.define('mw_sales_master_plan.view', function (require) {
	"use strict";

	var core = require('web.core');
	var data = require('web.data');
	var form_common = require('web.form_common');
	var Session = require('web.session');
	var formats = require('web.formats');
	var Model = require('web.DataModel');
	var time = require('web.time');
	var utils = require('web.utils');

	var QWeb = core.qweb;
	var _t = core._t;

	// SALES Dashboard
	// Company sales
	var SALES_PLAN_DASHBOARD_01 = form_common.FormWidget.extend(form_common.ReinitializeWidgetMixin, {
		template : "mw_sales_master_plan.SALES_PLAN_DASHBOARD_01",

		init: function() {

			// Required libs
        	$("head").append('<script type="text/javascript" src="mw_sales_master_plan/static/libs/drilldown.js"></script>');
   			$("head").append('<script type="text/javascript" src="mw_sales_master_plan/static/libs/exporting.js"></script>');
   			$("head").append('<script type="text/javascript" src="mw_sales_master_plan/static/libs/export-data.js"></script>');
   			$("head").append('<script type="text/javascript" src="mw_sales_master_plan/static/libs/highcharts-more.js"></script>');
   			
			this._super.apply(this, arguments);
			var self = this;

			this.set({
				year: false,
				month: false,
			});

			this.field_manager.on("field_changed:year", this, function() {
                this.set({"year": this.field_manager.get_field_value("year")});
            });
   		    this.field_manager.on("field_changed:month", this, function() {
                this.set({"month": this.field_manager.get_field_value("month")});
            });
            this.field_manager.on("field_changed:categ_id", this, function() {
                this.set({"categ_id": this.field_manager.get_field_value("categ_id")});
            });

			this.updating = false;
			this.defs = [];
			
			this.res_o2m_drop = new utils.DropMisordered();
			this.render_drop = new utils.DropMisordered();
			this.description_line = _t("/");
			
			// Original save function is overwritten in order to wait all running deferreds to be done before actually applying the save.
			this.view.original_save = _.bind(this.view.save, this.view);
			this.view.save = function(prepend_on_create){
				self.prepend_on_create = prepend_on_create;
				return $.when.apply($, self.defs).then(function(){
					return self.view.original_save(self.prepend_on_create);
				});
			};

		},

		initialize_field: function() {
			form_common.ReinitializeWidgetMixin.initialize_field.call(this);
			var self = this;
			self.on("change:year", self, self.initialize_content);
			self.on("change:month", self, self.initialize_content);
			self.on("change:categ_id", self, self.initialize_content);
		},
		initialize_content: function() {
			var self = this;
			this.destroy_content();
			var data_detail;

			return new Model("sales.plan.dashboard.01")
				.call("get_datas", [ 1, self.get('year'), self.get('month'), self.get('categ_id')])
					.then(function(detail){
						data_detail = detail;
				}).then(function(res){
					self.data_detail = data_detail;
	                self.display_data();
			});
		},
		destroy_content: function() {
			if (this.dfm) {
				this.dfm.destroy();
				this.dfm = undefined;
			}
		},

		display_data: function() {
			var self = this;
			self.$el.html(QWeb.render("mw_sales_master_plan.SALES_PLAN_DASHBOARD_01", {widget: self}));

			// DATA draw
			console.log("=========================disp", self.data_detail, self.get('year'));
			var datas = self.data_detail[0];

			// Company total
			if(datas['company_total_chart']){
        		var options = {
					chart: {
				        type: 'column'
				    },
				    title: {
				        text: 'Company total (All warehouses)'
				    },
				    xAxis: {
				        type: 'category',
				    },
				    yAxis: [{
				        min: 0,
				        title: {
				            text: 'Quantity',
				        }
				    }, 
				    {	
				    	gridLineWidth: 0,
				        title: {
				            text: 'Amount ($)',
				        },
				    },
				    { // Third yAxis
				        title: {
				            text: 'Performance %',
				        },
				        labels: {
				            format: '{value} %',
				        },
				        opposite: true,
				    }],
				    legend: {
				        shadow: false
				    },
				    tooltip: {
				        shared: true
				    },
				    plotOptions: {
				        column: {
				            grouping: false,
				            shadow: true,
				            borderWidth: 0
				        }
				    },
				    series: datas['company_total_chart'],
			    }
			    try{
	    			$('#company_total_chart').highcharts(options);
	    		}catch(err) {
		           console.log(err.message);
		        }
    		}
    		else {
				$('#company_total_chart').remove();
    		}

    		// Company PIE chart
    		if(datas['company_total_pie_chart']){
        		var options = {
        			chart: {
				        type: 'pie'
				    }, 
				    title: {
				        text: 'Total: '+numeral(datas['company_total_sale']).format('0,0')+' $',
				    },
				    plotOptions: {
				        series: {
				            dataLabels: {
				                enabled: true,
				                format: '{point.name}: <b>{point.percentage:.1f}%</b>',
				            }
				        }
				    },
				    tooltip: {
				        pointFormat: '{point.name}: {point.y:.1f} $',
				    },
				    series: datas['company_total_pie_chart'],
			    };
			    try{
	    			$('#company_total_pie_chart').highcharts(options);
	    		}catch(err) {
		           console.log(err.message);
		        }
    		}
    		else {
				$('#company_total_pie_chart').remove();
    		}

    		// PIE qty
    		if(datas['company_total_qty_pie_chart']){
        		var options = {
        			chart: {
				        type: 'pie'
				    }, 
				    title: {
				        text: 'Total: '+numeral(datas['company_total_sale_qty']).format('0,0')+' Qty',
				    },
				    plotOptions: {
				        series: {
				            dataLabels: {
				                enabled: true,
				                format: '{point.name}: <b>{point.percentage:.1f}%</b>',
				            }
				        }
				    },
				    tooltip: {
				        pointFormat: '{point.name}: {point.y:.1f} Qty',
				    },
				    series: datas['company_total_qty_pie_chart'],
			    };
			    try{
	    			$('#company_total_qty_pie_chart').highcharts(options);
	    		}catch(err) {
		           console.log(err.message);
		        }
    		}
    		else {
				$('#company_total_qty_pie_chart').remove();
    		}

    		// Company 12 months - $
        	if(datas['company_monthly_chart']){
        		var options = {
        			colors: ['#2b908f', '#90ee7e', '#f45b5b', '#7798BF', '#eeaaee',
      					     '#55BF3B', '#DF5353', '#7798BF', '#aaeeee'],
			        title: {
				        text: 'Company sales 12 months (Amount)'
				    },
				    xAxis: {
				        type: 'category',
				        labels: {
				            format: '{value} month',
				        },
				    },
				    tooltip: {
				        shared: true
				    },
				    yAxis: [
				    	{ // Primary yAxis
					        labels: {
					            format: '{value} $',
					        },
					        title: {
					            text: 'Amount',
					        },
					        opposite: true
					    },
					    { // Secondary yAxis
					        gridLineWidth: 0,
					        title: {
					            text: 'Performance %',
					        },
					        labels: {
					            format: '{value} %',
					        }
					    },
				    ],
				    series: datas['company_monthly_chart'],
			    };
			    try{
	    			$('#company_monthly_chart').highcharts(options);
	    		}catch(err) {
		           console.log(err.message);
		        }
    		}
    		// Company 12 months - Qty
        	if(datas['company_monthly_qty_chart']){
        		var options = {
        			colors: ['#2b908f', '#90ee7e', '#f45b5b', '#7798BF', '#aaeeee', '#ff0066', '#eeaaee',
      					     '#55BF3B', '#DF5353', '#7798BF', '#aaeeee'],
			        title: {
				        text: 'Company sales 12 months (Qty)'
				    },
				    xAxis: {
				        type: 'category',
				        labels: {
				            format: '{value} month',
				        },
				    },
				    tooltip: {
				        shared: true
				    },
				    yAxis: [
				    	{ // Primary yAxis
					        labels: {
					            format: '{value} Qty',
					        },
					        title: {
					            text: 'Quantity',
					        },
					        opposite: true
					    },
					    { // Secondary yAxis
					        gridLineWidth: 0,
					        title: {
					            text: 'Performance %',
					        },
					        labels: {
					            format: '{value} %',
					        }
					    },
				    ],
				    series: datas['company_monthly_qty_chart'],
			    };
			    try{
	    			$('#company_monthly_qty_chart').highcharts(options);
	    		}catch(err) {
		           console.log(err.message);
		        }
    		}

    		// Company donut - Amount
        	if(datas['amount_donut_chart']){
        		var options = {
        			colors: ['#110141','#710162','#a12a5e','#ed0345',
        					 '#ef6a32','#fbbf45','#aad962','#03c383',
        					 '#017351','#01545a','#26294a','#1a1334'],
        			chart: {
				        plotBackgroundColor: null,
				        plotBorderWidth: 0,
				        plotShadow: false
				    },
				    title: {
				        text: self.get('year')+'<br>Amount<br>performance',
				        align: 'center',
				        verticalAlign: 'middle',
				        y: 40
				    },
				    tooltip: {
				        pointFormat: '{series.name}: <b>{point.percentage:.1f}%</b>'
				    },
				    plotOptions: {
				        pie: {
				        	allowPointSelect: true,
				        	cursor: 'pointer',
				            dataLabels: {
				                enabled: true,
				                distance: -50,
				                style: {
				                    fontWeight: 'bold',
				                    color: 'white'
				                },
				                connectorColor: 'silver'
				            },
				            startAngle: -90,
				            endAngle: 90,
				            center: ['50%', '75%']
				        }
				    },
				    series: [{
				        type: 'pie',
				        name: 'Sales',
				        innerSize: '50%',
				        data: datas['amount_donut_chart'],
				    }]
			    };
			    try{
	    			$('#amount_donut_chart').highcharts(options);
	    		}catch(err) {
		           console.log(err.message);
		        }
    		}
    		else {
				$('#amount_donut_chart').remove();
    		}

    		// Company donut - Qty
        	if(datas['qty_donut_chart']){
        		var options = {
        			colors: ['#110141','#710162','#a12a5e','#ed0345',
        					 '#ef6a32','#fbbf45','#aad962','#03c383',
        					 '#017351','#01545a','#26294a','#1a1334'],
        			chart: {
				        plotBackgroundColor: null,
				        plotBorderWidth: 0,
				        plotShadow: false
				    },
				    title: {
				        text: self.get('year')+'<br>Quantity<br>performance',
				        align: 'center',
				        verticalAlign: 'middle',
				        y: 40
				    },
				    tooltip: {
				        pointFormat: '{series.name}: <b>{point.percentage:.1f}%</b>'
				    },
				    plotOptions: {
				        pie: {
				            dataLabels: {
				                enabled: true,
				                distance: -50,
				                style: {
				                    fontWeight: 'bold',
				                    color: 'white'
				                }
				            },
				            startAngle: -90,
				            endAngle: 90,
				            center: ['50%', '75%']
				        }
				    },
				    series: [{
				        type: 'pie',
				        name: 'Борлуулалт',
				        innerSize: '50%',
				        data: datas['qty_donut_chart'],
				    }]
			    };
			    try{
	    			$('#qty_donut_chart').highcharts(options);
	    		}catch(err) {
		           console.log(err.message);
		        }
    		}
    		else {
				$('#qty_donut_chart').remove();
    		}

		    // Performance - Amount
        	if(datas['amount_performance_chart']){
        		var options = {
        			colors:['#581845','#9D0C3F','#C70039','#FF5733','#FFC30F','#0099CC'],
			        title: {
				        text: 'Plan performance (amount)'
				    },
				    xAxis: {
				        type: 'category',
				    },
				    tooltip: {
				        shared: true
				    },
				    yAxis: [
				    	{ // Primary yAxis
					        labels: {
					            format: '{value} $',
					        },
					        title: {
					            text: 'Amount',
					        },
					        opposite: true
					    },
					    { // Secondary yAxis
					        gridLineWidth: 0,
					        title: {
					            text: 'Performance %',
					        },
					        labels: {
					            format: '{value} %',
					        }
					    },],
				    series: datas['amount_performance_chart'],
			    };
			    try{
	    			$('#amount_performance_chart').highcharts(options);
	    		}catch(err) {
		           console.log(err.message);
		        }
    		}
    		// 

    		// Performance - Qty
        	if(datas['qty_performance_chart']){
        		var options = {
        			colors:['#581845','#9D0C3F','#C70039','#FF5733','#FFC30F','#0099CC'],
			        title: {
				        text: 'Plan performance (quantity)'
				    },
				    xAxis: {
				        type: 'category',
				    },
				    tooltip: {
				        shared: true
				    },
				    yAxis: [
				    	{ // Primary yAxis
					        labels: {
					            format: '{value} Qty',
					        },
					        title: {
					            text: 'Quantity',
					        },
					        opposite: true
					    },
					    { // Secondary yAxis
					        gridLineWidth: 0,
					        title: {
					            text: 'Performance %',
					        },
					        labels: {
					            format: '{value} %',
					        }
					    },],
				    series: datas['qty_performance_chart'],
			    };
			    try{
	    			$('#qty_performance_chart').highcharts(options);
	    		}catch(err) {
		           console.log(err.message);
		        }
    		}
    		// 
		},
		// 	
	});
	core.form_custom_registry.add('mw_sales_master_plan_01', SALES_PLAN_DASHBOARD_01);

	// // Бялууны борлуулалт
	// var SALES_PLAN_DASHBOARD_02 = form_common.FormWidget.extend(form_common.ReinitializeWidgetMixin, {
	// 	template : "mw_sales_master_plan.SALES_PLAN_DASHBOARD_02",

	// 	init: function() {

	// 		// Шаардлагатай JS сангууд импорт хийх
 //            // Old version
 //        	$("head").append('<script type="text/javascript" src="mw_sales_master_plan/static/libs/drilldown.js"></script>');
 //   			$("head").append('<script type="text/javascript" src="mw_sales_master_plan/static/libs/exporting.js"></script>');
 //   			$("head").append('<script type="text/javascript" src="mw_sales_master_plan/static/libs/export-data.js"></script>');
   			
	// 		this._super.apply(this, arguments);
	// 		var self = this;

	// 		this.set({
	// 			year: false,
	// 			month: false,
	// 			inch_sizes: [],
	// 		});

	// 		this.field_manager.on("field_changed:year", this, function() {
 //                this.set({"year": this.field_manager.get_field_value("year")});
 //            });
 //   		    this.field_manager.on("field_changed:month", this, function() {
 //                this.set({"month": this.field_manager.get_field_value("month")});
 //            });
 //            this.field_manager.on("field_changed:inch_sizes", this, function() {
 //                this.set({"inch_sizes": this.field_manager.get_field_value("inch_sizes")});
 //            });
 //            this.field_manager.on("field_changed:type_names", this, function() {
 //                this.set({"type_names": this.field_manager.get_field_value("type_names")});
 //            });
 //            this.field_manager.on("field_changed:with_slice_cake", this, function() {
 //                this.set({"with_slice_cake": this.field_manager.get_field_value("with_slice_cake")});
 //            });

	// 		this.updating = false;
	// 		this.defs = [];
			
	// 		this.res_o2m_drop = new utils.DropMisordered();
	// 		this.render_drop = new utils.DropMisordered();
	// 		this.description_line = _t("/");
			
	// 		// Original save function is overwritten in order to wait all running deferreds to be done before actually applying the save.
	// 		this.view.original_save = _.bind(this.view.save, this.view);
	// 		this.view.save = function(prepend_on_create){
	// 			self.prepend_on_create = prepend_on_create;
	// 			return $.when.apply($, self.defs).then(function(){
	// 				return self.view.original_save(self.prepend_on_create);
	// 			});
	// 		};

	// 	},

	// 	initialize_field: function() {
	// 		form_common.ReinitializeWidgetMixin.initialize_field.call(this);
	// 		var self = this;
	// 		self.on("change:year", self, self.initialize_content);
	// 		self.on("change:month", self, self.initialize_content);
	// 		self.on("change:inch_sizes", self, self.initialize_content);
	// 		self.on("change:type_names", self, self.initialize_content);
	// 		self.on("change:with_slice_cake", self, self.initialize_content);
	// 	},
	// 	initialize_content: function() {
	// 		var self = this;
	// 		this.destroy_content();
	// 		var data_detail;

	// 		return new Model("sales.plan.dashboard.02")
	// 			.call("get_datas", [ 1, self.get('year'), self.get('month'), 
	// 						self.get('inch_sizes'),self.get('type_names'),self.get('with_slice_cake')])
	// 				.then(function(detail){
	// 					data_detail = detail;
	// 			}).then(function(res){
	// 				self.data_detail = data_detail;
	//                 self.display_data();
	// 		});
	// 	},
	// 	destroy_content: function() {
	// 		if (this.dfm) {
	// 			this.dfm.destroy();
	// 			this.dfm = undefined;
	// 		}
	// 	},

	// 	display_data: function() {
	// 		var self = this;
	// 		self.$el.html(QWeb.render("mw_sales_master_plan.SALES_PLAN_DASHBOARD_02", {widget: self}));

	// 		// DATA zurax
	// 		var datas = self.data_detail[0];
	// 		console.log('=========data===', datas);

	// 		// Компаний хэмжээний бялуу
	// 		// Брэнд Хаппи харьцуулалт
 //        	if(datas['brand_happy_inch_chart']){
 //        		var options = {
 //        			chart: {
	// 			        type: 'pie'
	// 			    },
	// 			    title: {
	// 			        text: 'Брэнд, Хаппи бялууны харьцаа'
	// 			    },
	// 			    subtitle: {
	// 			        text: 'Сарын нийт:'+numeral(datas['total_brand_happy']).format('0,0')+' ш',
	// 			    },
	// 			    yAxis: {
	// 			        title: {
	// 			            text: 'Дүн ₮',
	// 			        }
	// 			    },
	// 			    plotOptions: {
	// 			        pie: {
	// 			            shadow: false,
	// 			            center: ['40%', '40%']
	// 			        }
	// 			    },
	// 			    tooltip: {
	// 			        pointFormat: '{series.name}: <b>{point.percentage:.1f}%</b>',
	// 			    },
	// 			    series: [{
	// 			        name: 'Төрөл',
	// 			        data: datas['brand_happy_inch_chart'],
	// 			        size: '40%',
	// 			        dataLabels: {
	// 			            formatter: function () {
	// 			                return this.y > 5 ? this.point.name : null;
	// 			            },
	// 			            color: '#ffffff',
	// 			            distance: -30
	// 			        }
	// 			    }, {
	// 			        name: 'Хэмжээ',
	// 			        data: datas['brand_happy_drill_chart'],
	// 			        size: '80%',
	// 			        innerSize: '60%',
	// 			        dataLabels: {
	// 			            formatter: function () {
	// 			                // display only if larger than 1
	// 			                return this.y > 1 ? '<b>' + this.point.name + ':</b> ' +
	// 			                    this.y + 'ш' : null;
	// 			            }
	// 			        },
	// 			        id: 'versions'
	// 			    }],
	// 			    responsive: {
	// 			        rules: [{
	// 			            condition: {
	// 			                maxWidth: 400
	// 			            },
	// 			            chartOptions: {
	// 			                series: [{
	// 			                    id: 'versions',
	// 			                    dataLabels: {
	// 			                        enabled: false
	// 			                    }
	// 			                }]
	// 			            }
	// 			        }]
	// 			    }
	// 			};
	// 		    // 
	// 		    try{
	//     			$('#brand_happy_inch_chart').highcharts(options);
	//     		}catch(err) {
	// 	           console.log(err.message);
	// 	        }
 //    		}
 //    		else{
 //    			$('#brand_happy_inch_chart').remove();
 //    		}

 //    		// Брэнд инч харьцуулалт
 //        	if(datas['brand_pie_chart']){
 //        		var options = {
 //        			chart: {
	// 			        plotBackgroundColor: null,
	// 			        plotBorderWidth: null,
	// 			        plotShadow: false,
	// 			        type: 'pie'
	// 			    },
	// 			    title: {
	// 			        text: 'Брэнд бялууны борлуулалт инчээр'
	// 			    },
	// 			    subtitle: {
	// 			        text: 'Сарын нийт:'+numeral(datas['total_brand_amount']).format('0,0')+' ш',
	// 			    },
	// 			    tooltip: {
	// 			        pointFormat: '{series.name}: <b>{point.percentage:.1f}%</b>'
	// 			    },
	// 			    plotOptions: {
	// 			        pie: {
	// 			            allowPointSelect: true,
	// 			            cursor: 'pointer',
	// 			            dataLabels: {
	// 		                    enabled: false
	// 		                },
	// 			            showInLegend: true,
	// 			        }
	// 			    },
	// 			    series: datas['brand_pie_chart'],
	// 			};
	// 		    // 
	// 		    try{
	//     			$('#brand_pie_chart').highcharts(options);
	//     		}catch(err) {
	// 	           console.log(err.message);
	// 	        }
 //    		}
 //    		else{
 //    			$('#brand_pie_chart').remove();
 //    		}

 //    		// Happy инч харьцуулалт
 //        	if(datas['happy_pie_chart']){
 //        		var options = {
 //        			colors:['#9D0C3F','#C70039','#FF5733','#FFC30F','#0099CC'],
 //        			chart: {
	// 			        plotBackgroundColor: null,
	// 			        plotBorderWidth: null,
	// 			        plotShadow: false,
	// 			        type: 'pie'
	// 			    },
	// 			    title: {
	// 			        text: 'Happy бялууны борлуулалт инчээр'
	// 			    },
	// 			    subtitle: {
	// 			        text: 'Сарын нийт:'+numeral(datas['total_happy_amount']).format('0,0')+' ш',
	// 			    },
	// 			    tooltip: {
	// 			        pointFormat: '{series.name}: <b>{point.percentage:.1f}%</b>'
	// 			    },
	// 			    plotOptions: {
	// 			        pie: {
	// 			            allowPointSelect: true,
	// 			            cursor: 'pointer',
	// 			            dataLabels: {
	// 		                    enabled: false
	// 		                },
	// 			            showInLegend: true,
	// 			        }
	// 			    },
	// 			    series: datas['happy_pie_chart'],
	// 			};
	// 		    // 
	// 		    try{
	//     			$('#happy_pie_chart').highcharts(options);
	//     		}catch(err) {
	// 	           console.log(err.message);
	// 	        }
 //    		}
 //    		else{
 //    			$('#happy_pie_chart').remove();
 //    		}

 //    		// Комппаний нийт
 //    		if(datas['cake_total_chart']){
 //        		var options = {
	// 				chart: {
	// 			        type: 'column',
	// 			    },
	// 			    title: {
	// 			        text: 'Компаний борлуулалт'
	// 			    },
	// 			    xAxis: {
	// 			        type: 'category',
	// 			    },
	// 			    yAxis: [{
	// 			        min: 0,
	// 			        title: {
	// 			            text: 'Тоо хэмжээ (ш)',
	// 			        }
	// 			    }, 
	// 			    {	
	// 			    	gridLineWidth: 0,
	// 			        title: {
	// 			            text: 'Дүн (₮)',
	// 			        },
	// 			    },
	// 			    { // Third yAxis
	// 			        title: {
	// 			            text: 'Гүйцэтгэл %',
	// 			        },
	// 			        labels: {
	// 			            format: '{value} %',
	// 			        },
	// 			        opposite: true,
	// 			    }],
	// 			    legend: {
	// 			        shadow: false
	// 			    },
	// 			    tooltip: {
	// 			        shared: true
	// 			    },
	// 			    plotOptions: {
	// 			        column: {
	// 			            grouping: false,
	// 			            shadow: true,
	// 			            borderWidth: 0
	// 			        }
	// 			    },
	// 			    series: datas['cake_total_chart'],
	// 			    drilldown: datas['cake_total_chart_drill'],
	// 		    }
	// 		    try{
	//     			$('#cake_total_chart').highcharts(options);
	//     		}catch(err) {
	// 	           console.log(err.message);
	// 	        }
 //    		}
 //    		else {
	// 			$('#cake_total_chart').remove();
 //    		}

 //    		// 
	// 	    // Төлөвлөгөө гүйцэтгэлийн чарт - Бялуу инчээр
 //        	if(datas['cake_amount_performance_chart']){
 //        		var options = {
 //        			colors: ['#004D47', '#128277', '#52958B',
 //      						 '#55BF3B', '#DF5353', '#7798BF', '#aaeeee'],
	// 			    chart: {
	// 			        type: 'column'
	// 			    },
	// 			    title: {
	// 			        text: 'Бүтээгдэхүүн /Дүнгээр/'
	// 			    },
	// 			    xAxis: {
	// 			        type: 'category'
	// 			    },
	// 			    tooltip: {
	// 			        shared: true
	// 			    },
	// 			    yAxis: [
	// 			    	{ 
	// 				        title: {
	// 				            text: 'Мөнгөн дүн ₮',
	// 				        },
	// 				    },
	// 				    { 
	// 				        title: {
	// 				            text: 'Гүйцэтгэлийн %',
	// 				        },
	// 				        opposite: true,
	// 				    },
	// 			    ],
	// 			    plotOptions: {
	// 			        series: {
	// 			            borderWidth: 0,
	// 			            dataLabels: {
	// 			                enabled: true
	// 			            }
	// 			        }
	// 			    },
	// 			    series: datas['cake_amount_performance_chart'],
	// 			    drilldown: datas['cake_amount_drilldown'],
	// 			};
	// 		    // 
	// 		    try{
	//     			$('#cake_amount_performance_chart').highcharts(options);
	//     		}catch(err) {
	// 	           console.log(err.message);
	// 	        }
 //    		}
 //    		else{
 //    			$('#cake_amount_performance_chart').remove();
 //    		}

 //    		// Тоо хэмжээгээр
 //    		if(datas['cake_qty_performance_chart']){
 //        		var options = {
 //        			colors: ['#004D47', '#128277', '#52958B',
 //      						 '#55BF3B', '#DF5353', '#7798BF', '#aaeeee'],
	// 			    chart: {
	// 			        type: 'column'
	// 			    },
	// 			    title: {
	// 			        text: 'Бүтээгдэхүүн /Тоо хэмжээгээр/'
	// 			    },
	// 			    xAxis: {
	// 			        type: 'category'
	// 			    },
	// 			    tooltip: {
	// 			        shared: true
	// 			    },
	// 			    yAxis: [
	// 			    	{ 
	// 				        title: {
	// 				            text: 'Тоо хэмжээ Ш',
	// 				        },
	// 				    },
	// 				    { 
	// 				        title: {
	// 				            text: 'Гүйцэтгэлийн %',
	// 				        },
	// 				        opposite: true,
	// 				    },
	// 			    ],
	// 			    plotOptions: {
	// 			        series: {
	// 			            borderWidth: 0,
	// 			            dataLabels: {
	// 			                enabled: true
	// 			            }
	// 			        }
	// 			    },
	// 			    series: datas['cake_qty_performance_chart'],
	// 			    drilldown: datas['cake_qty_drilldown'],
	// 			};
	// 		    // 
	// 		    try{
	//     			$('#cake_qty_performance_chart').highcharts(options);
	//     		}catch(err) {
	// 	           console.log(err.message);
	// 	        }
 //    		}
 //    		else{
 //    			$('#cake_qty_performance_chart').remove();
 //    		}

 //    		// 
	// 	},
	// 	// 	
	// });
	// core.form_custom_registry.add('mw_sales_master_plan_02', SALES_PLAN_DASHBOARD_02);

	// // Бялууны өдрийн борлуулалт
	// var SALES_PLAN_DASHBOARD_0202 = form_common.FormWidget.extend(form_common.ReinitializeWidgetMixin, {
	// 	template : "mw_sales_master_plan.SALES_PLAN_DASHBOARD_0202",

	// 	init: function() {

	// 		// Шаардлагатай JS сангууд импорт хийх
 //            // Old version
 //        	$("head").append('<script type="text/javascript" src="mw_sales_master_plan/static/libs/drilldown.js"></script>');
 //   			$("head").append('<script type="text/javascript" src="mw_sales_master_plan/static/libs/exporting.js"></script>');
 //   			$("head").append('<script type="text/javascript" src="mw_sales_master_plan/static/libs/export-data.js"></script>');
   			
	// 		this._super.apply(this, arguments);
	// 		var self = this;

	// 		this.set({
	// 			warehouse_id: false,
	// 			date_start: false,
	// 			date_end: false,
	// 		});

	// 		this.field_manager.on("field_changed:warehouse_id", this, function() {
 //                this.set({"warehouse_id": this.field_manager.get_field_value("warehouse_id")});
 //            });
 //   		    this.field_manager.on("field_changed:date_start", this, function() {
 //                this.set({"date_start": this.field_manager.get_field_value("date_start")});
 //            });
 //            this.field_manager.on("field_changed:date_end", this, function() {
 //                this.set({"date_end": this.field_manager.get_field_value("date_end")});
 //            });
 //            this.field_manager.on("field_changed:inch_sizes", this, function() {
 //                this.set({"inch_sizes": this.field_manager.get_field_value("inch_sizes")});
 //            });
 //            this.field_manager.on("field_changed:type_names", this, function() {
 //                this.set({"type_names": this.field_manager.get_field_value("type_names")});
 //            });
 //            this.field_manager.on("field_changed:with_slice_cake", this, function() {
 //                this.set({"with_slice_cake": this.field_manager.get_field_value("with_slice_cake")});
 //            });

	// 		this.updating = false;
	// 		this.defs = [];
			
	// 		this.res_o2m_drop = new utils.DropMisordered();
	// 		this.render_drop = new utils.DropMisordered();
	// 		this.description_line = _t("/");
			
	// 		// Original save function is overwritten in order to wait all running deferreds to be done before actually applying the save.
	// 		this.view.original_save = _.bind(this.view.save, this.view);
	// 		this.view.save = function(prepend_on_create){
	// 			self.prepend_on_create = prepend_on_create;
	// 			return $.when.apply($, self.defs).then(function(){
	// 				return self.view.original_save(self.prepend_on_create);
	// 			});
	// 		};

	// 	},

	// 	initialize_field: function() {
	// 		form_common.ReinitializeWidgetMixin.initialize_field.call(this);
	// 		var self = this;
	// 		self.on("change:warehouse_id", self, self.initialize_content);
	// 		self.on("change:date_start", self, self.initialize_content);
	// 		self.on("change:date_end", self, self.initialize_content);
	// 		self.on("change:inch_sizes", self, self.initialize_content);
	// 		self.on("change:type_names", self, self.initialize_content);
	// 		self.on("change:with_slice_cake", self, self.initialize_content);
	// 	},
	// 	initialize_content: function() {
	// 		var self = this;
	// 		this.destroy_content();
	// 		var data_detail;

	// 		return new Model("sales.plan.dashboard.02")
	// 			.call("get_datas_days", [ 1, self.get('warehouse_id'), self.get('date_start'), self.get('date_end'), 
	// 						self.get('inch_sizes'),self.get('type_names'),self.get('with_slice_cake')])
	// 				.then(function(detail){
	// 					data_detail = detail;
	// 			}).then(function(res){
	// 				self.data_detail = data_detail;
	//                 self.display_data();
	// 		});
	// 	},
	// 	destroy_content: function() {
	// 		if (this.dfm) {
	// 			this.dfm.destroy();
	// 			this.dfm = undefined;
	// 		}
	// 	},

	// 	display_data: function() {
	// 		var self = this;
	// 		self.$el.html(QWeb.render("mw_sales_master_plan.SALES_PLAN_DASHBOARD_0202", {widget: self}));

	// 		// DATA zurax
	// 		var datas = self.data_detail[0];
	// 		console.log('======ss===data===', datas);

	// 		// AMOUNT
 //        	if(datas['cake_days_amount_chart']){
 //        		var options = {
 //        			// colors: ['#2c4a52', '#537072','#8e9b97', '#f4ebdb'],
 //        			colors: ['#46211a', '#693d3d','#ba5536', '#a43820'],
	// 			    chart: {
	// 			        type: 'column'
	// 			    },
	// 			    title: {
	// 			        text: datas['title']+' /Дүнгээр/'
	// 			    },
	// 			    subtitle: {
	// 			        text: 'Нийт, Брэнд: '+numeral(datas['total_brand_amount']).format('0,0') + ', Happy: '+ numeral(datas['total_happy_amount']).format('0,0'),
	// 			    },
	// 			    xAxis: {
	// 			        type: 'category'
	// 			    },
	// 			    tooltip: {
	// 			        shared: true
	// 			    },
	// 			    yAxis: [
	// 			    	{ 
	// 				        title: {
	// 				            text: 'Мөнгөн дүн ₮',
	// 				        },
	// 				    },
	// 				    // { 
	// 				    //     title: {
	// 				    //         text: 'Гүйцэтгэлийн %',
	// 				    //     },
	// 				    //     opposite: true,
	// 				    // },
	// 			    ],
	// 			    series: datas['cake_days_amount_chart'],
	// 			    drilldown: datas['cake_days_amount_drill'],
	// 			};
	// 		    // 
	// 		    try{
	//     			$('#cake_days_amount_chart').highcharts(options);
	//     		}catch(err) {
	// 	           console.log(err.message);
	// 	        }
 //    		}
 //    		else{
 //    			$('#cake_days_amount_chart').remove();
 //    		}

 //    		// QTY
 //    		// AMOUNT
 //        	if(datas['cake_days_qty_chart']){
 //        		var options = {
 //        			colors: ['#46211a', '#693d3d','#ba5536', '#a43820'],
	// 			    chart: {
	// 			        type: 'column'
	// 			    },
	// 			    title: {
	// 			        text: datas['title']+' /Ширхэг/'
	// 			    },  			
	// 			    subtitle: {
	// 			        text: 'Нийт, Брэнд: '+numeral(datas['total_brand_qty']).format('0,0') + ' Happy: '+ numeral(datas['total_happy_qty']).format('0,0'),
	// 			    },
	// 			    xAxis: {
	// 			        type: 'category'
	// 			    },
	// 			    tooltip: {
	// 			        shared: true
	// 			    },
	// 			    yAxis: [
	// 			    	{ 
	// 				        title: {
	// 				            text: 'Тоо хэмжээ Ш',
	// 				        },
	// 				    },
	// 				    // { 
	// 				    //     title: {
	// 				    //         text: 'Гүйцэтгэлийн %',
	// 				    //     },
	// 				    //     opposite: true,
	// 				    // },
	// 			    ],
	// 			    series: datas['cake_days_qty_chart'],
	// 			    drilldown: datas['cake_days_qty_drill'],
	// 			};
	// 		    // 
	// 		    try{
	//     			$('#cake_days_qty_chart').highcharts(options);
	//     		}catch(err) {
	// 	           console.log(err.message);
	// 	        }
 //    		}
 //    		else{
 //    			$('#cake_days_qty_chart').remove();
 //    		}

 //    		// 
	// 	},
	// 	// 	
	// });
	// core.form_custom_registry.add('mw_sales_master_plan_0202', SALES_PLAN_DASHBOARD_0202);

	// // Бүтээгдэхүүн ангилалаар
	// var SALES_PLAN_DASHBOARD_03 = form_common.FormWidget.extend(form_common.ReinitializeWidgetMixin, {
	// 	template : "mw_sales_master_plan.SALES_PLAN_DASHBOARD_03",

	// 	init: function() {

	// 		// Шаардлагатай JS сангууд импорт хийх
 //        	$("head").append('<script type="text/javascript" src="mw_sales_master_plan/static/libs/drilldown.js"></script>');
 //   			$("head").append('<script type="text/javascript" src="mw_sales_master_plan/static/libs/exporting.js"></script>');
 //   			$("head").append('<script type="text/javascript" src="mw_sales_master_plan/static/libs/export-data.js"></script>');
   			
	// 		this._super.apply(this, arguments);
	// 		var self = this;

	// 		this.field_manager.on("field_changed:year", this, function() {
 //                this.set({"year": this.field_manager.get_field_value("year")});
 //            });
 //   		    this.field_manager.on("field_changed:month", this, function() {
 //                this.set({"month": this.field_manager.get_field_value("month")});
 //            });
 //            this.field_manager.on("field_changed:categ_id", this, function() {
 //                this.set({"categ_id": this.field_manager.get_field_value("categ_id")});
 //            });
 //            this.field_manager.on("field_changed:warehouse_id", this, function() {
 //                this.set({"warehouse_id": this.field_manager.get_field_value("warehouse_id")});
 //            });

	// 		this.updating = false;
	// 		this.defs = [];
			
	// 		this.res_o2m_drop = new utils.DropMisordered();
	// 		this.render_drop = new utils.DropMisordered();
	// 		this.description_line = _t("/");
			
	// 		// Original save function is overwritten in order to wait all running deferreds to be done before actually applying the save.
	// 		this.view.original_save = _.bind(this.view.save, this.view);
	// 		this.view.save = function(prepend_on_create){
	// 			self.prepend_on_create = prepend_on_create;
	// 			return $.when.apply($, self.defs).then(function(){
	// 				return self.view.original_save(self.prepend_on_create);
	// 			});
	// 		};

	// 	},

	// 	initialize_field: function() {
	// 		form_common.ReinitializeWidgetMixin.initialize_field.call(this);
	// 		var self = this;
	// 		self.on("change:year", self, self.initialize_content);
	// 		self.on("change:month", self, self.initialize_content);
	// 		self.on("change:categ_id", self, self.initialize_content);
	// 		self.on("change:warehouse_id", self, self.initialize_content);
	// 	},
	// 	initialize_content: function() {
	// 		var self = this;
	// 		this.destroy_content();
	// 		var data_detail;

	// 		return new Model("sales.plan.dashboard.03")
	// 			.call("get_datas", [ 1, self.get('year'), self.get('month'), self.get('categ_id'), self.get('warehouse_id')])
	// 				.then(function(detail){
	// 					data_detail = detail;
	// 			}).then(function(res){
	// 				self.data_detail = data_detail;
	//                 self.display_data();
	// 		});
	// 	},
	// 	destroy_content: function() {
	// 		if (this.dfm) {
	// 			this.dfm.destroy();
	// 			this.dfm = undefined;
	// 		}
	// 	},

	// 	display_data: function() {
	// 		var self = this;
	// 		self.$el.html(QWeb.render("mw_sales_master_plan.SALES_PLAN_DASHBOARD_03", {widget: self}));

	// 		// DATA zurax
	// 		var datas = self.data_detail[0];
	// 		console.log("=========================disp", datas);

	// 		// Компаны кат
 //        	if(datas['company_category_chart']){
 //        		var options =  {
 //        			colors: ['#2b908f', '#90ee7e', '#f45b5b', '#7798BF', '#eeaaee',
 //      					     '#55BF3B', '#DF5353', '#7798BF', '#aaeeee'],
	// 			    chart: {
	// 			        type: 'column'
	// 			    },
	// 			    title: {
	// 			        text: 'Компаны борлуулалт ('+datas['category_name']+')',
	// 			    },
	// 			    xAxis: [{
	// 			        type: 'category'
	// 			    }],
	// 			    yAxis: [{ // Primary yAxis
	// 			        labels: {
	// 			            format: '{value} ₮',
	// 			            style: {
	// 			                color: Highcharts.getOptions().colors[1]
	// 			            }
	// 			        },
	// 			        title: {
	// 			            text: 'Мөнгөн дүн',
	// 			            style: {
	// 			                color: Highcharts.getOptions().colors[1]
	// 			            }
	// 			        }
	// 			    }, { // Secondary yAxis
	// 			        title: {
	// 			            text: 'Гүйцэтгэл %',
	// 			            style: {
	// 			                color: Highcharts.getOptions().colors[0]
	// 			            }
	// 			        },
	// 			        labels: {
	// 			            format: '{value} %',
	// 			            style: {
	// 			                color: Highcharts.getOptions().colors[0]
	// 			            }
	// 			        },
	// 			        opposite: true
	// 			    }],
	// 			    tooltip: {
	// 			        shared: true
	// 			    },
	// 			    series: datas['company_category_chart'],
	// 			};
	// 		    try{
	//     			$('#company_category_chart').highcharts(options);
	//     		}catch(err) {
	// 	           console.log(err.message);
	// 	        }
 //    		}
 //    		else {
 //    			$('#company_category_chart').remove();
 //    		}

	// 	    // Төлөвлөгөө гүйцэтгэлийн чарт
 //        	if(datas['product_chart']){
 //        		var options =  {
 //        			colors: ['#7798BF', '#ff0066',
 //      						 '#55BF3B', '#DF5353', '#7798BF', '#aaeeee'],
	// 			    chart: {
	// 			        type: 'column'
	// 			    },
	// 			    title: {
	// 			        text: 'Борлуулалт ангилалаар ('+datas['category_name']+')',
	// 			    },
	// 			    xAxis: [{
	// 			        type: 'category'
	// 			    }],
	// 			    yAxis: [{ // Primary yAxis
	// 			        labels: {
	// 			            format: '{value} ₮',
	// 			            style: {
	// 			                color: Highcharts.getOptions().colors[1]
	// 			            }
	// 			        },
	// 			        title: {
	// 			            text: 'Мөнгөн дүн',
	// 			            style: {
	// 			                color: Highcharts.getOptions().colors[1]
	// 			            }
	// 			        }
	// 			    }, { // Secondary yAxis
	// 			        title: {
	// 			            text: 'Гүйцэтгэл %',
	// 			            style: {
	// 			                color: Highcharts.getOptions().colors[0]
	// 			            }
	// 			        },
	// 			        labels: {
	// 			            format: '{value} %',
	// 			            style: {
	// 			                color: Highcharts.getOptions().colors[0]
	// 			            }
	// 			        },
	// 			        opposite: true
	// 			    }],
	// 			    tooltip: {
	// 			        shared: true
	// 			    },
	// 			    series: datas['product_chart'],
	// 			};
	// 		    try{
	//     			$('#product_chart').highcharts(options);
	//     		}catch(err) {
	// 	           console.log(err.message);
	// 	        }
 //    		}
 //    		else {
 //    			$('#product_chart').remove();
 //    		}
 //    		//
 //    		// Сонгосон ангилалыг бараагаар задалж харуулах чарт
 //        	if(datas['product_by_categ_chart']){
 //        		var options =  {
	// 			    chart: {
	// 			        zoomType: 'xy'
	// 			    },
	// 			    title: {
	// 			        text: datas['warehouse_name']+' - Бүтээгдэхүүнээр'
	// 			    },
	// 			    subtitle: {
	// 			        text: 'Нийт: '+datas['total_product_amount']+' ₮, Өмнөх нийт: '+datas['before_total_product_amount']+' ₮',
	// 			    },
	// 			    xAxis: [{
	// 			        type: 'category',
	// 			        crosshair: true
	// 			    }],
	// 			    yAxis: [{ // Primary yAxis
	// 			        labels: {
	// 			            format: '{value} ₮',
	// 			            style: {
	// 			                color: Highcharts.getOptions().colors[1]
	// 			            }
	// 			        },
	// 			        title: {
	// 			            text: 'Мөнгөн дүн',
	// 			            style: {
	// 			                color: Highcharts.getOptions().colors[1]
	// 			            }
	// 			        }
	// 			    }, { // Secondary yAxis
	// 			        title: {
	// 			            text: 'Мөнгөн дүн',
	// 			            style: {
	// 			                color: Highcharts.getOptions().colors[0]
	// 			            }
	// 			        },
	// 			        labels: {
	// 			            format: '{value} ₮',
	// 			            style: {
	// 			                color: Highcharts.getOptions().colors[0]
	// 			            }
	// 			        },
	// 			        opposite: true
	// 			    }],
	// 			    tooltip: {
	// 			        shared: true
	// 			    },
	// 			    legend: {
	// 			        layout: 'vertical',
	// 			        align: 'left',
	// 			        x: 120,
	// 			        verticalAlign: 'top',
	// 			        y: 100,
	// 			        floating: true,
	// 			        backgroundColor: (Highcharts.theme && Highcharts.theme.legendBackgroundColor) || '#FFFFFF'
	// 			    },
	// 			    series: datas['product_by_categ_chart'],
	// 			};
	// 		    try{
	//     			$('#product_by_categ_chart').highcharts(options);
	//     		}catch(err) {
	// 	           console.log(err.message);
	// 	        }
 //    		}
 //    		else {
 //    			$('#product_by_categ_chart').remove();
 //    		}
 //    		// 
	// 	},
	// 	// 	
	// });
	// core.form_custom_registry.add('mw_sales_master_plan_03', SALES_PLAN_DASHBOARD_03);

	// // Бүтээгдэхүүн задаргаа
	// var SALES_PLAN_DASHBOARD_0302 = form_common.FormWidget.extend(form_common.ReinitializeWidgetMixin, {
	// 	template : "mw_sales_master_plan.SALES_PLAN_DASHBOARD_0302",

	// 	init: function() {

	// 		// Шаардлагатай JS сангууд импорт хийх
 //        	$("head").append('<script type="text/javascript" src="mw_sales_master_plan/static/libs/drilldown.js"></script>');
 //   			$("head").append('<script type="text/javascript" src="mw_sales_master_plan/static/libs/exporting.js"></script>');
 //   			$("head").append('<script type="text/javascript" src="mw_sales_master_plan/static/libs/export-data.js"></script>');
   			
	// 		this._super.apply(this, arguments);
	// 		var self = this;

	// 		this.field_manager.on("field_changed:year", this, function() {
 //                this.set({"year": this.field_manager.get_field_value("year")});
 //            });
 //   		    this.field_manager.on("field_changed:month", this, function() {
 //                this.set({"month": this.field_manager.get_field_value("month")});
 //            });
 //            this.field_manager.on("field_changed:warehouse_id2", this, function() {
 //                this.set({"warehouse_id2": this.field_manager.get_field_value("warehouse_id2")});
 //            });
 //            this.field_manager.on("field_changed:day_date", this, function() {
 //                this.set({"day_date": this.field_manager.get_field_value("day_date")});
 //            });
 //            this.field_manager.on("field_changed:product_id", this, function() {
 //                this.set({"product_id": this.field_manager.get_field_value("product_id")});
 //            });

	// 		this.updating = false;
	// 		this.defs = [];
			
	// 		this.res_o2m_drop = new utils.DropMisordered();
	// 		this.render_drop = new utils.DropMisordered();
	// 		this.description_line = _t("/");
			
	// 		// Original save function is overwritten in order to wait all running deferreds to be done before actually applying the save.
	// 		this.view.original_save = _.bind(this.view.save, this.view);
	// 		this.view.save = function(prepend_on_create){
	// 			self.prepend_on_create = prepend_on_create;
	// 			return $.when.apply($, self.defs).then(function(){
	// 				return self.view.original_save(self.prepend_on_create);
	// 			});
	// 		};

	// 	},

	// 	initialize_field: function() {
	// 		form_common.ReinitializeWidgetMixin.initialize_field.call(this);
	// 		var self = this;
	// 		self.on("change:year", self, self.initialize_content);
	// 		self.on("change:month", self, self.initialize_content);
	// 		self.on("change:product_id", self, self.initialize_content);
	// 		self.on("change:warehouse_id2", self, self.initialize_content);
	// 		self.on("change:day_date", self, self.initialize_content);
	// 	},
	// 	initialize_content: function() {
	// 		var self = this;
	// 		this.destroy_content();
	// 		var data_detail;

	// 		return new Model("sales.plan.dashboard.03")
	// 			.call("get_datas_detailed", [ 1, self.get('year'), self.get('month'), self.get('product_id'), self.get('day_date'), self.get('warehouse_id2')])
	// 				.then(function(detail){
	// 					data_detail = detail;
	// 			}).then(function(res){
	// 				self.data_detail = data_detail;
	//                 self.display_data();
	// 		});
	// 	},
	// 	destroy_content: function() {
	// 		if (this.dfm) {
	// 			this.dfm.destroy();
	// 			this.dfm = undefined;
	// 		}
	// 	},

	// 	display_data: function() {
	// 		var self = this;
	// 		self.$el.html(QWeb.render("mw_sales_master_plan.SALES_PLAN_DASHBOARD_0302", {widget: self}));

	// 		// DATA zurax
	// 		var datas = self.data_detail[0];

	// 		// Бүтээгдэхүүн сараар - Тоогоор
 //        	if(datas['product_monthly_chart']){
 //        		var options = {
 //        			colors: ['#2b908f', '#90ee7e', '#f45b5b', '#7798BF', '#eeaaee',
 //      					     '#55BF3B', '#DF5353', '#7798BF', '#aaeeee'],
	// 		        title: {
	// 			        text: 'Бүтээгдэхүүн 12 сараар(ш)'
	// 			    },
	// 			    xAxis: {
	// 			        type: 'category',
	// 			        labels: {
	// 			            format: '{value} сар',
	// 			        },
	// 			    },
	// 			    tooltip: {
	// 			        shared: true
	// 			    },
	// 			    yAxis: [
	// 			    	{ // Primary yAxis
	// 				        labels: {
	// 				            format: '{value} ш',
	// 				            style: {
	// 				                color: Highcharts.getOptions().colors[2]
	// 				            }
	// 				        },
	// 				        title: {
	// 				            text: 'Тоо хэмжээ',
	// 				            style: {
	// 				                color: Highcharts.getOptions().colors[2]
	// 				            }
	// 				        },
	// 				        opposite: true
	// 				    },
	// 				    // { // Secondary yAxis
	// 				    //     gridLineWidth: 0,
	// 				    //     title: {
	// 				    //         text: 'Гүйцэтгэлийн хувь',
	// 				    //         style: {
	// 				    //             color: Highcharts.getOptions().colors[0]
	// 				    //         }
	// 				    //     },
	// 				    //     labels: {
	// 				    //         format: '{value} %',
	// 				    //         style: {
	// 				    //             color: Highcharts.getOptions().colors[0]
	// 				    //         }
	// 				    //     }
	// 				    // },
	// 			    ],
	// 			    series: datas['product_monthly_chart'],
	// 		    };
	// 		    try{
	//     			$('#product_monthly_chart').highcharts(options);
	//     		}catch(err) {
	// 	           console.log(err.message);
	// 	        }
 //    		}

 //    		// Сонгосон Бүтээгдэхүүнийг харуулах, өдрөөр задлах
 //    		if(datas['by_product_chart']){
 //        		var options = {
	// 			    chart: {
	// 			        type: 'column'
	// 			    },
	// 			    title: {
	// 			        text: datas['by_product_name']+' /Тоо хэмжээ/'
	// 			    },
	// 			    xAxis: {
	// 			        type: 'category'
	// 			    },
	// 			    yAxis: [
	// 			    	{ 
	// 				        title: {
	// 				            text: 'Тоо хэмжээ Ш',
	// 				        },
	// 				        labels: {
	// 				            format: '{value} ш',
	// 				            style: {
	// 				                color: Highcharts.getOptions().colors[1]
	// 				            }
	// 				        },
	// 				    },
	// 			    ],
	// 			    plotOptions: {
	// 			        series: {
	// 			            borderWidth: 0,
	// 			            dataLabels: {
	// 			                enabled: true,
	// 			                format: '{point.y:.1f}ш'
	// 			            }
	// 			        }
	// 			    },
	// 			    series: datas['by_product_chart'],
	// 			    drilldown: datas['by_product_drilldown_chart'],
	// 			};
	// 		    // 
	// 		    try{
	//     			$('#by_product_chart').highcharts(options);
	//     		}catch(err) {
	// 	           console.log(err.message);
	// 	        }
 //    		}
 //    		else {
	// 			$('#by_product_chart').remove();
 //    		}
 //    		// Сонгосон Бүтээгдэхүүнийг харуулах, цагаар задлах
 //    		if(datas['by_product_time_chart']){
 //        		var options = {
	// 			    chart: {
	// 			        type: 'spline'
	// 			    },
	// 			    title: {
	// 			        text: self.get('day_date')+'-ны өдрийн цагийн задаргаа',
	// 			    },
	// 			    subtitle: {
	// 		            text: 'Бүтээгдэхүүн: ' +datas['by_product_name'],
	// 		        },
	// 			    xAxis: {
	// 			        type: 'datetime',
	// 			        labels: {
	// 			            overflow: 'justify'
	// 			        }
	// 			    },
	// 			    yAxis: {
	// 			        title: {
	// 			            text: 'Тоо хэмжээ Ш'
	// 			        },
	// 			        minorGridLineWidth: 0,
	// 			        gridLineWidth: 0,
	// 			        alternateGridColor: null,
	// 			    },
	// 			    tooltip: {
	// 			        valueSuffix: ' ш'
	// 			    },
	// 			    plotOptions: {
	// 			        spline: {
	// 			            lineWidth: 3,
	// 			            states: {
	// 			                hover: {
	// 			                    lineWidth: 4
	// 			                }
	// 			            },
	// 			            marker: {
	// 			                enabled: false
	// 			            },
	// 			            pointInterval: 3600000, // one hour
	// 			            pointStart: Date.UTC(2017, 6, 20, 8, 0, 0)
	// 			        }
	// 			    },
	// 			    series: datas['by_product_time_chart'],
	// 			    navigation: {
	// 			        menuItemStyle: {
	// 			            fontSize: '10px'
	// 			        }
	// 			    }
	// 			};
	// 		    // 
	// 		    try{
	//     			$('#by_product_time_chart').highcharts(options);
	//     		}catch(err) {
	// 	           console.log(err.message);
	// 	        }
 //    		}
 //    		else {
	// 			$('#by_product_time_chart').remove();
 //    		}

	// 	},
	// 	// 	
	// });
	// core.form_custom_registry.add('mw_sales_master_plan_0302', SALES_PLAN_DASHBOARD_0302);

	// // Салбарын борлуулалт
	// var SALES_PLAN_DASHBOARD_04 = form_common.FormWidget.extend(form_common.ReinitializeWidgetMixin, {
	// 	template : "mw_sales_master_plan.SALES_PLAN_DASHBOARD_04",

	// 	init: function() {

	// 		// Шаардлагатай JS сангууд импорт хийх
	// 		$("head").append('<script type="text/javascript" src="mw_sales_master_plan/static/libs/boost.js"></script>');
 //   			$("head").append('<script type="text/javascript" src="mw_sales_master_plan/static/libs/boost-canvas.js"></script>');

 //        	$("head").append('<script type="text/javascript" src="mw_sales_master_plan/static/libs/drilldown.js"></script>');
 //   			$("head").append('<script type="text/javascript" src="mw_sales_master_plan/static/libs/exporting.js"></script>');
 //   			$("head").append('<script type="text/javascript" src="mw_sales_master_plan/static/libs/highcharts-more.js"></script>');
 //   			$("head").append('<script type="text/javascript" src="mw_sales_master_plan/static/libs/export-data.js"></script>');
   			
	// 		this._super.apply(this, arguments);
	// 		var self = this;

	// 		this.set({
	// 			year: false,
	// 			month: false,
	// 		});

	// 		this.field_manager.on("field_changed:year", this, function() {
 //                this.set({"year": this.field_manager.get_field_value("year")});
 //            });
 //   		    this.field_manager.on("field_changed:month", this, function() {
 //                this.set({"month": this.field_manager.get_field_value("month")});
 //            });

 //            this.field_manager.on("field_changed:warehouse_id", this, function() {
 //                this.set({"warehouse_id": this.field_manager.get_field_value("warehouse_id")});
 //            });

	// 		this.updating = false;
	// 		this.defs = [];
			
	// 		this.res_o2m_drop = new utils.DropMisordered();
	// 		this.render_drop = new utils.DropMisordered();
	// 		this.description_line = _t("/");
			
	// 		// Original save function is overwritten in order to wait all running deferreds to be done before actually applying the save.
	// 		this.view.original_save = _.bind(this.view.save, this.view);
	// 		this.view.save = function(prepend_on_create){
	// 			self.prepend_on_create = prepend_on_create;
	// 			return $.when.apply($, self.defs).then(function(){
	// 				return self.view.original_save(self.prepend_on_create);
	// 			});
	// 		};

	// 	},

	// 	initialize_field: function() {
	// 		form_common.ReinitializeWidgetMixin.initialize_field.call(this);
	// 		var self = this;
	// 		self.on("change:year", self, self.initialize_content);
	// 		self.on("change:month", self, self.initialize_content);
	// 		self.on("change:warehouse_id", self, self.initialize_content);
	// 	},
	// 	initialize_content: function() {
	// 		var self = this;
	// 		this.destroy_content();
	// 		var data_detail;

	// 		return new Model("sales.plan.dashboard.04")
	// 			.call("get_datas", [ 1, self.get('year'), self.get('month'), self.get('warehouse_id')])
	// 				.then(function(detail){
	// 					data_detail = detail;
	// 			}).then(function(res){
	// 				self.data_detail = data_detail;
	//                 self.display_data();
	// 		});
	// 	},
	// 	destroy_content: function() {
	// 		if (this.dfm) {
	// 			this.dfm.destroy();
	// 			this.dfm = undefined;
	// 		}
	// 	},

	// 	display_data: function() {
	// 		var self = this;
	// 		self.$el.html(QWeb.render("mw_sales_master_plan.SALES_PLAN_DASHBOARD_04", {widget: self}));

	// 		// DATA zurax
	// 		console.log("=========================disp", self.data_detail);
	// 		var datas = self.data_detail[0];

	// 		// Сонгосон салбарын тасгийн задаргаа
	// 		// Нийт борлуулалт
	// 		if(datas['branch_total_sales_chart']){
 //        		var options = {
	// 				chart: {
	// 			        type: 'column'
	// 			    },
	// 			    title: {
	// 			        text: 'Салбарын борлуулалт'
	// 			    },
	// 			    xAxis: {
	// 			        type: 'category',
	// 			    },
	// 			    yAxis: [{
	// 			        min: 0,
	// 			        title: {
	// 			            text: 'Тоо хэмжээ (ш)',
	// 			        }
	// 			    }, 
	// 			    {	
	// 			    	gridLineWidth: 0,
	// 			        title: {
	// 			            text: 'Дүн (₮)',
	// 			        },
	// 			    },
	// 			    { // Third yAxis
	// 			        title: {
	// 			            text: 'Гүйцэтгэл %',
	// 			        },
	// 			        labels: {
	// 			            format: '{value} %',
	// 			        },
	// 			        opposite: true,
	// 			    }],
	// 			    legend: {
	// 			        shadow: false
	// 			    },
	// 			    tooltip: {
	// 			        shared: true
	// 			    },
	// 			    plotOptions: {
	// 			        column: {
	// 			            grouping: false,
	// 			            shadow: true,
	// 			            borderWidth: 0
	// 			        }
	// 			    },
	// 			    series: datas['branch_total_sales_chart'],
	// 		    }
	// 		    try{
	//     			$('#branch_total_sales_chart').highcharts(options);
	//     		}catch(err) {
	// 	           console.log(err.message);
	// 	        }
 //    		}
 //    		else {
	// 			$('#branch_total_sales_chart').remove();
 //    		}

 //    		// Салбарын өсөлт бууралт сараар - Дүнгээр
 //        	if(datas['branch_monthly_chart']){
 //        		var options = {
 //        			colors:['#9D0C3F','#C70039','#FF5733','#FFC30F','#0099CC'],
	// 		        title: {
	// 			        text: 'Салбарын борлуулалт 12 сараар(₮)'
	// 			    },
	// 			    xAxis: {
	// 			        type: 'category',
	// 			        labels: {
	// 			            format: '{value} сар',
	// 			        },
	// 			    },
	// 			    tooltip: {
	// 			        shared: true
	// 			    },
	// 			    yAxis: [
	// 			    	{ // Primary yAxis
	// 				        labels: {
	// 				            format: '{value} ₮',
	// 				            style: {
	// 				                color: Highcharts.getOptions().colors[2]
	// 				            }
	// 				        },
	// 				        title: {
	// 				            text: 'Мөнгөн дүн',
	// 				            style: {
	// 				                color: Highcharts.getOptions().colors[2]
	// 				            }
	// 				        },
	// 				        opposite: true
	// 				    },
	// 				    { // Secondary yAxis
	// 				        gridLineWidth: 0,
	// 				        title: {
	// 				            text: 'Гүйцэтгэлийн хувь',
	// 				            style: {
	// 				                color: Highcharts.getOptions().colors[0]
	// 				            }
	// 				        },
	// 				        labels: {
	// 				            format: '{value} %',
	// 				            style: {
	// 				                color: Highcharts.getOptions().colors[0]
	// 				            }
	// 				        }
	// 				    },
	// 			    ],
	// 			    series: datas['branch_monthly_chart'],
	// 		    };
	// 		    try{
	//     			$('#branch_monthly_chart').highcharts(options);
	//     		}catch(err) {
	// 	           console.log(err.message);
	// 	        }
 //    		}
 //    		// Салбарын өсөлт бууралт сараар - Тоогоор
 //        	if(datas['branch_monthly_qty_chart']){
 //        		var options = {
 //        			colors:['#9D0C3F','#C70039','#FF5733','#FFC30F','#0099CC'],
	// 		        title: {
	// 			        text: 'Салбарын борлуулалт 12 сараар(ширхэг)'
	// 			    },
	// 			    xAxis: {
	// 			        type: 'category',
	// 			        labels: {
	// 			            format: '{value} сар',
	// 			        },
	// 			    },
	// 			    tooltip: {
	// 			        shared: true
	// 			    },
	// 			    yAxis: [
	// 			    	{ // Primary yAxis
	// 				        labels: {
	// 				            format: '{value} ш',
	// 				            style: {
	// 				                color: Highcharts.getOptions().colors[2]
	// 				            }
	// 				        },
	// 				        title: {
	// 				            text: 'Тоо хэмжээ',
	// 				            style: {
	// 				                color: Highcharts.getOptions().colors[2]
	// 				            }
	// 				        },
	// 				        opposite: true
	// 				    },
	// 				    { // Secondary yAxis
	// 				        gridLineWidth: 0,
	// 				        title: {
	// 				            text: 'Гүйцэтгэлийн хувь',
	// 				            style: {
	// 				                color: Highcharts.getOptions().colors[0]
	// 				            }
	// 				        },
	// 				        labels: {
	// 				            format: '{value} %',
	// 				            style: {
	// 				                color: Highcharts.getOptions().colors[0]
	// 				            }
	// 				        }
	// 				    },
	// 			    ],
	// 			    series: datas['branch_monthly_qty_chart'],
	// 		    };
	// 		    try{
	//     			$('#branch_monthly_qty_chart').highcharts(options);
	//     		}catch(err) {
	// 	           console.log(err.message);
	// 	        }
 //    		}

	// 		// Тасгаар харуулах
 //    		if(datas['branch_sales_chart']){
 //        		var options = {
	// 				chart: {
	// 			        type: 'column'
	// 			    },
	// 			    title: {
	// 			        text: 'Борлуулалт тасгаар'
	// 			    },
	// 			    xAxis: {
	// 			        type: 'category',
	// 			    },
	// 			    yAxis: [{
	// 			        min: 0,
	// 			        title: {
	// 			            text: 'Тоо хэмжээ (ш)',
	// 			        }
	// 			    }, 
	// 			    {	
	// 			    	gridLineWidth: 0,
	// 			        title: {
	// 			            text: 'Дүн (₮)',
	// 			        },
	// 			        opposite: true
	// 			    },
	// 			    { // Third yAxis
	// 			        title: {
	// 			            text: 'Гүйцэтгэл %',
	// 			        },
	// 			        labels: {
	// 			            format: '{value} %',
	// 			        },
	// 			    }],
	// 			    legend: {
	// 			        shadow: false
	// 			    },
	// 			    tooltip: {
	// 			        shared: true
	// 			    },
	// 			    plotOptions: {
	// 			        column: {
	// 			            grouping: false,
	// 			            shadow: true,
	// 			            borderWidth: 0
	// 			        }
	// 			    },
	// 			    series: datas['branch_sales_chart'],
	// 		    }
	// 		    try{
	//     			$('#branch_sales_chart').highcharts(options);
	//     		}catch(err) {
	// 	           console.log(err.message);
	// 	        }
 //    		}
 //    		else {
	// 			$('#branch_sales_chart').remove();
 //    		}

 //    		// 
 //    		// Тасгуудын борлуулалт эзлэх хувь
 //    		// Тасаг дотроо ангилалаар
 //        	if(datas['amount_pie_chart']){
 //        		var options = {
 //        			chart: {
	// 			        type: 'pie',
	// 			    },
	// 			    title: {
	// 			        text: 'Нийт борлуулалтад эзлэх %'
	// 			    },
	// 			    subtitle: {
	// 			        text: 'Дээр нь дарж бүлгээр задлаж харах боломжтой'
	// 			    },
	// 			    plotOptions: {
	// 			        series: {
	// 			        	allowPointSelect: true,
	// 			            dataLabels: {
	// 			                enabled: true,
	// 			                format: '{point.name}: {point.percentage:.1f}%'
	// 			            }
	// 			        }
	// 			    },
	// 			    // tooltip: {
	// 			    //     headerFormat: '<span style="font-size:11px">{series.name}</span><br>',
	// 			    //     pointFormat: '<span style="color:{point.color}">{point.name}</span>: <b>{point.y:.1f}</b><br/>'ь
	// 			    // },
	// 			    tooltip: {
	// 			        pointFormat: '{series.name}: <b>{point.y:.1f}₮</b>',
	// 			    },
	// 			    tooltip: {
				        
	// 			    },
	// 			    series: datas['amount_pie_chart'],
	// 			    drilldown: datas['amount_drill_pie_chart'],
	// 		    };
	// 		    try{
	//     			$('#amount_pie_chart').highcharts(options);
	//     		}catch(err) {
	// 	           console.log(err.message);
	// 	        }
 //    		}
 //    		else {
	// 			$('#amount_pie_chart').remove();
 //    		}

 //    		// Салбарын ангилалаар- Дүнгээр
 //        	if(datas['by_categ_sales_chart']){
 //        		var options = {
 //        			colors:['#BA3C3D','#F8A13F','#FF5733','#FFC30F','#0099CC'],
	// 		        title: {
	// 			        text: 'Сарын борлуулалт ангилалаар(₮)'
	// 			    },
	// 			    xAxis: {
	// 			        type: 'category',
	// 			    },
	// 			    tooltip: {
	// 			        shared: true
	// 			    },
	// 			    yAxis: [
	// 			    	{ // Primary yAxis
	// 				        labels: {
	// 				            format: '{value} ₮',
	// 				            style: {
	// 				                color: Highcharts.getOptions().colors[2]
	// 				            }
	// 				        },
	// 				        title: {
	// 				            text: 'Дүн',
	// 				            style: {
	// 				                color: Highcharts.getOptions().colors[2]
	// 				            }
	// 				        },
	// 				        opposite: true
	// 				    },
	// 				    { // Secondary yAxis
	// 				        gridLineWidth: 0,
	// 				        title: {
	// 				            text: 'Өсөлт',
	// 				            style: {
	// 				                color: Highcharts.getOptions().colors[0]
	// 				            }
	// 				        },
	// 				        labels: {
	// 				            format: '{value} %',
	// 				            style: {
	// 				                color: Highcharts.getOptions().colors[0]
	// 				            }
	// 				        }
	// 				    },
	// 			    ],
	// 			    series: datas['by_categ_sales_chart'],
	// 			    drilldown: datas['by_categ_sales_drill'],
	// 		    };
	// 		    try{
	//     			$('#by_categ_sales_chart').highcharts(options);
	//     		}catch(err) {
	// 	           console.log(err.message);
	// 	        }
 //    		}
 //    		// QTY
 //    		if(datas['by_categ_sales_qty_chart']){
 //        		var options = {
 //        			colors:['#BA3C3D','#F8A13F','#FF5733','#FFC30F','#0099CC'],
	// 		        title: {
	// 			        text: 'Сарын борлуулалт ангилалаар(Ш)'
	// 			    },
	// 			    xAxis: {
	// 			        type: 'category',
	// 			    },
	// 			    tooltip: {
	// 			        shared: true
	// 			    },
	// 			    yAxis: [
	// 			    	{ // Primary yAxis
	// 				        labels: {
	// 				            format: '{value} ш',
	// 				            style: {
	// 				                color: Highcharts.getOptions().colors[2]
	// 				            }
	// 				        },
	// 				        title: {
	// 				            text: 'Тоо хэмжээ',
	// 				            style: {
	// 				                color: Highcharts.getOptions().colors[2]
	// 				            }
	// 				        },
	// 				        opposite: true
	// 				    },
	// 				    { // Secondary yAxis
	// 				        gridLineWidth: 0,
	// 				        title: {
	// 				            text: 'Өсөлт',
	// 				            style: {
	// 				                color: Highcharts.getOptions().colors[0]
	// 				            }
	// 				        },
	// 				        labels: {
	// 				            format: '{value} %',
	// 				            style: {
	// 				                color: Highcharts.getOptions().colors[0]
	// 				            }
	// 				        }
	// 				    },
	// 			    ],
	// 			    series: datas['by_categ_sales_qty_chart'],
	// 			    drilldown: datas['by_categ_sales_qty_drill'],
	// 		    };
	// 		    try{
	//     			$('#by_categ_sales_qty_chart').highcharts(options);
	//     		}catch(err) {
	// 	           console.log(err.message);
	// 	        }
 //    		}

 //    		// 
	// 	},
	// 	// 	
	// });
	// core.form_custom_registry.add('mw_sales_master_plan_04', SALES_PLAN_DASHBOARD_04);

	// // Баярын борлуулалт
	// var SALES_PLAN_DASHBOARD_05 = form_common.FormWidget.extend(form_common.ReinitializeWidgetMixin, {
	// 	template : "mw_sales_master_plan.SALES_PLAN_DASHBOARD_05",

	// 	init: function() {

	// 		// Шаардлагатай JS сангууд импорт хийх
 //            // Old version
 //        	$("head").append('<script type="text/javascript" src="mw_sales_master_plan/static/libs/drilldown.js"></script>');
 //   			$("head").append('<script type="text/javascript" src="mw_sales_master_plan/static/libs/exporting.js"></script>');
 //   			$("head").append('<script type="text/javascript" src="mw_sales_master_plan/static/libs/highcharts-3d.js"></script>');
 //   			$("head").append('<script type="text/javascript" src="mw_sales_master_plan/static/libs/export-data.js"></script>');
   			
	// 		this._super.apply(this, arguments);
	// 		var self = this;

	// 		this.set({
	// 			year: false,
	// 			month: false,
	// 		});

	// 		this.field_manager.on("field_changed:year", this, function() {
 //                this.set({"year": this.field_manager.get_field_value("year")});
 //            });
 //            this.field_manager.on("field_changed:holiday", this, function() {
 //                this.set({"holiday": this.field_manager.get_field_value("holiday")});
 //            });
 //            this.field_manager.on("field_changed:product_type", this, function() {
 //                this.set({"product_type": this.field_manager.get_field_value("product_type")});
 //            });

	// 		this.updating = false;
	// 		this.defs = [];
			
	// 		this.res_o2m_drop = new utils.DropMisordered();
	// 		this.render_drop = new utils.DropMisordered();
	// 		this.description_line = _t("/");
			
	// 		// Original save function is overwritten in order to wait all running deferreds to be done before actually applying the save.
	// 		this.view.original_save = _.bind(this.view.save, this.view);
	// 		this.view.save = function(prepend_on_create){
	// 			self.prepend_on_create = prepend_on_create;
	// 			return $.when.apply($, self.defs).then(function(){
	// 				return self.view.original_save(self.prepend_on_create);
	// 			});
	// 		};

	// 	},

	// 	initialize_field: function() {
	// 		form_common.ReinitializeWidgetMixin.initialize_field.call(this);
	// 		var self = this;
	// 		self.on("change:year", self, self.initialize_content);
	// 		self.on("change:holiday", self, self.initialize_content);
	// 		self.on("change:product_type", self, self.initialize_content);
	// 	},
	// 	initialize_content: function() {
	// 		var self = this;
	// 		this.destroy_content();
	// 		var data_detail;

	// 		return new Model("sales.plan.dashboard.05")
	// 			.call("get_datas", [ 1, self.get('year'), self.get('holiday'), self.get('product_type')])
	// 				.then(function(detail){
	// 					data_detail = detail;
	// 			}).then(function(res){
	// 				self.data_detail = data_detail;
	//                 self.display_data();
	// 		});
	// 	},
	// 	destroy_content: function() {
	// 		if (this.dfm) {
	// 			this.dfm.destroy();
	// 			this.dfm = undefined;
	// 		}
	// 	},

	// 	display_data: function() {
	// 		var self = this;
	// 		self.$el.html(QWeb.render("mw_sales_master_plan.SALES_PLAN_DASHBOARD_05", {widget: self}));

	// 		// DATA zurax
	// 		console.log("=========================disp", self.data_detail);
	// 		var datas = self.data_detail[0];
	// 		// Нийт компаны
	// 		// Компаны Нийт борлуулалт
	// 		if(datas['holiday_total_sales_chart']){
 //        		var options = {
	// 				chart: {
	// 			        type: 'column'
	// 			    },
	// 			    title: {
	// 			        text: 'Компаны нийт борлуулалт'
	// 			    },
	// 			    xAxis: {
	// 			        type: 'category',
	// 			    },
	// 			    yAxis: [{
	// 			        min: 0,
	// 			        title: {
	// 			            text: 'Тоо хэмжээ (ш)',
	// 			        }
	// 			    }, 
	// 			    {	
	// 			    	gridLineWidth: 0,
	// 			        title: {
	// 			            text: 'Дүн (₮)',
	// 			        },
	// 			    },
	// 			    { // Third yAxis
	// 			        title: {
	// 			            text: 'Гүйцэтгэл %',
	// 			        },
	// 			        labels: {
	// 			            format: '{value} %',
	// 			        },
	// 			        opposite: true,
	// 			    }],
	// 			    legend: {
	// 			        shadow: false
	// 			    },
	// 			    tooltip: {
	// 			        shared: true
	// 			    },
	// 			    plotOptions: {
	// 			        column: {
	// 			            grouping: false,
	// 			            shadow: true,
	// 			            borderWidth: 0
	// 			        }
	// 			    },
	// 			    series: datas['holiday_total_sales_chart'],
	// 		    }
	// 		    try{
	//     			$('#holiday_total_sales_chart').highcharts(options);
	//     		}catch(err) {
	// 	           console.log(err.message);
	// 	        }
 //    		}
 //    		else {
	// 			$('#holiday_total_sales_chart').remove();
 //    		}

	// 		// Салбарын задаргаа
 //    		if(datas['holiday_sales_chart']){
 //        		var options = {
 //        			colors: ['#7cb5ec', '#f7a35c', '#90ee7e', '#ff0066',
 //      						 '#DF5353', '#7798BF', '#aaeeee', '#eeaaee', '#55BF3B',],
	// 		        title: {
	// 			        text: 'Баярын борлуулалт (тоо ширхэгээр)'
	// 			    },
	// 			    xAxis: [{
	// 			        type: 'category'
	// 			    }],
	// 			    tooltip: {
	// 			        shared: true
	// 			    },
	// 			    yAxis: [
	// 			    	{ // Primary yAxis
	// 				        labels: {
	// 				            format: '{value} ш',
	// 				        },
	// 				        title: {
	// 				            text: 'Тоо хэмжээ',
	// 				        },
	// 				        opposite: true
	// 				    },
	// 				    { // Secondary yAxis
	// 				        gridLineWidth: 0,
	// 				        title: {
	// 				            text: 'Гүйцэтгэлийн хувь',
	// 				        },
	// 				        labels: {
	// 				            format: '{value} %',
	// 				        }
	// 				    },
	// 			    ],
	// 			    series: datas['holiday_sales_chart'],
	// 			    drilldown: datas['holiday_sales_qty_drilldown_chart'],
	// 		    };
	// 		    try{
	//     			$('#holiday_sales_chart').highcharts(options);
	//     		}catch(err) {
	// 	           console.log(err.message);
	// 	        }
 //    		}
 //    		else {
	// 			$('#holiday_sales_chart').remove();
 //    		}
 //    		// Мөнгөн дүнгээр
 //    		if(datas['holiday_sales_amount_chart']){
 //        		var options = {
 //        			colors: ['#7cb5ec', '#f7a35c', '#90ee7e', '#ff0066',
 //      						 '#DF5353', '#7798BF', '#aaeeee', '#eeaaee', '#55BF3B',],
	// 		        title: {
	// 			        text: 'Баярын борлуулалт (мөнгөн дүнгээр)'
	// 			    },
	// 			    xAxis: [{
	// 			        type: 'category'
	// 			    }],
	// 			    tooltip: {
	// 			        shared: true
	// 			    },
	// 			    yAxis: [
	// 			    	{ // Primary yAxis
	// 				        labels: {
	// 				            format: '{value} ₮',
	// 				        },
	// 				        title: {
	// 				            text: 'Мөнгөн дүн',
	// 				        },
	// 				        opposite: true
	// 				    },
	// 				    { // Secondary yAxis
	// 				        gridLineWidth: 0,
	// 				        title: {
	// 				            text: 'Гүйцэтгэлийн хувь',
	// 				        },
	// 				        labels: {
	// 				            format: '{value} %',
	// 				        }
	// 				    },
	// 			    ],
	// 			    series: datas['holiday_sales_amount_chart'],
	// 			    drilldown: datas['holiday_sales_drilldown_chart'],
	// 		    };
	// 		    try{
	//     			$('#holiday_sales_amount_chart').highcharts(options);
	//     		}catch(err) {
	// 	           console.log(err.message);
	// 	        }
 //    		}
 //    		else {
	// 			$('#holiday_sales_amount_chart').remove();
 //    		}
	// 		// 
	// 	},
	// 	// 	
	// });
	// core.form_custom_registry.add('mw_sales_master_plan_05', SALES_PLAN_DASHBOARD_05);

	// // Баярын борлуулалт - Задаргаа
	// var SALES_PLAN_DASHBOARD_0502 = form_common.FormWidget.extend(form_common.ReinitializeWidgetMixin, {
	// 	template : "mw_sales_master_plan.SALES_PLAN_DASHBOARD_0502",

	// 	init: function() {

	// 		// Шаардлагатай JS сангууд импорт хийх
 //            // Old version
 //        	$("head").append('<script type="text/javascript" src="mw_sales_master_plan/static/libs/drilldown.js"></script>');
 //   			$("head").append('<script type="text/javascript" src="mw_sales_master_plan/static/libs/exporting.js"></script>');
 //   			$("head").append('<script type="text/javascript" src="mw_sales_master_plan/static/libs/highcharts-3d.js"></script>');
 //   			$("head").append('<script type="text/javascript" src="mw_sales_master_plan/static/libs/export-data.js"></script>');
   			
	// 		this._super.apply(this, arguments);
	// 		var self = this;

	// 		this.set({
	// 			year: false,
	// 			month: false,
	// 		});

	// 		this.field_manager.on("field_changed:year", this, function() {
 //                this.set({"year": this.field_manager.get_field_value("year")});
 //            });
 //            this.field_manager.on("field_changed:holiday", this, function() {
 //                this.set({"holiday": this.field_manager.get_field_value("holiday")});
 //            });
 //            this.field_manager.on("field_changed:warehouse_id", this, function() {
 //                this.set({"warehouse_id": this.field_manager.get_field_value("warehouse_id")});
 //            });
 //            this.field_manager.on("field_changed:product_type", this, function() {
 //                this.set({"product_type": this.field_manager.get_field_value("product_type")});
 //            });

	// 		this.updating = false;
	// 		this.defs = [];
			
	// 		this.res_o2m_drop = new utils.DropMisordered();
	// 		this.render_drop = new utils.DropMisordered();
	// 		this.description_line = _t("/");
			
	// 		// Original save function is overwritten in order to wait all running deferreds to be done before actually applying the save.
	// 		this.view.original_save = _.bind(this.view.save, this.view);
	// 		this.view.save = function(prepend_on_create){
	// 			self.prepend_on_create = prepend_on_create;
	// 			return $.when.apply($, self.defs).then(function(){
	// 				return self.view.original_save(self.prepend_on_create);
	// 			});
	// 		};

	// 	},

	// 	initialize_field: function() {
	// 		form_common.ReinitializeWidgetMixin.initialize_field.call(this);
	// 		var self = this;
	// 		self.on("change:year", self, self.initialize_content);
	// 		self.on("change:holiday", self, self.initialize_content);
	// 		self.on("change:warehouse_id", self, self.initialize_content);
	// 		self.on("change:product_type", self, self.initialize_content);
	// 	},
	// 	initialize_content: function() {
	// 		var self = this;
	// 		this.destroy_content();
	// 		var data_detail;

	// 		return new Model("sales.plan.dashboard.05")
	// 			.call("get_datas_detailed", [ 1, self.get('year'), self.get('holiday'), self.get('warehouse_id'), self.get('product_type')])
	// 				.then(function(detail){
	// 					data_detail = detail;
	// 			}).then(function(res){
	// 				self.data_detail = data_detail;
	//                 self.display_data();
	// 		});
	// 	},
	// 	destroy_content: function() {
	// 		if (this.dfm) {
	// 			this.dfm.destroy();
	// 			this.dfm = undefined;
	// 		}
	// 	},

	// 	display_data: function() {
	// 		var self = this;
	// 		self.$el.html(QWeb.render("mw_sales_master_plan.SALES_PLAN_DASHBOARD_0502", {widget: self}));

	// 		// DATA zurax
	// 		console.log("=========================disp", self.data_detail);
	// 		var datas = self.data_detail[0];

	// 		// Сонгосон салбарын тасгийн задаргаа
	// 		if(datas['holiday_sales_detail_chart']){
 //        		var options = {
	// 		        chart: {
	// 			        type: 'column'
	// 			    },
	// 			    title: {
	// 			        text: datas['holiday_warehouse_name'], 
	// 			    },
	// 			    xAxis: {
	// 			        categories: datas['holiday_categ_names'],
	// 			    },
	// 			    yAxis: [{
	// 			        min: 0,
	// 			        title: {
	// 			            text: 'Тоо хэмжээ Ш',
	// 			        }
	// 			    }, {
	// 			        title: {
	// 			            text: 'Мөнгөн дүн ₮',
	// 			        },
	// 			        opposite: true
	// 			    },
	// 			    { // Third yAxis
	// 			        title: {
	// 			            text: 'Гүйцэтгэл %',
	// 			        },
	// 			        labels: {
	// 			            format: '{value} %',
	// 			        },
	// 			    }],
	// 			    legend: {
	// 			        shadow: false
	// 			    },
	// 			    tooltip: {
	// 			        shared: true
	// 			    },
	// 			    plotOptions: {
	// 			        column: {
	// 			            grouping: false,
	// 			            shadow: false,
	// 			            borderWidth: 0
	// 			        }
	// 			    },
	// 			    series: datas['holiday_sales_detail_chart'],
	// 		    };
	// 		    try{
	//     			$('#holiday_sales_detail_chart').highcharts(options);
	//     		}catch(err) {
	// 	           console.log(err.message);
	// 	        }
 //    		}
 //    		else {
	// 			$('#holiday_sales_detail_chart').remove();
 //    		}
 //    		// Сонгосон салбарын тасгийн задаргаа - Ангилалаар
	// 		if(datas['holiday_by_categ_chart']){
 //        		var options = {
 //        			colors: ['#2b908f', '#90ee7e', '#f45b5b', '#7798BF', '#aaeeee', '#ff0066', '#eeaaee',
 //      						 '#55BF3B', '#DF5353', '#7798BF', '#aaeeee'],
	// 		        title: {
	// 			        text: 'Бүтээгдэхүүний ангилалаар'
	// 			    },
	// 			    xAxis: [{
	// 			        type: 'category'
	// 			    }],
	// 			    yAxis: [
	// 			    	{ // Primary yAxis
	// 				        labels: {
	// 				            format: '{value} ш',
	// 				        },
	// 				        title: {
	// 				            text: 'Тоо хэмжээ',
	// 				        },
	// 				        opposite: true
	// 				    },
					    
	// 			    ],
	// 			    series: datas['holiday_by_categ_chart'],
	// 		    };
	// 		    try{
	//     			$('#holiday_by_categ_chart').highcharts(options);
	//     		}catch(err) {
	// 	           console.log(err.message);
	// 	        }
 //    		}
 //    		else {
	// 			$('#holiday_by_categ_chart').remove();
 //    		}
 //    		// Эзлэх хувь ангилалаар
 //    		if(datas['holiday_by_categ_pie_chart']){
 //    			var width = 100/datas['holiday_by_categ_pie_chart'].length
 //    			for (var i = 0; i < datas['holiday_by_categ_pie_chart'].length; i++){
	//     			var div = $("<td></td>");
	//         		var options = {
	//         			chart: {
	// 				        type: 'pie'
	// 				    }, 
	// 				    title: {
	// 				        text: datas['holiday_day_names'][i]+'-нд эзлэх хувь'
	// 				    },
	// 				    subtitle: {
	// 				        text: 'Дээр нь дарж Бүтээгдэхүүнээр задлаж харах боломжтой'
	// 				    },
	// 				    plotOptions: {
	// 				        series: {
	// 				            dataLabels: {
	// 				                enabled: true,
	// 				                format: '{point.name}: {point.y:.1f}%'
	// 				            }
	// 				        }
	// 				    },
	// 				    tooltip: {
	// 				        pointFormat: '<span style="color:{point.color}">{point.name}</span>: <b>{point.y:.1f}</b><br/>'
	// 				    },
	// 				    series: [ datas['holiday_by_categ_pie_chart'][i] ],
	// 				    // drilldown: datas['holiday_by_categ_pie_drill_down_chart'][i],
	// 			    };
	// 			    try{
	// 			    	div.highcharts(options);
	// 	    			$('#holiday_by_categ_pie_chart').append(div);
	// 	    		}catch(err) {
	// 		           console.log(err.message);
	// 		        }
	// 	        }
 //    		}
 //    		else {
	// 			$('#holiday_by_categ_pie_chart').remove();
 //    		}
 //    		// 
	// 	},
	// 	// 	
	// });
	// core.form_custom_registry.add('mw_sales_master_plan_0502', SALES_PLAN_DASHBOARD_0502);

	// // Баярын борлуулалт - Задаргаа Шинэ
	// var SALES_PLAN_DASHBOARD_0503 = form_common.FormWidget.extend(form_common.ReinitializeWidgetMixin, {
	// 	template : "mw_sales_master_plan.SALES_PLAN_DASHBOARD_0503",

	// 	init: function() {

	// 		// Шаардлагатай JS сангууд импорт хийх
 //            // Old version
 //        	$("head").append('<script type="text/javascript" src="mw_sales_master_plan/static/libs/drilldown.js"></script>');
 //   			$("head").append('<script type="text/javascript" src="mw_sales_master_plan/static/libs/exporting.js"></script>');
 //   			$("head").append('<script type="text/javascript" src="mw_sales_master_plan/static/libs/highcharts-3d.js"></script>');
 //   			$("head").append('<script type="text/javascript" src="mw_sales_master_plan/static/libs/export-data.js"></script>');
   			
	// 		this._super.apply(this, arguments);
	// 		var self = this;

	// 		this.set({
	// 			year: false,
	// 			month: false,
	// 		});

	// 		this.field_manager.on("field_changed:year", this, function() {
 //                this.set({"year": this.field_manager.get_field_value("year")});
 //            });
 //            this.field_manager.on("field_changed:holiday", this, function() {
 //                this.set({"holiday": this.field_manager.get_field_value("holiday")});
 //            });
 //            this.field_manager.on("field_changed:warehouse_id", this, function() {
 //                this.set({"warehouse_id": this.field_manager.get_field_value("warehouse_id")});
 //            });
 //            this.field_manager.on("field_changed:product_type", this, function() {
 //                this.set({"product_type": this.field_manager.get_field_value("product_type")});
 //            });

	// 		this.updating = false;
	// 		this.defs = [];
			
	// 		this.res_o2m_drop = new utils.DropMisordered();
	// 		this.render_drop = new utils.DropMisordered();
	// 		this.description_line = _t("/");
			
	// 		// Original save function is overwritten in order to wait all running deferreds to be done before actually applying the save.
	// 		this.view.original_save = _.bind(this.view.save, this.view);
	// 		this.view.save = function(prepend_on_create){
	// 			self.prepend_on_create = prepend_on_create;
	// 			return $.when.apply($, self.defs).then(function(){
	// 				return self.view.original_save(self.prepend_on_create);
	// 			});
	// 		};

	// 	},

	// 	initialize_field: function() {
	// 		form_common.ReinitializeWidgetMixin.initialize_field.call(this);
	// 		var self = this;
	// 		self.on("change:year", self, self.initialize_content);
	// 		self.on("change:holiday", self, self.initialize_content);
	// 		self.on("change:warehouse_id", self, self.initialize_content);
	// 		self.on("change:product_type", self, self.initialize_content);
	// 	},
	// 	initialize_content: function() {
	// 		var self = this;
	// 		this.destroy_content();
	// 		var data_detail;

	// 		return new Model("sales.plan.dashboard.05")
	// 			.call("get_datas_new_detailed", [ 1, self.get('year'), self.get('holiday'), self.get('warehouse_id'), self.get('product_type')])
	// 				.then(function(detail){
	// 					data_detail = detail;
	// 			}).then(function(res){
	// 				self.data_detail = data_detail;
	//                 self.display_data();
	// 		});
	// 	},
	// 	destroy_content: function() {
	// 		if (this.dfm) {
	// 			this.dfm.destroy();
	// 			this.dfm = undefined;
	// 		}
	// 	},

	// 	display_data: function() {
	// 		var self = this;
	// 		self.$el.html(QWeb.render("mw_sales_master_plan.SALES_PLAN_DASHBOARD_0503", {widget: self}));

	// 		// DATA zurax
	// 		console.log("=============0503============disp", self.data_detail);
	// 		var datas = self.data_detail[0];

	// 		// Сонгосон салбарын тасгийн шинэ задаргаа
	// 		if(datas['holiday_new_detail_chart']){
 //        		var options = {
 //        			colors: ['#2b908f', '#90ee7e', '#f45b5b', '#7798BF', '#aaeeee', '#ff0066', '#eeaaee',
 //      					     '#55BF3B', '#DF5353', '#7798BF', '#aaeeee'],
	// 			    chart: {
	// 			        type: 'column'
	// 			    },
	// 			    title: {
	// 			        text: 'Салбарын баярын борлуулалт/мөнгөн дүнгээр/'
	// 			    },  			
	// 			    xAxis: {
	// 			        type: 'category'
	// 			    },
	// 			    tooltip: {
	// 			        shared: true
	// 			    },
	// 			    yAxis: [
	// 			    	{ 
	// 				        title: {
	// 				            text: 'Мөнгөн дүн ₮',
	// 				        },
	// 				    },
	// 			    ],
	// 			    series: datas['holiday_new_detail_chart'],
	// 			    drilldown: datas['holiday_new_detail_drilldown_chart'],
	// 			};
	// 		    try{
	//     			$('#holiday_new_detail_chart').highcharts(options);
	//     		}catch(err) {
	// 	           console.log(err.message);
	// 	        }
 //    		}
 //    		else {
	// 			$('#holiday_new_detail_chart').remove();
 //    		}
 //    		// QTY
 //    		// Сонгосон салбарын тасгийн шинэ задаргаа
	// 		if(datas['holiday_new_detail_qty_chart']){
 //        		var options = {
 //        			colors: ['#2b908f', '#90ee7e', '#f45b5b', '#7798BF', '#aaeeee', '#ff0066', '#eeaaee',
 //      					     '#55BF3B', '#DF5353', '#7798BF', '#aaeeee'],
	// 			    chart: {
	// 			        type: 'column'
	// 			    },
	// 			    title: {
	// 			        text: 'Салбарын баярын борлуулалт/тоо ширхэгээр/'
	// 			    },  			
	// 			    xAxis: {
	// 			        type: 'category'
	// 			    },
	// 			    tooltip: {
	// 			        shared: true
	// 			    },
	// 			    yAxis: [
	// 			    	{ 
	// 				        title: {
	// 				            text: 'Тоо хэмжээ Ш',
	// 				        },
	// 				    },
	// 			    ],
	// 			    series: datas['holiday_new_detail_qty_chart'],
	// 			    drilldown: datas['holiday_new_detail_qty_drilldown_chart'],
	// 			};
	// 		    try{
	//     			$('#holiday_new_detail_qty_chart').highcharts(options);
	//     		}catch(err) {
	// 	           console.log(err.message);
	// 	        }
 //    		}
 //    		else {
	// 			$('#holiday_new_detail_qty_chart').remove();
 //    		}
 //    		// 
	// 	},
	// 	// 	
	// });
	// core.form_custom_registry.add('mw_sales_master_plan_0503', SALES_PLAN_DASHBOARD_0503);

	// // Борлуулалт цагийн - Задаргаа
	// var SALES_PLAN_DASHBOARD_06 = form_common.FormWidget.extend(form_common.ReinitializeWidgetMixin, {
	// 	template : "mw_sales_master_plan.SALES_PLAN_DASHBOARD_06",

	// 	init: function() {

	// 		// Шаардлагатай JS сангууд импорт хийх
 //            // Old version
 //   			$("head").append('<script type="text/javascript" src="mw_sales_master_plan/static/libs/exporting.js"></script>');
 //   			$("head").append('<script type="text/javascript" src="mw_sales_master_plan/static/libs/highcharts-more.js"></script>');
 //   			$("head").append('<script type="text/javascript" src="mw_sales_master_plan/static/libs/heatmap.js"></script>');
 //   			$("head").append('<script type="text/javascript" src="mw_sales_master_plan/static/libs/boost-canvas.js"></script>');
 //   			$("head").append('<script type="text/javascript" src="mw_sales_master_plan/static/libs/boost.js"></script>');
 //   			$("head").append('<script type="text/javascript" src="mw_sales_master_plan/static/libs/data.js"></script>');
 //   			$("head").append('<script type="text/javascript" src="mw_sales_master_plan/static/libs/export-data.js"></script>');
   			
	// 		this._super.apply(this, arguments);
	// 		var self = this;

	// 		this.set({
	// 			year: false,
	// 		});

	// 		this.field_manager.on("field_changed:year", this, function() {
 //                this.set({"year": this.field_manager.get_field_value("year")});
 //            });
 //            this.field_manager.on("field_changed:warehouse_id", this, function() {
 //                this.set({"warehouse_id": this.field_manager.get_field_value("warehouse_id")});
 //            });

	// 		this.updating = false;
	// 		this.defs = [];
			
	// 		this.res_o2m_drop = new utils.DropMisordered();
	// 		this.render_drop = new utils.DropMisordered();
	// 		this.description_line = _t("/");
			
	// 		// Original save function is overwritten in order to wait all running deferreds to be done before actually applying the save.
	// 		this.view.original_save = _.bind(this.view.save, this.view);
	// 		this.view.save = function(prepend_on_create){
	// 			self.prepend_on_create = prepend_on_create;
	// 			return $.when.apply($, self.defs).then(function(){
	// 				return self.view.original_save(self.prepend_on_create);
	// 			});
	// 		};

	// 	},

	// 	initialize_field: function() {
	// 		form_common.ReinitializeWidgetMixin.initialize_field.call(this);
	// 		var self = this;
	// 		self.on("change:year", self, self.initialize_content);
	// 		self.on("change:warehouse_id", self, self.initialize_content);
	// 	},
	// 	initialize_content: function() {
	// 		var self = this;
	// 		this.destroy_content();
	// 		var data_detail;

	// 		return new Model("sales.plan.dashboard.06")
	// 			.call("get_datas", [ 1, self.get('year'), self.get('warehouse_id')])
	// 				.then(function(detail){
	// 					data_detail = detail;
	// 			}).then(function(res){
	// 				self.data_detail = data_detail;
	//                 self.display_data();
	// 		});
	// 	},
	// 	destroy_content: function() {
	// 		if (this.dfm) {
	// 			this.dfm.destroy();
	// 			this.dfm = undefined;
	// 		}
	// 	},

	// 	display_data: function() {
	// 		var self = this;
	// 		self.$el.html(QWeb.render("mw_sales_master_plan.SALES_PLAN_DASHBOARD_06", {widget: self}));

	// 		// DATA zurax
	// 		console.log("=========================disp", self.data_detail);
	// 		var datas = self.data_detail[0];

	// 		if(datas['time_analyze_data']){
 //        		var options = {
 //        			data: {
	// 			        csv: datas['time_analyze_data'],
	// 			    },

	// 			    chart: {
	// 			        type: 'heatmap',
	// 			        margin: [60, 10, 50, 50],
	// 			    },

	// 			    boost: {
	// 			        useGPUTranslations: true,
	// 			    },

	// 			    title: {
	// 			        text: 'Борлуулалт - Үйлчлүүлсэн цагаар',
	// 			        align: 'left',
	// 			        x: 40
	// 			    },

	// 			    subtitle: {
	// 			        text: self.get('year')+' он: '+datas['type'],
	// 			        align: 'left',
	// 			        x: 40
	// 			    },

	// 			    xAxis: {
	// 			        type: 'datetime',
	// 			        min: Date.UTC(self.get('year'), 0, 1),
	// 			        max: Date.UTC(self.get('year')+1, 0, 1),
	// 			        labels: {
	// 			            align: 'left',
	// 			            x: 5,
	// 			            y: 14,
	// 			            format: '{value:%B}' // long month
	// 			        },
	// 			        showLastLabel: false,
	// 			        tickLength: 16
	// 			    },
	// 			    yAxis: {
	// 			        title: {
	// 			            text: null
	// 			        },
	// 			        labels: {
	// 			            format: '{value}:00'
	// 			        },
	// 			        minPadding: 0,
	// 			        maxPadding: 0,
	// 			        startOnTick: false,
	// 			        endOnTick: false,
	// 			        tickPositions: [6,8,10,12,14,16,18,20,22,23],
	// 			        tickWidth: 1,
	// 			        min: 0,
	// 			        max: 23,
	// 			    },

	// 			    colorAxis: {
	// 			        min: -15,
	// 			        max: datas['max_qty'],
	// 			        startOnTick: false,
	// 			        endOnTick: false,
	// 			        labels: {
	// 			            format: '{value}'
	// 			        }
	// 			    },
	// 			    series: [{
	// 			        boostThreshold: 100,
	// 			        borderWidth: 0,
	// 			        nullColor: '#EFEFEF',
	// 			        colsize: 30 * 36e5, // one day
	// 			        tooltip: {
	// 			            headerFormat: 'Борлуулалт<br/>',
	// 			            pointFormat: '{point.x:%b %e, %Y} {point.y}:00: <b>{point.value} ш</b>'
	// 			        },
	// 			        turboThreshold: Number.MAX_VALUE, // #3404, remove after 4.0.5 release
	// 			    }]
	// 		    };
	// 		    try{
	//     			$('#time_analyze_sales_chart').highcharts(options);
	//     		}catch(err) {
	// 	           console.log(err.message);
	// 	        }
 //    		}
 //    		else {
	// 			$('#time_analyze_sales_chart').remove();
 //    		}
 //    		// 
	// 	},
	// 	// 	
	// });
	// core.form_custom_registry.add('mw_sales_master_plan_06', SALES_PLAN_DASHBOARD_06);

});
