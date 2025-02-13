# -*- encoding: utf-8 -*-
##############################################################################
#
#    USI-ERP, Enterprise Management Solution    
#    Copyright (C) 2007-2010 USI Co.,ltd (<http://www.usi.mn>). All Rights Reserved
#
#    ЮүЭсАй-ЕРП, Байгууллагын цогц мэдээлэлийн систем
#    зохиогчийн эрх авсан 2007-2010 ЮүЭсАй ХХК (<http://www.usi.mn>). 
#
#    Зохиогчийн зөвшөөрөлгүйгээр хуулбарлах ашиглахыг хориглоно.
#
#    Харилцах хаяг :
#    Э-майл : info@usi.mn
#    Утас : 976 + 70151145
#    Факс : 976 + 70151146
#    Баянзүрх дүүрэг, 4-р хороо, Энхүүд төв,
#    Улаанбаатар, Монгол Улс
#
#
##############################################################################

# import time
# import pooler
# import locale
# from report import report_sxw
# from tools.translate import _

#cash statement
from odoo.addons.c2c_reporting_tools.reports.standard_report import *
from odoo.addons.c2c_reporting_tools.flowables.simple_row_table import *
from odoo.addons.c2c_reporting_tools.c2c_helper import *
from odoo.addons.c2c_reporting_tools.translation import _
from reportlab.platypus import *
from reportlab.lib.colors import red, black, navy, white, green
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER, TA_JUSTIFY
import odoo.pooler as pooler

class report_cash_journal(StandardReport):

    ''' Мөнгөний журнал
    '''
    sty_little = ParagraphStyle('normal', fontName='Helvetica', fontSize=6, leading=12,
               textColor=navy, alignment=TA_CENTER, leftIndent=8, spaceAfter=10)
    
    th_style = ParagraphStyle('tableheaderbold', fontName='Helvetica-Bold', fontSize=7, leading=9, 
                alignment=TA_CENTER, leftIndent=3, rightIndent=3, spaceAfter=2, spaceBefore=2)

    td_right_style = ParagraphStyle('tabledataright', fontName='Helvetica', fontSize=6, leading=8, 
                    alignment=TA_RIGHT, leftIndent=3, rightIndent=1, spaceAfter=1, spaceBefore=2)
    td_left_style = ParagraphStyle('tabledataleft', fontName='Helvetica', fontSize=6, leading=8, 
                    alignment=TA_LEFT, leftIndent=1, rightIndent=3, spaceAfter=1, spaceBefore=2)
    td_center_style = ParagraphStyle('tabledataleft', fontName='Helvetica', fontSize=6, leading=8, 
                    alignment=TA_CENTER, leftIndent=1, rightIndent=3, spaceAfter=1, spaceBefore=2)
    styNormal = ParagraphStyle('normal', fontName='Helvetica', fontSize=8, leading=12,
               textColor=navy, alignment=TA_LEFT, leftIndent=8, spaceAfter=10)
    title_style = ParagraphStyle('tabledataleft', fontName='Helvetica-Bold', fontSize=12, leading=16, 
                    alignment=TA_CENTER, leftIndent=1, rightIndent=1, spaceAfter=10, spaceBefore=10)
    
    def get_template_title(self, cr, context):
        """ return the title of the report """
        return u'Мөнгөн хөрөнгийн журнал'
    
#inherited
#     def get_template(self, cr, context):
#         ''''Хөл толгой гаргахгүй болгох'''
#         doc = super(report_cash_journal,self).get_template(cr,context)
#         doc.footer_draw = False
#         doc.header_draw=False
#         doc.report_name = ""
#         return doc
#     
    def get_report_data(self, cr, uid, data, context=None):
        ''' Тухайн журналд тайлант хугацааны туршид бичигдэж батлагдсан 
            кассын зарлагын ордеруудыг олж боловсруулна.
        '''
        # Тухайн дансны тайлант хугацааны эхний үлдэгдэл
        statement_obj = self.pool.get('account.bank.statement')
        user_obj = self.pool.get('res.users')

