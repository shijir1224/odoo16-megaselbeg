odoo.define('mw_crm_call.crm_state', function (require) {
    "use strict";
    var AbstractField = require('web.AbstractField');
    var core = require('web.core');
    var field_registry = require('web.field_registry');
    var time = require('web.time');
    /**
     * This widget is used to display the availability on a workorder.
     */
    
    var TimeCounter = AbstractField.extend({
        supportedFieldTypes: [],
        /**
         * @override
         */
        

        willStart: function () {
            var self = this;
            var def = this._rpc({
                model: 'crm.call',
                method: 'search_read',
                domain: [
                    ['id', '=', this.record.data.id],
                ],
            }).then(function (result) {
                // if (self.mode === 'readonly') {
                var currentDate = new Date();
                self.duration = 0;
                _.each(result, function (data) {
                    self.duration += data.date_closed ?
                        self._getDateDifference(data.date_open, data.date_closed) :
                        self._getDateDifference(time.auto_str_to_date(data.date_open), currentDate);
                });
                // }
            });
            return Promise.all([this._super.apply(this, arguments), def]);
        },
    
        destroy: function () {
            this._super.apply(this, arguments);
            clearTimeout(this.timer);
        },
    
        //--------------------------------------------------------------------------
        // Public
        //--------------------------------------------------------------------------
    
        /**
         * @override
         */
        isSet: function () {
            return true;
        },
    
        //--------------------------------------------------------------------------
        // Private
        //--------------------------------------------------------------------------
    
        /**
         * Compute the difference between two dates.
         *
         * @private
         * @param {string} dateStart
         * @param {string} dateEnd
         * @returns {integer} the difference in millisecond
         */
        _getDateDifference: function (dateStart, dateEnd) {
            return moment(dateEnd).diff(moment(dateStart));
        },
        /**
         * @override
         */
        _render: function () {
            this._startTimeCounter();
        },
        /**
         * @private
         */
        _startTimeCounter: function () {
            var self = this;
            self.duration = self.duration ? self.duration : 0;
            clearTimeout(this.timer);
            console.log('this.record.dateee',this.record.data.state);
            if (this.record.data.state == 'draft') {
                this.timer = setTimeout(function () {
                    self.duration += 1000;
                    self._startTimeCounter();
                }, 1000);
            } else {
                clearTimeout(this.timer);
            }
            this.$el.html($('<span>' + moment.utc(this.duration).format("HH:mm:ss") + '</span>'));
        },
    });
    
    
    
    field_registry
        .add('crm_time_counter', TimeCounter);
    
    });
    