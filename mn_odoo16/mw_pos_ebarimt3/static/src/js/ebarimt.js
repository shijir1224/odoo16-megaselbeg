odoo.define('point_of_sale.mw_pos_ebarimt', function (require) {
    "use strict";

var { Order, Orderline,PosGlobalState } = require('point_of_sale.models');
const Registries = require('point_of_sale.Registries');

const PosEbarimtOrder = (Order) => class PosEbarimtOrder extends Order {		

    constructor(obj, options) {
        super(...arguments);
        this.bill_type = 'B2C_RECEIPT';
        this.is_with_ebarimt ='1';
        console.log('this.bill_type==== '+this.bill_type);
    }
    export_for_printing() {
        var result = super.export_for_printing(...arguments);
        var is_with_ebarimt=this.pos.company.is_with_ebarimt ;
        
        console.log('is_with_ebarimt---------------============== ',is_with_ebarimt);
        if (is_with_ebarimt){
			result.is_with_ebarimt = '1';
		}else{
			result.is_with_ebarimt = '0';
		}
        return result;
    }
                    
    export_as_JSON() {
        const json = super.export_as_JSON(...arguments);
            if (!this.bill_type) { this.bill_type = 'B2C_RECEIPT'; }
            json.bill_type = this.bill_type;
            console.log('this.bill_type '+ this.bill_type);
/*            if (this.bill_type === 'B2C_RECEIPT'){
                json.amount_total = this.get_total_without_tax();
                json.amount_tax = 0;
            }
            if (this.bill_type === '0'){
                json.amount_total = this.get_total_without_tax();
                json.amount_tax = 0;
            }*/
            json.customerReg = this.customerReg;
            json.customerName = this.customerName;
            return json;
    }
                    /*
        export_for_printing: function() {
            var receipt = _superOrder.prototype.export_for_printing.apply(this,arguments);
            if (!this.bill_type) { this.bill_type = '1'; }
            receipt.bill_type = this.bill_type;
            receipt.config_name = this.pos.config.name;
            receipt.customer_reg = this.customerReg;
            receipt.customer_name = this.customerName;
            if (this.bill_type === '0'){
                receipt.total_with_tax = this.get_total_without_tax();
                receipt.total_tax = 0;
                receipt.tax_details = [];
            }
            return receipt;
        },

        get_due: function(paymentline) {
            let total = 0;
            if (this.bill_type === '0'){
                total = this.get_total_without_tax();
            } else {
                total = this.get_total_with_tax();
            }
            let due = 0;
            if (!paymentline) {
                due = total - this.get_total_paid() + this.get_rounding_applied();
            } else {
                due = total;
                let lines = this.paymentlines.models;
                for (let i = 0; i < lines.length; i++) {
                    if (lines[i] === paymentline) {
                        break;
                    } else {
                        due -= lines[i].get_amount();
                    }
                }
            }
            return round_pr(due, this.pos.currency.rounding);
        },

        get_change: function(paymentline) {
            let change = 0;
            if (this.bill_type === '0'){
                change = this.get_total_without_tax();
            } else {
                change = this.get_total_with_tax();
            }
            if (!paymentline) {
                change = this.get_total_paid() - change - this.get_rounding_applied();
            } else {
                change = -change;
                let lines  = this.paymentlines.models;
                for (let i = 0; i < lines.length; i++) {
                    change += lines[i].get_amount();
                    if (lines[i] === paymentline) {
                        break;
                    }
                }
            }
            return round_pr(Math.max(0,change), this.pos.currency.rounding);
        },*/
    }
    
Registries.Model.extend(Order, PosEbarimtOrder);


const PosEbarimtOrderline = (Orderline) => class PosEbarimtOrderline extends Orderline {		

    /*
        export_as_JSON: function() {
            if (this.order.bill_type === '0'){
                json.price_subtotal_incl = this.get_price_without_tax();
                json.tax_ids = [];
            }
            return json;
        }

        export_for_printing: function() {
            var json = _superOrderline.prototype.export_for_printing.apply(this,arguments);
            json.tax_details = this.get_tax_details();
            json.product_id = this.product.id;
            if (this.order.bill_type === '0'){
                json.price_with_tax = this.get_price_without_tax();
            }
            return json;
        }

        get_all_prices: function(){
            var self = this;

            var price_unit = this.get_unit_price() * (1.0 - (this.get_discount() / 100.0));
            var taxtotal = 0;

            var product =  this.get_product();
            var taxes_ids = product.taxes_id;
            var taxes =  this.pos.taxes;
            var taxdetail = {};
            var product_taxes = [];

            _(taxes_ids).each(function(el){
                var tax = _.detect(taxes, function(t){
                    return t.id === el;
                });
                product_taxes.push.apply(product_taxes, self._map_tax_fiscal_position(tax));
            });
            product_taxes = _.uniq(product_taxes, function(tax) { return tax.id; });

            var all_taxes = this.compute_all(product_taxes, price_unit, this.get_quantity(), this.pos.currency.rounding);
            var all_taxes_before_discount = this.compute_all(product_taxes, this.get_unit_price(), this.get_quantity(), this.pos.currency.rounding);
            _(all_taxes.taxes).each(function(tax) {
                taxtotal += tax.amount;
                taxdetail[tax.id] = tax.amount;
            });

            var price_with_tax_before_discount = all_taxes_before_discount.total_included;
            var tax_total = taxtotal;
            var tax_details = taxdetail;
            if (this.order.bill_type === '0'){
                price_with_tax_before_discount = all_taxes_before_discount.total_excluded;
                tax_total = 0;
                tax_details = {};
            }
            var total_excluded=all_taxes.total_excluded;
            var total_void=all_taxes.total_void;
            var total_included=all_taxes.total_included;
            if (this.order.get_client() && this.order.get_client().nuat_no){
            	total_included=total_excluded;
            	tax_total=0;
            	total_void=undefined;
            }
            return {
                "priceWithTax": total_included,
                "priceWithoutTax": total_excluded,
                "priceSumTaxVoid": total_void,
                "priceWithTaxBeforeDiscount": price_with_tax_before_discount,
                "tax": tax_total,
                "taxDetails": tax_details,
            };
        }*/
        
    }
Registries.Model.extend(Orderline, PosEbarimtOrderline);    
/*
const PosEbarimtPaymentline = (Orderline) => class PosEbarimtPaymentline extends Paymentline {	
    models.Paymentline = models.Paymentline.extend({
        export_for_printing: function() {
            var json = _superPaymentline.prototype.export_for_printing.apply(this,arguments);
            json.payment_method_id = this.payment_method.id;
            return json;
        },


        export_as_JSON: function() {
            var json = _superPaymentline.prototype.export_as_JSON.apply(this,arguments);
            json.utga = this.order.utga;
            return json;
        },
                
    });

    var _superPos = models.PosModel;*/
    
const PosEbarimtPosGlobalState = (PosGlobalState) => class PosEbarimtPosGlobalState extends PosGlobalState {	    
                
        get_ebarimt_data(order){
            var self = this;
            var type="B2C_RECEIPT";
            if (order.bill_type==="B2B_RECEIPT"){
				type="B2B_RECEIPT"
			}
            var order=this.get_order();
            console.log('type.type '+type);
            console.log('order.get_total_with_tax+'+order.get_total_with_tax());
            console.log('order.order.get_total_tax()+'+order.get_total_tax());
            console.log('order.this.config.eb_district_code+'+this.config.eb_district_code);
            var date=new Date();
            var receipts=[];
            var items=[];
            var amountTotal=0;
            var totalVAT=0;
            var paidAmount=0;
            order.get_orderlines().forEach(function (orderline) {
                var product = orderline.product;
                var taxes=orderline.get_applicable_taxes();
                console.log('taxestaxestaxestaxestaxes ',taxes);
                amountTotal+=orderline.get_price_with_tax();
                totalVAT+=orderline.get_price_with_tax()-orderline.get_price_without_tax();
                var barcode="";
                if (product.barcode!==false){
					barcode=product.barcode;
				}
				console.log('orderline.tax_ids ',orderline.tax_ids)
	            var tmp={
	            					"name": product.display_name,
				                    "barCode": barcode,
				                    "barCodeType": "UNDEFINED",
				                    "classificationCode": "8843000",
				                    "measureUnit": "ш",
				                    "qty": orderline.get_quantity(),
				                    "unitPrice": orderline.get_quantity(),
				                    "totalBonus": 0,
				                    "totalVAT": orderline.get_price_with_tax()-orderline.get_price_without_tax(),
				                    "totalCityTax": 0,
				                    "totalAmount": orderline.get_price_with_tax(),
				            		"tax_ids":taxes
				                    }
	            items.push(tmp);                
            });

            var tmp2={
					"totalAmount":amountTotal,
            		"totalVAT":totalVAT,
            		 "taxType": "VAT_ABLE",
            		 "merchantTin":this.config.eb_tin,
            		 "items":items,
            		}
            paidAmount=amountTotal;
            receipts.push(tmp2)
	        console.log('receipts+++ ',receipts);
	        var abb=JSON.stringify(receipts)
	        console.log('abb+++ '+abb);
				    
			var dateString = new Date(    new Date().getFullYear(),
										    new Date().getMonth() - 1, 
										    10
									)
                    .toISOString()
                    .split("T")[0];            
            console.log('date=========1 '+dateString);
            if (this.config.eb_tin===false){
				alert('Merchant tin тохируулаагүй байна!!!');
			}
            if (order){
	            var js_data = { 
				    "totalAmount": order.get_total_with_tax(),
				    "totalVAT": order.get_total_tax(),
				    "totalCityTax": 0,
				    "districtCode": this.config.eb_district_code,
				    "merchantTin": this.config.eb_tin,//"73101472838",
				    "branchNo": "001",
				    "posNo": "001",
				    "customerTin": "",
				    "consumerNo": "",
				    "type": type,
				    "inactiveId": "",
				    "reportMonth": null,
	                    "receipts": receipts,
				    "payments": [
				        {
				            "code": "CASH",
				            "status": "PAID",
				            "paidAmount": paidAmount
				        }
				    ]
				    };
		        console.log('js_data========= '+js_data);
	            var etype='B2C_RECEIPT';
	            var number='';
	            var taxtype='1';
	            console.log('order.ebarimt_type ',order.bill_type);
	            if (order.bill_type=='B2B_RECEIPT'){
	                etype='B2B_RECEIPT';
	                number = order.customerReg.toUpperCase();
	                js_data["customerTin"]=number;
	            }
	            js_data["customerNo"]=number;
	            // if (bagts_eseh){
	            //     // bagts dr 3aar ilgee gesen taivan
	            //     etype='3';
	            //     js_data["customerNo"] = this.pos.company.vat;
	            // }
	            js_data["taxType"]=taxtype;
	            js_data["billType"]=etype;
	            js_data["type"]=etype;
	            
	            js_data["customerName"]=number;
	            
	            return js_data;
	            }
	            else{return false;
	            }
            
        }
    _flush_orders(orders, options) {
        var self = this;

        return this._save_to_server(orders, options).then(function (server_ids) {
            for (let i = 0; i < server_ids.length; i++) {
                self.validated_orders_name_server_id_map[server_ids[i].pos_reference] = server_ids[i].id;
            }
            self._after_flush_orders222(orders,server_ids)
            return server_ids;
        }).finally(function() {
            self._after_flush_orders(orders);
        });
    }                        
//    _save_to_server(orders, options) {
//        const ssp = super._save_to_server(orders, options);
      _after_flush_orders222(orders,server_ids) {
		 console.log('server_idsserver_ids ',server_ids);
	  //const ssp = super._after_flush_orders(orders);
        console.log('orders ',orders);
        //console.log('ssp '+ssp);
        var is_with_ebarimt=this.company.is_with_ebarimt;
        console.log('is_with_ebarimt111------: '+is_with_ebarimt);
        //return super._save_to_server(orders, options).then(function (){
        if (orders.length && is_with_ebarimt){
			for (let order of orders) {
				console.log('order '+order);
				//console.log('ordername '+order.name);
				var data=this.get_ebarimt_data(order);
				data=JSON.stringify(data)
	        //this.uiLock();
	        var url=this.company.ebarimt_url;
	        console.log('this.company: '+this.company.is_ebarimt_offline);
	        var settings = { 
	            "async": true,
	            "crossDomain": true,
	            "url": url+"/rest/receipt",
	            "method": "POST",
	            "headers": {
	    	                "content-type": "application/json; charset=utf-8", 
		                    "Access-Control-Allow-Origin": "*",
	//	                    'Access-Control-Allow-Methods': '*',
	//	                    'Access-Control-Allow-Credentials': true,
	//	                    'Access-Control-Allow-Headers':'*'
	
	                },
	            "processData": false,
	            "data": data 
	        } 
	
	// ajax start
		/*offline*/
				if (this.company.is_ebarimt_offline==true){
						console.log('offline ebarimt++++++');
						$.ajax(settings).done(function (response) {
			                    if (response.status=="SUCCESS") {
			                        $(".mn_class_bill_id").text(response.id);
			                        $(".mn_class_lottery").text(response.lottery);
			                        $(".mn_class_qr_data").attr("src", "/report/barcode/?barcode_type=QR&value=" + response.qrData + "&width=150&height=150");
			                    }
						}).fail(function (reject) {
							console.log('faile++++++', reject);
						});
					}
	//ajax finish   
				else{
	/* online */
					console.log('online ebarimt++++++');
			        var timeout =30000;
						this.env.services.rpc({
			                model: 'pos.order',
			                method: 'get_ebarimt',
			                args: [server_ids,data],
			                timeout:300000,
			                kwargs: {context: this.env.session.user_context},
			            }, {
			                timeout: timeout,
			            })
			            .then(function(result){
							console.log('result offline '+result);
							console.log('result typoe '+(typeof result));
							const aa=JSON.parse(result);
							console.log('result aa '+aa.status);
							if (aa.status=="ERROR"){
								alert('Ebartim error!!! '+aa.message);
							}
	                    if (result.length) {
							var lott='';
							if (aa.lottery){
								lott=aa.lottery;
							}
							console.log('result esult.lottery '+aa.lottery);
	                        $(".mn_class_bill_id").text(aa.id);
	                        $(".mn_class_lottery").text(lott);
	                        $(".mn_class_qr_data").attr("src", "/report/barcode/?barcode_type=QR&value=" + aa.qrData + "&width=150&height=150");
	                    }//		                self.failed = false;
	//		                self.set_synch('connected');
	//		                return server_ids;
			            }).catch(function (error){
			                console.warn('Failed to send orders----:', orders);
			                if(error.code === 200 ){    // Business Logic Error, not a connection problem
			                    if (!self.failed) {//|| options.show_error) && !options.to_invoice) {
			                        self.failed = error;
			                        throw error;
			                    }
			                }
			                throw error;
			            });
	     			}
				}
			}
			//})
        //return ssp;
    }
    }
Registries.Model.extend(PosGlobalState, PosEbarimtPosGlobalState);      
    /**/
});
