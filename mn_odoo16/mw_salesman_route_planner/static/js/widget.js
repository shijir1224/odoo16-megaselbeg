odoo.define('mw_salesman_route_planner.salesman_route', function (require) {
	"use strict";

	var Widget= require('web.Widget');
	var widgetRegistry = require('web.widget_registry');
	var data = require('web.data');
	var FieldManagerMixin = require('web.FieldManagerMixin');
	// var form_common = require('web.form_common');
    var session = require('web.session');
    var user = session.uid
    var company_id = session.user_companies.current_company
    var company_dataset = new data.DataSet(this, 'res.company');

	var core = require('web.core');
	var QWeb = core.qweb;

	var SalesmanRoute = Widget.extend(FieldManagerMixin, {
		template : "mw_salesman_route_planner.SalesmanRoute",
		init: function (parent, dataPoint) {
			this._super.apply(this, arguments);
			this.data = dataPoint.data;
        },
	    start: function() {
	    	var self = this;
	    	var ds = new data.DataSet(this, 'salesman.route.planner.line');
			ds.call('get_partner_datas', ['salesman.route.planner.line', this.data["id"]])
	            .then(function (res) {
	            	self.display_data(res);
            });
		},
		display_data: function(data) {
			var self = this;
			self.$el.html(QWeb.render("mw_salesman_route_planner.SalesmanRoute", {widget: self}));
            var company_data;
			company_dataset.call('get_location_data', [company_id])
	            .then(function (res) {
	            	company_data = res;
                    var map_obj;
                    if(data['partners']){
                    // Төв цэг компани тэмдэглэх
                    var company_location = new google.maps.LatLng(company_data.lat, company_data.lng);
                    map_obj = new google.maps.Map(document.getElementById('partner_on_map'), {
                        center: company_location,
                        zoom: 12,
                        streetViewControl: false,
                        zoomControlOptions: {
                            position: google.maps.ControlPosition.LEFT_CENTER
                        },
                    });
                    // Company
                    var marker_company = new google.maps.Marker({
                        position: company_location,
                        map: map_obj,
                        animation: google.maps.Animation.DROP,
                        title: company_data.name,
                        icon: 'http://maps.google.com/mapfiles/ms/icons/red-dot.png',
                    });
                    // Харилцагчид зурах
                    var waypoints = [];
                    for(var i=0;i<data['partners'].length;i++){
                        var marker_partner = new google.maps.Marker({
                            position: {lat: data['partners'][i]['lat'], lng: data['partners'][i]['long'] },
                            map: map_obj,
                            animation: google.maps.Animation.DROP,
                            title: data['partners'][i]['name'],
                            icon: 'http://maps.google.com/mapfiles/ms/icons/blue-dot.png',
                        });
                        // Тайлбар
                        // var infowindow_company = new google.maps.InfoWindow({
                        //     content: "<b>"+datas['partners'][i]['name']+"</b>"
                        // });
                        // infowindow_company.open(map_obj, marker_partner);
                        // Route бэлдэх
                        waypoints.push({'location':{
                            'lat':data['partners'][i]['lat'],
                            'lng':data['partners'][i]['long']}, stopover:true});
                    }

                    // Зам зурах
                    var directionsDisplay = new google.maps.DirectionsRenderer({suppressMarkers: true});
                    directionsDisplay.setMap(map_obj);
                    var start = new google.maps.LatLng(company_data.lat, company_data.lng);
                    var request = {
                        origin : start,
                        destination : start,
                        waypoints: waypoints,
                        travelMode : google.maps.TravelMode.WALKING,
                    };
                    var directionsService = new google.maps.DirectionsService();
                    directionsService.route(request, function(response, status) {
                        if (status == google.maps.DirectionsStatus.OK) {
                            directionsDisplay.setDirections(response);
                        }
                    });
                }
            });
		},
	});
	widgetRegistry.add(
	    'salesman_route', SalesmanRoute
	);

	// Явсан чиглэл MAP дээр харуулах
	var SalesmanRouteOnMap = Widget.extend(FieldManagerMixin, {
		template : "mw_salesman_route_planner.SalesmanRouteOnMap",
		init: function (parent, dataPoint) {
			this._super.apply(this, arguments);
			this.data = dataPoint.data;
        },
		updateState: function (dataPoint) {
			var self = this;
			if(dataPoint.data.date && dataPoint.data.salesman_id.ref){
				var dddd = dataPoint.data.date;
				var salesman_id = dataPoint.data.salesman_id.ref;
				self.get_locations(salesman_id, dddd);
			}
        },
		get_locations: function(salesman_id, date){
			var self = this;
			var ds = new data.DataSet(this, 'salesman.route.map.report');
			ds.call('get_user_location', ['salesman.route.map.report', salesman_id, date])
	            .then(function (res) {
	            	self.display_data(res);
            });
		},
		display_data: function(data) {
			var self = this;
			self.$el.html(QWeb.render("mw_salesman_route_planner.SalesmanRouteOnMap", {widget: self}));
			if(data.length > 0){
				// MAP зурах бэлдэх
				var start = new google.maps.LatLng(data[0]['lat'], data[0]['lng']);
                var end = new google.maps.LatLng(data[data.length-1]['lat'], data[data.length-1]['lng']);
				var map_obj = new google.maps.Map(document.getElementById('salesman_on_map'), {
				    center: end,
				    zoom: 12,
				    streetViewControl: false,
				    zoomControlOptions: {
				        position: google.maps.ControlPosition.LEFT_CENTER
				    },
				});
				// 
				var marker_company = new google.maps.Marker({
					    position: end,
					    map: map_obj,
					    animation: google.maps.Animation.DROP,
					    title: "Сүүлд",
						icon: 'http://maps.google.com/mapfiles/ms/icons/green-dot.png',
				});
				// Route - Борлуулагчийн явсан замыг бэлдэх
				var waypoints = [];
				var iter = 1;
				if(data.length > 22){
					iter = parseInt(data.length / 22);
				}
				var i=0;
				while(i<data.length){
					waypoints.push({'location':{
						'lat':data[i]['lat'], 
						'lng':data[i]['lng']}, stopover:true});
					i = i+iter;
		    	}
		    	// Зам зурах
                var directionsDisplay = new google.maps.DirectionsRenderer({suppressMarkers: true});
                directionsDisplay.setMap(map_obj); 

                var request = {
                    origin : start,
                    destination : end,
                    waypoints: waypoints,
                    travelMode : google.maps.TravelMode.DRIVING,
                };
                var directionsService = new google.maps.DirectionsService(); 
                directionsService.route(request, function(response, status) {
                    if (status == google.maps.DirectionsStatus.OK) {
                        directionsDisplay.setDirections(response);
                    }
                });
			}
			else {
				$('#salesman_on_map').text("Өгөгдөл олдсонгүй!");
			}

			// ---------------------
    	},
	});
	widgetRegistry.add(
	    'salesman_route_on_map', SalesmanRouteOnMap
	);

	// ------------END-------------
	var GoogleMapDraw = Widget.extend(FieldManagerMixin, {
		template : "mw_salesman_route_planner.GoogleMapDraw",
		init: function (parent, dataPoint) {
			this._super.apply(this, arguments);
			this.data = dataPoint.data;
        },
		updateState: function (dataPoint) {
			var self = this;
			if(dataPoint.data.date && dataPoint.data.salesman_id.ref){
				var dddd = dataPoint.data.date;
				var salesman_id = dataPoint.data.salesman_id.ref;
				self.initMap();
			}
        },
		get_locations: function(salesman_id, date){
			var self = this;
			var ds = new data.DataSet(this, 'salesman.route.map.report');
			ds.call('get_user_location', ['salesman.route.map.report', salesman_id, date])
	            .then(function (res) {
	            	self.display_data(res);
            });
		},
		display_data: function(data) {
			var self = this;
			self.$el.html(QWeb.render("mw_salesman_route_planner.GoogleMapDraw", {widget: self}));
			if(data.length > 0){
				// MAP зурах бэлдэх
				var start = new google.maps.LatLng(data[0]['lat'], data[0]['lng']);
                var end = new google.maps.LatLng(data[data.length-1]['lat'], data[data.length-1]['lng']);
				var map_obj = new google.maps.Map(document.getElementById('salesman_on_map'), {
				    center: end,
				    zoom: 12,
				    streetViewControl: false,
				    zoomControlOptions: {
				        position: google.maps.ControlPosition.LEFT_CENTER
				    },
				});
				//
				var marker_company = new google.maps.Marker({
					    position: end,
					    map: map_obj,
					    animation: google.maps.Animation.DROP,
					    title: "Сүүлд",
						icon: 'http://maps.google.com/mapfiles/ms/icons/blue-dot.png',
				});
				// Route - Борлуулагчийн явсан замыг бэлдэх
				var waypoints = [];
				var iter = 1;
				if(data.length > 22){
					iter = parseInt(data.length / 22);
				}
				var i=0;
				while(i<data.length){
					waypoints.push({'location':{
						'lat':data[i]['lat'],
						'lng':data[i]['lng']}, stopover:true});
					i = i+iter;
		    	}
		    	// Зам зурах
                var directionsDisplay = new google.maps.DirectionsRenderer({suppressMarkers: true});
                directionsDisplay.setMap(map_obj);

                var request = {
                    origin : start,
                    destination : end,
                    waypoints: waypoints,
                    travelMode : google.maps.TravelMode.DRIVING,
                };
                var directionsService = new google.maps.DirectionsService();
                directionsService.route(request, function(response, status) {
                    if (status == google.maps.DirectionsStatus.OK) {
                        directionsDisplay.setDirections(response);
                    }
                });
			}
			else {
				$('#salesman_on_map').text("Өгөгдөл олдсонгүй!");
			}
    	},
    	initMap: function () {
          const map = new google.maps.Map(
            document.getElementById("google_map_draw"),
            {
              center: { lat: -34.397, lng: 150.644 },
              zoom: 8,
            }
          );

          const drawingManager = new google.maps.drawing.DrawingManager({
            drawingMode: google.maps.drawing.OverlayType.MARKER,
            drawingControl: true,
            drawingControlOptions: {
              position: google.maps.ControlPosition.TOP_CENTER,
              drawingModes: [
                google.maps.drawing.OverlayType.MARKER,
                google.maps.drawing.OverlayType.CIRCLE,
                google.maps.drawing.OverlayType.POLYGON,
                google.maps.drawing.OverlayType.POLYLINE,
                google.maps.drawing.OverlayType.RECTANGLE,
              ],
            },
            markerOptions: {
              icon: "https://developers.google.com/maps/documentation/javascript/examples/full/images/beachflag.png",
            },
            circleOptions: {
              fillColor: "#ffff00",
              fillOpacity: 1,
              strokeWeight: 5,
              clickable: false,
              editable: true,
              zIndex: 1,
            },
          });
          drawingManager.setMap(map);
        },
        // TODO: Ажиллахгүй байна
	});
	widgetRegistry.add(
	    'google_map_draw', GoogleMapDraw
	);
});

