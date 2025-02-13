odoo.define('mw_technic_equipment.odometer_widget', function (require) {
	"use strict";

	var AbstractField = require('web.AbstractField');
	var QWeb = require('web.core').qweb;
	var core = require('web.core');
	var fields = require('web.basic_fields');
	var field_registry = require('web.field_registry');
	var _lt = core._lt;

	var OdometerWidget = AbstractField.extend({
		description: _lt("Odometer"),
		template: 'OdometerWidget',
		supportedFieldTypes: ['integer', 'float'],
		isQuickEditable: false,

		start: function () {
			// this.$leftMask = this.$('.o_mask').first();
			// this.$rightMask = this.$('.o_mask').last();
			// this.$pieValue = this.$('.o_pie_value');
			return this._super();
		},

		_onInput: function () {
			return;
		},
		_getValue: function () {
			console.log('=this get=', this, this.$el[0].value);
			var $input = this.$el.find('input');
			var val = this.$el[0].value;
			// console.log('===', this.$el[0].value);
			return val;
		},
		_renderReadonly: function () {
			this._super.apply(this, arguments);
			console.log('Im working fuck.')
			if (this.value) {
				this.$el.html(QWeb.render('odometer_widget', {
					'widget':this,
				}));
				var container = this.el.firstElementChild
				var odometer = new Odometer(
				{ 
					auto: false,
					el: container, 
					duration: 900,
					value: 0, 
					theme: 'car',
					animation: 'count',
					format: '(,ddd).d',
				});
				container.innerHTML = this.value;
			}
		},
		_render: function () {
			return this._renderReadonly();
		},
	});

	field_registry.add('odometer_widget', OdometerWidget);
});

odoo.define('mw_technic_equipment.TirePositionWidget', function (require) {
	"use strict";

	var Widget= require('web.Widget');
	var widgetRegistry = require('web.widget_registry');
	var data = require('web.data');
	// var FieldManagerMixin = require('web.FieldManagerMixin');

	var core = require('web.core');
	var QWeb = core.qweb;

	var TirePositionWidget = Widget.extend({
		template : "mw_technic_equipment.TirePositionWidget",
		events: {
			"click .tire_to_open": "to_open",
		},
		init: function (parent, dataPoint) {
			this._super.apply(this, arguments);
			this.data = dataPoint.data;
			this._updateData();
		},
		_updateData: function() {
			var self = this;
			if(self.data.position_format){
				if(self.data.tire_line){
					var ds = new data.DataSet(this, 'technic.equipment');
					ds.call('get_tire_line_datas', ['technic.equipment', self.data["id"]])
						.then(function (res) {
							if(res){
								self.display_data(res,false);
							}
					});
				}
				else{
					var ds = new data.DataSet(this, 'technic.equipment.setting');
					ds.call('get_position_format', ['technic.equipment.setting', self.data["id"]])
						.then(function (res) {
							self.display_data(false,true);
					});
				}
			}
		},

		start: function() {
			this._render();
			return this._super.apply(this, arguments) 
		},

		display_data: function(data, is_setting) {
			var self = this;
			self.$el.html(QWeb.render("mw_technic_equipment.TirePositionWidget", {widget: self}));
			var position_format = self.data.position_format
			console.log('==Technic tire line==');
			// Draw=================
			if(position_format){
				var tbody_tires = document.getElementById("tire_position");
				var tire_number = 1;
				var s = 0;
				var tire_icon = "/mw_technic_equipment/static/src/img/tire.png";
				var lines = position_format.split(",");
				for(var i=0;i<lines.length;i++){
					var tr = document.createElement("tr");
					tr.setAttribute("style", "height:130px");
					var pos = lines[i].split("-");
					var tire_count = parseInt(pos[1])/2;

					// Zvvn dugui
					var td1 = document.createElement("td");
					td1.setAttribute("align", "left");
					for(var j=1;j<=tire_count;j++){
						var str = "";
						var img=document.createElement("img");
						if(data){
							// Тухайн байрлал дээр дугуй байгаа эсэх
							if(tire_number in data){
								str = data[tire_number]['serial'] ? ": "+data[tire_number]['serial'] : '';
								img.setAttribute('data-tire_id', (data[tire_number]['tire_id'] ? data[tire_number]['tire_id'] : ''));
								img.setAttribute('class', "tire_to_open");
								s += 1;
							}
							else{
								img.setAttribute('class', "empty_tire");
							}
						}
						else{
							str = "";
						}
						img.setAttribute('src', tire_icon);
						img.setAttribute('title', tire_number.toString() + str);
						img.setAttribute('height', '100px');
						img.setAttribute('width', '40px');
						td1.appendChild(img);
						tire_number += 1;
					}
					tr.appendChild(td1);

					// Baruun dugui
					var td2 = document.createElement("td");
					td2.setAttribute('class', 'right_tires');
					for(var j=1;j<=tire_count;j++){
						var str = "";
						var img=document.createElement("img");
						if(data){
							// Тухайн байрлал дээр дугуй байгаа эсэх
							if(tire_number in data){
								str = data[tire_number]['serial'] ? ": "+data[tire_number]['serial'] : '';
								img.setAttribute('data-tire_id', (data[tire_number]['tire_id'] ? data[tire_number]['tire_id'] : ''));
								img.setAttribute('class', "tire_to_open");
								s += 1;
							}
							else{
								img.setAttribute('class', "empty_tire");
							}
						}
						else{
							str = "";
						}
						img.setAttribute('src', tire_icon);
						img.setAttribute('title', tire_number.toString() + str);
						img.setAttribute('height', '100px');
						img.setAttribute('width', '40px');
						td2.appendChild(img);
						tire_number += 1;
					}
					tr.appendChild(td2);
					// Мөр нэмэх
					if(tbody_tires){
						tbody_tires.appendChild(tr);
					}
				}
			}
		},
		to_open: function(event) {
			var t_id = event.toElement.dataset.tire_id;
			console.log("tire id = ",t_id);
			this.do_action({
				type: 'ir.actions.act_window',
				res_model: "technic.tire",
				res_id: parseInt(t_id),
				views: [[false, 'form']],
				target: 'current'
			});
		},
	});
	widgetRegistry.add(
		'tire_position_widget', TirePositionWidget
	);
	return TirePositionWidget
});

