# -*- coding: utf-8 -*-
from . import models

def pre_init_check(cr):
    from odoo.service import common
    from odoo.exceptions import Warning
    version_info = common.exp_version()
    server_serie = version_info.get('server_serie')
    print ("----server_serie ", server_serie)
    if server_serie != '16.0':
        raise Warning('Зөвхөн 13.0 хувилбар дээр суулгах бөлгөө. {}.'.format(server_serie))
    return True