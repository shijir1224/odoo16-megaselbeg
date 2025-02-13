# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging
from odoo.tools.safe_eval import safe_eval, time

_logger = logging.getLogger(__name__)

class ModelTool(models.Model):
	_name = 'model.tool'
	_description = 'Model Reindex Tool'
	
	index = fields.Integer(string='Start Index')
	tmp_partner_id = fields.Integer(string='TMP ID')
	
	state = fields.Selection([('draft','Draft'),('done','Done')], default='draft', readonly=True)
	line_ids = fields.One2many('model.tool.line', 'parent_id', string='Line IDS')

	def action_done(self):
		self.ensure_one()
		if not self.line_ids:
			if not self.line_ids.mapped('fields_ids'):
				return False
			return False
		self.state = 'done'

	def check_fields(self):
		self.ensure_one()
		for line in self.line_ids:
			if line.fields_ids:
				line

	def unlink(self):
		for tool in self:
			if tool.state == 'done':
				raise UserError(_('Cannet Delete!\nГүйцэтгэсэн ажилбарыг устгах боломжгүй!'))
		return super(ModelTool, self).unlink()

class ModelToolLine(models.Model):
	_name = 'model.tool.line'
	_description = 'Index update model list'

	parent_id = fields.Many2one('model.tool', string='Parent ID', ondelete='cascade')
	model_id = fields.Many2one('ir.model', string='Model')
	fields_ids = fields.Many2many('ir.model.fields', string='Fields', domain="[('relation','!=',False)]", compute="_compute_fields")
	date_start = fields.Datetime(string='Start time')
	date_end = fields.Datetime(string='End time')
	tmp_object_id = fields.Integer(string='TMP ID')
	index = fields.Integer(string='Start Index')
	domain = fields.Char(string='Domain')

	def unlink(self):
		for line in self:
			if line.parent_id.state == 'done':
				raise UserError(_('Cannot delete action performed!'))
		return super(ModelToolLine, self).unlink()

	@api.depends('model_id')
	def _compute_fields(self):
		for item in self:
			fields = self.env['ir.model.fields'].search([('ttype','in',['many2one','one2many','many2many']),('relation','=',item.model_id.model)])
			item.fields_ids = [(6,0,fields.ids)] if fields else []

	def change_old(self):
		self.ensure_one()
		if (self.date_start and self.date_end) or self.domain:
			object_ids = False
			if self.domain:
				if not isinstance(self.domain, list):
					return False
				domain = self.domain
				if self.model_id.model == 'res.partner':
					domain.extend([('id','<',2000000),('id','>',215367)])
			else:
				domain = [('create_date','>=',self.date_start),('create_date','<=',self.date_end)]