#        if data['statement_ids']:
#            statements = statement_obj.browse(cr, uid, data['statement_ids'], context=context)
#            balance_start = statement.balance_start
             
        
        ref = ''
#        start_balance = balance = statements[0].balance_start
        balance=0
        q="select  s.balance_start,s.name,p.date_start,s.date,s.state from \
                 account_bank_statement s left join account_period p on p.id=s.period_id \
                 where s.state='confirm' and \
                 s.journal_id={0} and \
                 s.date<='{1}' order by s.date desc limit 1".format(data['journal_id'],data['date_from'])
        cr.execute(q)
        fetched = cr.fetchall()
#         print "fetchedfetched ",fetched
        balance1=0
        balance2=0
        balance3=0
#         print "data['date_from'] ",data['date_from']
        if len(fetched)>0:
            balance1=fetched[0][0]
            date_before=balance=fetched[0][2]
            q2="select sum(amount) from account_bank_statement_line \
                where journal_id ={0} and date>='{1}' and date<='{2}'".format(data['journal_id'],date_before,data['date_from'])
            cr.execute(q2)
            fetched2 = cr.fetchall()
#             print "fetched2 ",fetched2
        else:
            q3="select  s.balance_start from \
                     account_bank_statement s left join account_period p on p.id=s.period_id \
                     where  \
                     s.journal_id={0} and \
                     s.date<='{1}' order by s.date desc limit 1".format(data['journal_id'],data['date_from'])
            cr.execute(q3)
            fetched3 = cr.fetchall()
#             print "fetched3 ",fetched3
            if fetched3:
                balance3=fetched3[0][0]
            
#             q2="select sum(amount) from account_bank_statement_line \
#                 where journal_id ={0} and date<'{1}'".format(data['journal_id'],data['date_from'])
#             cr.execute(q2)
#             fetched2 = cr.fetchall()
#             print "fetched22 ",fetched2
#             if fetched2 and fetched2[0][0]:
#                 balance2=fetched2[0][0]
#         print "balance3 ",balance3
#         print "balance1 ",balance1
#         print "balance2 ",balance2
        
#         balance=balance1+balance2+balance3
        balance=balance1+balance3
        balance_start=False
        if len(data['statement_ids'])==1:
            st=statement_obj.browse(cr,uid,data['statement_ids'][0])
            balance=st.balance_start
            q3="select  sum(amount) from \
                     account_bank_statement_line \
                     where  \
                     date<'{0}' and \
                     statement_id ={1} ".format(data['date_from'],st.id)
            cr.execute(q3)
            fetch = cr.fetchall()
            if fetch[0][0]:
                balance+=fetch[0][0]
            balance_start=balance
#         results = [{'name':'','date':'','ref':u'Эхний үлдэгдэл','income':0,'expense':0,'balance':balance,'partner':''}]
        results=[] 
        for statement in statement_obj.browse(cr, uid, data['statement_ids'], context=context):
            debit_acc = statement.journal_id.default_debit_account_id.code
            if not balance_start:
                balance_start=statement.balance_start
            for line in statement.line_ids:
                if line.date >= data['date_from'] and line.date <= data['date_to'] :
                    balance += line.amount
                    ref = line.ref and line.ref + ' / ' or ''
                    if line.note :
                         ref = ref+line.note
        #            for line in statement.line_ids:
                    amount = 0.0
                    income = 0.0
