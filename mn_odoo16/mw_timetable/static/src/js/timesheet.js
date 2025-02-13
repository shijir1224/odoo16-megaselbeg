/** @odoo-module **/

import { registry } from "@web/core/registry";
import { usePopover } from "@web/core/popover/popover_hook";
const data = require('web.data');
var rpc = require('web.rpc');

const { Component, EventBus, onWillRender,onWillUpdateProps } = owl;
class HrTimetable extends Component {
    setup() {
        this.bus = new EventBus();
        this.popover = usePopover();
        this.closePopover = null;
        this.calcData = {};
       
        
        this.initCalcData(this.props);
        onWillRender((nextProps) => this.initCalcData(nextProps));
    }
    
    initCalcData() {
       const info ={
        content: [],
        data: this.props.record,
        result_aa: '',
        time_line:[],
        times:[],
        date_from : null,
        date_to : null,
        query_data:'',
        date : null,
        days : ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'],
        d : null,
        dayName : null,
        mm : null,
        dd : null,
        yyyy : null,
        index:[]
        };

        if (info.data){
            info.content = info.data.data.line_ids; 
            info.date_from = info.data.data.date_from; 
            info.date_to = info.data.data.date_to; 
            // info.time_line = info.data.data.timetable_line_line_rltd
        }
        this.lines = info.content.records
        for(var ii of this.lines){
            info.time_line = ii.data.line_ids
        }
        // this.line_line =  info.time_line.records       
        var start = new Date(info.date_from); 
        var end = new Date(info.date_to); 
        while(start <= end){
            info.mm = ((start.getMonth()+1)>=10)?(start.getMonth()+1):'0'+(start.getMonth()+1);
            info.dd = ((start.getDate())>=10)? (start.getDate()) : '0' + (start.getDate());
            info.yyyy = start.getFullYear();
            info.date = info.yyyy+'-'+info.mm+'-'+info.dd;
            info.d = new Date(info.date);
            info.dayName= info.days[info.d.getDay()];
            info.times.push(info.dayName+ ' ' + info.mm + '-' + info.dd);
            start = new Date(start.setDate(start.getDate() + 1)); 
        }
        this.times = info.times;
       
    }
   
}
HrTimetable.template = "mw_timetable.HrTimetable";
HrTimetable.components = { HrTimetable };

registry.category("view_widgets").add("hr_monthly_timesheet", HrTimetable);
