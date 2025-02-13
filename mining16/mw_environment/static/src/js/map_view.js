odoo.mw_environment = function(instance, local) {
    var QWeb = instance.web.qweb;
    var _t = instance.web._t;
    var map;
    var markers = [];


    local.MapView = instance.web.View.extend({
        template: "gmaps",

        init: function(parent, dataset, view_id, options) {
            this._super(parent);
            this.set_default_options(options);
            this.view_manager = parent;
            this.dataset = dataset;
            this.dataset_index = 0;
            this.model = this.dataset.model;
            this.view_id = view_id;
            this.view_type = "gmaps";
        },

        view_loading: function(data) {
            var self = this;
            this.fields_view = data;

            this.$el.html(QWeb.render("gmaps", {fields_view: this.fields_view, elem_id: this.elem_id}));

            if (typeof google === "undefined") {
                window.ginit = this.on_ready;
                $.getScript("https://maps.googleapis.com/maps/api/js?key=AIzaSyD6DG_rmHN0F5ksKCdmpSjYYcTNiphGMuw&sensor=false&callback=ginit");
            } else {
                setTimeout(function() {
                    self.on_ready();
                }, 1000);
            }
        },

        on_ready: function() {

            var myLatlng = new google.maps.LatLng(47, 106);
            var mapOptions = {
                zoom: 5,
                center: myLatlng,
                mapTypeControl: false,
                scaleControl: false,
                streetViewControl: false,
                rotateControl: false,
                fullscreenControl: false,
            };

            var div_gmap = this.$el[0];

            map = new google.maps.Map(div_gmap, mapOptions);

            const controlDiv = document.createElement("div");
            for (let i = 0; i <= 5; i++) {
                var controlUI = document.createElement("div");
                controlUI.style.border = "2px solid #fff";
                controlUI.style.borderRadius = "3px";
                controlUI.style.boxShadow = "0 2px 6px rgba(0,0,0,.3)";
                controlUI.style.cursor = "pointer";
                controlUI.style.marginTop = "8px";
                controlUI.style.marginLeft = "8px";
                controlUI.style.textAlign = "center";
                controlDiv.appendChild(controlUI);
                var controlText = document.createElement("div");
                controlText.style.color = "rgb(255,255,255)";
                controlText.style.fontFamily = "Roboto,Arial,sans-serif";
                controlText.style.fontSize = "12px";
                controlText.style.lineHeight = "18px";
                controlText.style.paddingLeft = "5px";
                controlText.style.paddingRight = "5px";
                controlUI.appendChild(controlText);
                switch(i) {
                    case 0:
                        controlUI.style.backgroundColor = "#000";
                        controlText.innerHTML = "Бүгд";
                        break;
                    case 1:
                        controlUI.style.backgroundColor = "#fff200";
                        controlText.innerHTML = "Агаар";
                        break;
                    case 2:
                        controlUI.style.backgroundColor = "#00f";
                        controlText.innerHTML = "Ус";
                        break;
                    case 3:
                        controlUI.style.backgroundColor = "#8b4513";
                        controlText.innerHTML = "Хөрс";
                        break;
                    case 4:
                        controlUI.style.backgroundColor = "#911A81";
                        controlText.innerHTML = "Амьтан";
                        break;
                    case 5:
                        controlUI.style.backgroundColor = "#00b872";
                        controlText.innerHTML = "Ургамал";
                        break;
                }
                controlUI.addEventListener("click", () => {
                    for (let j = 0; j < markers.length; j++) {
                        if (i==0){
                            markers[j].setMap(map);
                        }else if (markers[j].tag==i){
                            markers[j].setMap(map);
                        }else{
                            markers[j].setMap(null);
                        }
                    }
                });

            }
            map.controls[google.maps.ControlPosition.TOP_LEFT].push(controlDiv);

            var self = this;
            self.dataset.read_slice(_.keys(self.fields_view.fields)).then(function(data) {
                _(data).each(self.do_load_record);
            });
            google.maps.event.trigger(map, "resize");
        },

        do_load_record: function(record) {
            var self = this;
            _(self.fields_view.arch.children).each(function(data) {
                self.do_add_item(data, record);
            });
        },

        do_add_item: function(item, record) {
            var self = this;

            if (item.tag == "widget" && item.attrs.name == "gmap_marker") {
                var self = this;
                var model = new instance.web.Model("env.mining.line");
                var modelComponent = new instance.web.Model("env.monitor.component");
                model.query(['id', 'name', 'code', 'latitude', 'longitude', 'monitor_category','bad_monitor'])
                     .filter([['is_active', '=', 'active'], ['mining_id', '=', record.id]])
                     .all().then(function (locations) {
                         _.each(locations, function(location) {

                            switch(location.monitor_category) {
                                case 'monitor3':
                                    image = "mw_environment/static/src/img/markers/yellow.png";
                                    color=1;
                                    break;
                                case 'monitor1':
                                    image = "mw_environment/static/src/img/markers/blue.png";
                                    color=2;
                                break;
                                case 'monitor2':
                                    image = "mw_environment/static/src/img/markers/brown.png";
                                    color=3;
                                    break;
                                case 'monitor4':
                                    image = "mw_environment/static/src/img/markers/purple.png";
                                    color=4;
                                    break;
                                case 'monitor5':
                                    image = "mw_environment/static/src/img/markers/green.png";
                                    color=5;
                                    break;
                                default:
                                    image = "mw_environment/static/src/img/markers/black.png";
                            }

                            var marker = new google.maps.Marker({
                                position: new google.maps.LatLng(location.latitude, location.longitude),
                                map: map,
                                icon: {
                                    url: image,
                                    labelOrigin: {x: 12, y: 11}
                                },
                                tag: color,
                                draggable: false,
                                title:location.name,
                                label: {
                                    text: " ",
                                    className: location.bad_monitor==true?'marker-label':'',
                                }
                            });

                            if ((location.monitor_category=="monitor1" || location.monitor_category=="monitor2" || location.monitor_category == "monitor3") && location.bad_monitor==true){
                                var breaches=""
                                modelComponent.call("get_breaches", [location.id]).then(function(result) {
                                    breaches= result;
                                });
                                setTimeout(function() {
                                    const contentString =
                                    '<div class="content">' +
                                        '<div class="siteNotice">'+record[item.attrs.description]+'</div>' +
                                        '<h3 class="firstHeading">'+location.code + ' ( ' + location.name+' )</h3>' +
                                        '<small>'+location.latitude + ', ' + location.longitude + '</small><br><br>' +
                                        '<div class="bodyContent">'+breaches+'</div>' +
                                    "</div>";
                                    const infowindow = new google.maps.InfoWindow({
                                        content: contentString,
                                    });
                                    marker.addListener("click", () => {
                                        infowindow.open({
                                          anchor: marker,
                                          map,
                                          shouldFocus: false,
                                        });
                                    });
                                    markers.push(marker);
                                }, 5000);

                            }else{
                                const contentString =
                                '<div class="content">' +
                                    '<div class="siteNotice">'+record[item.attrs.description]+'</div>' +
                                    '<h3 class="firstHeading">'+location.code + ' ( ' + location.name+' )</h3>' +
                                    '<small>'+location.latitude + ', ' + location.longitude + '</small><br><br>' +
                                "</div>";
                                //console.log(contentString);
                                const infowindow = new google.maps.InfoWindow({
                                    content: contentString,
                                });
                                marker.addListener("click", () => {
                                    infowindow.open({
                                      anchor: marker,
                                      map,
                                      shouldFocus: false,
                                    });
                                });
                                markers.push(marker);
                            }
                         });
                     });
            }
        },
    });

    instance.web.views.add("gmaps", "instance.MapView");
};