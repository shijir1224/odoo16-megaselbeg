# -*- coding: utf-8 -*-
##############################################################################
#
#   USI-ERP, Enterprise Management Solution	
#   Copyright (C) 2007-2010 USI Co.,ltd (<http://www.usi.mn>). All Rights Reserved
#	
#	ЮүЭсАй-ЕРП, Байгууллагын цогц мэдээлэлийн систем
#	зохиогчийн эрх авсан 2007-2010 ЮүЭсАй ХХК (<http://www.usi.mn>). 
#	
#	Зохиогчийн зөвшөөрөлгүйгээр хуулбарлах ашиглахыг хориглоно.
#	
#	Харилцах хаяг : 
#	Э-майл : info@usi.mn
#	Утас : 976 + 70151145
#	Факс : 976 + 70151146
#	Баянзүрх дүүрэг, 4-р хороо, Энхүүд төв,
#	Улаанбаатар, Монгол Улс
#	
##############################################################################
from odoo.addons.c2c_reporting_tools.reports.standard_report import *
from odoo.addons.c2c_reporting_tools.flowables.simple_row_table import *
from odoo.addons.c2c_reporting_tools.c2c_helper import *
from odoo.addons.c2c_reporting_tools.translation import _
from reportlab.platypus import *
from reportlab.lib.colors import red, black, navy, white, green
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER, TA_JUSTIFY
from odoo.tools.translate import _
import time

class account_cash_transaction(StandardReport):
    ''' Бэлэн мөнгөний гүйлгээний тайлан
    '''
    th_style = ParagraphStyle('tableheaderbold', fontName='Helvetica-Bold', fontSize=7, leading=10, 
                alignment=TA_CENTER, leftIndent=3, rightIndent=3, spaceAfter=2, spaceBefore=2)
    td_right_style = ParagraphStyle('tabledataright', fontName='Helvetica', fontSize=6, leading=9, 
                    alignment=TA_RIGHT, leftIndent=3, rightIndent=1, spaceAfter=1, spaceBefore=2)
    td_left_style = ParagraphStyle('tabledataleft', fontName='Helvetica', fontSize=6, leading=9, 
                    alignment=TA_LEFT, leftIndent=1, rightIndent=3, spaceAfter=1, spaceBefore=2)
    td_center_style = ParagraphStyle('tabledataleft', fontName='Helvetica', fontSize=6, leading=9, 
                    alignment=TA_CENTER, leftIndent=1, rightIndent=3, spaceAfter=1, spaceBefore=2)
    styNormal = ParagraphStyle('normal', fontName='Helvetica', fontSize=8, leading=11,
               textColor=navy, alignment=TA_LEFT, leftIndent=8, spaceAfter=10)
    title_style = ParagraphStyle('tabledataleft', fontName='Helvetica-Bold', fontSize=12, leading=14, 
                    alignment=TA_CENTER, leftIndent=1, rightIndent=1, spaceAfter=10, spaceBefore=10)
    
    def get_template_title(self, cr, context):
        """ return the title of the report """
        return u'БЭЛЭН МӨНГӨНИЙ ГҮЙЛГЭЭНИЙ ТАЙЛАН'
    
