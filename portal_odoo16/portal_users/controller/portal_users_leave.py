from datetime import datetime, timedelta
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.http import request
from odoo import http
from odoo.exceptions import UserError, ValidationError


class UsersTimetablePortal(CustomerPortal):
    def _prepare_home_portal_values(self, counters):
        rtn = super(UsersTimetablePortal, self)._prepare_home_portal_values(counters)
        current_user_id = request.env.context.get('uid')
        employee_list = request.env['hr.employee'].sudo().search([('user_id', '=', current_user_id)])
        if employee_list:
            rtn['leave_counts'] = request.env['hr.leave.mw'].sudo().search_count([('employee_id', '=', employee_list[0].id)])
        return rtn

    def daterange(self, date_from, date_to):
        start = datetime.strptime(date_from, "%Y-%m-%d")
        stop = datetime.strptime(date_to, "%Y-%m-%d")
        dates = []
        current_date = start
        while current_date <= stop:
            dates.append(current_date)
            current_date += timedelta(days=1)
        return dates

        # # print({} - {}, date_from, date_to)
        # for n in range(int((date_to - date_from).days) + 1):
        #     yield date_from + timedelta(n)

    def convert_time(self, t):
        print("t=", t)

        hours = int(t)
        print("hour=", hours)
        # Discard integer part. Ex 14.066664 -> 0.066664
        t %= 1
        minutes = int(t * 60)
        print("minutes=", minutes)
        # t24 -= minutes / 60
        # seconds = int(t24 * 3600)
        strHours = str(hours)
        if hours<10:
            strHours = "0" + str(hours)

        strMinutes = str(minutes)
        if minutes<10:
            strMinutes = "0" + str(minutes)

        strVal =strHours + ":" + strMinutes
        return strVal

    @http.route(['/my/newleave/<int:leave_id>'], type='http', method=["POST", "GET"], auth="user", website=True)
    def createNewLeave(self, leave_id, **kw):
        DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
        DATE_FORMAT = "%m/%d/%Y"
        HOURS_PER_DAY = 8

        current_user_id= request.env.context.get('uid')
        employee_list = request.env['hr.employee'].sudo().search([('user_id', '=', current_user_id)])
        company_list = request.env['res.company'].sudo().search([('id', '=', employee_list[0].company_id.id)])
        job_list = request.env['hr.job'].sudo().search([('id', '=', employee_list[0].job_id.id)])
        shift_time_list = request.env['hr.shift.time'].sudo().search([('is_request','=',True),('company_id', '=', employee_list[0].company_id.id), ('active', '=', True)])
        department_list = request.env['hr.department'].sudo().search([('id', '=', employee_list[0].department_id.id)])
        # sector_list = request.env['hr.department'].sudo().search([('id', '=', employee_list[0].department_id.parent_id.id)])

        if request.httprequest.method=="POST":
            # get flow
            required_add = []
            if not kw.get("employee"):
                required_add.append('Ажилтан')
            if not kw.get("company"):
                required_add.append('Компани')
            if not kw.get("department"):
                required_add.append('Хэлтэс')
            if kw.get("shift_plan") == 'Сонгоно уу':
                required_add.append('Хүсэлтийн төрөл')
            if not kw.get("date_from"):
                required_add.append('Эхлэх Огноо')
            if not kw.get("date_to"):
                required_add.append('Дууссан Огноо')
            if not kw.get("time_from"):
                required_add.append('Эхлэх Цаг')
            if not kw.get("time_to"):
                required_add.append('Дууссан Цаг')
            if not kw.get("description"):
                required_add.append('Тайлбар')

            if len(required_add)>1:
                raise ValidationError(str(required_add) + " талбаруудыг бөглөөгүй байна! Талбаруудын доор бичигдсэн анхааруулгыг гүйцэт уншина уу!!!")
            elif len(required_add)==1:
                raise ValidationError(str(required_add) + " талбарыг бөглөөгүй байна! Талбаруудын доор бичигдсэн анхааруулгыг гүйцэт уншина уу!!!")
            
            emp_id = request.env['hr.employee'].sudo().search([('id', '=', int(kw.get("employee")))])
            work_location_obj = request.env['hr.work.location'].sudo().search(
                [('id', '=', int(emp_id[0].work_location_id))])
            work_location_id = work_location_obj[0].id
            is_work_obj = request.env['hr.shift.time'].sudo().search([('id', '=', int(kw.get("shift_plan")))])
            is_work = is_work_obj[0].is_work
            search_domain = []
            search_domain.append(('model_id.model', '=', 'hr.leave.mw'))
            search_domain.append(('company_id', '=', emp_id[0].company_id.id))
            search_domain.append(('department_ids', 'in', [emp_id[0].department_id.id]))
            print ('search_domain ',search_domain)
            flow_id = request.env['dynamic.flow'].sudo().search(search_domain, order='sequence', limit=1)
            flow_line_id = request.env['dynamic.flow.line'].sudo().search(
                [('flow_id', '=', flow_id.id), ('state_type', '=', 'draft')], order='sequence', limit=1)
            print ('flow_id1 ',flow_id)

            # compute time
            time_from = datetime.strptime(kw.get("time_from"), '%H:%M')
            time_to = datetime.strptime(kw.get("time_to"), '%H:%M')

            date_from = kw.get("date_from")
            date_to = kw.get("date_to")
            lunch_hour = 1

            hours_from, minutes_from = kw.get("time_from").split(":")
            hours_to, minutes_to = kw.get("time_to").split(":")
            time_from_float = float(hours_from) + float(minutes_from)/60
            # time_from_float = float(kw.get("time_from").replace(":",""))
            time_to_float = float(hours_to) + float(minutes_to)/60

            if date_from == date_to:
                if int(hours_to) > int(hours_from):
                    if int(hours_to) > 13 and int(hours_from) <= 13:
                        number_of_hour = int(hours_to) - int(hours_from) - lunch_hour
                    else:
                        number_of_hour = int(hours_to) - int(hours_from)
                else:
                    raise ValidationError("Эхлэх, дуусах цагыг зөв оруулна уу!")
            elif date_from < date_to:
                if int(hours_to) > int(hours_from):
                    if int(hours_to) > 13 and int(hours_from) <= 13:
                        number_of_hour = int(hours_to) - int(hours_from) - lunch_hour
                    else:
                        number_of_hour = int(hours_to) - int(hours_from)
                else:
                    number_of_hour = 24 - int(hours_from) + int(hours_to)
            else:
                raise ValidationError("Эхлэх, дуусах огноог зөв оруулна уу!")
                

            st_d = 0
            en_d = 0
            val_days = 0
            val_total_hour = 0
            if date_from and date_to:
                day_too = 0
                st_d = date_from
                en_d = date_to

                if work_location_id == 1:
                    if is_work == 'business_trip' or is_work == 'training':
                        for single_date in self.daterange(st_d, en_d):
                            day_too += 1
                            print('Testing Holiday location===2: %s  %s  %s' % (
                                day_too, st_d, en_d))
                    else:
                        for single_date in self.daterange(st_d, en_d):
                            day_too += 1 if single_date.weekday() < 5 else 0
                        print('Testing Holiday location===1: %s  %s  %s' % (
                            day_too, st_d, en_d))
                else:
                    for single_date in self.daterange(st_d, en_d):
                        day_too += 1
                        print('Testing Holiday location===2: %s  %s  %s' % (
                        day_too, st_d, en_d))

                val_days = day_too
                val_total_hour = val_days * number_of_hour

            vals ={"employee_id": int(kw.get("employee")),
                   "company_id": int(kw.get("company")),
                   "department_id": int(kw.get("department")),
                   "shift_plan_id": int(kw.get("shift_plan")),
                   "flow_id": int(flow_id[0].id),
                   "flow_line_id": int(flow_line_id[0].id),
                   "is_work": is_work,
                   "state_type": "draft",
                   "date_from": kw.get("date_from"),
                   "date_to": kw.get("date_to"),
                   "time_from": time_from_float,
                   "time_to": time_to_float,
                   "description": kw.get("description"),
                   "work_location_id": emp_id[0].work_location_id.id,
                   "days": val_days,
                   "total_hour": val_total_hour
                  }

            if int(kw.get("record_id")) == 0:
                id = request.env['hr.leave.mw'].sudo().create(vals)
                current_rec = request.env['hr.leave.mw'].sudo().search([('id', '=', id[0].id)])
                loc_val = {"work_location_id": work_location_id}
                current_rec[0].sudo().write(loc_val)
            else:
                edit_rec = request.env['hr.leave.mw'].sudo().search([('id', '=', int(kw.get("record_id")))], limit=1)
                edit_rec.sudo().write(vals)
            return request.redirect('/my/leavelist')

        # page content
        if leave_id == 0:
            vals = {'current_leave_id': "0",
                    'employees': employee_list, 'companies': company_list,
                    'jobs': job_list, 'departments': department_list,
                    # 'sectors': sector_list, 
                    'shift_times': shift_time_list,
                    'page_name': "new_leave",
                    'current_state': "draft",
                    'return_desc' : "Удирдлагын коммент",
                    'current_time_from': "00:00",
                    'current_time_to': "00:00",
                    }
        else:
            current_leave_record = request.env['hr.leave.mw'].sudo().search([('id', '=', leave_id)])
            rec_date_from = str(current_leave_record[0].date_from)
            rec_date_to = str(current_leave_record[0].date_to)
            float_time_from =current_leave_record[0].time_from
            float_time_to = current_leave_record[0].time_to
            rec_time_from = self.convert_time(float_time_from)
            rec_time_to = self.convert_time(float_time_to)



            vals = {'current_date_from' : rec_date_from[0:10],
                    'current_date_to': rec_date_to[0:10],
                    'current_time_from': rec_time_from,
                    'current_time_to': rec_time_to,
                    'current_shift_plan': current_leave_record[0].shift_plan_id.id,
                    'current_description': current_leave_record[0].description,
                    'current_leave_id': current_leave_record[0].id,
                    'employees': employee_list, 'companies': company_list,
                    'jobs': job_list, 'departments': department_list,
                    # 'sectors': sector_list, 
                    'shift_times': shift_time_list,
                    'page_name': "new_leave",
                    'current_state': current_leave_record[0].state_type,
                    'return_desc' : current_leave_record[0].return_description
                    }

        return request.render("portal_users.new_leave_form_portal", vals)
    
    @http.route(['/my/newleave/editLeaveType/<int:leave_id>'], type='http', method=["POST", "GET"], auth="user", website=True)
    def editLeaveType(self, leave_id, **kw):
        current_user_id= request.env.context.get('uid')
        employee_list = request.env['hr.employee'].sudo().search([('user_id', '=', current_user_id)])
        company_list = request.env['res.company'].sudo().search([('id', '=', employee_list[0].company_id.id)])
        job_list = request.env['hr.job'].sudo().search([('id', '=', employee_list[0].job_id.id)])
        shift_time_list = request.env['hr.shift.time'].sudo().search([('is_request','=',True),('company_id', '=', employee_list[0].company_id.id), ('active', '=', True)])
        department_list = request.env['hr.department'].sudo().search([('id', '=', employee_list[0].department_id.id)])
        # sector_list = request.env['hr.department'].sudo().search([('type','=','sector'),('id', '=', employee_list[0].department_id.parent_id.id)])

        if request.httprequest.method=="GET":
            search_domain = []
            search_domain.append(('model_id.model', '=', 'hr.leave.mw'))
            search_domain.append(('company_id', '=', employee_list[0].company_id.id))
            search_domain.append(('department_ids', 'in', [employee_list[0].department_id.id]))

            flow_id = request.env['dynamic.flow'].sudo().search(search_domain, order='sequence', limit=1)
            flow_line_id_sent = request.env['dynamic.flow.line'].sudo().search(
                [('flow_id', '=', flow_id.id), ('state_type', '=', 'sent')], order='sequence', limit=1)
            flow_line_id_draft = request.env['dynamic.flow.line'].sudo().search(
                [('flow_id', '=', flow_id.id), ('state_type', '=', 'draft')], order='sequence', limit=1)


            vals_sent ={
                   "flow_line_id": int(flow_line_id_sent[0].id)
                  }
            vals_draft ={
                   "flow_line_id": int(flow_line_id_draft[0].id)
                  }
            back_url ="/my/newleave/0"
            if leave_id :
                edit_rec = request.env['hr.leave.mw'].sudo().search([('id', '=', leave_id)], limit=1)
                if edit_rec.flow_line_id.state_type == 'draft':
                    edit_rec.sudo().update(vals_sent)
                elif edit_rec.flow_line_id.state_type == 'sent':
                    edit_rec.sudo().update(vals_draft)

                back_url = "/my/newleave/" + str(leave_id)
            return request.redirect(back_url)
   
        # page content
        if leave_id == 0:
            vals = {'current_leave_id': "0",
                    'employees': employee_list, 'companies': company_list,
                    'jobs': job_list, 'departments': department_list,
                    # 'sectors': sector_list, 
                    'shift_times': shift_time_list,
                    'page_name': "new_leave",
                    'current_state': "draft",
                    'return_desc' : "Удирдлагын коммент",
                    'current_time_from': "00:00",
                    'current_time_to': "00:00",
                    }
        else:
            current_leave_record = request.env['hr.leave.mw'].sudo().search([('id', '=', leave_id)])
            rec_date_from = str(current_leave_record[0].date_from)
            rec_date_to = str(current_leave_record[0].date_to)
            float_time_from =current_leave_record[0].time_from
            float_time_to = current_leave_record[0].time_to
            rec_time_from = self.convert_time(float_time_from)
            rec_time_to = self.convert_time(float_time_to)

            vals = {'current_date_from' : rec_date_from[0:10],
                    'current_date_to': rec_date_to[0:10],
                    'current_time_from': rec_time_from,
                    'current_time_to': rec_time_to,
                    'current_shift_plan': current_leave_record[0].shift_plan_id.id,
                    'current_description': current_leave_record[0].description,
                    'current_leave_id': current_leave_record[0].id,
                    'employees': employee_list, 'companies': company_list,
                    'jobs': job_list, 'departments': department_list,
                    # 'sectors': sector_list, 
                    'shift_times': shift_time_list,
                    'page_name': "new_leave",
                    'current_state': current_leave_record[0].state_type,
                    'return_desc' : current_leave_record[0].return_description
                    }

        return request.render("portal_users.new_leave_form_portal", vals)

    @http.route(['/my/leavelist'], type='http', website=True)
    def UsersTimetablePortalListView(self, **kw):
        current_user_id = request.env.context.get('uid')
        employee_list = request.env['hr.employee'].sudo().search([('user_id', '=', current_user_id)])
        print("employee = ", employee_list[0].id)
        leaves = request.env['hr.leave.mw'].sudo().search([('employee_id', '=', employee_list[0].id)])
        return request.render("portal_users.leaves_list_view_portal", {'leaves':leaves, 'page_name': "list_leave"})

    # @http.route(['/my/orders/<int:order_id>'], type='http', auth="public", website=True)
    # def portal_order_page(self, order_id, report_type=None, access_token=None, message=False, download=False, **kw):