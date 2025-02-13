
from odoo import _, api, models
from odoo.tools.misc import format_date, get_lang

# class Base(models.AbstractModel):
#     _inherit = 'base'

#     def _get_date_column_label(self, date, field, span, step):
        
#         locale = get_lang(self.env).code
#         _labelize = self._get_date_formatter(step, field, locale=locale)

#         if field.type == 'datetime':  # we want the column label to be the infos in user tz, while the date domain should still be in UTC
#             _date_tz = date.astimezone(pytz.timezone(self._context.get('tz') or 'UTC'))
#         else:
#             _date_tz = date
        
#         date_name = _date_tz.strftime('%Y %m-%d')

#         if 'mining.' in self._name:
#             date_name = _labelize(_date_tz)
#             if step=='day':
#                 date_name = _date_tz.strftime('%Y %m-%d')
#             elif step=='month':
#                 date_name = _date_tz.strftime('%Y-%m')
        
#         return ("%s/%s" % (field.to_string(date), field.to_string(date + self._grid_step_by(step))), date_name)