#     def get_report_barcode(self, cr, context=None):
#         ''' Баримтын кодыг зураасан код болгож зурах '''
#         order = self.pool.get('account.bank.statement').browse(cr, 1, self.datas['ids'][0], context)
#         if not order.paymaster_report_name :
#             False
#         code = order.paymaster_report_name or '-----'
#         barcode_prefix = order.company_id.barcode_prefix or ''
#         return barcode_prefix + code
    
    def get_report_data(self, cr, uid, statement, context=None):
        ''' Тухайн журналд тайлант хугацааны туршид бичигдэж батлагдсан 
            кассын зарлагын ордеруудыг олж боловсруулна.
        '''
        if context is None:
            context = {}
        results = []
        start_balance = balance = statement.balance_start
        cr.execute("select id, name, date, ref, amount from account_bank_statement_line "
                   "where statement_id = %s and amount >= 0 "
                   "order by date, name", (statement.id,))
        fetched = cr.fetchall()
        if fetched:
            for id, name, date, ref, amount in fetched:
                balance += amount
                results.append({
                    'name': name,
                    'date': date,
                    'ref': ref or '',
                    'income': (amount > 0 and amount) or 0,
                    'expense': (amount < 0 and amount) or 0,
                    'balance': balance
                })
        cr.execute("select id, name, date, ref, amount from account_bank_statement_line "
                   "where statement_id = %s and amount < 0 "
                   "order by date, name", (statement.id,))
        fetched = cr.fetchall()
        if fetched:
            for id, name, date, ref, amount in fetched:
                balance += amount
                results.append({
                    'name': name,
                    'date': date,
                    'ref': ref or '',
                    'income': (amount > 0 and amount) or 0,
                    'expense': (amount < 0 and amount) or 0,
                    'balance': balance
                })
        
        return results, start_balance
    
    def get_story(self):
        ''' Тайлангийн өгөгдлүүдийг боловсруулж, PDF -г зурна.
            A4 цаасний стандарт хэмжээ 210x297 үүний тайлангийн бие нь
            Хэвтээ хэлбэрээр 280x200 байхаар тогтоолоо.
            
        '''
        from datetime import datetime
        
        story = []
        cr = self.cr
        uid = self.uid 
        context = self.context
        
        statement = self.pool.get('account.bank.statement').browse(cr, uid, self.datas['ids'][0], context=context)
        company = statement.company_id
        if not company:
            company_ids = self.pool.get('res.company').search(cr, uid, [])
            company = self.pool.get('res.company').search(cr, uid, company_ids[0], context=context)
        
        date_str = '%s-%s' % (
            datetime.strptime(statement.date,'%Y-%m-%d').strftime('%Y.%m.%d'),
            (statement.closing_date and datetime.strptime(statement.closing_date, '%Y-%m-%d %H:%M:%S').strftime('%Y.%m.%d')) or time.strftime('%Y.%m.%d')
        )
        
        pretty = c2c_helper.comma_me # Тоог мянгатын нарийвчлалтай болгодог method
        nullpara = Paragraph('', self.td_center_style)
        xpara = Paragraph('x', self.td_center_style)
          
          
#         print statement.paymaster_id
              
        grid = [[
            Paragraph(u'Маягт МХ-4', self.styNormal),
            Paragraph(u"Байгууллагын нэр: %s" % company.name, self.styNormal)
        ],[
            Paragraph(u'Бэлэн мөнгөний гүйлгээний тайлан', self.title_style),
            nullpara
        ],[
            Paragraph(u"Дугаар: %s" % statement.name, self.styNormal),
            Paragraph(u"Тайлант хугацаа: %s" % date_str, self.styNormal),
        ],[
#             Paragraph(u'Мөнгөний нярав : %s' % statement.paymaster_id.name, styNormal),
            '',
            Paragraph(u"Валют: %s" % ((statement.currency and statement.currency.name) or company.currency_id.name), self.styNormal)
        ]]
        
        tsGrid = TableStyle([
                ('GRID', (0,0), (-1,-1), 0.25, colors.white),
                ('SPAN', (0,1), (1,1))
        ])
        
        story.append(Table(grid, style=tsGrid, colWidths=[110*mm,90*mm]))
        story.append(Spacer(10,10))
        
        grid = [[
            Paragraph(u'Д/д', self.th_style),
            Paragraph(u'Баримтын', self.th_style),
            nullpara,
            Paragraph(u'Гүйлгээний утга', self.th_style),
            Paragraph(u'Гүйлгээний мөнгөн дүн', self.th_style),
            nullpara,
            Paragraph(u'Үлдэгдлийн дүн', self.th_style)
        ],[
            nullpara,
            Paragraph(u'Огноо', self.th_style),
            Paragraph(u'Дугаар', self.th_style),
            nullpara,
            Paragraph(u'Орлого', self.th_style),
            Paragraph(u'Зарлага', self.th_style),
            nullpara
        ]]
        gstyle = [
            ('BOX', (0,0), (-1,-1), 0.60, colors.black),
            ('GRID', (0,0), (-1,1), 0.40, colors.black),
            ('LINEBELOW', (0,1),(-1,-1), 0.40, colors.lightgrey), # хэвтээ зураас
            ('LINEAFTER', (0,1), (-1,-1), 0.40, colors.black), # Босоо зураас
            #('LINEBELOW', (0,-2), (-1,-2), 0.40, colors.black),
            #('LINEAFTER', (0,1),(-1,-2), 0.20, colors.grey), # lightgrey
            ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
            ('SPAN', (0,0), (0,1)), # БАГАНА, МӨР
            ('SPAN', (1,0), (2,0)),
            ('SPAN', (3,0), (3,1)),
            ('SPAN', (4,0), (5,0)),
            ('SPAN', (6,0), (6,1)),
            ('TOPPADDING', (0,0), (-1,-1), 3),
            ('BOTTOMPADDING', (0,0), (-1,-1), 0),
            ('LEFTPADDING', (0,0), (-1,-1), 1),
            ('RIGHTPADDING', (0,0), (-1,-1), 1)
        ]
