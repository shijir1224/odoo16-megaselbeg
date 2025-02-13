# -*- coding: utf-8 -*-
##############################################################################
#
from zk import ZK
from odoo import api, models, fields
from odoo import _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
import logging
_logger = logging.getLogger(__name__)

class HrAttendanceTerminal(models.Model):
	_name = "hr.attendance.terminal"
	_description = "hr attendance terminal"
	_inherit = ['mail.thread']
	_order = 'name'


	date = fields.Datetime('Date', default=fields.Datetime.now(), readonly=True)
	name = fields.Char(u'Terminal Number', copy=False, required=True,
		states={'configured': [('readonly', True)]})
	location = fields.Char(u'Physical location', copy=False, required=True,
		states={'configured': [('readonly', True)]})
	ip = fields.Char(u'IP address', copy=False, size=15, required=True,
		states={'configured': [('readonly', True)]})
	port = fields.Char(u'Port number', copy=False,
		states={'configured': [('readonly', True)]})
	port_no = fields.Integer('Port No', required=True)
	description = fields.Html(string=u'Description',
		states={'configured': [('readonly', True)]})
	date_from = fields.Date(u'Date From', required=True, )
	date_to = fields.Date(u'Date To', required=True, )
	employee_id = fields.Many2one('hr.employee',string='Ажилтан')
	find_field_name = fields.Char(string=u'Ажилтанг олох талбар', copy=False, required=True,
		default='rf_key', help="Ирцийн мэдээллийг ажилтантай холбох талбарын нэр байна",
		states={'configured': [('readonly', True)]})
	tz_diff = fields.Integer(u'TimeZone', copy=False, default=8,
		states={'configured': [('readonly', True)]})

	# DATABASE or DEVICE
	connect_type = fields.Selection([
			('to_device', 'Төхөөрөмж рүү'),
			('to_database', 'Датабаз руу'),],
			default='to_device', string=u'Холболтын төрөл', required=True,
			states={'configured': [('readonly', True)]},)

	db_name = fields.Char(u'DB name', copy=False,
		help=u"ДБ руу холбогдож байгаа бол базын нэр, Access руу холбогдож байгаа бол замыг бичнэ",
		states={'configured': [('readonly', True)]})
	db_user = fields.Char(u'DB User', copy=False,
		states={'configured': [('readonly', True)]})
	db_password = fields.Char(u'DB Password', copy=False,
		states={'configured': [('readonly', True)]})
	db_raw_query = fields.Text(u'Attendance Raw query',
		states={'configured': [('readonly', True)]})
	db_user_raw_query = fields.Text(string=u'User Raw query',
		states={'configured': [('readonly', True)]})

	terminal_attendance_line = fields.One2many('terminal.attendance.line', 'terminal_id', string=u'Attendance line',
		states={'configured': [('readonly', True)]},)
	terminal_user_line = fields.One2many('terminal.user.line', 'terminal_id', string=u'USER line',
		states={'configured': [('readonly', True)]},)

	check_in_out_device = fields.Boolean(string=u'Орох, гарах төхөөрөмж шалгах эсэх', default=False,
		states={'configured': [('readonly', True)]})
	in_device_names = fields.Text(string=u'Орох ирцийн Төхөөрөмжийн нэрс',
		states={'configured': [('readonly', True)]})
	out_device_names = fields.Text(string=u'Гарах ирцийн Төхөөрөмжийн нэрс',
		states={'configured': [('readonly', True)]})

	state = fields.Selection([
			('draft', 'Draft'),
			('configured', 'Configured')],
			default='draft', string='State', tracking=True)
	_sql_constraints = [
		# ('ip_uniq', 'unique(ip)', u'IP хаяг давхардсан байна!'),
		('name_uniq', 'unique(name)', u'Төхөөрөмжийн дугаар давхардсан байна!'),
	]

	############## Overrided method
	def unlink(self):
		for s in self:
			if s.state != 'draft':
				raise UserError(_(u'Ноорог төлөвтэй бичлэгийг устгаж болно!'))
		return super(HrAttendanceTerminal, self).unlink()

	### Тохиргоо батлах
	def action_to_config(self):
		self.state = 'configured'

	### Тохиргоо цуцлах
	def action_to_back(self):
		self.state = 'draft'

	def _get_query(self, context):
		if not self.db_raw_query:
			if 'is_auto' not in context or not context['is_auto']:
				raise UserError(_(u'DB-аас ирц татах QUERY-г тохируулна уу!'))
			return False
		query = self.db_raw_query % (self.date_from.strftime("%Y-%m-%d"), self.date_to.strftime("%Y-%m-%d"))
		return query

	

	def get_connection(self):
		self.ensure_one()
		conn = None
		# create ZK instance
		zk = ZK(self.ip, port=self.port_no, timeout=5, password=False, force_udp=False, ommit_ping=False)
		try:
			# connect to device
			conn = zk.connect()
			# disable device, this method ensures no activity on the device while the process is run
			conn.disable_device()
			# Test Voice: Say Thank You
			conn.test_voice()
			_logger.info(u"'%s' төхөөрөмж рүү амжилттай холбогдлоо." % self.name)
		except Exception as e:
			raise ValidationError(_('Connection open failed: %s') % e)
		return conn

	### Ирц татах
	def get_attendance(self):
		attendance_obj = self.env['mw.attendance']
		tmp_attendance_obj = self.env['terminal.attendance.line']
		if self.terminal_attendance_line:
			self.terminal_attendance_line.unlink()
		obj = self
		tz = self.tz_diff
		context = dict(self._context)
		
		# Хэрэв төхөөрөмжөөс татах бол
		if self.connect_type == 'to_device':
			dddd = obj.date_from.strftime("%Y-%m-%d")
			date_to = obj.date_to.strftime("%Y-%m-%d")
			zk = ZK(obj.ip, int(obj.port_no), timeout=60, password=0, force_udp=False, ommit_ping=False)
			res = zk.connect()
			# res.disable_device()
			_logger.info('----TERMINAL----RES %s',res)
			if res:
				if not self.employee_id:
					att_lines = zk.get_attendance()
					if att_lines:
						emp_count = 0
						att_count = 0
						for line in att_lines:
							rfid = str(line.user_id)
							dddd_str = line.timestamp.strftime('%Y-%m-%d %H:%M:%S')
							if obj.date_from.strftime("%Y-%m-%d") <= dddd_str[:10] and dddd_str[:10]<=obj.date_to.strftime("%Y-%m-%d"):
								employee_id = self.env['hr.employee'].search([(self.find_field_name,'=',rfid)], limit=1)
								
								if employee_id:
									data = {
											'attendance_time': line.timestamp - timedelta(hours=tz),
											'employee_id': employee_id.id,
											'department_id': employee_id.department_id.id,
											'job_id': employee_id.job_id.id,
											'name': employee_id.name,
											'device_id': self.name,
											'date': dddd_str[:10],
										}
									match_date = line.timestamp - timedelta(hours=tz)
									if not attendance_obj.sudo().search([('attendance_time', '=', match_date), ('employee_id', '=', employee_id.id)]):
										att_obj = self.env['mw.attendance'].create(data)
										att_count += 1
									datac = {
										'terminal_id': self.id,
										'rfid_key': rfid,
										'employee_id': employee_id.id,
										'sign_in': dddd_str[:10],
										'sign_out': dddd_str[:10],
									}
									datac_obj = tmp_attendance_obj.create(datac)
									
									emp_count += 1									
										
							str1 = "%s өдөр нийт %d ажилтны %d ирцийн мэдээлэл орлоо."%(dddd, emp_count, att_count)
							self.description = str1
							
					else:
						if 'is_auto' not in context or not context['is_auto']:
							raise UserError(_(u'Ирцийн мэдээлэл олдсонгүй!'))
				else:
					att_lines = zk.get_attendance()
					if att_lines:
						emp_count = 0
						att_count = 0
						for line in att_lines:
							dddd_str = line.timestamp.strftime('%Y-%m-%d %H:%M:%S')
							if obj.date_from.strftime("%Y-%m-%d") <= dddd_str[:10] and dddd_str[:10]<=obj.date_to.strftime("%Y-%m-%d"):
								employee_id = self.env['hr.employee'].search([('id','=',self.employee_id.id)], limit=1)
								if employee_id:
									data = {
											'attendance_time': line.timestamp  - timedelta(hours=tz),
											'employee_id': employee_id.id,
											'name': employee_id.name,
											'date': dddd_str[:10],
										}
									if not attendance_obj.sudo().search([('attendance_time', '=', dddd_str), ('employee_id', '=', employee_id.id)]):
										att_obj = self.env['mw.attendance'].create(data)
										att_count += 1
									emp_count += 1								
							str1 = "%s өдөр нийт %d ажилтны %d ирцийн мэдээлэл орлоо."%(dddd, emp_count, att_count)
							self.description = str1
					else:
						if 'is_auto' not in context or not context['is_auto']:
							raise UserError(_(u'Ирцийн мэдээлэл олдсонгүй!'))
			else:
				if 'is_auto' not in context or not context['is_auto']:
					raise UserError(_(u'Төхөөрөмжтэй холбогдсонгүй!'))
		# Датабазаас татах бол
		elif self.connect_type == 'to_database':
			if not self._get_query(context):
				if 'is_auto' not in context or not context['is_auto']:
					raise UserError(_(u'Ирцний QUERY-г тохируулна уу!'))
				return
			cur = False
			try:
				conn = pymssql.connect(
					database = self.db_name,
					user = self.db_user,
					password = self.db_password,
					host = self.ip,
					port = self.port)
				cur = conn.cursor()
			except pymssql.InterfaceError:
				raise UserError(_(u'Холболт амжилтгүй боллоо!'))
			except pymssql.DatabaseError:
				raise UserError(_(u'DB error, Холболт амжилтгүй боллоо!'))
			# ===========================================================
			sql = self._get_query(context)
			cur.execute(sql)
			result = cur.fetchall()
			if not result:
				if 'is_auto' not in context or not context['is_auto']:
					raise UserError(_(u'Ирцийн мэдээлэл олдсонгүй!'))
			# Old data delete
			self.terminal_attendance_line.unlink()
			warning_info = []
			ok_atts = 0
			for line in result:
				rfid = line[0].strip()
				rfid = rfid.lstrip('0')
				date_obj = line[1] - timedelta(hours=tz)
				dddd_str = date_obj.strftime('%Y-%m-%d %H:%M:%S')
				employee_id = self.env['hr.employee'].search([(self.find_field_name,'=',rfid)], limit=1)
				if employee_id:
					in_out = False
					device_name = ''
					if len(line) >= 3:
						in_out = self._get_attendance_type(line[2])
						device_name = line[2]
					data = {
						'attendance_time': date_obj,
						'employee_id': employee_id.id,
						'name': employee_id.name +': '+device_name,
						'date': line[1],
						'attendance_type': in_out,
					}
					if not attendance_obj.sudo().search([('attendance_time','=',dddd_str),('employee_id','=',employee_id.id)]):
						att_obj = attendance_obj.create(data)
						ok_atts += 1
						_logger.info('----TERMINAL--mw.att created--user att-%s', str(data))
					# Create LINEs ------------------------------------------
					tmp_attendance_obj = self.env['terminal.attendance.line']
					data = {
						'terminal_id': self.id,
						'rfid_key': rfid,
						'employee_id': employee_id.id,
						'sign_in': line[1],
						'sign_out': date_obj,
					}
					att_obj = tmp_attendance_obj.create(data)
					_logger.info('----TERMINAL--LINE created--user att-%s', str(data))
				else:
					warning_info.append(rfid)
			str1 = "<b style='color:green'>%s-%s өдөр нийт %d ирцийн мэдээллээс %d нь орлоо.</b>"%(self.date_from.strftime("%Y-%m-%d"), self.date_to.strftime("%Y-%m-%d"),len(result), ok_atts)
			self.description = str1 +'<br/><div style="color:red">Warning: '+', '.join(warning_info)+"</div>"
		return True

	# Орох, Гарах төхөөрөмжийн нэрэнд байвал ирцийн төрлийг олох
	def _get_attendance_type(self, device):
		if self.in_device_names and device in [x.strip() for x in self.in_device_names.split(',')]:
			return 'in'
		elif self.out_device_names and device in [x.strip() for x in self.out_device_names.split(',')]:
			return 'out'
		else:
			return False

	# Авто ирц татах === CRON ================
	@api.model
	def _auto_download_attendance(self):
		confs = self.env['hr.attendance.terminal'].search([('state','=','configured')], order="name")
		ctx = dict(self._context or {})
		for line in confs:
			yesterday = datetime.now() - timedelta(days=1)
			line.date_from = yesterday
			line.date_to = datetime.now()
			line.with_context(ctx).get_attendance()

	### Ирц устгах
	def clear_attendance(self):
		obj = self
		# zk = self.get_connection()
		res = self.get_connection()
		if res:
			res.clearAttendance()
		else:
			raise UserError(_(u'Төхөөрөмжтэй холбогдсонгүй!'))
		obj.write({'description': datetime.now().strftime("%Y-%m-%d")+u' : Төхөөрөмж дээрх ирцийн мэдээлэл цэвэрлэгдсэн'})
		return True

	### USER татах
	def get_users(self):
		obj = self
		# Remove User line
		obj.terminal_user_line.unlink()
		if self.connect_type == 'to_device':
			# Get
			zk = ZK(obj.ip, int(obj.port_no),timeout=5)
			res = zk.connect()
			res.disable_device()
			if res:
				users = res.get_users()
				_logger.info('----TERMINAL----USERS %s',users)
				if users:
					for key in users:
						rfid = users[key][0]
						employee = self.env['hr.employee'].search([(self.find_field_name,'=',rfid)], limit=1)
						data = {
							'terminal_id': obj.id,
							'rfid_key': rfid,
							'employee_name': employee.name if employee else users[key][1],
						}
						obj.terminal_user_line = [(0, 0, data)]
				else:
					_logger.info('----TERMINAL----user get- NO users')
			else:
				raise UserError(_(u'Төхөөрөмжтэй холбогдсонгүй!'))
		# DB ээс татах бол
		else:
			try:
				conn = pymssql.connect(
					database = self.db_name,
					user = self.db_user,
					password = self.db_password,
					host = self.ip,
					port = self.port)
				_logger.info('----DATABASE----Connection-%s',conn)
				cur = conn.cursor()
				sql = self.db_user_raw_query
				cur.execute(sql)
				result = cur.fetchall()
				for line in result:
					_logger.info('----TERMINAL----user get-%s', str(line))
					rfid = line[1]
					employee = self.env['hr.employee'].search([(self.find_field_name,'=',rfid)], limit=1)
					nnnn = line[2] +' (device)'
					if employee:
						nnnn = employee.name +' (erp)'
					data = {
						'terminal_id': obj.id,
						'rfid_key': rfid,
						'employee_name': nnnn,
					}
					obj.terminal_user_line = [(0, 0, data)]
			except Exception as e:
				raise UserError(_(u'Холболт амжилтгүй боллоо! %s'%(e)))
			except pymssql.DatabaseError:
				raise UserError(_(u'DB error, Холболт амжилтгүй боллоо! %s' % str(pymssql.DatabaseError)))
		return True

	### TEST
	def test_button(self):
		_logger.info('----TERMINAL----TEST %s',self.connect_type)
		if self.connect_type == 'to_device':
			obj = self
			zk = ZK(obj.ip, int(obj.port_no),timeout=5,password=0, force_udp=False, ommit_ping=False)
			res = zk.connect()
			res.disable_device()
			_logger.info('----TERMINAL----RES-%s',res)
			if res:
				_logger.info('----TERMINAL----Connection-%s',zk.connect())
			else:
				raise UserError(_(u'Төхөөрөмжтэй холбогдсонгүй!'))
		elif self.connect_type == 'to_database':
			try:
				conn = pymssql.connect(
					database = self.db_name,
					user = self.db_user,
					password = self.db_password,
					host = self.ip,
					port = self.port)
				_logger.info('----DATABASE----Connection-%s',conn)
			except Exception as e:
			# except pymssql.InterfaceError:
				raise UserError(_(u'Холболт амжилтгүй боллоо! %s'%(e)))
			except pymssql.DatabaseError:
				raise UserError(_(u'DB error, Холболт амжилтгүй боллоо!'))

		return True

