# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models
from odoo.exceptions import UserError,AccessError
import logging
_logger = logging.getLogger(__name__)

class IrAttachment(models.Model):
	_inherit = 'ir.attachment'

	def create(self, vals_list):
		res = super(IrAttachment, self).create(vals_list)
		if res:
			if res.res_model and res.res_id:
				attached_model = self.env[res.res_model].browse(res.res_id)
				log_message = u"<span style='color: green'>Хавсралт файл оруулав:</span> {}".format(res.name)
				try:
					attached_model.message_post(body=log_message)
				except Exception as ex:
					_logger.error("ATTACH CREATE - MSG POST ERROR: {}".format(ex))
		return res

	def unlink(self):
		for attachment in self:
			if attachment:
				if attachment.res_model and attachment.res_id:
					attached_model = self.env[attachment.res_model].browse(attachment.res_id)
					log_message = u"{} <span style='color: red'>нэртэй хавсралт файлыг устгав.</span>".format(attachment.name)
					try:
						attached_model.message_post(body=log_message)
					except Exception as ex:
						_logger.error("ATTACH UNLINK - MSG POST ERROR: {}".format(ex))
		return super(IrAttachment, self).unlink()
	
	# def unlink(self):
	#     for s in self:
	#         sql='SELECT ir_attachment_id FROM insurance_claim_required_material_line_ir_attachment_rel WHERE ir_attachment_id ={} '.format(s.id)
	#         self._cr.execute(sql)
	#         result = self._cr.fetchall()
	#         if result:
	#             raise UserError(('НТ хавсралт тул устгах боломжтой!'))
	#     return super(IrAttachment, self).unlink()
# 
# #     def search_read_all(self,domain,fields):
#     def search_read_all(self, domain=None, fields=None, model=None, res_id=None):

#         res = self.search_read(domain,fields)
#         r=[]
#         ids=[]
#         if model and res_id:
#             obj = self.env[model].browse(res_id)
#             if hasattr(obj, 'attachment_ids'):
#                 att = obj.attachment_ids
#                 for i in att:
#                     ids.append(i.id)
#                     r.append({'id':i.id,
#                         'name':i.name,
#                         'mimetype':i.mimetype})
#             if hasattr(obj, 'other_attachment_ids'):
#                 other_att = obj.other_attachment_ids
#                 for i in other_att:
#                     ids.append(i.id)
#                     r.append({'id':i.id,
#                         'name':i.name,
#                         'mimetype':i.mimetype})   
#             if hasattr(obj, 'video_attachment_ids'):
#                 other_att = obj.video_attachment_ids
#                 for i in other_att:
#                     ids.append(i.id)
#                     r.append({'id':i.id,
#                         'name':i.name,
#                         'mimetype':i.mimetype})                       
#             #required_material_line НТ шаардлагатай материал
#             if hasattr(obj, 'required_material_line'):
#                 material_att = obj.required_material_line
#                 for att in material_att:
#                     for i in att.attachment_ids:
#                         ids.append(i.id)
#                         r.append({'id':i.id,
#                             'name':i.name,
#                             'mimetype':i.mimetype})   
#                         
#         
#         if res and res[0].get('id',0) not in ids:
#             r+=res
#         
#         return r