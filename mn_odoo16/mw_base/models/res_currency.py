# -*- coding: utf-8 -*-

from odoo import api, fields, models
import logging
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import requests
from dateutil.relativedelta import relativedelta
from datetime import datetime, date as cnvert_date, timedelta
import time
_logger = logging.getLogger(__name__)


class Currency(models.Model):
    _inherit = "res.currency"
    _description = "Currency"

    @api.model
    def _get_conversion_rate(self, from_currency, to_currency, company, date):
        currency_rates = (from_currency + to_currency)._get_rates(company, date)
        res = currency_rates.get(from_currency.id) / currency_rates.get(to_currency.id)
        _logger.warning('rate res {}.'.format(res))
        return res

    def _download_currency_rate(self,from_date=None):
        rate_obj = self.env['res.currency.rate']
        curr_obj = self.env['res.currency']
        companies = self.env['res.company'].search([])
        if not from_date:
            rate_date = (fields.Date.today() - relativedelta(days=1)).strftime('%Y-%m-%d')
            date  = (fields.Date.today()).strftime('%Y-%m-%d')
            for record in curr_obj.search([('active','=',True)]):
    #             rate = requests.get('http://monxansh.appspot.com/xansh.json?currency=' + record.name)
                url='https://www.mongolbank.mn/api/v1/currencyrate/single?currency={0}&date={1}'.format(record.name,rate_date)
                rate = requests.get(url)
                rate_json = rate.json()
                _logger.warning('record.name res {}.'.format(record.name))
                if rate_json.get('success',False):
                    rate = float(rate_json['result'][record.name].replace(',',''))
                    _logger.warning('rate res {}.'.format(rate))
    #                 date = datetime.strptime(rate_json['result']['RATE_DATE'], DEFAULT_SERVER_DATETIME_FORMAT)
    #                 if date.day != fields.Date.today().day:
    #                     date = date + relativedelta(days=1)
                    for company in companies:
                            _logger.warning('company res {}.'.format(company))
                            existing_rate = rate_obj.search([('currency_id', '=', record.id), ('name', '=', date), ('company_id', '=',  company.id)])
                            _logger.warning('existing_rate res {}.'.format(existing_rate))
                            if not existing_rate:
                                rate_obj.create({
                                    'currency_id': record.id,
                                    'company_id': company.id,
                                    'name': date,
                                    'rate': rate,
                                })            
        else:
            rate_date = datetime.strptime(from_date, '%Y-%m-%d')
            date  = (rate_date).strftime('%Y-%m-%d')
#             rate_date = (rate_date - relativedelta(days=1)).strftime('%Y-%m-%d')
#             start_date = cnvert_date(2023, 3, 1)
            start_date = cnvert_date(int(from_date.split('-')[0]), int(from_date.split('-')[1]), int(from_date.split('-')[2]))
            end_date = (fields.Date.today()) #.strftime('%Y-%m-%d')
            delta = timedelta(days=1)
            
            while start_date <= end_date:
                for record in curr_obj.search([('active','=',True),('name','!=','MNT')]):
        #             rate = requests.get('http://monxansh.appspot.com/xansh.json?currency=' + record.name)
                    url='https://www.mongolbank.mn/api/v1/currencyrate/single?currency={0}&date={1}'.format(record.name,start_date)
                    rate = requests.get(url)
                    rate_json = rate.json()
                    _logger.warning('record.name res {}.'.format(record.name))
                    _logger.warning('rate_json {}.'.format(rate_json))
                    time.sleep(2)
                    if rate_json.get('success',False):
                        rate = float(rate_json['result'][record.name].replace(',',''))
                        _logger.warning('rate res {}.'.format(rate))
        #                 date = datetime.strptime(rate_json['result']['RATE_DATE'], DEFAULT_SERVER_DATETIME_FORMAT)
        #                 if date.day != fields.Date.today().day:
        #                     date = date + relativedelta(days=1)
                        start_date += delta
                        for company in companies:
                                _logger.warning('company res {}.'.format(company))
                                existing_rate = rate_obj.search([('currency_id', '=', record.id), ('name', '=', start_date), ('company_id', '=',  company.id)])
                                _logger.warning('existing_rate res {}.'.format(existing_rate))
                                if not existing_rate:
                                    rate_obj.create({
                                        'currency_id': record.id,
                                        'company_id': company.id,
                                        'name': start_date,
                                        'rate': rate,
                                    }) 
                start_date += delta
                time.sleep(1)
