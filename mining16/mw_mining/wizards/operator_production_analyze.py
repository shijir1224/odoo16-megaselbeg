# -*- coding: utf-8 -*-
from datetime import date, datetime,timedelta
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import UserError, ValidationError

class purchase_create_stock_move_reoprt(models.TransientModel):
	_name = 'report.operator.production.analyze.wiz'
	_description = 'Report operator production analyze wiz'

	date_start = fields.Date(string=u'Эхлэх огноо', required=True)
	date_end = fields.Date(string=u'Дуусах огноо', required=True)

	# picking_type_id = fields.Many2one('stock.location',string=u'Эх байрлал', domain=[('usage','=','internal')], readonly=True)

	def get_domain(self, domain):
		domain.append(('date','>=',self.date_start))
		domain.append(('date','<=',self.date_end))
		# domain.append(('report_wizard_id','=',self.id))
		# if self.picking_type_id:
		# 	domain.append(('location_id','=',self.picking_type_id.id))
		# domain.append(('state','in', ['confirmed','waiting','partially_available','assigned']))
		return domain

	def action_to_view(self):
		domain = []
		action = self.env.ref('mw_mining.action_mining_report_operator_analyze_tree')


		query = """
	delete from report_operator_production_analyze;

				insert into report_operator_production_analyze (date, branch_id, shift, part,
				operator_id, technic_id, report_wizard_id, dump_production_m3, exca_production_m3, production_id)
		SELECT
				mde.date,
				mde.branch_id,
				mde.shift,
				mde.part,
				meol.operator_id,
				mel.technic_id as technic_id,
				1,
				case when mpel.dump_id = mel.technic_id then SUM(mpel.sum_m3) else 0 end AS dump_sum_m3,
				case when mpel.excavator_id = mel.technic_id then SUM(mpel.sum_m3) else 0 end AS exca_sum_m3,
				mpel.production_id
			FROM mining_motohour_entry_line AS mel
			LEFT JOIN mining_motohour_entry_operator_line meol on (mel.id = meol.motohour_cause_id)
			left JOIN mining_production_entry_line mpel on ((mpel.dump_id = mel.technic_id or mpel.excavator_id = mel.technic_id) and mel.motohour_id=mpel.production_id)
			LEFT JOIN mining_daily_entry mde on (mde.id = mel.motohour_id)
			where mde.date>='{0}' and  mde.date<='{1}' and meol.operator_id is not null
			group by mde.date, mde.branch_id, mde.shift, mde.part, meol.operator_id, technic_id, mde.id, mpel.dump_id, mpel.excavator_id, mpel.production_id;
		""".format(str(self.date_start),str(self.date_end))
		print(query)
		self.env.cr.execute(query)
		vals = action.read()[0]
		print(vals)
		vals['domain'] = self.get_domain(domain)
		vals['context'] = {}
		print('====--------',self.get_domain(domain))
		return vals