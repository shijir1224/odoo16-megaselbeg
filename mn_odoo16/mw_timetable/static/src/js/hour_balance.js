/** @odoo-module **/

import { registry } from "@web/core/registry";
import { usePopover } from "@web/core/popover/popover_hook";

const { Component, EventBus, onWillRender } = owl;
console.log('xxxxxx ');
export class HourBalanceDynamic extends Component {
    setup() {
        this.bus = new EventBus();
        this.popover = usePopover();
        this.closePopover = null;
        this.calcData = {};
        onWillRender(() => {
            this.initCalcData();
        })
    }

    initCalcData() {
        const info ={
            balance: [],
            balance_line: [],
            balance_line_hour:[],
            sum_amount :[],
            data: this.props.record,
            };
        var i = 0
        var j =0
        var sum=0
        var ll=''
        var ssum =0
        var k =0
        
        if (info.data){
            info.balance = info.data.data.balance_line_ids; 
            for (var line of info.balance.records) {
                info.balance_line = line.data.balance_line_line_ids
            };
            var len = info.balance.records.length
            if (info.balance.records[0]){
                var len2 = info.balance.records[0].data.balance_line_line_hour_ids.records.length-1
            }
            while (k <= len2){
                while (j <= len){
                    if (info.balance.records[j]){
                        var line = info.balance.records[j]
                            i=k
                            if(line){
                                if (line.data.balance_line_line_hour_ids.records[i]){
                                    ll = line.data.balance_line_line_hour_ids.records[i]
                                    if (parseFloat(ll.data.display_name)>0)
                                        sum += parseFloat(ll.data.display_name)
                                        i+=1
                                }
                            }
                    };
                    ssum = sum
                    j+=1
                }
                info.sum_amount.push(ssum)
                sum=0
                k+=1
                j=0
                if (k>len2){
                    break;
                }
            }           
            console.log('info.sum_amount',info.sum_amount)
        }
        this.line_line_hour = info.balance_line_hour.records
        this.line_line = info.balance_line.records
        this.lines = info.balance.records
        this.sum_foot = info.sum_amount
    }
}

HourBalanceDynamic.template = "mw_timetable.HourBalanceDynamic";

registry.category("view_widgets").add("hr_dynamic_balance", HourBalanceDynamic);
