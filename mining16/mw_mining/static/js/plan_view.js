odoo.define('mw_mining.plan_view', function (require) {
    "use strict";
    var Widget= require('web.Widget');
    var widgetRegistry = require('web.widget_registry');
    var data = require('web.data');
    var FieldManagerMixin = require('web.FieldManagerMixin');

    var core = require('web.core');
    var QWeb = core.qweb;

    var miningplanview= Widget.extend(FieldManagerMixin, {
		template : "mw_mining.plan_view",
		events: {
            "click .plan_cell": "go_to",  
            "click #tbbk_download_pdf": "download_pdf", 
            "click .tablink": "go_to_tab", 
        },
		init: function (parent, dataPoint) {
			this._super.apply(this, arguments);
            this.data = dataPoint.data;
            console.log('-----------------mining_plan_view');
			// $("head").append('<script type="text/javascript" src="mw_mining/static/libs/jspdf.js"></script>');
        },
        start: function () {
            var self = this;
            console.log('===', self);
            if (self.data["date_start"]!=undefined && self.data["date_end"]!=undefined && self.data["branch_id"]['data'] != undefined && self.data["group_type"]!=undefined && self.data["plan_type"] != undefined){
                var ds = new data.DataSet(this, 'mining.plan.view');
                console.log('self.data',self.data);
                ds.call('get_datas', ['mining.plan.view', self.data["date_start"], self.data["date_end"], self.data["branch_id"]['data']['id'] , self.data["group_type"], self.data["view_type"], self.data["plan_type"] ])
                    .then(function (res) {
                        self.display_data(res);
                });
            }
            
        },
		display_data: function(data) {
			var self = this;
    		self.date_cols = data.date_cols;
            self.plan_lines = data.plan_lines;
            self.plan_type = data.plan_type;
            console.log("=======DRAW=====", self);
            self.$el.html(QWeb.render("mw_mining.plan_view", {widget: self}));
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
	    'mining_plan_view', miningplanview
    );
});