class TerminalAttendanceLine(models.Model):
	_name = "terminal.attendance.line"
	_description = "terminal attendance line"
	_order = 'rfid_key, employee_id'

	terminal_id = fields.Many2one('hr.attendance.terminal', u'Terminal Number',
		states={'done': [('readonly', True)]})
	sign_in = fields.Datetime('Sign in', required=True, readonly=True)
	sign_out = fields.Datetime('Sign out', readonly=True)
	employee_id = fields.Many2one('hr.employee', u'Employee',
		states={'done': [('readonly', True)]})
	rfid_key = fields.Char(string=u'RFID Key', size=15, help=u'Хурууны хээ уншигч төхөөрөмж дээрх дугаар')
	state = fields.Selection([
			('draft', 'Draft'),
			('imported', 'Imported')],
			default='draft', string='State', tracking=True)

class TerminalUserLine(models.Model):
	_name = "terminal.user.line"
	_description = "terminal user line"
	_order = 'rfid_key, employee_name'

	terminal_id = fields.Many2one('hr.attendance.terminal', u'Terminal Number', )
	rfid_key = fields.Char(string=u'RFID Key', size=15, help=u'Хурууны хээ уншигч төхөөрөмж дээрх дугаар')
	employee_name = fields.Char(string=u'Employee', )




class HrEmployee(models.Model):
    _inherit = "hr.employee"

    rfid_key = fields.Char(string=u'RFID Key', size=15, help=u'Хурууны хээ уншигч төхөөрөмж дээрх дугаар')
    _sql_constraints = [('rfid_key_uniq','unique(rfid_key)', 'RFID Key must be unique!')]