#                 if self.model_id.model == 'res.partner':
#                     domain.extend([('id','<',2000000),('id','>',215367)])
			object_ids = self.env[self.model_id.model].search(domain)
			model_name = self.model_id.model.replace('.','_')
			# NOT NULL COLUMNS
			query = """SELECT column_name FROM information_schema.columns WHERE table_schema = 'public' AND table_name = '{0}' AND is_nullable = 'NO'""".format(model_name)
			self.env.cr.execute(query)
			query_result = self.env.cr.dictfetchall()

			not_null_columns = []
			for result in query_result:
				not_null_columns.append(result['column_name'])
			i = 1
			for object_id in object_ids:
			# if object_ids:
				# TEST
				# res_id = object_ids.filtered(lambda r: r.id==536172)
				res_id = object_id
				
				increased_id = res_id.id+self.parent_id.index
				# model_name = self.model_id.model.replace('.','_')

				# # NOT NULL COLUMNS
				# query = """SELECT column_name FROM information_schema.columns WHERE table_schema = 'public' AND table_name = '{0}' AND is_nullable = 'NO'""".format(model_name)
				# self.env.cr.execute(query)
				# query_result = self.env.cr.dictfetchall()

				# not_null_columns = []
				# for result in query_result:
				#     not_null_columns.append(result['column_name'])
				
				# Get Constraints
				query = """
					SELECT * FROM (
						SELECT
							pgc.contype as constraint_type,
							pgc.conname as constraint_name,
							ccu.table_schema AS table_schema,
							kcu.table_name as table_name,
							CASE WHEN (pgc.contype = 'f') THEN kcu.COLUMN_NAME ELSE ccu.COLUMN_NAME END as column_name, 
							CASE WHEN (pgc.contype = 'f') THEN ccu.TABLE_NAME ELSE (null) END as reference_table,
							CASE WHEN (pgc.contype = 'f') THEN ccu.COLUMN_NAME ELSE (null) END as reference_col,
							CASE WHEN (pgc.contype = 'p') THEN 'yes' ELSE 'no' END as auto_inc,
							CASE WHEN (pgc.contype = 'p') THEN 'NO' ELSE 'YES' END as is_nullable,

								'integer' as data_type,
								'0' as numeric_scale,
								'32' as numeric_precision
						FROM
							pg_constraint AS pgc
							JOIN pg_namespace nsp ON nsp.oid = pgc.connamespace
							JOIN pg_class cls ON pgc.conrelid = cls.oid
							JOIN information_schema.key_column_usage kcu ON kcu.constraint_name = pgc.conname
							LEFT JOIN information_schema.constraint_column_usage ccu ON pgc.conname = ccu.CONSTRAINT_NAME 
							AND nsp.nspname = ccu.CONSTRAINT_SCHEMA
						UNION
							SELECT  null as constraint_type , null as constraint_name , 'public' as "table_schema" ,
							table_name , column_name, null as refrence_table , null as refrence_col , 'no' as auto_inc ,
							is_nullable , data_type, numeric_scale , numeric_precision
							FROM information_schema.columns cols 
							Where 1=1
							AND table_schema = 'public'
							and column_name not in(
								SELECT CASE WHEN (pgc.contype = 'f') THEN kcu.COLUMN_NAME ELSE kcu.COLUMN_NAME END 
								FROM
								pg_constraint AS pgc
								JOIN pg_namespace nsp ON nsp.oid = pgc.connamespace
								JOIN pg_class cls ON pgc.conrelid = cls.oid
								JOIN information_schema.key_column_usage kcu ON kcu.constraint_name = pgc.conname
								LEFT JOIN information_schema.constraint_column_usage ccu ON pgc.conname = ccu.CONSTRAINT_NAME 
								AND nsp.nspname = ccu.CONSTRAINT_SCHEMA
							)
						)   as foo where table_name='{0}' and constraint_name like '%uniq'
						ORDER BY table_name desc
				""".format(model_name)
				# self.env.cr.execute(query)
				# query_result = self.env.cr.dictfetchall()

				query = """
					CREATE OR REPLACE FUNCTION f_random_text(
							length integer
						)
						RETURNS text AS
						$body$
						WITH chars AS (
							SELECT unnest(string_to_array('A B C D E F G H I J K L M N O P Q R S T U V W X Y Z 0 1 2 3 4 5 6 7 8 9', ' ')) AS _char
						),
						charlist AS
						(
							SELECT _char FROM chars ORDER BY random() LIMIT $1
						)
						SELECT string_agg(_char, '')
						FROM charlist
						;
						$body$
						LANGUAGE sql;
						INSERT INTO {0}
						VALUES 
							(DEFAULT, DEFAULT),
							(DEFAULT, DEFAULT);
				""".format(model_name)
				# self.env.cr.execute(query)
				# query_result = self.env.cr.dictfetchall()
#                print("====================================================")
				print(query_result)
