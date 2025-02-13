/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService, useOwnedDialogs } from "@web/core/utils/hooks";
import { usePopover } from "@web/core/popover/popover_hook";
const rpc = require('web.rpc');
//import { useService } from "@web/core/utils/hooks";

const { Component, EventBus, onWillRender, onWillUpdateProps, onWillStart } = owl;
export class SalaryOrder extends Component {
    setup() {
        this.orm = useService("orm");
        this.rpc = useService("rpc");
        this.actionService = useService("action");
        this.bus = new EventBus();
        this.popover = usePopover();
        this.closePopover = null;
        this.calcData = {};
        this.allPlans = [];
        onWillRender(() => {
            this.initCalcData();
            // this.load_server_data();
        })
        // this.line_line = [];
    }
	async tatahButtonClicked_MW(params = {}) {
		var com_id = false;
		var tax_data = $('div[id="salary_order"]'); //.val();
		console.log('tax_data',tax_data);
		var data = document.getElementById("salary_order").innerHTML;
		//console.log('data',data);
		var self=this;
		const aa = await rpc.query({
			model: "salary.order",
			method: 'download_data',
			args: [[],data],
		}).then(function (result) {
			console.log('resultresult ',result.url);
			var url=result.url;
			//console.log('urlurl',url);
			self.actionService.doAction({ type: "ir.actions.act_url", url });
			//return result;
				});
		
		/*
		for (var partner of this.partners) {
			let key = 'input[id="{0}"]';
			var key_honog = key.replace("{0}", partner.honog_id);
			var key_tax = key.replace("{0}", partner.tax_id);
			var key_insurance = key.replace("{0}", partner.insurance_id);
			var honog_data = $(key_honog).val();
			var tax_data = $(key_tax).val();
			var insurance_data = $(key_insurance).val();

			let key_option = 'option[id="{0}"][value="{1}"]';
			console.log('key_technic_type:', key_technic_type, technic_type_data);
			var key_technic_type = key_option.replace("{0}", partner.technic_type_id).replace("{1}", partner.technic_type_value);
			var technic_type_data = $(key_technic_type).val();

			const aa = await rpc.query({
				model: "foreign.logistic.comparison",
				method: 'save_compar_data',
				args: [partner.compare_id, technic_type_data, honog_data, tax_data, insurance_data, partner],
			})
			com_id = partner.compare_id;
		}
		this.action.doAction({
			type: 'ir.actions.act_window',
			res_model: 'foreign.logistic.comparison',
			res_id: parseInt(com_id),
			views: [[false, 'form']],
			target: 'current'
		});*/
	}
	
    async initCalcData() {
        const info ={
            salary: [],
            s_line: [],
            s_line1: [],
            sum_amount: [],
            data: this.props.record,
            };
		var i = 0
        var j =0
        var sum=0
        var ll=''
        var ssum =0
        var k =0
        if (info.data){
            info.salary = info.data.data.order_line; 
            for (var line of info.salary.records) {
                info.s_line = line.data.so_line_line          
            }
            for (var line of info.salary.records) {
                info.s_line1 = line.data.so_line_line1   				  
            }
			var len = info.salary.records.length
            if (info.salary.records[0]){
                var len2 = info.salary.records[0].data.so_line_line1.records.length-1
            }
            while (k <= len2){
                while (j <= len){
                    if (info.salary.records[j]){
                        var line = info.salary.records[j]
                            i=k
                            if(line){
                                if (line.data.so_line_line1.records[i]){
                                    ll = line.data.so_line_line1.records[i]
                                    if (parseFloat(ll.data.display_name)>0)
                                        sum += parseFloat(ll.data.display_name)
                                        i+=1
                                }
                            }
                    };
                    // ssum = sum
					ssum = parseFloat(sum.toFixed(2)).toLocaleString();

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
            console.log('c',info.sum_amount)
			
			
        }
        // console.log('-=-=-=-=-=-records',info.data.data.order_line )
        // console.log('-=-=-=-=-=-kkkkkk',info.salary.records  )
        // console.log('info.s_linegggggggg',info.s_line1.records)
        this.line_ids = info.salary.records
        this.l_line = info.s_line.records
        this.line_line = info.s_line1.records
        this.sum_foot = info.sum_amount
        
    }
}

SalaryOrder.template = "mw_salary.SalaryOrder";

registry.category("view_widgets").add("hr_salary_order", SalaryOrder);