#                     user_code=user_obj.browse(cr,uid,line.create_uid).accountant_code
                    q3="select  create_uid from \
                             account_bank_statement_line \
                             where  \
                             id={0} ".format(line.id)
                    cr.execute(q3)
                    fetch = cr.fetchone()
                    user_code=''
                    if fetch:
                        user_code=user_obj.browse(cr,uid,fetch[0]).accountant_code
                    
                    if line.amount > 0:
                          results.append({
                                    'name': line.name,
                                    'date': line.date,
                                    'ref':  ref,
                                    'income': line.amount,
#                                     'income': abs(line.price_with_tax - line.price_subtotal),
                                    'balance': balance,
                                    'expense': 0,
#                                     'credit_acc': line.account_id.code,
#                                     'debit_acc': line.statement_line_tax_id[0].account_collected_id.code,
                                    'partner':line.partner_id.name,
                                    'user':user_code
                                })
                    else:
                        results.append({
                                    'name': line.name,
                                    'date': line.date,
                                    'ref':  ref,
                                    'income': 0,
#                                     'income': abs(line.price_with_tax),
                                    'expense': abs(line.amount),
#                                     'credit_acc': line.account_id.code,
#                                     'debit_acc': debit_acc,
                                    'partner':line.partner_id.name,
                                    'balance': balance,
                                    'user':user_code
                                })
        return results,balance_start

    def get_excel(self,data):
        self.datas = data
        story = self.get_story()
        return story
    
    def get_excel_data(self,cr,uid,datas,context):
        ''' excel ээр гүйлгээ балансыг гаргахад дуудагдах'''
        global data
        
        data = datas['form']
        
        self.cr = cr
        self.uid = uid
        self.datas = datas
        self.context = context
        self.pool = pooler.get_pool(self.cr.dbname)
        self.lang = context.get('lang', None)

        #get objects
        if self.objects_name:
            self.objects = pooler.get_pool(self.cr.dbname).get(self.objects_name).browse(self.cr, self.uid, self.ids)

#         lines = self.create_report_data(cr, uid, data, context)
        lines,balance_start = self.get_report_data(cr, uid, data, context=context)
        return lines,balance_start
    

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
        data = self.datas['form']
#        datas ийг super дээр цэнэглэж өгнө^
        statement_obj = self.pool.get('account.bank.statement')
        journal_obj = self.pool.get('account.journal')
        
#         journal_id = journal_obj.search(cr,uid,[('default_debit_account_id','=',data['account_id'])])
#         if journal_id:
        if data['journal_id']:
            journal = journal_obj.browse(cr,uid,data['journal_id'])#[0]
#        st_ids = statement_obj.search(cr,uid,[('journal_id','=',journal_id)])
        
#        st_ids2 = statement_obj.search(cr,uid,[('journal_id','=',journal_id),('date','=',data['date_from'])])
#        print "st_ids2 ",st_ids2
        if data['statement_ids']:
            balance_start = statement_obj.browse(cr, uid, data['statement_ids'][0], context=context).balance_start