#                print("====================================================")
				if not query_result:
					continue
				# Make increased buffer IDS
				buffer_ids =[increased_id, -1*increased_id]
				update_columns = ["{0}=excluded.{0}".format(column) for column in not_null_columns]
				# COPY #1
				# columns_data = [",concat('FAKE: ',{0})".format(buffer_ids[0]) for data in range(len(not_null_columns)-1)]
				# query = """INSERT INTO {0} ({2}) VALUES ({1}{3}) ON CONFLICT (id) DO UPDATE SET {4}""".format(model_name, buffer_ids[0], ', '.join(not_null_columns), ' '.join(columns_data), ', '.join(update_columns))
				# self.env.cr.execute(query)
				# COPY #2
				columns_data = [",concat('FAKE: ',{0})".format(buffer_ids[1])]
				if len(not_null_columns) > 2:
					columns_data.extend([",{0}".format(8) for data in range(len(not_null_columns)-2)])
				if 'company_id' in not_null_columns:
					columns_data[not_null_columns.index('company_id')-1] = ',1'
				
				query = """INSERT INTO {0} ({2}) VALUES ({1}{3}) ON CONFLICT (id) DO UPDATE SET {4}""".format(model_name, buffer_ids[1], ', '.join(not_null_columns), ' '.join(columns_data), ', '.join(update_columns))
				# print(query)
				self.env.cr.execute(query)
				# Foregin key should update increased ID
				for field in self.fields_ids.filtered(lambda r: r.ttype == 'many2one' and r.compute != '1'):
				# for field in self.fields_ids:
					if field.related:
						continue
					fiel_model_name = field.model_id.model.replace('.','_')
					# query = """update {0} set {1} = {2} where {1} = {3}""".format(fiel_model_name, field.name, buffer_ids[0], res_id.id)
					# self.env.cr.execute(query)
					# TEST
					try:
						query = """
							SELECT table_name 
							FROM information_schema.tables 
							WHERE table_schema='public' AND table_type='BASE TABLE' and table_name = '{0}'
						""".format(fiel_model_name)
						print(query)
						self.env.cr.execute(query)
						query_result = self.env.cr.dictfetchall()
					except Exception:
						query_result = False
					if not query_result:
						continue
					try:
						relation_object_ids = self.env[field.model_id.model].sudo().search([(field.name,'=', res_id.id)])
					except Exception:
						relation_object_ids = False
					if relation_object_ids:
						# print(relation_object_ids.mapped(field.name))
						# print(field.model_id.model, [(field.name,'=', res_id.id)])
						# print('compute', field.search([]))
						# print({field.name: buffer_ids[0]}, res_id)
						try:
							if field.search:
								relation_object_ids.sudo().write({field.name: buffer_ids[1]})
								query = """update {0} set id = {1} where id = {2}""".format(model_name, buffer_ids[0], res_id.id)
								relation_object_ids.sudo().write({field.name: buffer_ids[0]})
						except Exception:
							continue
					i += 1
				if i == 5:
					break
				# raise UserError(_('ID CHANGER'))
				
	@api.model
	def _cron_change(self):
		tool_line_id = self.env['model.tool.line'].search([('model_id.model','=','res.partner'),('domain','!=',False)], limit=1)
		query = "select count(id) from res_partner where create_date >= '2022-09-01' and create_date <= '2022-12-01' and id < 2000000 and id > 215367;"
		self.env.cr.execute(query)
		result_max = self.env.cr.fetchall()
		if result_max[0][0]>0:
			_logger.info('Left res_partner IDS: %s'%(result_max[0][0]))
			tool_line_id.change()
		return False
	
	def change(self):
		model_name = self.model_id.model.replace('.','_')
		if self.model_id.model == 'res.partner':
			sql='''select 
					att2.attname as "child_column", 
					cl.relname as "parent_table", 
					att.attname as "parent_column",
					con.child_table
				from
				(select 
						unnest(con1.conkey) as "parent", 
						unnest(con1.confkey) as "child", 
						con1.conname as constraint_name,
						con1.confrelid, 
						con1.conrelid,
						cl.relname as child_table,
						ns.nspname as child_schema
					from 
						pg_class cl
						join pg_namespace ns on cl.relnamespace = ns.oid
						join pg_constraint con1 on con1.conrelid = cl.oid
					where  con1.contype = 'f'
				) con
				join pg_attribute att on
					att.attrelid = con.confrelid and att.attnum = con.child
				join pg_class cl on
					cl.oid = con.confrelid
				join pg_attribute att2 on
					att2.attrelid = con.conrelid and att2.attnum = con.parent
				where cl.relname like '%res_partner' and con.child_table not in ('partner_duplicate','change_partner_info') '''
		else:
			sql='''select 
					att2.attname as "child_column", 
					cl.relname as "parent_table", 
					att.attname as "parent_column",
					con.child_table
				from
				(select 
						unnest(con1.conkey) as "parent", 
						unnest(con1.confkey) as "child", 
						con1.conname as constraint_name,
						con1.confrelid, 
						con1.conrelid,
						cl.relname as child_table,
						ns.nspname as child_schema
					from 
						pg_class cl
						join pg_namespace ns on cl.relnamespace = ns.oid
						join pg_constraint con1 on con1.conrelid = cl.oid
					where  con1.contype = 'f'
				) con
				join pg_attribute att on
					att.attrelid = con.confrelid and att.attnum = con.child
				join pg_class cl on
					cl.oid = con.confrelid
				join pg_attribute att2 on
					att2.attrelid = con.conrelid and att2.attnum = con.parent
				where cl.relname like '%{0}' '''.format(model_name)
		self.env.cr.execute(sql)
		alls = self.env.cr.fetchall()
		tmp_partner_id=self.tmp_object_id
		domain=safe_eval(self.domain)
		print ('domain ',domain)
		
		print ('domain ',type(domain))
		if  domain:
			partner_ids=self.env[self.model_id.model].search(domain).filtered(lambda r: r.id != tmp_partner_id)
		else:
			print ('tmp_partner_id ',tmp_partner_id)
			print ('self.model_id.model ',self.model_id.model)
			partner_ids=self.env[self.model_id.model].search([('id','!=',tmp_partner_id)])
			print ('partner_ids ',partner_ids)
		#    print "Am: ",p