odoo.define('mw_technic_equipment.tire_inspection_widget', function (require) {
	"use strict";

	var Widget= require('web.Widget');
	var widgetRegistry = require('web.widget_registry');
	var data = require('web.data');
	var FieldManagerMixin = require('web.FieldManagerMixin');

	var core = require('web.core');
	var QWeb = core.qweb;

	// Дугуйн элэгдэл 
	var TireInspectionWidget = Widget.extend(FieldManagerMixin, {
		template : "mw_technic_equipment.TireInspectionWidget",
		init: function (parent, dataPoint) {
			this._super.apply(this, arguments);
			this.data = dataPoint.data;
		},
		start: function() {
			var self = this;
			var ds = new data.DataSet(this, 'technic.tire');
			ds.call('get_inspection_datas', ['technic.tire', self.data["id"]])
				.then(function (res) {
					self.display_data(res);
			});
		},
		display_data: function(data) {
			var self = this;
			console.log("=======Tire inspection widget=====", data);
			self.$el.html(QWeb.render("mw_technic_equipment.TireInspectionWidget", {widget: self}));
			var datas = data
			if(datas){
				var options = {
					chart: {
						zoomType: 'x'
					},
					title: {
						text: 'Дугуйн элэгдлийн граф'
					},
					xAxis: {
						type: 'datetime'
					},
					yAxis: [{ // Primery
						min: 0,
						title: {
							text: 'Хээний элэгдэл',
						},
						labels: {
							format: '{value} %',
						},
					}, 
					{ // Second yAxis
						title: {
							text: 'Мото/ц, КМ-ээр элэгдсэн',
						},
						labels: {
							format: '{value} %',
						},
						opposite: true,
					}],
					legend: {
						enabled: true
					},
					plotOptions: {
						area: {
							fillColor: {
								linearGradient: {
									x1: 0,
									y1: 0,
									x2: 0,
									y2: 1
								},
								stops: [
									[0, Highcharts.getOptions().colors[0]],
									[1, Highcharts.Color(Highcharts.getOptions().colors[0]).setOpacity(0).get('rgba')]
								]
							},
							marker: {
								radius: 2
							},
							lineWidth: 1,
							states: {
								hover: {
									lineWidth: 1
								}
							},
							threshold: null
						}
					},
					series: datas,
				}
				try{
					$('#tire_inspection_div').highcharts(options);
				}catch(err) {
				   console.log(err.message);
				}
			}
			else {
				$('#tire_inspection_div').remove();
			}
		},

	});
	widgetRegistry.add(
		'tire_inspection_widget', TireInspectionWidget
	);
	return TireInspectionWidget
});

