odoo.define('mw_mining.mining_motohour', function (require) {
    "use strict";
    var Widget= require('web.Widget');
    var widgetRegistry = require('web.widget_registry');
    var data = require('web.data');
    var FieldManagerMixin = require('web.FieldManagerMixin');

    var core = require('web.core');
    var QWeb = core.qweb;
    var dialogs = require('web.view_dialogs');
    var TechnicMotohour = Widget.extend(FieldManagerMixin, {
        template : "mw_mining.TechnicMotohour",
        events: {
            "click .oe_technic_row td": "go_to",
            // "click .oe_technic_motohour_fullscreen img": "launchFullscreen",
            // "click .oe_technic_motohour_refresh img": "launchRefresh",
            "click .oe_technic_motohour_timeline_head_cause div": "cause_go_to",
        },
   
        init: function (parent, dataPoint) {
            this._super.apply(this, arguments);
            this.data = dataPoint.data;
            this.query_data = false;
            this.motohour_lines = [];
            this.mining_mh_causes = [];
            // this.can_write = 'can_write' in this.attrs ? JSON.parse(this.attrs.can_write) : true;

        },
        _render: function () {
            var self = this;
            var get_data = this.data;
            var data_ids = get_data.id;
            var ds = new data.DataSet(this, 'mining.daily.entry');
        
            ds.call('get_motohour_js', [data_ids]).then(function(result) {
                // var metadata = result[0];
                if ( result!=undefined){
                    self.query_data = result[0];
                    self.mining_mh_causes = result['mining_mh_causes'];
                    self.motohour_lines = result['motohour_line'];
                    var times = [];
                    
                    if (get_data.shift=='day'){
                        times=['07:00','08:00','09:00','10:00','11:00','12:00','13:00','14:00','15:00','16:00','17:00','18:00']
                    }
                    if (get_data.shift=='night'){
                        times=['19:00','20:00','21:00','22:00','23:00','00:00','01:00','02:00','03:00','04:00','05:00','06:00']
                    }
                    self.times = times;
                    self.$el.html(QWeb.render("mw_mining.TechnicMotohour", {widget: self}));
                    self.display_data_res(result);
                }
                // return $.when(def, self._super.apply(self, arguments));
            });
        },
        start: function () {
            var self = this;
            this._render();
            return this._super.apply(this, arguments);
        },
        
        display_data_res: function(res_data){
            var self = this;
            var get_data = this.data;
            var get_shift = get_data.shift;
            console.log('display_data_res-----------display_data_res');
            _.each(res_data['mining_mh_causes'], function(details) {
                $('[data-cause-name="' + details.name + '"]').css
                                    ({  'border-top':'4px solid '+details.color,
                                        'background-color': self.hex2rgb(self.nameToHex(details.color)),
                                    });
                $('[data-cause-name="' + details.name + '"]').attr('title'
                                    ,details.cause_name);
            });

            _.each(res_data['motohour_line'], function(motohour) {
                    var i = 0;
                    _.each(motohour.causes, function(item){

                        var time_start = item.r_start_time;
                        var how_start = true;
                        i++;
                        // if (i == motohour.causes.length && real_how_start == true){
                        //     how_start = false;
                        // }
                        if (how_start==true){
                            var st_time = item.r_start_time;
                            var hours = parseInt(st_time);
                            var minutes = parseInt((st_time - hours)*60);
                            if (((st_time - hours)*60 - minutes)>0.5) minutes++;
                            if (get_shift=='day'){hours -= 7.0;}
                            if (get_shift=='night'){hours -= 19.0;}
                            time_start = hours*60+minutes;
                            st_time = item.diff_time;
                            hours = parseInt(st_time);
                            minutes = parseInt((st_time - hours)*60);
                            if (((st_time - hours)*60 - minutes)>0.5) minutes++;
                            var diff_time = hours*60 + minutes;
                            $('[data-start-time="' + item.line_id+'"]').html("<p data-id='"+motohour.motohour+"'  style='line-height: normal;'>"+item.cause+"<br/>("+self.format_client(item.start_time)+")</p>");
                            $('[data-start-time="' + item.line_id + '"]').css
                                ({'width':diff_time,
                                    'border-top':'4px solid '+item.color,
                                    'background-color': self.hex2rgb(self.nameToHex(item.color)),
                                    'left':time_start+'px',
                                    'height': '28px'
                                });
                            var r_diff_time = item.start_time+item.diff_time;
                            if (r_diff_time>23){r_diff_time -= 24; }
                            var desc = item.description;
                            if (desc == 'undefined / false') desc = '';
                            $('[data-start-time="' + item.line_id+'"]').attr('title'
                                ,item.cause_name+' ('+self.format_client(item.start_time)+'-'+self.format_client(r_diff_time)+')'
                                +'\n'+' WORK TIME '+self.format_client(item.diff_time)+'\n'+desc);
                        }
                    });
                    // this.$('[data-first_odometer_value="'+motohour.motohour+'"]').html(motohour.first_odometer_value.toFixed(1));
                    // this.$('[data-last_odometer_value="'+motohour.motohour+'"]').html(motohour.last_odometer_value.toFixed(1));
                    // this.$('[data-work_diff_time="'+motohour.motohour+'"]').html(self.format_client(motohour.work_diff_time));
                    // this.$('[data-diff_odometer_value="'+motohour.motohour+'"]').html(motohour.diff_odometer_value.toFixed(1));
                    // this.$('[data-motohour_time="'+motohour.motohour+'"]').html(motohour.motohour_time.toFixed(1));
                    // this.$('[data-production_time="'+motohour.motohour+'"]').html(self.format_client(motohour.production_time));
                    // this.$('[data-repair_time="'+motohour.motohour+'"]').html(self.format_client(motohour.repair_time));
                    // this.$('[data-work_time="'+motohour.motohour+'"]').html(self.format_client(motohour.work_time));
            });

        },
       
        go_to: function(event) {
            var self = this;
            var line_id = $(event.target).data('id') || false;
            // event.stopPropagation();
            // event.preventDefault();
            console.log('query_data',this.query_data);
            new dialogs.FormViewDialog(this, {
                type: 'ir.actions.act_window',
                res_model: 'mining.motohour.entry.line',
                res_id: line_id,
                view_type: 'form',
                view_mode: 'form',
                views: [[false, 'form']],
                target: 'new',
                readonly: (this.query_data=='draft'),
                on_saved: this.trigger_up.bind(this, 'reload'),
            }).open();
        },
        cause_go_to: function(event){
            var cause_id = JSON.parse($(event.target).data("cause_id"));
            var self = this;
            _.each(self.mining_mh_causes, function(details) {
                if (details.id == cause_id){
                    if (self.clicked_cause.indexOf(details.name) == -1){
                        this.$('[data-cause-name="' + details.name + '"]').css({  
                            'border-top':'0px solid ',
                            'border-bottom':'7px solid '+details.color,
                        });
                        self.clicked_cause.push(details.name);
                    }else{
                        this.$('[data-cause-name="' + details.name + '"]').css({  
                            'border-top':'4px solid '+details.color,
                            'border-bottom':'0px solid ',
                        });
                        self.clicked_cause.pop(details.name);
                    }
                }
            });
            _.each(self.motohour_lines, function(motohour) {
                        _.each(motohour.causes, function(item){
                            if (self.clicked_cause.length==0){
                                this.$('[data-start-time="' + item.line_id+'"]').show();
                            }else{
                                if (self.clicked_cause.indexOf(item.cause) != -1){
                                    this.$('[data-start-time="' + item.line_id+'"]').show();
                                }else{
                                    this.$('[data-start-time="' + item.line_id+'"]').hide();
                                }
                            }
                        });
            });
            
        },
        query_sheets: function() {
            var self = this;
            if (self.updating)
                return;
            var commands = this.field_manager.get_field_value("motohour_line");
            this.res_o2m_drop.add(new instance.web.Model(this.view.model).call("resolve_2many_commands", ["motohour_line", commands, [], 
                    new instance.web.CompoundContext()]))
                .then(function(result) {
                self.querying = true;
                self.set({sheets: result});
                self.querying = false;
            });
        },
        
        // updateState: function (dataPoint) {
        //     var self = this;
        //     console.log('dataPoint.data',dataPoint.data);
        //     // if(dataPoint.data.group_by && dataPoint.data.date_from && dataPoint.data.date_to){
        //     //     var group_by = dataPoint.data.group_by;
        //     //     var date_from = dataPoint.data.date_from;
        //     //     var date_to = dataPoint.data.date_to;
                
        //         self.get_locations(group_by, date_from, date_to);
        //     // }
        //      this.display_data(false);
        // },
        

        
        real_time_display:function(now_real_how_start){
            self = this;
            var tagName = document.getElementsByTagName('img');
            var leftbar = 0;
            for (var i = 0; i < tagName.length; i++) {
                if (tagName[i].className =='fs_button'){ leftbar=i;}
            }
            if (self.real_timer == null && tagName[leftbar]!=undefined && now_real_how_start==true){
                var real_timer = setInterval(function(){
                    d = new Date();
                     self.query_sheets();
                     if (tagName[leftbar]!=undefined || now_real_how_start==false){
                        clearInterval(real_timer);
                     }
                },300000);
            }
        },
        // display_data: function(get_data) {
        //     var self = this;
        //     console.log("=======DRAW=====", get_data);
            
        //     var get_data = data;
        //     var this_data = this.data;
        //     this.mining_mh_causes = get_data['mining_mh_causes'];
        //     this.motohour_lines = get_data.motohour_line;
        //     this.$el.html(QWeb.render("mw_mining.TechnicMotohour", {widget: this}));
        //     // var cause_ids = lines[0].motohour_cause_line;
        //     // _.each(cause_ids, function(value){
        //     //         _.each(cause_details, function(res){
        //     //             if(res.id==value){
        //     //                 var temp = {
        //     //                 'start_time':res.start_time
        //     //                 ,'r_start_time':res.r_start_time
        //     //                 ,'description':res.work_order_id[1]+' / '+res.job_description
        //     //                 ,'diff_time': res.diff_time
        //     //                 , 'cause':res.cause_id[1]
        //     //                 , 'color': res.color
        //     //                 , 'line_id':res.id
        //     //                 , 'cause_name':res.cause_name}
        //     //                 causes.push(temp);
        //     //             }
        //     //         });
        //     //     });
        //     var today_now = new Date();
        //     var get_shift = this_data.shift;
        //     var get_date = this_data.date;
        //     var real_how_start = false;
        //     var time_value = parseInt(today_now.toString('HH'));

        //     if (get_date == today_now.toString('yyyy-MM-dd')){
        //         if (get_shift=='day' && (7<=time_value && time_value<19)){
        //             real_how_start = true;
        //         }
        //         if (get_shift=='night' && ((19<=time_value && time_value<=23) || (0<=time_value && time_value<7)) ){
        //             real_how_start = true;
        //         }
        //     }
        //     _.each(self.mining_mh_causes, function(details) {
        //         this.$('[data-cause-name="' + details.name + '"]').css
        //                             ({  'border-top':'4px solid '+details.color,
        //                                 'background-color': self.hex2rgb(self.nameToHex(details.color)),
        //                             });
        //         this.$('[data-cause-name="' + details.name + '"]').attr('title'
        //                             ,details.cause_name);
        //     });



        //     // if(self.timer==null && real_how_start==true){
        //     //     d = new Date();
        //     //     left_time = parseInt(d.toString('HH'));
        //     //     if (get_shift=='day'){left_time -=7.0;}
        //     //     if (get_shift=='night' && left_time>7){left_time -= 19.0;}
        //     //     left_time = left_time*60+parseInt(d.toString('mm'));
        //     //      _.each(motohour_lines, function(motohour) {
        //     //                 if (motohour.causes.length>0){
        //     //                     item = motohour.causes[motohour.causes.length-1];
        //     //                         st_time = item.r_start_time;
        //     //                         hours = parseInt(st_time);
        //     //                         minutes = parseInt((st_time - hours)*60);
        //     //                         if (((st_time - hours)*60 - minutes)>0.5) minutes++;
        //     //                         if (get_shift=='day'){hours -= 7.0;}
        //     //                         if (get_shift=='night'){hours -= 19.0;}
        //     //                         time_start = hours*60+minutes;
        //     //                         diff_time = left_time - time_start;
        //     //                         this.$('[data-start-time="' + item.line_id+'"]').html(item.cause+'<br> <span>('+self.format_client(item.start_time)+')</span>');
        //     //                         this.$('[data-start-time="' + item.line_id + '"]').css
        //     //                         ({'width':diff_time,
        //     //                             'border-top':'4px solid '+item.color,
        //     //                             'background-color': self.hex2rgb(self.nameToHex(item.color)),
        //     //                             'left':time_start+'px',
        //     //                             'height': '28px'
        //     //                         });
        //     //                         hours = parseInt(d.toString('HH'));
        //     //                         minutes = parseInt(d.toString('mm'));
        //     //                         st_time = hours + minutes/60;
        //     //                         desc = item.description;
        //     //                         if (desc == 'undefined / false') desc = '';
        //     //                         this.$('[data-start-time="' + item.line_id+'"]').attr('title'
        //     //                         ,item.cause_name+' ('+self.format_client(item.start_time)+'-'+self.format_client(st_time)+')'
        //     //                         +'\n'+' WORK TIME '+self.format_client(st_time-item.start_time)+'\n'+desc);
        //     //                 }
        //     //         });
        //     //     this.$('[class="'+'oe_technic_motohour_cursor'+'"]').css
        //     //                     ({'left':left_time-20.5,});
        //     //     lin_height = this.$('[class="'+'oe_technic_motohour'+'"]').height() - 63;
        //     //     this.$('[class="'+'oe_technic_motohour_cursor_line'+'"]').css
        //     //                     ({'left':(left_time),
        //     //                         'height':lin_height });
        //     //     this.$('[class="'+'oe_technic_motohour_cursor_indicator'+'"]').html(d.toString('HH:mm'));
                
        //     //     var timer = setInterval(function(){
        //     //             d = new Date();
        //     //             left_time = parseInt(d.toString('HH'));
        //     //             if (get_shift=='day'){left_time -=7.0;}
        //     //             if (get_shift=='night' && left_time>7){left_time -= 19.0;}
        //     //             left_time = left_time*60+parseInt(d.toString('mm'));
        //     //             if (left_time>719 || real_how_start==false){
        //     //                 clearInterval(timer);
        //     //                 real_how_start =false;
        //     //             }
        //     //             _.each(motohour_lines, function(motohour) {
        //     //                 if (motohour.causes.length>0 && real_how_start==true){
        //     //                     item = motohour.causes[motohour.causes.length-1];
        //     //                         st_time = item.r_start_time;
        //     //                         hours = parseInt(st_time);
        //     //                         minutes = parseInt((st_time - hours)*60);
        //     //                         if (((st_time - hours)*60 - minutes)>0.5) minutes++;
        //     //                         if (get_shift=='day'){hours -= 7.0;}
        //     //                         if (get_shift=='night'){hours -= 19.0;}
        //     //                         time_start = hours*60+minutes;
        //     //                         diff_time = left_time - time_start;
        //     //                         this.$('[data-start-time="' + item.line_id+'"]').html(item.cause+'<br> <span>('+self.format_client(item.start_time)+')</span>');
        //     //                         this.$('[data-start-time="' + item.line_id + '"]').css
        //     //                         ({'width':diff_time,
        //     //                             'border-top':'4px solid '+item.color,
        //     //                             'background-color': self.hex2rgb(self.nameToHex(item.color)),
        //     //                             'left':time_start+'px',
        //     //                             'height': '28px'
        //     //                         });
        //     //                         hours = parseInt(d.toString('HH'));
        //     //                         minutes = parseInt(d.toString('mm'));
        //     //                         st_time = hours + minutes/60;
        //     //                         desc = item.description;
        //     //                         if (desc == 'undefined / false') desc = '';
        //     //                         this.$('[data-start-time="' + item.line_id+'"]').attr('title'
        //     //                         ,item.cause_name+' ('+self.format_client(item.start_time)+'-'+self.format_client(st_time)+')'
        //     //                         +'\n'+' WORK TIME '+self.format_client(st_time-item.start_time)+'\n'+desc);
        //     //                 }
        //     //         });
        //     //             this.$('[class="'+'oe_technic_motohour_cursor'+'"]').animate
        //     //                     ({'left':left_time-20.5,
        //     //                     });
        //     //             lin_height = this.$('[class="'+'oe_technic_motohour'+'"]').height() - 63;
        //     //             this.$('[class="'+'oe_technic_motohour_cursor_line'+'"]').animate
        //     //                     ({'left':(left_time),
        //     //                         'height':lin_height
        //     //                     });
        //     //             this.$('[class="'+'oe_technic_motohour_cursor_indicator'+'"]').html(d.toString('HH:mm'));
        //     //         }, 300000);
                    
        //     // }else{
        //     //     clearInterval(timer);
        //     //     _.each(motohour_lines, function(motohour) {
        //     //         if (motohour.causes.length>0){
        //     //             item = motohour.causes[motohour.causes.length-1];
        //     //             if (item.diff_time==0){
        //     //                 this.$('[data-start-time="' + item.line_id + '"]').hide();
        //     //             }
        //     //         }
        //     //     });
        //     //     real_how_start = false;
        //     //     this.$('[class="'+'oe_technic_motohour_cursor'+'"]').hide();
        //     //     this.$('[class="'+'oe_technic_motohour_cursor_line'+'"]').hide();
        //     // }


        //     _.each(this.motohour_lines, function(motohour) {
        //             i = 0;
        //             console.log('motohour',motohour);
        //             // _.each(motohour.causes, function(item){
        //             //     time_start = item.r_start_time;
        //             //     how_start = true;
        //             //     i++;
        //             //     if (i == motohour.causes.length && real_how_start == true){
        //             //         how_start = false;
        //             //     }
        //             //     if (how_start==true){
        //             //         st_time = item.r_start_time;
        //             //         hours = parseInt(st_time);
        //             //         minutes = parseInt((st_time - hours)*60);
        //             //         if (((st_time - hours)*60 - minutes)>0.5) minutes++;
        //             //         if (get_shift=='day'){hours -= 7.0;}
        //             //         if (get_shift=='night'){hours -= 19.0;}
        //             //         time_start = hours*60+minutes;
        //             //         st_time = item.diff_time;
        //             //         hours = parseInt(st_time);
        //             //         minutes = parseInt((st_time - hours)*60);
        //             //         if (((st_time - hours)*60 - minutes)>0.5) minutes++;
        //             //         diff_time = hours*60 + minutes
        //             //         this.$('[data-start-time="' + item.line_id+'"]').html(item.cause+'<br> <span>('+self.format_client(item.start_time)+')</span>');
        //             //         this.$('[data-start-time="' + item.line_id + '"]').css
        //             //             ({'width':diff_time,
        //             //                 'border-top':'4px solid '+item.color,
        //             //                 'background-color': self.hex2rgb(self.nameToHex(item.color)),
        //             //                 'left':time_start+'px',
        //             //                 'height': '28px'
        //             //             });
        //             //         r_diff_time = item.start_time+item.diff_time;
        //             //         if (r_diff_time>23){r_diff_time -= 24; }
        //             //         desc = item.description;
        //             //         if (desc == 'undefined / false') desc = '';
        //             //         this.$('[data-start-time="' + item.line_id+'"]').attr('title'
        //             //             ,item.cause_name+' ('+self.format_client(item.start_time)+'-'+self.format_client(r_diff_time)+')'
        //             //             +'\n'+' WORK TIME '+self.format_client(item.diff_time)+'\n'+desc);
        //             //     }
        //             // });
        //             // this.$('[data-first_odometer_value="'+motohour.motohour+'"]').html(motohour.first_odometer_value.toFixed(1));
        //             // this.$('[data-last_odometer_value="'+motohour.motohour+'"]').html(motohour.last_odometer_value.toFixed(1));
        //             // this.$('[data-work_diff_time="'+motohour.motohour+'"]').html(self.format_client(motohour.work_diff_time));
        //             // this.$('[data-diff_odometer_value="'+motohour.motohour+'"]').html(motohour.diff_odometer_value.toFixed(1));
        //             // this.$('[data-motohour_time="'+motohour.motohour+'"]').html(motohour.motohour_time.toFixed(1));
        //             // this.$('[data-production_time="'+motohour.motohour+'"]').html(self.format_client(motohour.production_time));
        //             // this.$('[data-repair_time="'+motohour.motohour+'"]').html(self.format_client(motohour.repair_time));
        //             // this.$('[data-work_time="'+motohour.motohour+'"]').html(self.format_client(motohour.work_time));
        //     });
        //     self.real_time_display(real_how_start);
        // },

        format_client:function(value){
    var pattern = '%02d:%02d';
    if (value < 0) {
        value = Math.abs(value);
        pattern = '-' + pattern;
    }
    var hour = Math.floor(value);
    var min = Math.round((value % 1) * 60);
    if (min === 60){
        min = 0;
        hour = hour + 1;
    }
    return _.str.sprintf(pattern, hour, min);
},

        nameToHex: function(colour) {
            var colours = {
                "aliceblue": "#f0f8ff",
                "antiquewhite": "#faebd7",
                "aqua": "#00ffff",
                "aquamarine": "#7fffd4",
                "azure": "#f0ffff",
                "beige": "#f5f5dc",
                "bisque": "#ffe4c4",
                "black": "#000000",
                "blanchedalmond": "#ffebcd",
                "blue": "#0000ff",
                "blueviolet": "#8a2be2",
                "brown": "#a52a2a",
                "burlywood": "#deb887",
                "cadetblue": "#5f9ea0",
                "chartreuse": "#7fff00",
                "chocolate": "#d2691e",
                "coral": "#ff7f50",
                "cornflowerblue": "#6495ed",
                "cornsilk": "#fff8dc",
                "crimson": "#dc143c",
                "cyan": "#00ffff",
                "darkblue": "#00008b",
                "darkcyan": "#008b8b",
                "darkgoldenrod": "#b8860b",
                "darkgray": "#a9a9a9",
                "darkgreen": "#006400",
                "darkkhaki": "#bdb76b",
                "darkmagenta": "#8b008b",
                "darkolivegreen": "#556b2f",
                "darkorange": "#ff8c00",
                "darkorchid": "#9932cc",
                "darkred": "#8b0000",
                "darksalmon": "#e9967a",
                "darkseagreen": "#8fbc8f",
                "darkslateblue": "#483d8b",
                "darkslategray": "#2f4f4f",
                "darkturquoise": "#00ced1",
                "darkviolet": "#9400d3",
                "deeppink": "#ff1493",
                "deepskyblue": "#00bfff",
                "dimgray": "#696969",
                "dodgerblue": "#1e90ff",
                "firebrick": "#b22222",
                "floralwhite": "#fffaf0",
                "forestgreen": "#228b22",
                "fuchsia": "#ff00ff",
                "gainsboro": "#dcdcdc",
                "ghostwhite": "#f8f8ff",
                "gold": "#ffd700",
                "goldenrod": "#daa520",
                "gray": "#808080",
                "green": "#008000",
                "greenyellow": "#adff2f",
                "honeydew": "#f0fff0",
                "hotpink": "#ff69b4",
                "indianred ": "#cd5c5c",
                "indigo": "#4b0082",
                "ivory": "#fffff0",
                "khaki": "#f0e68c",
                "lavender": "#e6e6fa",
                "lavenderblush": "#fff0f5",
                "lawngreen": "#7cfc00",
                "lemonchiffon": "#fffacd",
                "lightblue": "#add8e6",
                "lightcoral": "#f08080",
                "lightcyan": "#e0ffff",
                "lightgoldenrodyellow": "#fafad2",
                "lightgrey": "#d3d3d3",
                "lightgreen": "#90ee90",
                "lightpink": "#ffb6c1",
                "lightsalmon": "#ffa07a",
                "lightseagreen": "#20b2aa",
                "lightskyblue": "#87cefa",
                "lightslategray": "#778899",
                "lightsteelblue": "#b0c4de",
                "lightyellow": "#ffffe0",
                "lime": "#00ff00",
                "limegreen": "#32cd32",
                "linen": "#faf0e6",
                "magenta": "#ff00ff",
                "maroon": "#800000",
                "mediumaquamarine": "#66cdaa",
                "mediumblue": "#0000cd",
                "mediumorchid": "#ba55d3",
                "mediumpurple": "#9370d8",
                "mediumseagreen": "#3cb371",
                "mediumslateblue": "#7b68ee",
                "mediumspringgreen": "#00fa9a",
                "mediumturquoise": "#48d1cc",
                "mediumvioletred": "#c71585",
                "midnightblue": "#191970",
                "mintcream": "#f5fffa",
                "mistyrose": "#ffe4e1",
                "moccasin": "#ffe4b5",
                "navajowhite": "#ffdead",
                "navy": "#000080",
                "oldlace": "#fdf5e6",
                "olive": "#808000",
                "olivedrab": "#6b8e23",
                "orange": "#ffa500",
                "orangered": "#ff4500",
                "orchid": "#da70d6",
                "palegoldenrod": "#eee8aa",
                "palegreen": "#98fb98",
                "paleturquoise": "#afeeee",
                "palevioletred": "#d87093",
                "papayawhip": "#ffefd5",
                "peachpuff": "#ffdab9",
                "peru": "#cd853f",
                "pink": "#ffc0cb",
                "plum": "#dda0dd",
                "powderblue": "#b0e0e6",
                "purple": "#800080",
                "red": "#ff0000",
                "rosybrown": "#bc8f8f",
                "royalblue": "#4169e1",
                "saddlebrown": "#8b4513",
                "salmon": "#fa8072",
                "sandybrown": "#f4a460",
                "seagreen": "#2e8b57",
                "seashell": "#fff5ee",
                "sienna": "#a0522d",
                "silver": "#c0c0c0",
                "skyblue": "#87ceeb",
                "slateblue": "#6a5acd",
                "slategray": "#708090",
                "snow": "#fffafa",
                "springgreen": "#00ff7f",
                "steelblue": "#4682b4",
                "tan": "#d2b48c",
                "teal": "#008080",
                "thistle": "#d8bfd8",
                "tomato": "#ff6347",
                "turquoise": "#40e0d0",
                "violet": "#ee82ee",
                "wheat": "#f5deb3",
                "white": "#ffffff",
                "whitesmoke": "#f5f5f5",
                "yellow": "#ffff00",
                "yellowgreen": "#9acd32"
            };

            if (typeof colours[colour.toLowerCase()] != undefined) return colours[colour.toLowerCase()];
            return false;
        },
        hex2rgb: function(col) {
            var r, g, b;
            if (col.charAt(0) == '#') {
                col = col.substr(1);
            }
            r = col.charAt(0) + col.charAt(1);
            g = col.charAt(2) + col.charAt(3);
            b = col.charAt(4) + col.charAt(5);
            r = parseInt(r, 16);
            g = parseInt(g, 16);
            b = parseInt(b, 16);
            return 'rgba(' + r + ',' + g + ',' + b + ',0.2)';
        },
    });
    widgetRegistry.add(
        'technic_motohour', TechnicMotohour
    );

});
