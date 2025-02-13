# -*- encoding: utf-8 -*-
############################################################################################
#
#    Managewall-ERP, Enterprise Management Solution    
#    Copyright (C) 2007-2017 mw Co.,ltd (<http://www.managewall.mn>). All Rights Reserved
#    $Id:  $
#
#    Менежволл-ЕРП, Байгууллагын цогц мэдээлэлийн систем
#    Зохиогчийн зөвшөөрөлгүйгээр хуулбарлах ашиглахыг хориглоно.
#
#
#
############################################################################################

from datetime import timedelta
from lxml import etree

import base64
import time
import datetime
from datetime import datetime

import logging
from odoo import api, fields, models, _
from odoo import models, fields, api, _
from odoo.tools.safe_eval import safe_eval as eval
from odoo.exceptions import UserError

import time
import datetime
from datetime import timedelta
from lxml import etree

from odoo.tools.translate import _

import xlwt
from xlwt import *
# from odoo.addons.c2c_reporting_tools.c2c_helper import *
from operator import itemgetter
# from odoo.addons.mn_base import report_helper
# logger = netsvc.Logger()
logger = logging.getLogger('odoo')

class account_partner_ledger(models.TransientModel):
    """
        Өглөгийн дансны товчоо
    """
    
#     _inherit = "abstract.report.excel"
    _inherit = "account.partner.ledger2"

    account_id = fields.Many2one('account.account', 'Account', domain=[('user_type_id.type','in',['payable','receivable'])])

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