// =====================================
// Компонентийн Widget - Техник дээрх
odoo.define('mw_technic_equipment.technic_component_detail_viewer', function (require) {
	"use strict";

	// Click дарж байрлал авах
	$(document).on('click', 'div.part_number', function(event){
		console.log("click component");
	});

	var Widget= require('web.Widget');
	var widgetRegistry = require('web.widget_registry');
	var data = require('web.data');
	var FieldManagerMixin = require('web.FieldManagerMixin');
	var Session = require('web.session');

	var core = require('web.core');
	var QWeb = core.qweb;

	var TechnicComponentDetailViewer = Widget.extend(FieldManagerMixin, {
		template : "mw_technic_equipment.TechnicComponentDetailViewer",
		init: function (parent, dataPoint) {
			this._super.apply(this, arguments);
			this.data = dataPoint.data;
			$("head").append('<script type="text/javascript" src="highchart_libs_module/static/libs/exporting.js"></script>');
   			$("head").append('<script type="text/javascript" src="highchart_libs_module/static/libs/export-data.js"></script>');
   			$("head").append('<script type="text/javascript" src="highchart_libs_module/static/libs/drilldown.js"></script>');
		},
		start: function() {
			var self = this;
			var ds = new data.DataSet(this, 'technic.equipment');
			ds.call('get_component_datas', ['technic.equipment', self.data["id"]])
				.then(function (res) {
					self.display_data(res);
			});
		},
		display_data: function(data) {
			var self = this;
			var datas = data;
			console.log("=====technic component===", datas);
			self.$el.html(QWeb.render("mw_technic_equipment.TechnicComponentDetailViewer", {widget: self}));
			// DATA zurax
			if(datas.length > 0){
				var id = self.data["id"];
				var pic_width = 650;
				var pic_height = 400;
				var url = Session.url('/web/binary/image', {model: 'technic.equipment', field: 'img_of_parts', id: id});
				if(url){
					var img = "<img src="+url+" style='z-index:-1;' class='img_detail' name='img_of_parts_2'></div>";
					$('#viewer_container').append(img);
				}
				// Width, Height авах
				if(self.data.pic_width > 0){
					pic_width = self.data.pic_width;
				}
				if(self.data.pic_height > 0){
					pic_height = self.data.pic_height;
				}
				console.log('==w h ',pic_width, pic_height);
				var content = '';
				for(var i=0;i<datas.length;i++){
					var line_id = datas[i]['line_id'];
					var number = datas[i]['number'];
					var top = datas[i]['top']-10;
					var left = datas[i]['left']-10;
					var title = "<h5>"+datas[i]['title'] +"</h5><br/>\
								<table>\
								<tr><td width=65%><b>Нийт мото/цаг:</b></td><td align=right width=35%>"+ datas[i]['total_odometer']+"</td></tr>\
								<tr><td><b>Засварт орсон мото/цаг:</b></td><td align=right>"+ datas[i]['last_odometer']+"</td></tr>\
								<tr><td><b>Ажилласан мото/цаг:</b></td><td align=right>"+ datas[i]['diff']+"</td></tr></table>";
					// Create
					var div = $("<div class='part_number' style='top:"+top+"px;left:"+left+"px' title='"+title+"'>"+number+"</div>");
					div.tooltip({'html': true,
								 'delay': {'show':100,'hide':200}});
					$('#viewer_container').append(div)
				}
				$("img[name='img_of_parts_2']").width(pic_width);
				$("img[name='img_of_parts_2']").height(pic_height);
			}
			else {
				$('#viewer_container').remove();
			}
		},

	});
	widgetRegistry.add(
		'technic_component_detail_viewer', TechnicComponentDetailViewer
	);
});

// Компонентийн Widget - Тохиргоон дээрх
odoo.define('mw_technic_equipment.component_detail_viewer', function (require) {
	"use strict";

	// Click дарж байрлал авах
	$(document).on('click', 'div.detail_view', function(event){
		var left = event.pageX - $(this).offset().left;
		var top = event.pageY - $(this).offset().top;
		$('#pos_left').text("Postion X: "+left.toFixed(1)+" px");
		$('#pos_top').text("Postion Y: "+top.toFixed(1)+" px");
	});

	var Widget= require('web.Widget');
	var widgetRegistry = require('web.widget_registry');
	var data = require('web.data');
	var FieldManagerMixin = require('web.FieldManagerMixin');
	var Session = require('web.session');

	var core = require('web.core');
	var QWeb = core.qweb;

	var ComponentDetailViewer = Widget.extend(FieldManagerMixin, {
		template : "mw_technic_equipment.ComponentDetailViewer",
		init: function (parent, dataPoint) {
			this._super.apply(this, arguments);
			this.data = dataPoint.data;
		},
		start: function() {
			var self = this;
			var ds = new data.DataSet(this, 'technic.equipment.setting');
			ds.call('get_datas', ['technic.equipment.setting', self.data["id"]])
				.then(function (res) {
					self.display_data(res);
			});
		},
		display_data: function(data) {
			var self = this;
			console.log("====setting===Component detail=====", data, self.data);
			self.$el.html(QWeb.render("mw_technic_equipment.ComponentDetailViewer", {widget: self}));
			var datas = data;
			var id = self.data["id"];
			var pic_width = 650;
			var pic_height = 400;
			// Width, Height авах
			if(self.data.pic_width > 0){
				pic_width = self.data.pic_width;
			}
			if(self.data.pic_height > 0){
				pic_height = self.data.pic_height;
			}
			// DATA zurax
			if(datas.length > 0){
				var content = '';
				for(var i=0;i<datas.length;i++){
					var number = datas[i]['number'];
					var title = datas[i]['title'];
					var top = datas[i]['top']-10;
					var left = datas[i]['left']-10;
					var div = "<div id="+id+" class='part_number' style='top:"+top+"px;left:"+left+"px' title='"+title+"'>"+number+"</div>";
					content += div;
				}
				$('#viewer_container').append(content);
				$("img[name='img_of_parts']").width(pic_width);
				$("img[name='img_of_parts']").height(pic_height);
			}
			// else {
			// 	$('#viewer_container').remove();
   //  		}
		},

	});
	widgetRegistry.add(
		'component_detail_viewer', ComponentDetailViewer
	);
});