#        
#        # Ингээд л болоо
#        story.append(Table(grid, style=TableStyle(gstyle), colWidths=[10*mm,30*mm,20*mm,60*mm,25*mm,25*mm,30*mm])) # unlimited
#        
#        builder = SimpleRowsTableBuilder(title=False)
#        builder.REPEAT_ROWS = 1
#        #columns
#        builder.add_text_column('1', width='28', extra={'header_font_size': 7, 'font_size': 6, 'align':'CENTER'})
#        builder.add_text_column('2', width='85', extra={'header_font_size': 7, 'font_size': 6, 'align':'CENTER'})
#        builder.add_text_column('3', width='58', extra={'header_font_size': 7, 'font_size': 6, 'align':'CENTER'})
#        builder.add_text_column('4', width='170', extra={'header_font_size': 7, 'font_size': 6, 'align':'CENTER'})
#        builder.add_num_column('5', width='70', decimals=2, extra={'header_font_size': 7, 'font_size': 6, 'align':'CENTER'})
#        builder.add_num_column('6', width='70', decimals=2, extra={'header_font_size': 7, 'font_size': 6, 'align':'CENTER'})
#        builder.add_num_column('7', width='85', decimals=2, extra={'header_font_size': 7, 'font_size': 6, 'align':'CENTER'})
        
        lines, balance = self.get_report_data(cr, uid, statement, context=context)
        grid.append([
            Paragraph(u'x', self.td_center_style),
            Paragraph(u'x', self.td_center_style),
            Paragraph(u'x', self.td_center_style),
            Paragraph(u'<b>Эхний үлдэгдэл</b>', self.td_center_style),
            nullpara,nullpara,
            Paragraph(pretty(balance, separator=","), self.td_right_style)
        ])
        
        # Гүйлгээний мөр бүрийг байгуулна.
        number_in = number_ex = 0
        total_in = total_ex = 0
        number = 1
        for line in lines :
            grid.append([
                Paragraph(str(number), self.td_left_style),
                Paragraph(line['date'], self.td_center_style),
                Paragraph(line['ref'], self.td_left_style),
                Paragraph(line['name'], self.td_left_style),
                Paragraph(pretty(line['income'], separator=","), self.td_right_style),
                Paragraph(pretty(line['expense'], separator=","), self.td_right_style),
                Paragraph(pretty(line['balance'], separator=","), self.td_right_style)
            ])
            if line['income']:
                number_in += 1
                total_in += line['income']
            else :
                number_ex += 1
                total_ex += line['expense']
            number += 1
        
        # DEBUG MODE
        if number < 10:
            while number <= 10:
                grid.append([
                    Paragraph(str(number), self.td_left_style),
                    nullpara,
                    nullpara,
                    nullpara,
                    nullpara,
                    nullpara,
                    nullpara
                ])
                number += 1
        
        grid.append([
            nullpara,
            nullpara,
            nullpara,
            Paragraph('<b>НИЙТ ДҮН :</b>', self.td_center_style),
            Paragraph(pretty(total_in, separator=","), self.td_right_style),
            Paragraph(pretty(total_ex, separator=","), self.td_right_style),
            nullpara
        ])
        t = Table(grid,'100%',repeatRows=2)
        t._argW = [10*mm,20*mm,30*mm,60*mm,25*mm,25*mm,30*mm]
        t.setStyle(TableStyle(gstyle))
        t.hAlign = 'LEFT'
        story.append(t)
        
        story.append(Spacer(15,15))
        
        # Тайлангийн доод хэсэгт гарын үсэг зурах жижиг хүснэгт бэлдэнэ.
        tsGrid = TableStyle([
                ('GRID', (0,0), (-1,-1), 0.25, colors.white),
                ('FONT', (0,0),(-1,-1),'Helvetica', 8),
                ('SPAN', (0,0),(1,0)),
                ('SPAN', (0,1),(1,1)),
                ('SPAN', (0,2),(1,2)),
        ])
        
        grid = [
            [Paragraph(u'Тайланд орлогын %s ширхэг, зарлагын %s ширхэг баримтыг хавсаргав.' % (number_in, number_ex), self.td_left_style), nullpara],
            [Paragraph(u'Тайлан гаргасан мөнгөний нярав .........................................../<font color="white">____________________________________</font>/', self.td_left_style), nullpara],
            [Paragraph(u'Шалгаж хүлээн авсан нягтлан бодогч ............................................./<font color="white">____________________________________</font>/', self.td_left_style), nullpara],
            [nullpara, Paragraph(u'Шалгаж хүлээн авсан огноо ................................', self.td_left_style)]
        ]
        story.append(Table(grid, style=tsGrid, colWidths=[30*mm,140*mm]))
        
        return story
    
account_cash_transaction('report.account.cash.statement.paymaster', "Cash Transaction Statement", 'account.bank.statement', StandardReport.A4_PORTRAIT)
