/** @odoo-module **/

export const MAP_THEMES = {
    default: [],
    aubergine: [
        {
            elementType: 'geometry',
            stylers: [
                {
                    color: '#1d2c4d',
                },
            ],
        },
        {
            elementType: 'labels.text.fill',
            stylers: [
                {
                    color: '#8ec3b9',
                },
            ],
        },
        {
            elementType: 'labels.text.stroke',
            stylers: [
                {
                    color: '#1a3646',
                },
            ],
        },
        {
            featureType: 'administrative.country',
            elementType: 'geometry.stroke',
            stylers: [
                {
                    color: '#4b6878',
                },
            ],
        },
        {
            featureType: 'administrative.land_parcel',
            elementType: 'labels.text.fill',
            stylers: [
                {
                    color: '#64779e',
                },
            ],
        },
        {
            featureType: 'administrative.province',
            elementType: 'geometry.stroke',
            stylers: [
                {
                    color: '#4b6878',
                },
            ],
        },
        {
            featureType: 'landscape.man_made',
            elementType: 'geometry.stroke',
            stylers: [
                {
                    color: '#334e87',
                },
            ],
        },
        {
            featureType: 'landscape.natural',
            elementType: 'geometry',
            stylers: [
                {
                    color: '#023e58',
                },
            ],
        },
        {
            featureType: 'poi',
            elementType: 'geometry',
            stylers: [
                {
                    color: '#283d6a',
                },
            ],
        },
        {
            featureType: 'poi',
            elementType: 'labels.text.fill',
            stylers: [
                {
                    color: '#6f9ba5',
                },
            ],
        },
        {
            featureType: 'poi',
            elementType: 'labels.text.stroke',
            stylers: [
                {
                    color: '#1d2c4d',
                },
            ],
        },
        {
            featureType: 'poi.business',
            stylers: [
                {
                    visibility: 'off',
                },
            ],
        },
        {
            featureType: 'poi.park',
            elementType: 'geometry.fill',
            stylers: [
                {
                    color: '#023e58',
                },
            ],
        },
        {
            featureType: 'poi.park',
            elementType: 'labels.text',
            stylers: [
                {
                    visibility: 'off',
                },
            ],
        },
        {
            featureType: 'poi.park',
            elementType: 'labels.text.fill',
            stylers: [
                {
                    color: '#3C7680',
                },
            ],
        },
        {
            featureType: 'road',
            elementType: 'geometry',
            stylers: [
                {
                    color: '#304a7d',
                },
            ],
        },
        {
            featureType: 'road',
            elementType: 'labels.text.fill',
            stylers: [
                {
                    color: '#98a5be',
                },
            ],
        },
        {
            featureType: 'road',
            elementType: 'labels.text.stroke',
            stylers: [
                {
                    color: '#1d2c4d',
                },
            ],
        },
        {
            featureType: 'road.highway',
            elementType: 'geometry',
            stylers: [
                {
                    color: '#2c6675',
                },
            ],
        },
        {
            featureType: 'road.highway',
            elementType: 'geometry.stroke',
            stylers: [
                {
                    color: '#255763',
                },
            ],
        },
        {
            featureType: 'road.highway',
            elementType: 'labels.text.fill',
            stylers: [
                {
                    color: '#b0d5ce',
                },
            ],
        },
        {
            featureType: 'road.highway',
            elementType: 'labels.text.stroke',
            stylers: [
                {
                    color: '#023e58',
                },
            ],
        },
        {
            featureType: 'transit',
            elementType: 'labels.text.fill',
            stylers: [
                {
                    color: '#98a5be',
                },
            ],
        },
        {
            featureType: 'transit',
            elementType: 'labels.text.stroke',
            stylers: [
                {
                    color: '#1d2c4d',
                },
            ],
        },
        {
            featureType: 'transit.line',
            elementType: 'geometry.fill',
            stylers: [
                {
                    color: '#283d6a',
                },
            ],
        },
        {
            featureType: 'transit.station',
            elementType: 'geometry',
            stylers: [
                {
                    color: '#3a4762',
                },
            ],
        },
        {
            featureType: 'water',
            elementType: 'geometry',
            stylers: [
                {
                    color: '#0e1626',
                },
            ],
        },
        {
            featureType: 'water',
            elementType: 'labels.text.fill',
            stylers: [
                {
                    color: '#4e6d70',
                },
            ],
        },
    ],
    night: [
        {
            elementType: 'geometry',
            stylers: [
                {
                    color: '#242f3e',
                },
            ],
        },
        {
            elementType: 'labels.text.fill',
            stylers: [
                {
                    color: '#746855',
                },
            ],
        },
        {
            elementType: 'labels.text.stroke',
            stylers: [
                {
                    color: '#242f3e',
                },
            ],
        },
        {
            featureType: 'administrative.locality',
            elementType: 'labels.text.fill',
            stylers: [
                {
                    color: '#d59563',
                },
            ],
        },
        {
            featureType: 'poi',
            elementType: 'labels.text',
            stylers: [
                {
                    visibility: 'off',
                },
            ],
        },
        {
            featureType: 'poi',
            elementType: 'labels.text.fill',
            stylers: [
                {
                    color: '#d59563',
                },
            ],
        },
        {
            featureType: 'poi.business',
            stylers: [
                {
                    visibility: 'off',
                },
            ],
        },
        {
            featureType: 'poi.park',
            elementType: 'geometry',
            stylers: [
                {
                    color: '#263c3f',
                },
            ],
        },
        {
            featureType: 'poi.park',
            elementType: 'labels.text.fill',
            stylers: [
                {
                    color: '#6b9a76',
                },
            ],
        },
        {
            featureType: 'road',
            elementType: 'geometry',
            stylers: [
                {
                    color: '#38414e',
                },
            ],
        },
        {
            featureType: 'road',
            elementType: 'geometry.stroke',
            stylers: [
                {
                    color: '#212a37',
                },
            ],
        },
        {
            featureType: 'road',
            elementType: 'labels.icon',
            stylers: [
                {
                    visibility: 'off',
                },
            ],
        },
        {
            featureType: 'road',
            elementType: 'labels.text.fill',
            stylers: [
                {
                    color: '#9ca5b3',
                },
            ],
        },
        {
            featureType: 'road.highway',
            elementType: 'geometry',
            stylers: [
                {
                    color: '#746855',
                },
            ],
        },
        {
            featureType: 'road.highway',
            elementType: 'geometry.stroke',
            stylers: [
                {
                    color: '#1f2835',
                },
            ],
        },
        {
            featureType: 'road.highway',
            elementType: 'labels.text.fill',
            stylers: [
                {
                    color: '#f3d19c',
                },
            ],
        },
        {
            featureType: 'transit',
            stylers: [
                {
                    visibility: 'off',
                },
            ],
        },
        {
            featureType: 'transit',
            elementType: 'geometry',
            stylers: [
                {
                    color: '#2f3948',
                },
            ],
        },
        {
            featureType: 'transit.station',
            elementType: 'labels.text.fill',
            stylers: [
                {
                    color: '#d59563',
                },
            ],
        },
        {
            featureType: 'water',
            elementType: 'geometry',
            stylers: [
                {
                    color: '#17263c',
                },
            ],
        },
        {
            featureType: 'water',
            elementType: 'labels.text.fill',
            stylers: [
                {
                    color: '#515c6d',
                },
            ],
        },
        {
            featureType: 'water',
            elementType: 'labels.text.stroke',
            stylers: [
                {
                    color: '#17263c',
                },
            ],
        },
    ],
    dark: [
        {
            elementType: 'geometry',
            stylers: [
                {
                    color: '#212121',
                },
            ],
        },
        {
            elementType: 'labels.icon',
            stylers: [
                {
                    visibility: 'off',
                },
            ],
        },
        {
            elementType: 'labels.text.fill',
            stylers: [
                {
                    color: '#757575',
                },
            ],
        },
        {
            elementType: 'labels.text.stroke',
            stylers: [
                {
                    color: '#212121',
                },
            ],
        },
        {
            featureType: 'administrative',
            elementType: 'geometry',
            stylers: [
                {
                    color: '#757575',
                },
            ],
        },
        {
            featureType: 'administrative.country',
            elementType: 'labels.text.fill',
            stylers: [
                {
                    color: '#9e9e9e',
                },
            ],
        },
        {
            featureType: 'administrative.land_parcel',
            stylers: [
                {
                    visibility: 'off',
                },
            ],
        },
        {
            featureType: 'administrative.locality',
            elementType: 'labels.text.fill',
            stylers: [
                {
                    color: '#bdbdbd',
                },
            ],
        },
        {
            featureType: 'poi',
            elementType: 'labels.text.fill',
            stylers: [
                {
                    color: '#757575',
                },
            ],
        },
        {
            featureType: 'poi.park',
            elementType: 'geometry',
            stylers: [
                {
                    color: '#181818',
                },
            ],
        },
        {
            featureType: 'poi.park',
            elementType: 'labels.text.fill',
            stylers: [
                {
                    color: '#616161',
                },
            ],
        },
        {
            featureType: 'poi.park',
            elementType: 'labels.text.stroke',
            stylers: [
                {
                    color: '#1b1b1b',
                },
            ],
        },
        {
            featureType: 'road',
            elementType: 'geometry.fill',
            stylers: [
                {
                    color: '#2c2c2c',
                },
            ],
        },
        {
            featureType: 'road',
            elementType: 'labels.text.fill',
            stylers: [
                {
                    color: '#8a8a8a',
                },
            ],
        },
        {
            featureType: 'road.arterial',
            elementType: 'geometry',
            stylers: [
                {
                    color: '#373737',
                },
            ],
        },
        {
            featureType: 'road.highway',
            elementType: 'geometry',
            stylers: [
                {
                    color: '#3c3c3c',
                },
            ],
        },
        {
            featureType: 'road.highway.controlled_access',
            elementType: 'geometry',
            stylers: [
                {
                    color: '#4e4e4e',
                },
            ],
        },
        {
            featureType: 'road.local',
            elementType: 'labels.text.fill',
            stylers: [
                {
                    color: '#616161',
                },
            ],
        },
        {
            featureType: 'transit',
            elementType: 'labels.text.fill',
            stylers: [
                {
                    color: '#757575',
                },
            ],
        },
        {
            featureType: 'water',
            elementType: 'geometry',
            stylers: [
                {
                    color: '#000000',
                },
            ],
        },
        {
            featureType: 'water',
            elementType: 'labels.text.fill',
            stylers: [
                {
                    color: '#3d3d3d',
                },
            ],
        },
    ],
    retro: [
        {
            elementType: 'geometry',
            stylers: [
                {
                    color: '#ebe3cd',
                },
            ],
        },
        {
            elementType: 'labels.text.fill',
            stylers: [
                {
                    color: '#523735',
                },
            ],
        },
        {
            elementType: 'labels.text.stroke',
            stylers: [
                {
                    color: '#f5f1e6',
                },
            ],
        },
        {
            featureType: 'administrative',
            elementType: 'geometry.stroke',
            stylers: [
                {
                    color: '#c9b2a6',
                },
            ],
        },
        {
            featureType: 'administrative.land_parcel',
            elementType: 'geometry.stroke',
            stylers: [
                {
                    color: '#dcd2be',
                },
            ],
        },
        {
            featureType: 'administrative.land_parcel',
            elementType: 'labels.text.fill',
            stylers: [
                {
                    color: '#ae9e90',
                },
            ],
        },
        {
            featureType: 'landscape.natural',
            elementType: 'geometry',
            stylers: [
                {
                    color: '#dfd2ae',
                },
            ],
        },
        {
            featureType: 'poi',
            elementType: 'geometry',
            stylers: [
                {
                    color: '#dfd2ae',
                },
            ],
        },
        {
            featureType: 'poi',
            elementType: 'labels.text.fill',
            stylers: [
                {
                    color: '#93817c',
                },
            ],
        },
        {
            featureType: 'poi.park',
            elementType: 'geometry.fill',
            stylers: [
                {
                    color: '#a5b076',
                },
            ],
        },
        {
            featureType: 'poi.park',
            elementType: 'labels.text.fill',
            stylers: [
                {
                    color: '#447530',
                },
            ],
        },
        {
            featureType: 'road',
            elementType: 'geometry',
            stylers: [
                {
                    color: '#f5f1e6',
                },
            ],
        },
        {
            featureType: 'road.arterial',
            elementType: 'geometry',
            stylers: [
                {
                    color: '#fdfcf8',
                },
            ],
        },
        {
            featureType: 'road.highway',
            elementType: 'geometry',
            stylers: [
                {
                    color: '#f8c967',
                },
            ],
        },
        {
            featureType: 'road.highway',
            elementType: 'geometry.stroke',
            stylers: [
                {
                    color: '#e9bc62',
                },
            ],
        },
        {
            featureType: 'road.highway.controlled_access',
            elementType: 'geometry',
            stylers: [
                {
                    color: '#e98d58',
                },
            ],
        },
        {
            featureType: 'road.highway.controlled_access',
            elementType: 'geometry.stroke',
            stylers: [
                {
                    color: '#db8555',
                },
            ],
        },
        {
            featureType: 'road.local',
            elementType: 'labels.text.fill',
            stylers: [
                {
                    color: '#806b63',
                },
            ],
        },
        {
            featureType: 'transit.line',
            elementType: 'geometry',
            stylers: [
                {
                    color: '#dfd2ae',
                },
            ],
        },
        {
            featureType: 'transit.line',
            elementType: 'labels.text.fill',
            stylers: [
                {
                    color: '#8f7d77',
                },
            ],
        },
        {
            featureType: 'transit.line',
            elementType: 'labels.text.stroke',
            stylers: [
                {
                    color: '#ebe3cd',
                },
            ],
        },
        {
            featureType: 'transit.station',
            elementType: 'geometry',
            stylers: [
                {
                    color: '#dfd2ae',
                },
            ],
        },
        {
            featureType: 'water',
            elementType: 'geometry.fill',
            stylers: [
                {
                    color: '#b9d3c2',
                },
            ],
        },
        {
            featureType: 'water',
            elementType: 'labels.text.fill',
            stylers: [
                {
                    color: '#92998d',
                },
            ],
        },
    ],
    silver: [
        {
            elementType: 'geometry',
            stylers: [
                {
                    color: '#f5f5f5',
                },
            ],
        },
        {
            elementType: 'labels.icon',
            stylers: [
                {
                    visibility: 'off',
                },
            ],
        },
        {
            elementType: 'labels.text.fill',
            stylers: [
                {
                    color: '#616161',
                },
            ],
        },
        {
            elementType: 'labels.text.stroke',
            stylers: [
                {
                    color: '#f5f5f5',
                },
            ],
        },
        {
            featureType: 'administrative.land_parcel',
            elementType: 'labels.text.fill',
            stylers: [
                {
                    color: '#bdbdbd',
                },
            ],
        },
        {
            featureType: 'poi',
            elementType: 'geometry',
            stylers: [
                {
                    color: '#eeeeee',
                },
            ],
        },
        {
            featureType: 'poi',
            elementType: 'labels.text.fill',
            stylers: [
                {
                    color: '#757575',
                },
            ],
        },
        {
            featureType: 'poi.park',
            elementType: 'geometry',
            stylers: [
                {
                    color: '#e5e5e5',
                },
            ],
        },
        {
            featureType: 'poi.park',
            elementType: 'labels.text.fill',
            stylers: [
                {
                    color: '#9e9e9e',
                },
            ],
        },
        {
            featureType: 'road',
            elementType: 'geometry',
            stylers: [
                {
                    color: '#ffffff',
                },
            ],
        },
        {
            featureType: 'road.arterial',
            elementType: 'labels.text.fill',
            stylers: [
                {
                    color: '#757575',
                },
            ],
        },
        {
            featureType: 'road.highway',
            elementType: 'geometry',
            stylers: [
                {
                    color: '#dadada',
                },
            ],
        },
        {
            featureType: 'road.highway',
            elementType: 'labels.text.fill',
            stylers: [
                {
                    color: '#616161',
                },
            ],
        },
        {
            featureType: 'road.local',
            elementType: 'labels.text.fill',
            stylers: [
                {
                    color: '#9e9e9e',
                },
            ],
        },
        {
            featureType: 'transit.line',
            elementType: 'geometry',
            stylers: [
                {
                    color: '#e5e5e5',
                },
            ],
        },
        {
            featureType: 'transit.station',
            elementType: 'geometry',
            stylers: [
                {
                    color: '#eeeeee',
                },
            ],
        },
        {
            featureType: 'water',
            elementType: 'geometry',
            stylers: [
                {
                    color: '#c9c9c9',
                },
            ],
        },
        {
            featureType: 'water',
            elementType: 'labels.text.fill',
            stylers: [
                {
                    color: '#9e9e9e',
                },
            ],
        },
    ],
    atlas: [
        {
            stylers: [
                {
                    visibility: 'on',
                },
            ],
        },
        {
            featureType: 'administrative',
            elementType: 'geometry.fill',
            stylers: [
                {
                    color: '#f5f5f5',
                },
            ],
        },
        {
            featureType: 'administrative',
            elementType: 'labels.text.fill',
            stylers: [
                {
                    color: '#003975',
                },
            ],
        },
        {
            featureType: 'administrative.locality',
            elementType: 'labels.text.fill',
            stylers: [
                {
                    weight: 1,
                },
            ],
        },
        {
            featureType: 'administrative.neighborhood',
            elementType: 'labels.text.fill',
            stylers: [
                {
                    color: '#90b1d5',
                },
            ],
        },
        {
            featureType: 'landscape.man_made',
            elementType: 'geometry',
            stylers: [
                {
                    color: '#fcfcfc',
                },
                {
                    visibility: 'on',
                },
            ],
        },
        {
            featureType: 'landscape.natural',
            elementType: 'geometry',
            stylers: [
                {
                    color: '#fcfcfc',
                },
            ],
        },
        {
            featureType: 'landscape.natural.landcover',
            elementType: 'geometry',
            stylers: [
                {
                    color: '#f2f2f2',
                },
            ],
        },
        {
            featureType: 'landscape.natural.terrain',
            elementType: 'geometry',
            stylers: [
                {
                    color: '#bfeecd',
                },
            ],
        },
        {
            featureType: 'poi.attraction',
            elementType: 'labels.icon',
            stylers: [
                {
                    color: '#32b2c3',
                },
            ],
        },
        {
            featureType: 'poi.attraction',
            elementType: 'labels.text.fill',
            stylers: [
                {
                    color: '#32b2c3',
                },
            ],
        },
        {
            featureType: 'poi.business',
            elementType: 'labels.icon',
            stylers: [
                {
                    color: '#6c87ea',
                },
            ],
        },
        {
            featureType: 'poi.business',
            elementType: 'labels.text.fill',
            stylers: [
                {
                    weight: 2,
                },
            ],
        },
        {
            featureType: 'poi.government',
            elementType: 'geometry',
            stylers: [
                {
                    color: '#ebf7ff',
                },
            ],
        },
        {
            featureType: 'poi.park',
            elementType: 'geometry',
            stylers: [
                {
                    color: '#dafbe2',
                },
            ],
        },
        {
            featureType: 'poi.park',
            elementType: 'labels.icon',
            stylers: [
                {
                    color: '#44ca66',
                },
            ],
        },
        {
            featureType: 'poi.park',
            elementType: 'labels.text.fill',
            stylers: [
                {
                    color: '#33a34f',
                },
            ],
        },
        {
            featureType: 'poi.school',
            elementType: 'geometry',
            stylers: [
                {
                    color: '#f5e0f3',
                },
            ],
        },
        {
            featureType: 'road.arterial',
            elementType: 'geometry.fill',
            stylers: [
                {
                    color: '#ededed',
                },
            ],
        },
        {
            featureType: 'road.arterial',
            elementType: 'geometry.stroke',
            stylers: [
                {
                    color: '#cfcfcf',
                },
            ],
        },
        {
            featureType: 'road.highway',
            elementType: 'geometry.fill',
            stylers: [
                {
                    color: '#90d59c',
                },
            ],
        },
        {
            featureType: 'road.highway',
            elementType: 'geometry.stroke',
            stylers: [
                {
                    color: '#598860',
                },
            ],
        },
        {
            featureType: 'road.highway.controlled_access',
            elementType: 'geometry.fill',
            stylers: [
                {
                    color: '#8ac0f0',
                },
            ],
        },
        {
            featureType: 'road.highway.controlled_access',
            elementType: 'geometry.stroke',
            stylers: [
                {
                    color: '#2e7dc2',
                },
            ],
        },
        {
            featureType: 'road.local',
            elementType: 'geometry.fill',
            stylers: [
                {
                    color: '#fcfcfc',
                },
            ],
        },
        {
            featureType: 'road.local',
            elementType: 'geometry.stroke',
            stylers: [
                {
                    color: '#93d3fb',
                },
            ],
        },
        {
            featureType: 'transit',
            stylers: [
                {
                    visibility: 'off',
                },
            ],
        },
        {
            featureType: 'water',
            elementType: 'geometry',
            stylers: [
                {
                    color: '#bde6fa',
                },
            ],
        },
    ],
    muted_blue: [
        {
            featureType: 'all',
            stylers: [
                {
                    saturation: 0,
                },
                {
                    hue: '#e7ecf0',
                },
            ],
        },
        {
            featureType: 'road',
            stylers: [
                {
                    saturation: -70,
                },
            ],
        },
        {
            featureType: 'transit',
            stylers: [
                {
                    visibility: 'off',
                },
            ],
        },
        {
            featureType: 'poi',
            stylers: [
                {
                    visibility: 'off',
                },
            ],
        },
        {
            featureType: 'water',
            stylers: [
                {
                    visibility: 'simplified',
                },
                {
                    saturation: -60,
                },
            ],
        },
    ],
    pale_down: [
        {
            featureType: 'administrative',
            elementType: 'all',
            stylers: [
                {
                    visibility: 'on',
                },
                {
                    lightness: 33,
                },
            ],
        },
        {
            featureType: 'landscape',
            elementType: 'all',
            stylers: [
                {
                    color: '#f2e5d4',
                },
            ],
        },
        {
            featureType: 'poi.park',
            elementType: 'geometry',
            stylers: [
                {
                    color: '#c5dac6',
                },
            ],
        },
        {
            featureType: 'poi.park',
            elementType: 'labels',
            stylers: [
                {
                    visibility: 'on',
                },
                {
                    lightness: 20,
                },
            ],
        },
        {
            featureType: 'road',
            elementType: 'all',
            stylers: [
                {
                    lightness: 20,
                },
            ],
        },
        {
            featureType: 'road.highway',
            elementType: 'geometry',
            stylers: [
                {
                    color: '#c5c6c6',
                },
            ],
        },
        {
            featureType: 'road.arterial',
            elementType: 'geometry',
            stylers: [
                {
                    color: '#e4d7c6',
                },
            ],
        },
        {
            featureType: 'road.local',
            elementType: 'geometry',
            stylers: [
                {
                    color: '#fbfaf7',
                },
            ],
        },
        {
            featureType: 'water',
            elementType: 'all',
            stylers: [
                {
                    visibility: 'on',
                },
                {
                    color: '#acbcc9',
                },
            ],
        },
    ],
    subtle_gray: [
        {
            featureType: 'administrative',
            elementType: 'all',
            stylers: [
                {
                    saturation: '-100',
                },
            ],
        },
        {
            featureType: 'administrative.province',
            elementType: 'all',
            stylers: [
                {
                    visibility: 'off',
                },
            ],
        },
        {
            featureType: 'landscape',
            elementType: 'all',
            stylers: [
                {
                    saturation: -100,
                },
                {
                    lightness: 65,
                },
                {
                    visibility: 'on',
                },
            ],
        },
        {
            featureType: 'poi',
            elementType: 'all',
            stylers: [
                {
                    saturation: -100,
                },
                {
                    lightness: '50',
                },
                {
                    visibility: 'simplified',
                },
            ],
        },
        {
            featureType: 'road',
            elementType: 'all',
            stylers: [
                {
                    saturation: '-100',
                },
            ],
        },
        {
            featureType: 'road.highway',
            elementType: 'all',
            stylers: [
                {
                    visibility: 'simplified',
                },
            ],
        },
        {
            featureType: 'road.arterial',
            elementType: 'all',
            stylers: [
                {
                    lightness: '30',
                },
            ],
        },
        {
            featureType: 'road.local',
            elementType: 'all',
            stylers: [
                {
                    lightness: '40',
                },
            ],
        },
        {
            featureType: 'transit',
            elementType: 'all',
            stylers: [
                {
                    saturation: -100,
                },
                {
                    visibility: 'simplified',
                },
            ],
        },
        {
            featureType: 'water',
            elementType: 'geometry',
            stylers: [
                {
                    hue: '#ffff00',
                },
                {
                    lightness: -25,
                },
                {
                    saturation: -97,
                },
            ],
        },
        {
            featureType: 'water',
            elementType: 'labels',
            stylers: [
                {
                    lightness: -25,
                },
                {
                    saturation: -100,
                },
            ],
        },
    ],
    shift_worker: [
        {
            stylers: [
                {
                    saturation: -100,
                },
                {
                    gamma: 1,
                },
            ],
        },
        {
            elementType: 'labels.text.stroke',
            stylers: [
                {
                    visibility: 'off',
                },
            ],
        },
        {
            featureType: 'poi.business',
            elementType: 'labels.text',
            stylers: [
                {
                    visibility: 'off',
                },
            ],
        },
        {
            featureType: 'poi.business',
            elementType: 'labels.icon',
            stylers: [
                {
                    visibility: 'off',
                },
            ],
        },
        {
            featureType: 'poi.place_of_worship',
            elementType: 'labels.text',
            stylers: [
                {
                    visibility: 'off',
                },
            ],
        },
        {
            featureType: 'poi.place_of_worship',
            elementType: 'labels.icon',
            stylers: [
                {
                    visibility: 'off',
                },
            ],
        },
        {
            featureType: 'road',
            elementType: 'geometry',
            stylers: [
                {
                    visibility: 'simplified',
                },
            ],
        },
        {
            featureType: 'water',
            stylers: [
                {
                    visibility: 'on',
                },
                {
                    saturation: 50,
                },
                {
                    gamma: 0,
                },
                {
                    hue: '#50a5d1',
                },
            ],
        },
        {
            featureType: 'administrative.neighborhood',
            elementType: 'labels.text.fill',
            stylers: [
                {
                    color: '#333333',
                },
            ],
        },
        {
            featureType: 'road.local',
            elementType: 'labels.text',
            stylers: [
                {
                    weight: 0.5,
                },
                {
                    color: '#333333',
                },
            ],
        },
        {
            featureType: 'transit.station',
            elementType: 'labels.icon',
            stylers: [
                {
                    gamma: 1,
                },
                {
                    saturation: 50,
                },
            ],
        },
    ],
    even_lighter: [
        {
            featureType: 'administrative',
            elementType: 'labels.text.fill',
            stylers: [
                {
                    color: '#6195a0',
                },
            ],
        },
        {
            featureType: 'landscape',
            elementType: 'all',
            stylers: [
                {
                    color: '#f2f2f2',
                },
            ],
        },
        {
            featureType: 'landscape',
            elementType: 'geometry.fill',
            stylers: [
                {
                    color: '#ffffff',
                },
            ],
        },
        {
            featureType: 'poi',
            elementType: 'all',
            stylers: [
                {
                    visibility: 'off',
                },
            ],
        },
        {
            featureType: 'poi.park',
            elementType: 'geometry.fill',
            stylers: [
                {
                    color: '#e6f3d6',
                },
                {
                    visibility: 'on',
                },
            ],
        },
        {
            featureType: 'road',
            elementType: 'all',
            stylers: [
                {
                    saturation: -100,
                },
                {
                    lightness: 45,
                },
                {
                    visibility: 'simplified',
                },
            ],
        },
        {
            featureType: 'road.highway',
            elementType: 'all',
            stylers: [
                {
                    visibility: 'simplified',
                },
            ],
        },
        {
            featureType: 'road.highway',
            elementType: 'geometry.fill',
            stylers: [
                {
                    color: '#f4d2c5',
                },
                {
                    visibility: 'simplified',
                },
            ],
        },
        {
            featureType: 'road.highway',
            elementType: 'labels.text',
            stylers: [
                {
                    color: '#4e4e4e',
                },
            ],
        },
        {
            featureType: 'road.arterial',
            elementType: 'geometry.fill',
            stylers: [
                {
                    color: '#f4f4f4',
                },
            ],
        },
        {
            featureType: 'road.arterial',
            elementType: 'labels.text.fill',
            stylers: [
                {
                    color: '#787878',
                },
            ],
        },
        {
            featureType: 'road.arterial',
            elementType: 'labels.icon',
            stylers: [
                {
                    visibility: 'off',
                },
            ],
        },
        {
            featureType: 'transit',
            elementType: 'all',
            stylers: [
                {
                    visibility: 'off',
                },
            ],
        },
        {
            featureType: 'water',
            elementType: 'all',
            stylers: [
                {
                    color: '#eaf6f8',
                },
                {
                    visibility: 'on',
                },
            ],
        },
        {
            featureType: 'water',
            elementType: 'geometry.fill',
            stylers: [
                {
                    color: '#eaf6f8',
                },
            ],
        },
    ],
    unsaturated_brown: [
        {
            elementType: 'geometry',
            stylers: [
                {
                    hue: '#ff4400',
                },
                {
                    saturation: -68,
                },
                {
                    lightness: -4,
                },
                {
                    gamma: 0.72,
                },
            ],
        },
        {
            featureType: 'road',
            elementType: 'labels.icon',
        },
        {
            featureType: 'landscape.man_made',
            elementType: 'geometry',
            stylers: [
                {
                    hue: '#0077ff',
                },
                {
                    gamma: 3.1,
                },
            ],
        },
        {
            featureType: 'water',
            stylers: [
                {
                    hue: '#00ccff',
                },
                {
                    gamma: 0.44,
                },
                {
                    saturation: -33,
                },
            ],
        },
        {
            featureType: 'poi.park',
            stylers: [
                {
                    hue: '#44ff00',
                },
                {
                    saturation: -23,
                },
            ],
        },
        {
            featureType: 'water',
            elementType: 'labels.text.fill',
            stylers: [
                {
                    hue: '#007fff',
                },
                {
                    gamma: 0.77,
                },
                {
                    saturation: 65,
                },
                {
                    lightness: 99,
                },
            ],
        },
        {
            featureType: 'water',
            elementType: 'labels.text.stroke',
            stylers: [
                {
                    gamma: 0.11,
                },
                {
                    weight: 5.6,
                },
                {
                    saturation: 99,
                },
                {
                    hue: '#0091ff',
                },
                {
                    lightness: -86,
                },
            ],
        },
        {
            featureType: 'transit.line',
            elementType: 'geometry',
            stylers: [
                {
                    lightness: -48,
                },
                {
                    hue: '#ff5e00',
                },
                {
                    gamma: 1.2,
                },
                {
                    saturation: -23,
                },
            ],
        },
        {
            featureType: 'transit',
            elementType: 'labels.text.stroke',
            stylers: [
                {
                    saturation: -64,
                },
                {
                    hue: '#ff9100',
                },
                {
                    lightness: 16,
                },
                {
                    gamma: 0.47,
                },
                {
                    weight: 2.7,
                },
            ],
        },
    ],
    uber: [
        {
            featureType: 'administrative',
            elementType: 'geometry.fill',
            stylers: [
                {
                    color: '#d6e2e6',
                },
            ],
        },
        {
            featureType: 'administrative',
            elementType: 'geometry.stroke',
            stylers: [
                {
                    color: '#cfd4d5',
                },
            ],
        },
        {
            featureType: 'administrative',
            elementType: 'labels.text.fill',
            stylers: [
                {
                    color: '#7492a8',
                },
            ],
        },
        {
            featureType: 'administrative.neighborhood',
            elementType: 'labels.text.fill',
            stylers: [
                {
                    lightness: 25,
                },
            ],
        },
        {
            featureType: 'landscape.man_made',
            elementType: 'geometry.fill',
            stylers: [
                {
                    color: '#dde2e3',
                },
            ],
        },
        {
            featureType: 'landscape.man_made',
            elementType: 'geometry.stroke',
            stylers: [
                {
                    color: '#cfd4d5',
                },
            ],
        },
        {
            featureType: 'landscape.natural',
            elementType: 'geometry.fill',
            stylers: [
                {
                    color: '#dde2e3',
                },
            ],
        },
        {
            featureType: 'landscape.natural',
            elementType: 'labels.text.fill',
            stylers: [
                {
                    color: '#7492a8',
                },
            ],
        },
        {
            featureType: 'landscape.natural.terrain',
            elementType: 'all',
            stylers: [
                {
                    visibility: 'off',
                },
            ],
        },
        {
            featureType: 'poi',
            elementType: 'geometry.fill',
            stylers: [
                {
                    color: '#dde2e3',
                },
            ],
        },
        {
            featureType: 'poi',
            elementType: 'labels.text.fill',
            stylers: [
                {
                    color: '#588ca4',
                },
            ],
        },
        {
            featureType: 'poi',
            elementType: 'labels.icon',
            stylers: [
                {
                    saturation: -100,
                },
            ],
        },
        {
            featureType: 'poi.park',
            elementType: 'geometry.fill',
            stylers: [
                {
                    color: '#a9de83',
                },
            ],
        },
        {
            featureType: 'poi.park',
            elementType: 'geometry.stroke',
            stylers: [
                {
                    color: '#bae6a1',
                },
            ],
        },
        {
            featureType: 'poi.sports_complex',
            elementType: 'geometry.fill',
            stylers: [
                {
                    color: '#c6e8b3',
                },
            ],
        },
        {
            featureType: 'poi.sports_complex',
            elementType: 'geometry.stroke',
            stylers: [
                {
                    color: '#bae6a1',
                },
            ],
        },
        {
            featureType: 'road',
            elementType: 'labels.text.fill',
            stylers: [
                {
                    color: '#41626b',
                },
            ],
        },
        {
            featureType: 'road',
            elementType: 'labels.icon',
            stylers: [
                {
                    saturation: -45,
                },
                {
                    lightness: 10,
                },
                {
                    visibility: 'on',
                },
            ],
        },
        {
            featureType: 'road.highway',
            elementType: 'geometry.fill',
            stylers: [
                {
                    color: '#c1d1d6',
                },
            ],
        },
        {
            featureType: 'road.highway',
            elementType: 'geometry.stroke',
            stylers: [
                {
                    color: '#a6b5bb',
                },
            ],
        },
        {
            featureType: 'road.highway',
            elementType: 'labels.icon',
            stylers: [
                {
                    visibility: 'on',
                },
            ],
        },
        {
            featureType: 'road.highway.controlled_access',
            elementType: 'geometry.fill',
            stylers: [
                {
                    color: '#9fb6bd',
                },
            ],
        },
        {
            featureType: 'road.arterial',
            elementType: 'geometry.fill',
            stylers: [
                {
                    color: '#ffffff',
                },
            ],
        },
        {
            featureType: 'road.local',
            elementType: 'geometry.fill',
            stylers: [
                {
                    color: '#ffffff',
                },
            ],
        },
        {
            featureType: 'transit',
            elementType: 'labels.icon',
            stylers: [
                {
                    saturation: -70,
                },
            ],
        },
        {
            featureType: 'transit.line',
            elementType: 'geometry.fill',
            stylers: [
                {
                    color: '#b4cbd4',
                },
            ],
        },
        {
            featureType: 'transit.line',
            elementType: 'labels.text.fill',
            stylers: [
                {
                    color: '#588ca4',
                },
            ],
        },
        {
            featureType: 'transit.station',
            elementType: 'all',
            stylers: [
                {
                    visibility: 'off',
                },
            ],
        },
        {
            featureType: 'transit.station',
            elementType: 'labels.text.fill',
            stylers: [
                {
                    color: '#008cb5',
                },
                {
                    visibility: 'on',
                },
            ],
        },
        {
            featureType: 'transit.station.airport',
            elementType: 'geometry.fill',
            stylers: [
                {
                    saturation: -100,
                },
                {
                    lightness: -5,
                },
            ],
        },
        {
            featureType: 'water',
            elementType: 'geometry.fill',
            stylers: [
                {
                    color: '#a6cbe3',
                },
            ],
        },
    ],
    wy: [
        {
            featureType: 'all',
            elementType: 'geometry.fill',
            stylers: [
                {
                    weight: '2.00',
                },
            ],
        },
        {
            featureType: 'all',
            elementType: 'geometry.stroke',
            stylers: [
                {
                    color: '#9c9c9c',
                },
            ],
        },
        {
            featureType: 'all',
            elementType: 'labels.text',
            stylers: [
                {
                    visibility: 'on',
                },
            ],
        },
        {
            featureType: 'landscape',
            elementType: 'all',
            stylers: [
                {
                    color: '#f2f2f2',
                },
            ],
        },
        {
            featureType: 'landscape',
            elementType: 'geometry.fill',
            stylers: [
                {
                    color: '#ffffff',
                },
            ],
        },
        {
            featureType: 'landscape.man_made',
            elementType: 'geometry.fill',
            stylers: [
                {
                    color: '#ffffff',
                },
            ],
        },
        {
            featureType: 'poi',
            elementType: 'all',
            stylers: [
                {
                    visibility: 'off',
                },
            ],
        },
        {
            featureType: 'road',
            elementType: 'all',
            stylers: [
                {
                    saturation: -100,
                },
                {
                    lightness: 45,
                },
            ],
        },
        {
            featureType: 'road',
            elementType: 'geometry.fill',
            stylers: [
                {
                    color: '#eeeeee',
                },
            ],
        },
        {
            featureType: 'road',
            elementType: 'labels.text.fill',
            stylers: [
                {
                    color: '#7b7b7b',
                },
            ],
        },
        {
            featureType: 'road',
            elementType: 'labels.text.stroke',
            stylers: [
                {
                    color: '#ffffff',
                },
            ],
        },
        {
            featureType: 'road.highway',
            elementType: 'all',
            stylers: [
                {
                    visibility: 'simplified',
                },
            ],
        },
        {
            featureType: 'road.arterial',
            elementType: 'labels.icon',
            stylers: [
                {
                    visibility: 'off',
                },
            ],
        },
        {
            featureType: 'transit',
            elementType: 'all',
            stylers: [
                {
                    visibility: 'off',
                },
            ],
        },
        {
            featureType: 'water',
            elementType: 'all',
            stylers: [
                {
                    color: '#46bcec',
                },
                {
                    visibility: 'on',
                },
            ],
        },
        {
            featureType: 'water',
            elementType: 'geometry.fill',
            stylers: [
                {
                    color: '#c8d7d4',
                },
            ],
        },
        {
            featureType: 'water',
            elementType: 'labels.text.fill',
            stylers: [
                {
                    color: '#070707',
                },
            ],
        },
        {
            featureType: 'water',
            elementType: 'labels.text.stroke',
            stylers: [
                {
                    color: '#ffffff',
                },
            ],
        },
    ],
    interface_map: [
        {
            featureType: 'all',
            elementType: 'labels.text',
            stylers: [
                {
                    color: '#878787',
                },
            ],
        },
        {
            featureType: 'all',
            elementType: 'labels.text.stroke',
            stylers: [
                {
                    visibility: 'off',
                },
            ],
        },
        {
            featureType: 'landscape',
            elementType: 'all',
            stylers: [
                {
                    color: '#f9f5ed',
                },
            ],
        },
        {
            featureType: 'road.highway',
            elementType: 'all',
            stylers: [
                {
                    color: '#f5f5f5',
                },
            ],
        },
        {
            featureType: 'road.highway',
            elementType: 'geometry.stroke',
            stylers: [
                {
                    color: '#c9c9c9',
                },
            ],
        },
        {
            featureType: 'water',
            elementType: 'all',
            stylers: [
                {
                    color: '#aee0f4',
                },
            ],
        },
    ],
    blue_water: [
        {
            featureType: 'administrative',
            elementType: 'labels.text.fill',
            stylers: [
                {
                    color: '#444444',
                },
            ],
        },
        {
            featureType: 'landscape',
            elementType: 'all',
            stylers: [
                {
                    color: '#f2f2f2',
                },
            ],
        },
        {
            featureType: 'poi',
            elementType: 'all',
            stylers: [
                {
                    visibility: 'off',
                },
            ],
        },
        {
            featureType: 'road',
            elementType: 'all',
            stylers: [
                {
                    saturation: -100,
                },
                {
                    lightness: 45,
                },
            ],
        },
        {
            featureType: 'road.highway',
            elementType: 'all',
            stylers: [
                {
                    visibility: 'simplified',
                },
            ],
        },
        {
            featureType: 'road.arterial',
            elementType: 'labels.icon',
            stylers: [
                {
                    visibility: 'off',
                },
            ],
        },
        {
            featureType: 'transit',
            elementType: 'all',
            stylers: [
                {
                    visibility: 'off',
                },
            ],
        },
        {
            featureType: 'water',
            elementType: 'all',
            stylers: [
                {
                    color: '#46bcec',
                },
                {
                    visibility: 'on',
                },
            ],
        },
    ],
    blue_essense: [
        {
            featureType: 'landscape.natural',
            elementType: 'geometry.fill',
            stylers: [
                {
                    visibility: 'on',
                },
                {
                    color: '#e0efef',
                },
            ],
        },
        {
            featureType: 'poi',
            elementType: 'geometry.fill',
            stylers: [
                {
                    visibility: 'on',
                },
                {
                    hue: '#1900ff',
                },
                {
                    color: '#c0e8e8',
                },
            ],
        },
        {
            featureType: 'road',
            elementType: 'geometry',
            stylers: [
                {
                    lightness: 100,
                },
                {
                    visibility: 'simplified',
                },
            ],
        },
        {
            featureType: 'road',
            elementType: 'labels',
            stylers: [
                {
                    visibility: 'off',
                },
            ],
        },
        {
            featureType: 'transit.line',
            elementType: 'geometry',
            stylers: [
                {
                    visibility: 'on',
                },
                {
                    lightness: 700,
                },
            ],
        },
        {
            featureType: 'water',
            elementType: 'all',
            stylers: [
                {
                    color: '#7dcdcd',
                },
            ],
        },
    ],
    line_drawing: [
        {
            featureType: 'all',
            elementType: 'geometry',
            stylers: [
                {
                    visibility: 'off',
                },
            ],
        },
        {
            featureType: 'all',
            elementType: 'labels',
            stylers: [
                {
                    visibility: 'off',
                },
            ],
        },
        {
            featureType: 'landscape',
            elementType: 'all',
            stylers: [
                {
                    color: '#ffffff',
                },
                {
                    visibility: 'on',
                },
            ],
        },
        {
            featureType: 'road',
            elementType: 'geometry',
            stylers: [
                {
                    visibility: 'simplified',
                },
                {
                    color: '#000000',
                },
                {
                    weight: '.88',
                },
            ],
        },
        {
            featureType: 'road',
            elementType: 'labels',
            stylers: [
                {
                    visibility: 'simplified',
                },
            ],
        },
        {
            featureType: 'road',
            elementType: 'labels.text',
            stylers: [
                {
                    visibility: 'simplified',
                },
                {
                    color: '#010101',
                },
            ],
        },
        {
            featureType: 'road',
            elementType: 'labels.text.fill',
            stylers: [
                {
                    color: '#010101',
                },
            ],
        },
        {
            featureType: 'road',
            elementType: 'labels.text.stroke',
            stylers: [
                {
                    color: '#ffffff',
                },
                {
                    visibility: 'simplified',
                },
                {
                    weight: '1.50',
                },
            ],
        },
        {
            featureType: 'road.highway',
            elementType: 'all',
            stylers: [
                {
                    visibility: 'simplified',
                },
            ],
        },
        {
            featureType: 'road.highway',
            elementType: 'labels',
            stylers: [
                {
                    visibility: 'off',
                },
            ],
        },
        {
            featureType: 'road.arterial',
            elementType: 'labels',
            stylers: [
                {
                    visibility: 'simplified',
                },
            ],
        },
        {
            featureType: 'road.local',
            elementType: 'labels',
            stylers: [
                {
                    visibility: 'on',
                },
            ],
        },
        {
            featureType: 'road.local',
            elementType: 'labels.text.stroke',
            stylers: [
                {
                    hue: '#ff0000',
                },
                {
                    visibility: 'on',
                },
            ],
        },
        {
            featureType: 'water',
            elementType: 'all',
            stylers: [
                {
                    color: '#ffffff',
                },
                {
                    visibility: 'simplified',
                },
            ],
        },
    ],
};
