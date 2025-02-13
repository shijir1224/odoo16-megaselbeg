from odoo import api, fields, models
from odoo.exceptions import UserError
from datetime import date
import math
from odoo.addons.mw_technic_equipment.models.technic_equipment import TECHNIC_TYPE
from odoo.addons.mw_technic_equipment.models.technic_equipment import ODOMETER_UNIT


TECHNIC_TYPE.extend([('butluur','Бутлуур'),
                ('shigshuur','Шигшүүр'),
                ('conver','Конвейер'),
                ('plotatsi','Флотаци'),
                ('utguruuleh','Өтгөрүүлэх, Шүүх, Хатаах'),
                ('nasos','Насос'),
                ('gravitatsi','Гравитаци'),
                ('teerem','Тээрэм'),
                ('feeding_device','Тэжээх төхөөрөмж'),
                ('classify','Ангилах'),
                ('transport','Зөөвөрлөх'),
                ('grinding','Нунтаглах'),
                ('stir','Хутгах'),
                ('thincken','Өтгөрүүлэх'),
                ('dehydration','Усгүйжүүлэх'),
                ('urguh_teewerleh','Өргөх, тээвэрлэх'),
                ('tunlah','Тунлах'),
                ('reserve','Нөөцлөх')])
                
ODOMETER_UNIT.extend([('tn/tsag','Тн/цаг'),
                ('m3/tsag','М3/цаг'),
                ('m2/tsag','М2/цаг'),
                ('kvt','КВТ/цаг'),])

class TechnicEquipmentSetting(models.Model):
    _inherit = 'factory.equipment.setting'
    
    technic_type = fields.Selection(TECHNIC_TYPE)
    odometer_unit = fields.Selection(ODOMETER_UNIT)