#             partner_id=form.check_partner_id.id
#             if form.type in ('update','delete'):
#                 partner_id=form.from_partner_id.id
#             if not partner_id:
#                 raise UserError((u'Харилцагч сонго2!.'))
		result_max = False
		if self.model_id.model == 'res.partner':
			query = "select max(id) from res_partner where id < 2300000"
			self.env.cr.execute(query)
			result_max = self.env.cr.fetchall()
		new_id=self.parent_id.index if self.index == 0 else self.index
		if result_max:
			new_id = result_max[0][0] + 1
			_logger.info("select max(id) from res_partner%s"%(new_id))
		cnt=1
		for partner in partner_ids:
			
			datas=[]
			res=[]
			i=0
			is_data=False
			old_partner_id=partner.id
#             print ('partner name+++++++++: '+partner.name)
   # if self.model_id.model == 'res.partner.bank':
   # 	_logger.info('object.name+++++++++ %s cnt %s'%(str(partner.display_name),str(cnt)))
   # else:
   # 	_logger.info('object.name+++++++++ %s cnt %s'%(str(partner.name),str(cnt)))
			cr=self.env.cr

			for p in alls:
				sql="select * from "+p[3]+' where "'+p[0]+'"='+str(partner.id)+""
#                 print ("sql ",sql)
				self.env.cr.execute(sql)
				data = self.env.cr.fetchall()
#                 print ("data ",data)
				#    connection.commit()
				if len(data)>0:
					is_data=True
					#        datas.append({'table':p[3],'data':data,'rel':p[0]})
	#                 datas.append({'table':p[3],'rel':p[0]})
	#                 if form.type=='update':
#                     print ("Am: ",p)
					sql="update "+p[3]+' set "'+p[0]+'"='+str(tmp_partner_id)+' where "'+p[0]+'"='+str(partner.id)
#                     print ("sql ",sql)
					cr.execute(sql)
					cr.commit()
#                     print (a)
			model_name = self.model_id.model.replace('.','_')
			sql="update " + model_name +" set id= "+str(new_id)+" where id="+str(partner.id)+""
#             print ("sql ",sql)
			cr.execute(sql)
			cr.commit()
			for p in alls:
				sql="select * from "+p[3]+' where "'+p[0]+'"='+str(tmp_partner_id)+""
#                 print ("sql ",sql)
				self.env.cr.execute(sql)
				data = self.env.cr.fetchall()
#                 print ("data ",data)
				#    connection.commit()
				cr=self.env.cr
				if len(data)>0:
					is_data=True
					#        datas.append({'table':p[3],'data':data,'rel':p[0]})
	#                 datas.append({'table':p[3],'rel':p[0]})
	#                 if form.type=='update':
#                     print ("Am: ",p)
					sql="update "+p[3]+' set "'+p[0]+'"='+str(new_id)+' where "'+p[0]+'"='+str(tmp_partner_id)
#                     print ("sql ",sql)
					cr.execute(sql)
					cr.commit()
			cnt+=1
#                     print (a)
#             sql="update res_partner set id= "+new_id+" where "+p[0]+"="+str(partner.id)+""
#             print ("sql ",sql)
#             cr.execute(sql)
#             cr.commit()
			new_id+=1
#             break        
			
