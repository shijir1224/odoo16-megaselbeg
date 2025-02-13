# -*- coding: utf-8 -*-

import copy
from lxml import etree
import odoo
from odoo import api, fields, models, tools, _

class View(models.Model):
	_inherit = 'ir.ui.view'

	def _apply_group(self, model, node, modifiers, fields):
		
		Model = self.env[model]

		if node.tag == 'field' and node.get('name') in Model._fields:
			field = Model._fields[node.get('name')]
			if field.groups and not self.user_has_groups(groups=field.groups):
				node.getparent().remove(node)
				fields.pop(node.get('name'), None)
				# no point processing view-level ``groups`` anymore, return
				return False
		if node.get('groups'):
			can_see = self.user_has_groups(groups=node.get('groups'))
			if not can_see:
				node.set('invisible', '1')
				modifiers['invisible'] = True
				if 'attrs' in node.attrib:
					del node.attrib['attrs']    # avoid making field visible later
			del node.attrib['groups']
		# add the evaluation of our no_groups attribute
		elif node.get('no_groups'):
			cant_see = self.user_has_groups( groups=node.get('no_groups'))
			if cant_see:
				node.set('invisible', '1')
				modifiers['invisible'] = True
				if 'attrs' in node.attrib:
					del(node.attrib['attrs']) #avoid making field visible later
			del(node.attrib['no_groups'])
		# Зөвхөн readonly болгох
		elif node.get('readonly-groups'):
			# print '++++++++++++++++++++++++READONLY GROUP+++++++++++++++++', node.get('readonly-groups')
			can_see_group = True
			if node.get('groups'):
				can_see_group = self.user_has_groups(groups=node.get('groups'))
			if can_see_group:
				can_see = self.user_has_groups(groups=node.get('readonly-groups'))
				if can_see:
					node.set('invisible', '0')
					modifiers['invisible'] = False
					node.set('readonly', '1')
					modifiers['readonly'] = True
					if 'attrs' in node.attrib:
						del node.attrib['attrs']    
				del node.attrib['readonly-groups']
		return True

class ir_ui_menu(models.Model):
	_inherit = 'ir.ui.menu'

	no_groups_id = fields.Many2many('res.groups', 'ir_ui_menu_no_group_rel', 'menu_id', 'gid',string='No Groups')

	@api.model
	@tools.ormcache('frozenset(self.env.user.groups_id.ids)', 'debug')
	def _visible_menu_ids(self, debug=False):
		res = super(ir_ui_menu, self)._visible_menu_ids(debug)
		menus = self.browse(res)
		hasah_ids = []
		for item in menus.filtered(lambda menu: menu.no_groups_id):
			u_ids = item.mapped('no_groups_id.users')
			if self.env.user.id in u_ids.ids:
				hasah_ids.append(item.id)
		if hasah_ids:
			ddd = res - set(hasah_ids)
			res = ddd
		return res
