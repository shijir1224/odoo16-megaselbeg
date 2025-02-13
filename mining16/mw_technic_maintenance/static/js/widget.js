odoo.define('mw_technic_maintenance.maintenance_timesheet', function (require) {
	"use strict";

	var Widget= require('web.Widget');
	var widgetRegistry = require('web.widget_registry');
	var data = require('web.data');
	var FieldManagerMixin = require('web.FieldManagerMixin');

	var dialogs = require('web.view_dialogs');

	var core = require('web.core');
	var QWeb = core.qweb;

	var MaintenanceTimesheet = Widget.extend(FieldManagerMixin, {
		template : "mw_technic_maintenance.MaintenanceTimesheet",
		init: function (parent, dataPoint) {
			this._super.apply(this, arguments);
			this.data = dataPoint.data;
        },
	    start: function() {
	    	var self = this;
	    	var ds = new data.DataSet(this, 'maintenance.workorder');
			ds.call('get_timesheet_datas', ['maintenance.workorder', this.data["id"]])
	            .then(function (res) {
	            	self.display_data(res);
            });
		},
		display_data: function(data) {
			var self = this;
			console.log("=======DRAW=====", data);
			self.$el.html(QWeb.render("mw_technic_maintenance.MaintenanceTimesheet", {widget: self}));
			var datas = data;
			// DATA zurax
			// WO timesheet
			if(datas['timesheet_data']){
        		var options = {
        			colors: ['#2b908f', '#90ee7e', '#f45b5b', '#7798BF', '#eeaaee',
      					     '#55BF3B', '#DF5353', '#7798BF', '#aaeeee'],
					chart: {
				        type: 'columnrange',
				        inverted: true
				    },
				    title: {
				        text: 'Засварын ажлын цаг'
				    },
				    subtitle: {
				        text: 'Ажлын цагийн задаргаа'
				    },
				    xAxis: {
				    	categories: datas['timesheet_categories'],
				    },
				    yAxis: {
			            type: 'datetime',
			            title: {
			                text: 'Хугацаа'
			            }
			        },
				    tooltip: {
					    formatter: function() {
					        return '<b>Зарцуулсан цаг:</b> ' + String(this.point.info)+' цаг';
					    },
					},
				    legend: {
				        enabled: false
				    },
				    series: [{
				        name: 'Заруулсан цаг',
				        colorByPoint: true,
				        colors: datas['timesheet_colors'],
				        data: datas['timesheet_data'],
				    }]
			    }
			    try{
	    			$('#maintenance_timesheet').highcharts(options);
	    		}catch(err) {
		           console.log(err.message);
		        }
    		}
    		else {
				$('#maintenance_timesheet').remove();
    		}
    		// ---------------------------------------------------
		},
	});
	widgetRegistry.add(
	    'maintenance_timesheet', MaintenanceTimesheet
	);

	// Урьдчилсан төлөвлөгөөний Timeline
	var MaintenancePlanTimeline = Widget.extend(FieldManagerMixin, {
		template : "mw_technic_maintenance.MaintenancePlanTimeline",
		events: {
	        'click button.full_screen': 'setFullScreen',
	    },
	    setFullScreen: function () {
	        if( document.fullscreenElement ||
			    document.webkitFullscreenElement ||
			    document.mozFullScreenElement ||
			    document.msFullscreenElement )
			{
			    if (document.exitFullscreen) {
			      document.exitFullscreen();
			    } else if (document.mozCancelFullScreen) {
			      document.mozCancelFullScreen();
			    } else if (document.webkitExitFullscreen) {
			      document.webkitExitFullscreen();
			    } else if (document.msExitFullscreen) {
			      document.msExitFullscreen();
			    }
			}
			else {
			    var element = $('#div_plan_timeline').get(0);
			    if (element.requestFullscreen) {
			      element.requestFullscreen();
			    } else if (element.mozRequestFullScreen) {
			      element.mozRequestFullScreen();
			    } else if (element.webkitRequestFullscreen) {
			      element.webkitRequestFullscreen(Element.ALLOW_KEYBOARD_INPUT);
			    } else if (element.msRequestFullscreen) {
			      element.msRequestFullscreen();
			    }
			  }
	    },
		init: function (parent, dataPoint) {
			this._super.apply(this, arguments);
			this.data = dataPoint.data;
        },
	    start: function() {
	    	var self = this;
	    	var ds = new data.DataSet(this, 'maintenance.plan.generator');
			ds.call('get_plan_datas', ['maintenance.plan.generator', this.data["id"]])
	            .then(function (res) {
	            	self.display_data(res);
            });
		},
		display_data: function(data) {
			var self = this;
			self.$el.html(QWeb.render("mw_technic_maintenance.MaintenancePlanTimeline", {widget: self}));
			var datas = data;
			//
			// DATA zurax
			if(datas['timeline_data']){
				var series = [];
				var ooto = datas['timeline_data']
				$.each(ooto.reverse(), function(i, flow) {
				    var item = {
				        name: flow.name,
				        data: [],
				        info: flow.info,
				    };
				    $.each(flow.intervals, function(j, interval) {
				        item.data.push({
				            x: interval.from,
				            y: i,
				            info: interval.info,
				            from: interval.from,
				            to: interval.to
				        }, {
				            x: interval.to,
				            y: i,
				            info: interval.info,
				            from: interval.from,
				            to: interval.to
				        });
				        // add a null value between intervals
				        if (flow.intervals[j + 1]) {
				            item.data.push(
				                [(interval.to + flow.intervals[j + 1].from) / 2, null]
				            );
				        }
				    });
				    series.push(item);
				});

        		var options = {
					chart: {
			            renderTo: 'div_plan_timeline',
			            zoomType: 'x',
			        },
			        title: {
			            text: 'Төлөвлөгөөний Timeline'
			        },
			        xAxis: {
			            type: 'datetime',
			            dateTimeLabelFormats: {
			                day: '%Y-%m-%d',
			            }
			        },
			        yAxis: {
			            tickInterval: 1,
			            min: -0.5,
			            max: ooto.length-0.5,
			            labels: {
			                formatter: function() {
			                    if (ooto[this.value]) {
			                        return '<b>'+ooto[this.value].name+'</b>';
			                    }
			                }
			            },
			            startOnTick: false,
			            endOnTick: false,
			            tickmarkPlacement: 'between',
			            title: { text: null },
			            minPadding: 0.2,
			            maxPadding: 0.2
			        },
			        legend: {
			            align: 'right',
			            verticalAlign: 'top',
			            layout: 'vertical',
			            reversed: true,
			            x: 0,
			            y: 100
			        },
			        tooltip: {
			            crosshairs: true,
			            formatter: function() {
			                return '<b>'+ this.series.name + '</b> - '+this.point.options.technic_name+'<br/>' +
			                    Highcharts.dateFormat('%Y-%m-%d', this.point.options.from) +
			                    ', ' + this.point.options.info;
			            }
			        },
			        plotOptions: {
			            line: {
			                lineWidth: 11,
			                marker: {
			                    enabled: false
			                },
			                dataLabels: {
			                    enabled: true,
			                    align: 'left',
			                    formatter: function() {
			                        return this.point.options && this.point.options.label;
			                    }
			                }
			            }
			        },
			        series: series,
			    }
			    try{
	    			$('#div_plan_timeline').highcharts(options);
	    		}catch(err) {
		           console.log(err.message);
		        }
    		}
    		else {
				$('#container').remove();
    		}
    		// --------------------------
		},
	});
	widgetRegistry.add(
	    'maintenance_plan_timeline', MaintenancePlanTimeline
	);

	// Урьдчилсан төлөвлөгөөний Calendar
	var MaintenancePlanCalendar = Widget.extend(FieldManagerMixin, {
		template : "mw_technic_maintenance.MaintenancePlanCalendar",
		events: {
	        'click button.full_screen': 'setFullScreen',
	        'click span.slider': 'clickToggle',
	    },
	    setFullScreen: function () {
	        if( document.fullscreenElement ||
			    document.webkitFullscreenElement ||
			    document.mozFullScreenElement ||
			    document.msFullscreenElement )
			{
			    if (document.exitFullscreen) {
			      document.exitFullscreen();
			    } else if (document.mozCancelFullScreen) {
			      document.mozCancelFullScreen();
			    } else if (document.webkitExitFullscreen) {
			      document.webkitExitFullscreen();
			    } else if (document.msExitFullscreen) {
			      document.msExitFullscreen();
			    }
			}
			else {
			    var element = $('#calendar_parent').get(0);
			    if (element.requestFullscreen) {
			      element.requestFullscreen();
			    } else if (element.mozRequestFullScreen) {
			      element.mozRequestFullScreen();
			    } else if (element.webkitRequestFullscreen) {
			      element.webkitRequestFullscreen(Element.ALLOW_KEYBOARD_INPUT);
			    } else if (element.msRequestFullscreen) {
			      element.msRequestFullscreen();
			    }
			}
	    },
	    clickToggle: function (e) {
			setTimeout(function(){
				// ----
				if(e.currentTarget.previousElementSibling.checked) {
					var color = e.currentTarget.previousElementSibling.dataset.color;
					e.currentTarget.style.backgroundColor = color;
					var tds = $('td.day[data-name="'+e.currentTarget.dataset.name+'"]');
					for(var i=0;i<tds.length;i++){
						tds[i].style['box-shadow'] = tds[i].dataset.css;
					}
				}
				else {
					e.currentTarget.style.backgroundColor = '#ccc';
					var tds = $('td.day[data-name="'+e.currentTarget.dataset.name+'"]');
					for(var i=0;i<tds.length;i++){
						tds[i].dataset.css = tds[i].style['box-shadow'];
					}
					tds.css('box-shadow','none');
				}
				// ----
			}, 300);
	    },
		init: function (parent, dataPoint) {
			this._super.apply(this, arguments);
			this.data = dataPoint.data;
        },
	    start: function() {
	    	var self = this;
	    	$("#toggle_div").attr('class',this.data["id"]);
	    	var ds = new data.DataSet(this, 'maintenance.plan.generator');
			ds.call('get_plan_calendar_datas', ['maintenance.plan.generator', this.data["id"], []])
	            .then(function (res) {
	            	self.display_data(res);
            });
		},
		display_data: function(data) {
			var self = this;
			self.$el.html(QWeb.render("mw_technic_maintenance.MaintenancePlanCalendar", {widget: self}));
			var datas = data;
			console.log("-1--data", datas);
			// Toggle zurax
			if(datas['pm_names']){
				for(var key in datas['pm_names']){
					var toggle = "<label class='switch' title='"+datas['pm_names'][key]['name']+"'>"
									+ "<input type='checkbox' checked class='pm_toggle'"
											+" data-id='"+datas['pm_names'][key]['id']+"'"
											+" data-color='"+datas['pm_names'][key]['color']+"'"
											+"/>"
									+ "<span class='slider round' data-name='"+datas['pm_names'][key]['name']+"'"
											+" style='background-color:"+datas['pm_names'][key]['color']+"'"
											+" data-id='"+datas['pm_names'][key]['id']+"'/>"
								+ "</label>";
					$("#toggle_div").append(toggle);
				}
			}
			// DATA calendar zurax
			if(datas['calendar_data']){
				for(var i=0;i<datas['calendar_data'].length;i++){
					// String to Date
					var temp = datas['calendar_data'][i].startDate
					var dddd = new Date(parseInt(temp.substring(0,4)), parseInt(temp.substring(5,7))-1, parseInt(temp.substring(8,10)));
					datas['calendar_data'][i].startDate = dddd;
					var temp = datas['calendar_data'][i].endDate
					var dddd = new Date(parseInt(temp.substring(0,4)), parseInt(temp.substring(5,7))-1, parseInt(temp.substring(8,10)));
					datas['calendar_data'][i].endDate = dddd;
				}
				// Settings
				var options = {
			        enableContextMenu: true,
			        alwaysHalfDay: true,
			        minDate: datas['calendar_data'][0].startDate,
			        maxDate: datas['calendar_data'][datas['calendar_data'].length-1].endDate,
			        mouseOnDay: function(e) {
			            if(e.events.length > 0) {
			                var content = '';
			                for(var i in e.events) {
			                    content += '<div class="event-tooltip-content">'
		                                    + '<div class="event-name" style="color:' + e.events[i].color + '"><b>' + e.events[i].name + '</b></div>'
		                                    + '<div class="event-location"> Техник: <b>' + e.events[i].technic_name + '</b></div>'
		                                    + '<div class="event-location"> Гүйлт: <b>' + e.events[i].pm_odometer + '</b></div>'
		                                    + '<div class="event-location"> Зогсох цаг: <b>' + e.events[i].work_time + '</b></div>'
		                                + '</div>';
			                }
			                $(e.element).popover({
			                    trigger: 'manual',
			                    container: 'body',
			                    html:true,
			                    content: content
			                });
			                $(e.element).popover('show');
			            }
			        },
			        mouseOutDay: function(e) {
			            if(e.events.length > 0) {
			                $(e.element).popover('hide');
			            }
			        },
			        dataSource: datas['calendar_data'],
			    }
				$('#div_plan_calendar').calendar(options);
    		}
    		else {
    			$('#container').remove();
    		}
    		// --------------------------
		},
	});
	widgetRegistry.add(
	    'maintenance_plan_calendar', MaintenancePlanCalendar
	);

	// Maintenance DB 01
	var MAINTENANCE_DASHBOARD_01 = Widget.extend(FieldManagerMixin, {
		template : "mw_technic_maintenance.MAINTENANCE_DASHBOARD_01",
		init: function (parent, dataPoint) {
			this._super.apply(this, arguments);
        },
		updateState: function(dataPoint) {
	    	var self = this;
	    	var ds = new data.DataSet(this, 'maintenance.dashboard.01');
			console.log(dataPoint.data["branch_id"]['data']['id'])
			ds.call('get_datas', ['maintenance.dashboard.01', dataPoint.data["date_start"], dataPoint.data["date_end"], dataPoint.data["branch_id"]['data']['id'] ])
	            .then(function (res) {
	            	self.display_data(res);
            });
		},
		display_data: function(data) {
			var self = this;
			console.log("=====1==DRAW=====", data);
			self.$el.html(QWeb.render("mw_technic_maintenance.MAINTENANCE_DASHBOARD_01", {widget: self}));
    		// ---------------------------------------------
    		var datas = data;
			// DATA zurax
			if(datas['by_technic_type']){
        		var options = {
        			colors: ['#2b908f', '#90ee7e', '#f45b5b', '#7798BF', '#eeaaee',
      					     '#55BF3B', '#DF5353', '#7798BF', '#aaeeee'],
					chart: {
				        type: 'column'
				    },
				    title: {
				        text: 'Техникийн төрлөөр'
				    },
				    subtitle: {
				        text: datas['by_technic_type_title'],
				    },
				    xAxis: {
				        type: 'category',
				    },
				    tooltip: {
				        shared: true,
				    },
				    plotOptions: {
				        series: {
				            borderWidth: 0,
				            dataLabels: {
				                enabled: true,
				                format: '{point.y:.1f}%',
				                style: {
					                fontSize: '11px',
					                fontFamily: 'Verdana, sans-serif'
					            }
				            }
				        }
				    },
				    yAxis: [
					    { // Secondary yAxis
					        gridLineWidth: 1,
					        title: {
					            text: 'Гүйцэтгэлийн хувь',
					        },
					        labels: {
					            format: '{value} %',
					        }
					    },
				    ],
				    series: datas['by_technic_type'],
			    }
			    try{
	    			$('#by_technic_type').highcharts(options);
	    		}catch(err) {
		           console.log(err.message);
		        }
    		}
    		else {
				$('#by_technic_type').remove();
    		}
    		// WO performance
    		if(datas['wo_performance_div']){
        		var options = {
					chart: {
				        type: 'column'
				    },
				    title: {
				        text: 'WorkOrder гүйцэтгэл'
				    },
				    xAxis: {
				        type: 'category',
				    },
				    tooltip: {
				        shared: true,
				    },
				    yAxis: [
				    	{ // Primary yAxis
					        labels: {
					            format: '{value} ш',
					        },
					        title: {
					            text: 'Тоо ширхэг',
					        },
					        opposite: true
					    },
					    { // Secondary yAxis
					        gridLineWidth: 1,
					        title: {
					            text: 'Гүйцэтгэлийн хувь',
					        },
					        labels: {
					            format: '{value} %',
					        }
					    },
				    ],
				    series: datas['wo_performance_div'],
			    }
			    try{
	    			$('#wo_performance_div').highcharts(options);
	    		}catch(err) {
		           console.log(err.message);
		        }
    		}
    		else {
				$('#wo_performance_div').remove();
    		}

    		// Employee performance
    		if(datas['employee_performance_div']){
        		var options = {
					chart: {
				        type: 'column'
				    },
				    title: {
				        text: 'Хүн цагийн гүйцэтгэл'
				    },
				    xAxis: {
				        type: 'category',
				    },
				    tooltip: {
				        shared: true,
				    },
				    yAxis: [
				    	{ // Primary yAxis
					        labels: {
					            format: '{value} х/ц',
					        },
					        title: {
					            text: 'Хүн цаг',
					        },
					        opposite: true
					    },
					    { // Secondary yAxis
					        gridLineWidth: 1,
					        title: {
					            text: 'Гүйцэтгэлийн хувь',
					        },
					        labels: {
					            format: '{value} %',
					        }
					    },
				    ],
				    series: datas['employee_performance_div'],
			    }
			    try{
	    			$('#employee_performance_div').highcharts(options);
	    		}catch(err) {
		           console.log(err.message);
		        }
    		}
    		else {
				$('#employee_performance_div').remove();
    		}

    		// Засварын цаг - Техникийн системээр
    		if(datas['repairtime_by_system']){
        		var options = {
        			colors: ['#7798BF', '#aaeeee'],
					chart: {
				        type: 'column'
				    },
				    title: {
				        text: 'Засварын цаг(системээр)'
				    },
				    xAxis: {
				        type: 'category',
				    },
				    tooltip: {
				        shared: true,
				    },
				    plotOptions: {
				        series: {
				            borderWidth: 0,
				            dataLabels: {
				                enabled: true,
				                format: '{point.y:.1f}цаг',
				                style: {
					                fontSize: '11px',
					                fontFamily: 'Verdana, sans-serif'
					            }
				            }
				        }
				    },
				    yAxis: [
					    { // Secondary yAxis
					        gridLineWidth: 1,
					        title: {
					            text: 'Цаг',
					        },
					        labels: {
					            format: '{value} цаг',
					        }
					    },
				    ],
				    series: datas['repairtime_by_system'],
			    }
			    try{
	    			$('#repairtime_by_system_div').highcharts(options);
	    		}catch(err) {
		           console.log(err.message);
		        }
    		}
    		else {
				$('#repairtime_by_system_div').remove();
    		}

    		// ===============================================================
		},
	});
	widgetRegistry.add(
	    'maintenance_dashboard_01', MAINTENANCE_DASHBOARD_01
	);

	// Maintenance DB 02
	var MAINTENANCE_DASHBOARD_02= Widget.extend(FieldManagerMixin, {
		template : "mw_technic_maintenance.MAINTENANCE_DASHBOARD_02",
		init: function (parent, dataPoint) {
			this._super.apply(this, arguments);
        },
		updateState: function(dataPoint) {
	    	var self = this;
	    	var ds = new data.DataSet(this, 'maintenance.dashboard.02');
			ds.call('get_datas', ['maintenance.dashboard.02', dataPoint.data["date_start"], dataPoint.data["date_end"], dataPoint.data["technic_id"], dataPoint.data["branch_id"]['data']['id'] ])
	            .then(function (res) {
	            	self.display_data(res);
            });
		},
		display_data: function(data) {
			var self = this;
			console.log("=======DRAW=====", data);
			self.$el.html(QWeb.render("mw_technic_maintenance.MAINTENANCE_DASHBOARD_02", {widget: self}));
    		// ---------------------------------------------
    		var datas = data;
			// DATA zurax
			// month_WO performance
    		if(datas['month_wo_performance_div']){
        		var options = {
					chart: {
				        type: 'column'
				    },
				    title: {
				        text: 'WorkOrder гүйцэтгэл'
				    },
				    xAxis: {
				        type: 'category',
				    },
				    tooltip: {
				        shared: true,
				    },
				    yAxis: [
				    	{ // Primary yAxis
					        labels: {
					            format: '{value} ш',
					        },
					        title: {
					            text: 'Тоо ширхэг',
					        },
					        opposite: true
					    },
					    { // Secondary yAxis
					        gridLineWidth: 1,
					        title: {
					            text: 'Гүйцэтгэлийн хувь',
					        },
					        labels: {
					            format: '{value} %',
					        }
					    },
				    ],
				    series: datas['month_wo_performance_div'],
			    }
			    try{
	    			$('#month_wo_performance_div').highcharts(options);
	    		}catch(err) {
		           console.log(err.message);
		        }
    		}
    		else {
				$('#month_wo_performance_div').remove();
    		}

    		// month_ Employee performance
    		if(datas['month_employee_performance_div']){
        		var options = {
					chart: {
				        type: 'column'
				    },
				    title: {
				        text: 'Хүн цагийн гүйцэтгэл'
				    },
				    xAxis: {
				        type: 'category',
				    },
				    tooltip: {
				        shared: true,
				    },
				    yAxis: [
				    	{ // Primary yAxis
					        labels: {
					            format: '{value} х/ц',
					        },
					        title: {
					            text: 'Хүн цаг',
					        },
					        opposite: true
					    },
					    { // Secondary yAxis
					        gridLineWidth: 1,
					        title: {
					            text: 'Гүйцэтгэлийн хувь',
					        },
					        labels: {
					            format: '{value} %',
					        }
					    },
				    ],
				    series: datas['month_employee_performance_div'],
			    }
			    try{
	    			$('#month_employee_performance_div').highcharts(options);
	    		}catch(err) {
		           console.log(err.message);
		        }
    		}
    		else {
				$('#month_employee_performance_div').remove();
    		}
			// WORK
			if(datas['by_monthly_work_tbb']){
        		var options = {
        			colors: ['#2b908f', '#90ee7e', '#f45b5b', '#7798BF', '#eeaaee',
      					     '#55BF3B', '#DF5353', '#7798BF', '#aaeeee'],
					chart: {
				        type: 'column'
				    },
				    title: {
				        text: 'Ажилласан ТББ'
				    },
				    // subtitle: {
				    //     text: 'Ажлын цагийн задаргаа'
				    // },
				    xAxis: {
				        type: 'category',
				    },
				    tooltip: {
				        shared: true,
				    },
				    plotOptions: {
				        series: {
				            borderWidth: 0,
				            dataLabels: {
				                enabled: true,
				                format: '{point.y:.1f}%',
				                style: {
					                fontSize: '11px',
					                fontFamily: 'Verdana, sans-serif'
					            }
				            }
				        }
				    },
				    yAxis: [
					    { // Secondary yAxis
					        gridLineWidth: 1,
					        title: {
					            text: 'Гүйцэтгэлийн хувь',
					        },
					        labels: {
					            format: '{value} %',
					        }
					    },
				    ],
				    series: datas['by_monthly_work_tbb'],
			    }
			    try{
	    			$('#by_monthly_work_tbb').highcharts(options);
	    		}catch(err) {
		           console.log(err.message);
		        }
    		}
    		else {
				$('#by_monthly_work_tbb').remove();
    		}

			// PLAN
			if(datas['by_monthly_plan_tbb']){
        		var options = {
        			colors: ['#2b908f', '#90ee7e', '#f45b5b', '#7798BF', '#eeaaee',
      					     '#55BF3B', '#DF5353', '#7798BF', '#aaeeee'],
					chart: {
				        type: 'column'
				    },
				    title: {
				        text: 'Төлөвлөсөн ТББ'
				    },
				    // subtitle: {
				    //     text: 'Ажлын цагийн задаргаа'
				    // },
				    xAxis: {
				        type: 'category',
				    },
				    tooltip: {
				        shared: true,
				    },
				    plotOptions: {
				        series: {
				            borderWidth: 0,
				            dataLabels: {
				                enabled: true,
				                format: '{point.y:.1f}%',
				                style: {
					                fontSize: '11px',
					                fontFamily: 'Verdana, sans-serif'
					            }
				            }
				        }
				    },
				    yAxis: [
					    { // Secondary yAxis
					        gridLineWidth: 1,
					        title: {
					            text: 'Гүйцэтгэлийн хувь',
					        },
					        labels: {
					            format: '{value} %',
					        }
					    },
				    ],
				    series: datas['by_monthly_plan_tbb'],
			    }
			    try{
	    			$('#by_monthly_plan_tbb').highcharts(options);
	    		}catch(err) {
		           console.log(err.message);
		        }
    		}
    		else {
				$('#by_monthly_plan_tbb').remove();
    		}

    		// ===============================================================
		},
	});
	widgetRegistry.add(
	    'maintenance_dashboard_02', MAINTENANCE_DASHBOARD_02
	);

	// Maintenance DB 03
	var MAINTENANCE_DASHBOARD_03= Widget.extend(FieldManagerMixin, {
		template : "mw_technic_maintenance.MAINTENANCE_DASHBOARD_03",
		events: {
            "click .plan_cell": "go_to",  
            "click #tbbk_download_pdf": "download_pdf", 
            "click .tablink": "go_to_tab", 
        },
		init: function (parent, dataPoint) {
			this._super.apply(this, arguments);
			this.data = dataPoint.data;
			$("head").append('<script type="text/javascript" src="mw_technic_maintenance/static/libs/jspdf.js"></script>');
        },
        start: function () {
            var self = this;
            console.log('===', self);
            var ds = new data.DataSet(this, 'maintenance.dashboard.03');
			ds.call('get_datas', ['maintenance.dashboard.03', self.data["date_start"], self.data["date_end"], self.data["branch_id"]['data']['id'] ])
	            .then(function (res) {
	            	self.plan_lines = res['plan_lines']
	            	self.performance_lines = res['performance_lines']
	            	self.display_data(res, self.data["date_start"], self.data["date_end"]);
            });
        },
		updateState: function(dataPoint) {
	    	var self = this;
	    	var ds = new data.DataSet(this, 'maintenance.dashboard.03');
			ds.call('get_datas', ['maintenance.dashboard.03', dataPoint.data["date_start"], dataPoint.data["date_end"], dataPoint.data["branch_id"]['data']['id'] ])
	            .then(function (res) {
	            	self.plan_lines = res['plan_lines']
	            	self.performance_lines = res['performance_lines']
	            	self.display_data(res, dataPoint.data["date_start"], dataPoint.data["date_end"]);
            });
		},
		display_data: function(data, date_start, date_end) {
			var self = this;
    		// ---------------------------------------------
    		var start = new Date(date_start); //yyyy-mm-dd
            var end = new Date(date_end); //yyyy-mm-dd
            var times = []
            while(start <= end){
                var mm = ((start.getMonth()+1)>=10)?(start.getMonth()+1):'0'+(start.getMonth()+1);
                var dd = ((start.getDate())>=10)? (start.getDate()) : '0' + (start.getDate());
                var yyyy = start.getFullYear();

                var date = yyyy+'-'+mm+'-'+dd;
                var days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
                var d = new Date(date);
                var dayName = days[d.getDay()];
                 //yyyy-mm-dd
                times.push(dayName+' '+mm+'/'+dd);
                start = new Date(start.setDate(start.getDate() + 1)); //date increase by 1
            }
            self.times = times;
            console.log("=======DRAW=====", data, self.times);
            self.$el.html(QWeb.render("mw_technic_maintenance.MAINTENANCE_DASHBOARD_03", {widget: self}));
    		// ===============================================================
		},
		go_to: function(event) {
          var self = this;
          var tt_id = JSON.parse($(event.target).data("id"));
          new dialogs.FormViewDialog(this, {
              type: 'ir.actions.act_window',
              res_model: 'maintenance.plan.line',
              res_id: tt_id,
              view_type: 'form',
              view_mode: 'form',
              views: [[false, 'form']],
              target: 'new',
              readonly: (this.query_data=='done'),
              on_saved: this.trigger_up.bind(this, 'reload'),
          }).open();
        },
        download_pdf: function(event) {
          	var self = this;
          	var doc = new jsPDF();
			doc.fromHTML($('#tbbk_table'));
		    doc.save('tbbk.pdf');
        },
        go_to_tab: function(event) {
          	var self = this;
          	var i, tabcontent, tablinks, tab_id;
			  tabcontent = document.getElementsByClassName("tabcontent");
			  for (i = 0; i < tabcontent.length; i++) {
			    tabcontent[i].style.display = "none";
			  }
			  tablinks = document.getElementsByClassName("tablink");
			  for (i = 0; i < tablinks.length; i++) {
			    tablinks[i].style.backgroundColor = "";
			  }
			  document.getElementById(event.currentTarget.title).style.display = "block";
			  event.currentTarget.style.backgroundColor = "#312f9a";
        },
	});
	widgetRegistry.add(
	    'maintenance_dashboard_03', MAINTENANCE_DASHBOARD_03
	);

	// Maintenance DB 04
	var MAINTENANCE_DASHBOARD_04 = Widget.extend(FieldManagerMixin, {
		template : "mw_technic_maintenance.MAINTENANCE_DASHBOARD_04",
		init: function (parent, dataPoint) {
			this._super.apply(this, arguments);
        },
		updateState: function(dataPoint) {
	    	var self = this;
	    	var ds = new data.DataSet(this, 'maintenance.dashboard.04');
			ds.call('get_datas', ['maintenance.dashboard.04', dataPoint.data["date_start"], dataPoint.data["date_end"], dataPoint.data["branch_id"]['data']['id'] ])
	            .then(function (res) {
	            	self.all_technic_info = res['all_technic_info'];
	            	self.display_data(res);
            });
		},
		display_data: function(data) {
			var self = this;
			console.log("=====4==DRAW=====", data);
			self.$el.html(QWeb.render("mw_technic_maintenance.MAINTENANCE_DASHBOARD_04", {widget: self}));
    		// ---------------------------------------------
    		var datas = data;
			// DATA zurax
			// Бүх техникийн ТББ, гүйцэтгэл
			if(datas['all_technic_data']){
        		var options = {
					chart: {
				        type: 'column'
				    },
				    title: {
				        text: 'ТББ болон Ашиглалт'
				    },
				    xAxis: {
				        categories: [
				            'Бэлэн байдал',
				            'Ашиглалт',
				        ],
				        crosshair: true
				    },
				    tooltip: {
				        shared: true,
				    },
				    plotOptions: {
				        series: {
				            borderWidth: 0,
				            dataLabels: {
				                enabled: true,
				                format: '{point.y:.1f}%',
				                style: {
					                fontSize: '11px',
					                fontFamily: 'Verdana, sans-serif'
					            }
				            }
				        }
				    },
				    yAxis: [
					    { // Primary yAxis
					        gridLineWidth: 1,
					        title: {
					            text: 'Гүйцэтгэлийн хувь',
					        },
					        labels: {
					            format: '{value} %',
					        }
					    },
				    ],
				    series: datas['all_technic_data'],
			    }
			    try{
	    			$('#all_technic_data').highcharts(options);
	    		}catch(err) {
		           console.log(err.message);
		        }
    		}
    		else {
				$('#all_technic_data').remove();
    		}
    		// Засварын цагаар - Нийт
    		if(datas['total_repairtime_by_type']){
        		var options = {
					chart: {
				        type: 'pie'
				    },
				    title: {
				        text: 'Нийт засварын цагууд'
				    },
				    tooltip: {
				        pointFormat: '{series.name}: <b>{point.percentage:.1f}%</b>'
				    },
				    accessibility: {
				        point: {
				            valueSuffix: '%'
				        }
				    },
				    plotOptions: {
				        pie: {
				            allowPointSelect: true,
				            cursor: 'pointer',
				            dataLabels: {
				                enabled: true,
				                format: '<b>{point.name}</b>: {point.y:.1f} ц',
				                connectorColor: 'silver'
				            }
				        }
				    },
				    series: datas['total_repairtime_by_type'],
			    }
			    try{
	    			$('#total_repairtime_by_type').highcharts(options);
	    		}catch(err) {
		           console.log(err.message);
		        }
    		}
    		else {
				$('#total_repairtime_by_type').remove();
    		}
    		// Засварын цагаар - Exca
    		if(datas['exca_repairtime_by_type']){
        		var options = {
					chart: {
				        type: 'pie'
				    },
				    title: {
				        text: 'Экскаватор засварын цагууд'
				    },
				    tooltip: {
				        pointFormat: '{series.name}: <b>{point.percentage:.1f}%</b>'
				    },
				    accessibility: {
				        point: {
				            valueSuffix: '%'
				        }
				    },
				    plotOptions: {
				        pie: {
				            allowPointSelect: true,
				            cursor: 'pointer',
				            dataLabels: {
				                enabled: true,
				                format: '<b>{point.name}</b>: {point.y:.1f} ц',
				                connectorColor: 'silver'
				            }
				        }
				    },
				    series: datas['exca_repairtime_by_type'],
			    }
			    try{
	    			$('#exca_repairtime_by_type').highcharts(options);
	    		}catch(err) {
		           console.log(err.message);
		        }
    		}
    		else {
				$('#exca_repairtime_by_type').remove();
    		}
    		// Засварын цагаар - Dump
    		if(datas['dump_repairtime_by_type']){
        		var options = {
					chart: {
				        type: 'pie'
				    },
				    title: {
				        text: 'Дамп засварын цагууд'
				    },
				    tooltip: {
				        pointFormat: '{series.name}: <b>{point.percentage:.1f}%</b>'
				    },
				    accessibility: {
				        point: {
				            valueSuffix: '%'
				        }
				    },
				    plotOptions: {
				        pie: {
				            allowPointSelect: true,
				            cursor: 'pointer',
				            dataLabels: {
				                enabled: true,
				                format: '<b>{point.name}</b>: {point.y:.1f} ц',
				                connectorColor: 'silver'
				            }
				        }
				    },
				    series: datas['dump_repairtime_by_type'],
			    }
			    try{
	    			$('#dump_repairtime_by_type').highcharts(options);
	    		}catch(err) {
		           console.log(err.message);
		        }
    		}
    		else {
				$('#dump_repairtime_by_type').remove();
    		}
    		// Засварын цагаар - Support
    		if(datas['support_repairtime_by_type']){
        		var options = {
					chart: {
				        type: 'pie'
				    },
				    title: {
				        text: 'Туслах ТТ засварын цагууд'
				    },
				    tooltip: {
				        pointFormat: '{series.name}: <b>{point.percentage:.1f}%</b>'
				    },
				    accessibility: {
				        point: {
				            valueSuffix: '%'
				        }
				    },
				    plotOptions: {
				        pie: {
				            allowPointSelect: true,
				            cursor: 'pointer',
				            dataLabels: {
				                enabled: true,
				                format: '<b>{point.name}</b>: {point.y:.1f} ц',
				                connectorColor: 'silver'
				            }
				        }
				    },
				    series: datas['support_repairtime_by_type'],
			    }
			    try{
	    			$('#support_repairtime_by_type').highcharts(options);
	    		}catch(err) {
		           console.log(err.message);
		        }
    		}
    		else {
				$('#support_repairtime_by_type').remove();
    		}
    		// Зогсолтын мэдээ
    		if(datas['stopped_by_status']){
        		var options = {
					chart: {
				        type: 'column'
				    },
				    title: {
				        text: datas['stopped_by_status_title']
				    },
				    xAxis: {
				        type: 'category'
				    },
				    legend: {
				        enabled: true
				    },
				    plotOptions: {
				        series: {
				            borderWidth: 0,
				            dataLabels: {
				                enabled: true
				            }
				        }
				    },
				    series: datas['stopped_by_status'],
				    drilldown: datas['stopped_by_status_drill'],
			    }
			    try{
	    			$('#stopped_by_status').highcharts(options);
	    		}catch(err) {
		           console.log(err.message);
		        }
    		}
    		else {
				$('#stopped_by_status').remove();
				$('#stopped_by_status_pie').remove();
    		}
    		// Зогсолтын мэдээ
    		if(datas['total_by_status']){
    			// PIE
		        var options = {
					chart: {
				        type: 'pie'
				    },
				    title: {
				        text: "Нийт техник"
				    },
				    tooltip: {
				        pointFormat: '{series.name}: <b>{point.percentage:.1f}%</b>'
				    },
				    accessibility: {
				        point: {
				            valueSuffix: '%'
				        }
				    },
				    plotOptions: {
				        pie: {
				            allowPointSelect: true,
				            cursor: 'pointer',
				            dataLabels: {
				                enabled: true,
				                format: '<b>{point.name}</b>: {point.y:.1f} ш',
				                connectorColor: 'silver'
				            }
				        }
				    },
				    series: datas['total_by_status'],
			    }
			    try{
	    			$('#total_by_status').highcharts(options);
	    		}catch(err) {
		           console.log(err.message);
		        }
	        }
    		else {
				$('#total_by_status').remove();
    		}
    		// Ажилтны TIMESHEET мэдээлэл
    		if(datas['total_timesheet']){
        		var options = {
					chart: {
				        type: 'column'
				    },
				    title: {
				        text: 'Цаг ашиглалт, хүн цаг'
				    },
				    xAxis: {
				        categories: [
				            'Нийт ажиллах хүчин чадал',
				            'Нийт ажилласан',
				        ],
				        crosshair: true
				    },
				    tooltip: {
				        shared: true,
				    },
				    plotOptions: {
				        series: {
				            borderWidth: 0,
				            dataLabels: {
				                enabled: true,
				                format: '{point.y:.1f} ц',
				                style: {
					                fontSize: '11px',
					                fontFamily: 'Verdana, sans-serif'
					            }
				            }
				        }
				    },
				    yAxis: [
					    { // Primary yAxis
					        gridLineWidth: 1,
					        title: {
					            text: 'Хүн цаг',
					        },
					        labels: {
					            format: '{value} х/ц',
					        }
					    },
				    ],
				    series: datas['total_timesheet'],
			    }
			    try{
	    			$('#total_timesheet').highcharts(options);
	    		}catch(err) {
		           console.log(err.message);
		        }
    		}
    		else {
				$('#total_timesheet').remove();
    		}
    		// Timesheet PIE
    		if(datas['total_timesheet_pie']){
        		var options = {
					chart: {
				        type: 'pie'
				    },
				    title: {
				        text: 'Засварын төрлөөр'
				    },
				    tooltip: {
				        pointFormat: '{series.name}: <b>{point.percentage:.1f}%</b>'
				    },
				    accessibility: {
				        point: {
				            valueSuffix: '%'
				        }
				    },
				    plotOptions: {
				        pie: {
				            allowPointSelect: true,
				            cursor: 'pointer',
				            dataLabels: {
				                enabled: true,
				                format: '<b>{point.name}</b>: {point.y:.1f} х/ц',
				                connectorColor: 'silver'
				            }
				        }
				    },
				    series: datas['total_timesheet_pie'],
			    }
			    try{
	    			$('#total_timesheet_pie').highcharts(options);
	    		}catch(err) {
		           console.log(err.message);
		        }
    		}
    		else {
				$('#total_timesheet_pie').remove();
    		}

    		// Planned WO
    		if(datas['work_order_planned']){
        		var options = {
					chart: {
				        type: 'pie'
				    },
				    title: {
				        text: datas['work_order_planned_title']
				    },
				    tooltip: {
				        pointFormat: '{series.name}: <b>{point.percentage:.1f}%</b>'
				    },
				    accessibility: {
				        point: {
				            valueSuffix: '%'
				        }
				    },
				    plotOptions: {
				        pie: {
				            allowPointSelect: true,
				            cursor: 'pointer',
				            dataLabels: {
				                enabled: true,
				                format: '<b>{point.name}</b>: {point.y:.1f} ц',
				                connectorColor: 'silver'
				            }
				        }
				    },
				    series: datas['work_order_planned'],
			    }
			    try{
	    			$('#work_order_planned').highcharts(options);
	    		}catch(err) {
		           console.log(err.message);
		        }
    		}
    		else {
				$('#work_order_planned').remove();
    		}
    		// UnPlanned WO
    		if(datas['work_order_unplanned']){
        		var options = {
					chart: {
				        type: 'pie'
				    },
				    title: {
				        text: datas['work_order_unplanned_title']
				    },
				    tooltip: {
				        pointFormat: '{series.name}: <b>{point.percentage:.1f}%</b>'
				    },
				    accessibility: {
				        point: {
				            valueSuffix: '%'
				        }
				    },
				    plotOptions: {
				        pie: {
				            allowPointSelect: true,
				            cursor: 'pointer',
				            dataLabels: {
				                enabled: true,
				                format: '<b>{point.name}</b>: {point.y:.1f} ц',
				                connectorColor: 'silver'
				            }
				        }
				    },
				    series: datas['work_order_unplanned'],
			    }
			    try{
	    			$('#work_order_unplanned').highcharts(options);
	    		}catch(err) {
		           console.log(err.message);
		        }
    		}
    		else {
				$('#work_order_unplanned').remove();
    		}
    		
    		// ===============================================================
		},
	});
	widgetRegistry.add(
	    'maintenance_dashboard_04', MAINTENANCE_DASHBOARD_04
	);

});
