# -*- coding: utf-8 -*-
import json
import time
from odoo import http

from odoo.tools.safe_eval import safe_eval, time
from werkzeug.urls import url_decode
from odoo.http import content_disposition, request, \
    serialize_exception as _serialize_exception

from odoo.tools import html_escape
import logging
_logger = logging.getLogger(__name__)

from odoo.addons.web.controllers.report import ReportController

class ReportControllerInherit(ReportController):

    @http.route([
        '/report/<converter>/<reportname>',
        '/report/<converter>/<reportname>/<docids>',
    ], type='http', auth='user', website=True)
    def report_routes(self, reportname, docids=None, converter=None, **data):
        report = request.env['ir.actions.report']._get_report_from_name(reportname)
        context = dict(request.env.context)

        if converter == 'pdf' and report.populating_ms_word_template:
            if docids:
                docids = [int(i) for i in docids.split(',')]
            if data.get('options'):
                data.update(json.loads(data.pop('options')))
            if data.get('context'):
                # Ignore 'lang' here, because the context in data is the one from the webclient *but* if
                # the user explicitely wants to change the lang, this mechanism overwrites it.
                data['context'] = json.loads(data['context'])
                if data['context'].get('lang'):
                    del data['context']['lang']
                context.update(data['context'])
            datas = request.env[report.model].search([('id', '=', docids[0])])
            if report.type_export == 'pdf':
                pdf = report.with_context(context).render_doc_doc(datas, data=data)[0]
                pdfhttpheaders = [('Content-Type', 'application/pdf'), ('Content-Length', len(pdf))]
                return request.make_response(pdf, headers=pdfhttpheaders)
            else:
                docx = report.with_context(context).render_doc_doc(datas, data=data)[0]
                docxhttpheaders = [
                    ('Content-Type', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')]
                return request.make_response(docx, headers=docxhttpheaders)
        else:
            return super(ReportControllerInherit, self).report_routes(reportname,docids,converter,**data)

    @http.route(['/report/download'], type='http', auth="user")
    def report_download(self, data, context=None):
        requestcontent = json.loads(data)
        url, type = requestcontent[0], requestcontent[1]
        reportname = '???'
        try:
            if type in ['qweb-pdf', 'qweb-text']:
                converter = 'pdf' if type == 'qweb-pdf' else 'text'
                extension = 'pdf' if type == 'qweb-pdf' else 'txt'

                pattern = '/report/pdf/' if type == 'qweb-pdf' else '/report/text/'
                reportname = url.split(pattern)[1].split('?')[0]

                docids = None
                if '/' in reportname:
                    reportname, docids = reportname.split('/')

                if docids:
                    # Generic report:
                    response = self.report_routes(reportname, docids=docids, converter=converter, context=context)
                else:
                    # Particular report:
                    data = dict(url_decode(url.split('?')[1]).items())  # decoding the args represented in JSON
                    if 'context' in data:
                        context, data_context = json.loads(context or '{}'), json.loads(data.pop('context'))
                        context = json.dumps({**context, **data_context})
                    response = self.report_routes(reportname, converter=converter, context=context, **data)

                report = request.env['ir.actions.report']._get_report_from_name(reportname)
                if not report.populating_ms_word_template:
                    return super(ReportControllerInherit, self).report_download(data,context)
                if report.type_export == 'pdf':
                    extension = 'pdf'
                else:
                    extension = 'docx'

                filename = "%s.%s" % (report.name, extension)

                if docids:
                    ids = [int(x) for x in docids.split(",")]
                    obj = request.env[report.model].browse(ids)
                    if report.print_report_name and not len(obj) > 1:
                        report_name = safe_eval(report.print_report_name, {'object': obj, 'time': time})
                        filename = "%s.%s" % (report_name, extension)
                response.headers.add('Content-Disposition', content_disposition(filename))
                return response
            else:
                return
        except Exception as e:
            _logger.exception("Error while generating report %s", reportname)
            se = _serialize_exception(e)
            error = {
                'code': 200,
                'message': "Odoo Server Error",
                'data': se
            }
            return request.make_response(html_escape(json.dumps(error)))
