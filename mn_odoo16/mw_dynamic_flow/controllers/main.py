# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import werkzeug

from odoo.api import Environment
import odoo.http as http
from odoo.http import request
from odoo import SUPERUSER_ID
from odoo import registry as registry_get

from odoo.tools.misc import get_lang

import logging
_logger = logging.getLogger(__name__)

class FlowActionNextStage(http.Controller):

    @http.route('/flow/action_next_stage', type='http', auth="public")
    def accept(self, db, model_name, id, user_id_id, flow_line_id, **kwargs):
        # %s/flow/action_next_stage?db=%s&amp;model_name=%s&amp;id=%s&amp;user_id_id=user_base_id_id
        
        registry = registry_get(db)
        error_msg = False
        model_model = model_name
        with registry.cursor() as cr:
            try:
                env = Environment(cr, SUPERUSER_ID, {})
                model_model = env['ir.model'].search([('model', '=', model_name)], limit=1).name
                obj = env[model_name].search([('id', '=', id)], limit=1)
                _logger.info('action_next_stage ################# %s  '%(obj))
                _logger.info('action_next_stage*********** %s %s %s %s'%(model_model,obj,obj.flow_line_id.id,flow_line_id))
                if str(obj.flow_line_id.id)==str(flow_line_id):
                    _logger.info('action_next_stage^^^^^^^^^^^^^^^action_next_stage %s %s'%(model_model,obj))
                    obj.with_user(user_id_id).action_next_stage()
                
                print ('model_model********************',model_model)
            except Exception as e:
                error_msg = str(e)
                _logger.info('FlowActionNextStage %s'%(e))
        return self.view(db, model_name, id, user_id_id, error_msg, model_model)

    @http.route('/flow/action_next_stage/view', type='http', auth="public")
    def view(self, db, model_name, id, user_id_id, error_msg, model_model):
        registry = registry_get(db)
        
        with registry.cursor() as cr:
            # Since we are in auth=none, create an env with SUPERUSER_ID
            env = Environment(cr, SUPERUSER_ID, {})
            obj = env[model_name].search([('id', '=', id)], limit=1)
            lang = env['res.users'].search([('id', '=', user_id_id)], limit=1).lang or get_lang(request.env).code
            
            if not obj:
                return obj.not_found()
            response_content = env['ir.ui.view'].with_context(lang=lang).render_template(
                'mw_dynamic_flow.object_action_next_status', {
                    'next_obj': obj,
                    'error_msg': error_msg,
                    'model_model': model_model,
                })
            return request.make_response(response_content, headers=[('Content-Type', 'text/html')])