#        statement = statement_obj.browse(cr, uid, st_ids, context=context)
#        print "statement ",statement
#        statement = statement_obj.browse(cr, uid, statement_obj.search(cr,uid,[('account_id','=',data['account_id']),('date','>',data['date_from']),('date','<=',data['date_to'])]), context=context)
        company = data['company_name']
        if not company:
            company_ids = self.pool.get('res.company').search(cr, uid, [])
            company = self.pool.get('res.company').search(cr, uid, company_ids[0], context=context)
        if data['date_from']:
            closing_date = data['date_from'].split(" ")
        else:
            closing_date = str(datetime.now()).split(" ")
        date_str = '%s-%s' % (
            datetime.strptime(data['date_to'],'%Y-%m-%d').strftime('%Y.%m.%d'),
            datetime.strptime((closing_date[0] or time.strftime('%Y-%m-%d')),'%Y-%m-%d').strftime('%Y.%m.%d')
        )

        pretty = c2c_helper.comma_me # Тоог мянгатын нарийвчлалтай болгодог method
        nullpara = Paragraph('', self.td_center_style)
        xpara = Paragraph('x', self.td_center_style)
        
        grid = [[
            nullpara,
            Paragraph(u'Санхүү, эдийн засгийн сайдын 2002 оны 191 тоот тушаалаар батлав. ', self.sty_little),
        ]]
        
        tsGrid = TableStyle([
                ('GRID', (0,0), (-1,-1), 0.25, colors.white),
                ('SPAN', (0,1), (1,1))
        ])
        
        story.append(Table(grid, style=tsGrid, colWidths=[140*mm,70*mm]))

        grid = [[
            Paragraph(u'Харилцахын тайлан', self.title_style),
        ]]
        
        tsGrid = TableStyle([
                ('GRID', (0,0), (-1,-1), 0.25, colors.white),
                ('SPAN', (0,1), (1,1))
        ])
        if journal.type=='bank' and journal.bank_id:
             dans=journal.bank_id.name 
        else:
            dans= ' '
        
        story.append(Table(grid, style=tsGrid, colWidths=[210*mm]))
        grid = [[
            Paragraph(u"Байгууллагын нэр: %s" % company, self.styNormal),
            Paragraph(u'Журналын төрөл: %s ' %(journal.type) , self.styNormal)
        ],[
#             Paragraph(u"Данс : %s %s" % (data['account_code'],data['account_name']), self.styNormal),
            Paragraph(u"Данс : %s " % (journal.name), self.styNormal),
#             Paragraph(u"Банкны нэр : %s " % (dans), self.styNormal),
            nullpara,
        ],[
            Paragraph(u"Банкны нэр : %s " % (dans), self.styNormal),
            nullpara,
#            Paragraph(u"Эхний үлдэгдэл: %s" % (balance_start), self.styNormal)
        ],[
            Paragraph(u"Тайлант хугацаа: %s" % date_str, self.styNormal),
            nullpara,
#            Paragraph(u"Эхний үлдэгдэл: %s" % (balance_start), self.styNormal)
        ]]
        
        tsGrid = TableStyle([
                ('GRID', (0,0), (-1,-1), 0.25, colors.white),
                ('SPAN', (0,1), (1,1))
        ])
        
        story.append(Table(grid, style=tsGrid, colWidths=[130*mm,80*mm]))
        
        grid = [[
            Paragraph(u'Огноо', self.th_style),
            Paragraph(u'Баримтын дугаар', self.th_style),
            Paragraph(u'Харилцагчийн нэр', self.th_style),
            Paragraph(u'Гүйлгээний утга', self.th_style),
            Paragraph(u'Дүн', self.th_style),
#             Paragraph(u'Бусад дансанд', self.th_style),
            nullpara,
            nullpara,
        ],[
            nullpara,
            nullpara,
            nullpara,
            nullpara,
            Paragraph(u'Орлого', self.th_style),
            Paragraph(u'Зарлага', self.th_style),
            Paragraph(u'Үлдэгдэл', self.th_style),
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
            ('SPAN', (1,0), (1,1)),
            ('SPAN', (2,0), (2,1)),
            ('SPAN', (3,0), (3,1)),
            ('SPAN', (4,0), (6,0)),
#             ('SPAN', (5,0), (6,0)),
#            ('SPAN', (7,0), (7,1))
        ]
        withs=[18*mm,20*mm,35*mm,56*mm,23*mm,24*mm,25*mm]
        # Ингээд л болоо
        story.append(Table(grid, style=TableStyle(gstyle), colWidths=withs)) # unlimited
        
#         builder = SimpleRowsTableBuilder(title=False)
#         builder.REPEAT_ROWS = 1
#         #columns
#         builder.add_text_column('1', width='42.6', extra={'header_font_size': 7, 'font_size': 6, 'align':'CENTER'})#13*2.84 гм 2.84 өөр үржив
#         builder.add_text_column('2', width='42.6', extra={'header_font_size': 7, 'font_size': 6, 'align':'CENTER'})
#         builder.add_text_column('3', width='99.4', extra={'header_font_size': 7, 'font_size': 6, 'align':'CENTER'})
#         builder.add_text_column('4', width='170.4', extra={'header_font_size': 7, 'font_size': 6, 'align':'CENTER'})
#         builder.add_num_column('5', width='71', decimals=2, extra={'header_font_size': 7, 'font_size': 6, 'align':'CENTER'})
#         builder.add_num_column('6', width='59.64', decimals=2, extra={'header_font_size': 7, 'font_size': 6, 'align':'CENTER'})
#         builder.add_num_column('7', width='59.64', decimals=2, extra={'header_font_size': 7, 'font_size': 6, 'align':'CENTER'})
#        builder.add_num_column('8', width='73.5', decimals=2, extra={'header_font_size': 7, 'font_size': 6, 'align':'CENTER'})
        
        lines,balance = self.get_report_data(cr, uid, data, context=context)
        ending = balance_start
        if data.has_key('sort_by'):
            if data['sort_by']=='date':
                lines.sort(key=lambda x: x['date'])
            elif data['sort_by'] == 'partner':
                lines.sort(key=lambda x: x['partner'])
            elif data['sort_by'] == 'number':
                try:
                    lines.sort(key=lambda x: int(x['name']))
                except ValueError:
                    raise osv.except_osv(_(u'Анхааруулга !'), _(u'Кассын тайлангийн мөрийн дугаарууд тоо байх ёстой, засна уу.'))
                    
#        for l in lines:
#        print "lines ",lines
#         builder.add_text_cell('x')
#         builder.add_text_cell('x')
#         builder.add_text_cell('x')
#         builder.add_text_cell('x')
#         builder.add_text_cell(u'Эхний үлдэгдэл')
#         builder.add_empty_cell()
#         builder.add_empty_cell()
#        builder.add_num_cell(balance, extra={'align':'RIGHT'})
        
        # Гүйлгээний мөр бүрийг байгуулна.
        number_in = number_ex = 0
        total_in = total_ex = 0
        number = 1
#         for line in lines :
# #            print "line['ref'] ",line['ref']
# #            ending = ending + line['income'] - line['income']
#             builder.add_text_cell(line['date'], extra={'align':'CENTER'})
#             builder.add_text_cell(line['name'], extra={'align':'LEFT'})
#             builder.add_text_cell(line['partner'], extra={'align':'LEFT'})
#             builder.add_text_cell(line['ref'], extra={'align':'LEFT'})
#             builder.add_num_cell(line['income'], extra={'align':'RIGHT'})
#             builder.add_num_cell(line['expense'], extra={'align':'RIGHT'})
#             builder.add_num_cell(line['balance'], extra={'align':'RIGHT'})
#  
#             builder.add_text_cell(line['debit_acc'], extra={'align':'LEFT'})
#             builder.add_text_cell(line['credit_acc'], extra={'align':'LEFT'})
#            builder.add_num_cell(ending, extra={'align':'RIGHT'})
#            if line['income']:
#                number_in += 1
#                total_in += line['income']
#            else :
#                number_ex += 1
#                total_ex += line['income']
#            number += 1
        
#         builder.add_empty_cell()
#         builder.add_empty_cell()
#         builder.add_empty_cell()
#         builder.add_text_cell('<b>НИЙТ ДҮН :</b>', extra={'align':'RIGHT'})
#         builder.add_subtotal_num_cell(extra={'font_size':6,'align':'RIGHT'})
# #        builder.add_subtotal_num_cell(extra={'font_size':6,'align':'RIGHT'})
#         builder.add_empty_cell()
#         builder.add_empty_cell()
#         story.append(builder.get_table())
#         grid=[[]]
        ending=balance
        grid=[[
#                 Paragraph(str(number), self.td_left_style),
                Paragraph('', self.td_center_style),
                Paragraph('', self.td_left_style),
                Paragraph('', self.td_left_style),
                Paragraph(u'Эхний үлдэгдэл' , self.th_style),
                Paragraph('', self.td_left_style),
                Paragraph('', self.td_left_style),
                Paragraph(pretty(balance, separator=","), self.th_style)
            ]]

        for line in lines :
            ending+=line['income']-line['expense']
            grid.append([
#                 Paragraph(str(number), self.td_left_style),
                Paragraph(line['date'], self.td_center_style),
                Paragraph(line['ref'], self.td_left_style),
                Paragraph(line['partner'] and line['partner'] or '', self.td_left_style),
                Paragraph(line['name'], self.td_left_style),
                Paragraph(pretty(line['income'], separator=","), self.td_right_style),
                Paragraph(pretty(line['expense'], separator=","), self.td_right_style),
#                 Paragraph(pretty(line['balance'], separator=","), self.td_right_style)
                Paragraph(pretty(ending, separator=","), self.td_right_style)
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
#                     Paragraph(str(number), self.td_left_style),
                    nullpara,
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
            Paragraph(pretty(total_in, separator=","), self.th_style),
            Paragraph(pretty(total_ex, separator=","), self.th_style),
            nullpara
        ])
        grid.append([
                Paragraph('', self.td_center_style),
                Paragraph('', self.td_left_style),
                Paragraph('', self.td_left_style),
                Paragraph(u'Эцсийн үлдэгдэл' , self.th_style),
                Paragraph('', self.td_left_style),
                Paragraph('', self.td_left_style),
                Paragraph(pretty(ending, separator=","), self.th_style)
        ])
#         t = Table(grid,'100%',repeatRows=2)
#         t._argW = withs
#         t.setStyle(TableStyle(gstyle))
#         t.hAlign = 'LEFT'
#         story.append(t)
        gstyle = [
            ('BOX', (0,0), (-1,-1), 0.60, colors.black),
            ('GRID', (0,0), (-1,1), 0.40, colors.black),
            ('LINEBELOW', (0,1),(-1,-1), 0.40, colors.lightgrey), # хэвтээ зураас
            ('LINEAFTER', (0,1), (-1,-1), 0.40, colors.black), # Босоо зураас
            #('LINEBELOW', (0,-2), (-1,-2), 0.40, colors.black),
            #('LINEAFTER', (0,1),(-1,-2), 0.20, colors.grey), # lightgrey
            ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
#             ('SPAN', (0,0), (0,1)), # БАГАНА, МӨР
#             ('SPAN', (1,0), (1,1)),
#             ('SPAN', (2,0), (2,1)),
#             ('SPAN', (3,0), (3,1)),
#             ('SPAN', (4,0), (6,0)),
#             ('SPAN', (5,0), (6,0)),
#            ('SPAN', (7,0), (7,1))
        ]

        story.append(Table(grid, style=TableStyle(gstyle), colWidths=withs)) # unlimited
        
        story.append(Spacer(30,30))
        # Тайлангийн доод хэсэгт гарын үсэг зурах жижиг хүснэгт бэлдэнэ.
        tsGrid = TableStyle([
                ('GRID', (0,0), (-1,-1), 0.25, colors.white),
                ('FONT', (0,0),(-1,-1),'Helvetica', 8),
                ('SPAN', (0,0),(1,0)),
                ('SPAN', (0,1),(1,1)),
                ('SPAN', (0,2),(1,2)),
        ])
        
        grid = [
            [Paragraph(u'Хөтөлсөн нягтлан бодогч .........................................../<font color="white">____________________________________</font>/', self.td_left_style), nullpara],
            [Paragraph(u'Хянасан ерөнхий (ахлах) нягтлан бодогч ............................................./<font color="white">____________________________________</font>/', self.td_left_style), nullpara],
            [nullpara, Paragraph(u'Шалгаж хүлээн авсан огноо ................................', self.td_left_style)]
        ]
        story.append(Table(grid, style=tsGrid, colWidths=[30*mm,140*mm]))
        return story
    
report_cash_journal('report.cash.journal', "Cash income journal", 'account.bank.statement', StandardReport.A4_PORTRAIT)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
