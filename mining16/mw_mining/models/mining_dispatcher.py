# -*- coding: utf-8 -*-

# from openerp.osv import fields, osv
# from openerp.osv.orm import browse_record, browse_null
# from openerp.tools.translate import _
# from datetime import datetime, timedelta
import pytz
from odoo import api, fields, models, tools, _
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError, Warning

from io import BytesIO
import base64
import xlsxwriter
from tempfile import NamedTemporaryFile
import os, xlrd

# from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, SUPERUSER_ID
import statistics
from odoo.addons.mw_technic_equipment.models.technic_equipment import TECHNIC_TYPE
from odoo.addons.mw_technic_equipment.models.technic_equipment import OWNER_TYPE

import logging

_logger = logging.getLogger(__name__)


class mining_daily_entry(models.Model):
    _name = "mining.daily.entry"
    _description = "The Daily Entry"
    _inherit = ["mail.thread"]
    STATE_SELECTION = [
        ("draft", "Draft"),
        ("approved", "Approved"),
    ]

    @api.depends("production_line.sum_m3", "production_line.res_count")
    def _sum_all(self):
        res = {}
        for obj in self:
            sum_m3 = 0.0
            sum_tn = 0
            sum_mineral_m3 = 0.0
            for item in obj.production_line:
                if item.is_production:
                    sum_m3 += item.sum_m3
                    sum_tn += item.sum_tn
                if item.material_id.mining_product_type == "mineral":
                    sum_mineral_m3 += item.sum_m3

            obj.sum_soil_m3 = sum_m3
            obj.sum_coal_tn = sum_tn
            obj.sum_mineral_m3 = sum_mineral_m3

        return res

    # def _get_production_entry(self):
    #     result = {}
    #     for line in self.pool.get('mining.production.entry.line').browse(cr, uid, ids, context=context):
    #         result[line.production_id.id] = True
    #     return result.keys()
    # by Bayasaa Нэр оноох Өдөр+Ээлж

    @api.depends("date", "shift")
    def _set_name(self):
        for item in self:
            item.name = str(item.date) + "-" + item.shift

    @api.depends("production_line")
    def _sum_res_count(self):
        for item in self:
            item.sum_res_count = sum(item.production_line.mapped("res_count"))
            print("====", len(item.production_line))
            if item.production_line:
                item.average_haul_distance = sum(
                    item.production_line.mapped("haul_distance")
                ) / len(item.production_line)
            else:
                item.average_haul_distance = 0

    @api.depends(
        "motohour_line.motohour_time",
        "motohour_line.repair_time",
        "motohour_line.production_time",
        "motohour_line.work_time",
    )
    def _sum_motohour_time(self):
        for item in self:
            item.sum_motohour_time = sum(item.motohour_line.mapped("motohour_time"))
            item.sum_repair_time = sum(item.motohour_line.mapped("repair_time"))
            item.sum_work_time = sum(item.motohour_line.mapped("production_time"))
            item.sum_production_time = sum(item.motohour_line.mapped("work_time"))
            count_technic = len(item.motohour_line.filtered(lambda r: r.is_tbbk))
            item.sum_tbbk_count = count_technic
            item.count_technic = len(item.motohour_line)
            sum_sum = sum(item.motohour_line.mapped("tbbk"))
            if count_technic > 0:
                item.sum_tbbk = sum_sum / count_technic
            item.sum_tbbk_sum = sum_sum

    def action_call_func2(self):
        obj3 = self.env["mining.daily.entry"].search([])
        for item in obj3:
            for line in item.motohour_line:
                line._sum_time()

    def get_shift(self):
        time = datetime.now(pytz.timezone(self.env.user.tz)).hour
        if time < 7 or 19 <= time:
            return 'night'
        return 'day'

    name = fields.Char(string="Name", readonly=True, store=True, compute="_set_name")
    date = fields.Date(
        "Date", required=True, states={"approved": [("readonly", True)]}, index=True, default=fields.Date.context_today
    )
    branch_id = fields.Many2one(
        "res.branch",
        "Branch",
        required=True,
        states={"approved": [("readonly", True)]},
        index=True,
        default=lambda self: self.env.user.branch_id
    )
    shift = fields.Selection(
        [("day", "Өдөр"), ("night", "Шөнө")],
        "Ээлж",
        required=True,
        states={"approved": [("readonly", True)]},
        index=True,
        default=get_shift
    )
    part = fields.Selection(
        [("a", "A"), ("b", "B"), ("c", "C"), ("d", "D")],
        "Хэсэг",
        required=True,
        states={"approved": [("readonly", True)]},
        index=True,
    )
    user_id = fields.Many2one("res.users", "Бүртгэсэн", required=True, default=lambda self: self.env.user)
    production_line = fields.One2many(
        "mining.production.entry.line",
        "production_id",
        "Production Line",
        states={"approved": [("readonly", True)]},
    )
    state = fields.Selection(
        STATE_SELECTION, "State", readonly=True, tracking=True, default="draft"
    )
    master_id = fields.Many2one(
        "res.users", "Master", states={"approved": [("readonly", True)]}, required=True
    )
    notes = fields.Html(
        "Note",
        required=True,
    )
    hab_info = fields.Html(
        "ХАБЭАБО-н мэдээлэл:",
    )
    foot_info = fields.Html("Уурхайн дарга")
    repair_info = fields.Html(
        "Засварын мэдээлэл:",
    )
    hab_line = fields.One2many(
        "mining.hab.line",
        "daily_id",
        string="Ажиллах хүч",
        states={"approved": [("readonly", True)]},
    )
    sum_soil_m3 = fields.Float(string="Нийт хөрс м3", compute="_sum_all", store=True)
    sum_coal_tn = fields.Float(string="Нийт нүүрс тн", compute="_sum_all", store=True)
    sum_mineral_m3 = fields.Float(string="Нийт Элс м3", compute="_sum_all")
    motohour_line = fields.One2many(
        "mining.motohour.entry.line",
        "motohour_id",
        string="Мотоцагийн мөр",
        states={"approved": [("readonly", True)]},
    )
    sum_res_count = fields.Float(
        string="Нийт ресс", compute="_sum_res_count", store=True
    )
    sum_motohour_time = fields.Float(
        string="Гүйсэн мотоцаг", compute="_sum_motohour_time", store=True
    )
    sum_repair_time = fields.Float(
        string="Засвар Мотоцаг", compute="_sum_motohour_time", store=True
    )
    sum_production_time = fields.Float(
        string="Бүтээлтэй мотоцаг", compute="_sum_motohour_time", store=True
    )
    sum_work_time = fields.Float(
        string="Ажиласан мотоцаг", compute="_sum_motohour_time", store=True
    )
    sum_tbbk = fields.Float(
        string="ТББК %", compute="_sum_motohour_time", store=True, group_operator="avg"
    )
    sum_tbbk_count = fields.Float(
        string="ТББК -д орсон техникийн тоо", compute="_sum_motohour_time", store=True
    )
    sum_tbbk_sum = fields.Float(string="ТББК Нийт ", compute="_sum_motohour_time")
    average_haul_distance = fields.Float(
        string="Дундаж талын зай", readonly=1, compute="_sum_res_count", store=True
    )
    import_data_id = fields.Many2many(
        "ir.attachment",
        "mining_daily_entry_import_data_rel",
        "data_id",
        "attach_id",
        "Мотоцаг Файл",
        copy=False,
    )
    import_data_production_id = fields.Many2many(
        "ir.attachment",
        "mining_daily_entry_import_data_prod_rel",
        "data_id",
        "attach_id",
        "Бүтээл Файл",
        copy=False,
    )
    night_row = fields.Integer(
        "Шөнийн ээлжний бүртгэл эхлэх мөр", default=94, copy=False
    )

    import_employee_id = fields.Many2many(
        "ir.attachment",
        "mining_daily_entry_import_data_rel",
        "data_id",
        "attach_id",
        "Оператор Файл",
        copy=False,
    )

    import_technic_ids = fields.Many2many(
        "technic.equipment",
        "mining_daily_entry_technic_import_rel",
        "entry_id",
        "technic_id",
        "Import technic",
        copy=False,
    )
    remove_technic_ids = fields.Many2many(
        "technic.equipment",
        "mining_daily_entry_technic_remove_rel",
        "entry_id",
        "technic_id",
        "Selective removal technique",
        copy=False,
    )
    mh_line_technic_ids = fields.Many2many(
        "technic.equipment", compute="_compute_mh_line_technic_ids"
    )

    technic_id = fields.Many2one(
        "technic.equipment", related="motohour_line.technic_id"
    )

    count_technic = fields.Integer(
        "Total technic", compute="_sum_motohour_time", readonly=True, store=True
    )

    is_fixing = fields.Boolean("Нөхөж засах эсэх?", deafult=False, readonly=True)

    @api.depends("motohour_line")
    def _compute_mh_line_technic_ids(self):
        for item in self:
            item.mh_line_technic_ids = item.motohour_line.mapped("technic_id")

    def action_remove_custom_technic(self):
        if not self.remove_technic_ids:
            raise UserError("Сонгож устгах техникээ сонгоно уу!!")
        obj = self
        technic_ids = self.remove_technic_ids

        montohour_line_ids = obj.motohour_line.filtered(
            lambda r: r.technic_id.id in technic_ids.ids
        )
        montohour_line_ids.unlink()
        self.remove_technic_ids = False

    def action_call_func(self):

        for line in self.production_line:
            line._sum_all()

        obj3 = self.env["mining.daily.entry"].search([])
        for item in obj3:
            for line in item.production_line:
                line._sum_all()

    def action_call_func_own(self):
        for line in self.production_line:
            line._sum_all()
        for line in self.motohour_line:
            line._sum_time()

    def action_import_custom_technic(self):
        if not self.import_technic_ids:
            raise UserError("Импортлох техникээ сонгоно уу!!")
        obj = self
        technic_ids = self.import_technic_ids.ids

        for item in obj.motohour_line:
            if item.technic_id.id in technic_ids:
                technic_ids.remove(item.technic_id.id)

        for technic in technic_ids:
            if not obj.motohour_line.filtered(lambda r: r.technic_id.id == technic):
                tech_id = self.env["technic.equipment"].browse(technic)
                data = {
                    "technic_id": tech_id.id,
                    "motohour_id": obj.id,
                    "last_km": tech_id.total_km,
                    "first_odometer_value": tech_id.total_odometer,
                }
                m_line_ids = self.env["mining.motohour.entry.line"].create(data)
        self.import_technic_ids = False

    def get_technic_by_name(self, technic_name):
        technic_obj = self.env["technic.equipment"]
        tech_id = technic_obj.search(
            [("park_number", "=", technic_name), ("branch_id", "=", self.branch_id.id)],
            limit=1,
        )
        if not tech_id:
            tech_id = technic_obj.search(
                [
                    ("program_code", "=", technic_name),
                    ("branch_id", "=", self.branch_id.id),
                ],
                limit=1,
            )
        return tech_id

    def get_block_by_name(self, block_name):
        obj = self.env["mining.location"]
        _logger.info("block name %s val %s " % (block_name, type(block_name)))
        obj_id = obj.search([("name", "=", block_name)], limit=1)
        return obj_id

    def get_pile_by_name(self, pile_name):
        obj = self.env["mining.pile"]
        obj_id = obj.search([("name", "=", pile_name)], limit=1)
        return obj_id

    def get_import_val(self, type, val):
        if type == "float":
            try:
                val = float(val)
            except Exception as e:
                val = 0
                _logger.info("float wroooooooooong %s val %s " % (e, val))
        elif type == "str":
            try:
                val = val.strip()
            except Exception as e:
                if isinstance(val, float):
                    val = int(val)
                if not isinstance(val, int):
                    val = ""
                _logger.info("str wroooooooooong %s val %s" % (e, val))
        elif type == "int":
            try:
                val = int(val)
            except Exception as e:
                val = 0
                _logger.info("int wroooooooooong %s val %s" % (e, val))
        return val

    def get_emp_by_name(self, operator_firstname, operator_lastname):
        found_emp = self.env["hr.employee"].search(
            [("name", "=", operator_firstname), ("last_name", "=", operator_lastname)],
            limit=1,
        )
        return found_emp

    def get_cause_id(
        self, cause_code, line_id, cause_time_minute, is_not_remove_cause=False
    ):
        cause_obj = self.env["mining.motohours.cause"]
        cause_line_obj = self.env["mining.motohour.entry.cause.line"]
        cause_line_id = False
        cause_id = cause_obj.search([("name", "=", cause_code)], limit=1)
        if cause_time_minute == " ":
            return True
        if cause_id:
            if (cause_time_minute > 0 and cause_time_minute) or (
                cause_time_minute == 0 and is_not_remove_cause
            ):

                if line_id.motohour_cause_line:
                    last_cause_line_id = line_id.motohour_cause_line[
                        len(line_id.motohour_cause_line) - 1
                    ]
                    last_start_time = last_cause_line_id.start_time
                    last_time_minute = 0
                    if (
                        last_cause_line_id.cause_time_minute == 0
                        and last_cause_line_id.is_not_remove
                    ) and (
                        last_cause_line_id.cause_id.calc_actual
                        or last_cause_line_id.cause_id.calc_production
                    ):
                        last_time_minute = 0
                    else:
                        last_time_minute = last_cause_line_id.cause_time_minute / 60

                    cause_line_id = cause_line_obj.create(
                        {
                            "cause_id": cause_id.id,
                            "motohour_cause_id": line_id.id,
                            "start_time": last_start_time + last_time_minute,
                            "cause_time_minute": cause_time_minute,
                            "is_not_remove": is_not_remove_cause,
                        }
                    )
                else:
                    if line_id.motohour_id.shift == "day":
                        last_start_time = 7
                    else:
                        last_start_time = 19
                    cause_line_id = cause_line_obj.create(
                        {
                            "cause_id": cause_id.id,
                            "motohour_cause_id": line_id.id,
                            "start_time": last_start_time,
                            "cause_time_minute": cause_time_minute,
                            "is_not_remove": is_not_remove_cause,
                        }
                    )
                #
        return cause_line_id

    def create_production_line(
        self,
        dump_id,
        excavator_id,
        material_id,
        res_count,
        block_id,
        level,
        pile_id,
        haul_value,
    ):
        return (
            0,
            0,
            {
                "dump_id": dump_id.id,
                "excavator_id": excavator_id.id,
                "material_id": material_id.id,
                "is_production": material_id.is_productivity,
                "res_count": res_count,
                "from_location": block_id.id if block_id else False,
                "level": level,
                "for_pile": pile_id.id if pile_id else False,
                "haul_distance": haul_value,
            },
        )

    def action_import_employee(self):
        daily_type = self.env.context.get("daily_type", False)

        cause_obj = self.env["mining.motohours.cause"]
        motohour_line_obj = self.env["mining.motohour.entry.line"]
        employee_obj = self.env["hr.employee"]
        operator_line_obj = self.env["mining.motohour.entry.operator.line"]
        material_obj = self.env["mining.material"]
        import_config = self.env["mining.dispatcher.import.config"].search(
            [("type", "=", "motoh"), ("branch_id", "=", self.branch_id.id)], limit=1
        )
        sheet_day = 0
        if daily_type == "motohour":
            date = self.date
            sheet_day = date.day - 1
            import_data = self.import_data_id[0].datas
            if not import_config:
                raise UserError("Мотоцагийн Тохиргоо олдсонгүй Админд хандана уу")
        elif daily_type == "production":
            import_config = self.env["mining.dispatcher.import.config"].search(
                [("type", "=", "prod"), ("branch_id", "=", self.branch_id.id)], limit=1
            )
            sheet_day = 0
            date = self.date
            sheet_day = date.day - 1
            import_data = self.import_data_production_id[0].datas

        if not import_data:
            raise UserError("Оруулах эксэлээ Импортлох эксел-д хийнэ үү ")

        fileobj = NamedTemporaryFile("w+b")
        fileobj.write(base64.decodebytes(import_data))
        fileobj.seek(0)
        if not os.path.isfile(fileobj.name):
            raise UserError(
                "Алдаа Мэдээллийн файлыг уншихад алдаа гарлаа.\nЗөв файл эсэхийг шалгаад дахин оролдоно уу!"
            )
        book = xlrd.open_workbook(fileobj.name)

        try:
            if daily_type == "motohour":
                sheet = book.sheet_by_index(sheet_day)
            elif daily_type == "production":
                sheet = book.sheet_by_index(sheet_day)

        except:
            raise UserError("Алдаа Sheet -ны дугаар буруу байна.")
        nrows = sheet.nrows

        technic_obj = self.env["technic.equipment"]

        if daily_type == "motohour":
            rowi = 3
            if self.shift == "night":
                rowi = self.night_row
            else:
                nrows = self.night_row
            for item in range(rowi, nrows):
                row = sheet.row(item)
                technic_name = self.get_import_val(
                    "str", row[import_config.technic_name_col].value
                )
                operator_firstname = self.get_import_val(
                    "str", row[import_config.firstname_col].value
                )
                operator_lastname = self.get_import_val(
                    "str", row[import_config.lastname_col].value
                )
                last_odometer_value = self.get_import_val(
                    "float", row[import_config.last_motoh_col].value
                )
                _logger.info(
                    "+++++++++++ --####--%s---%s" % (technic_name, last_odometer_value)
                )
                last_km_value = self.get_import_val(
                    "float", row[import_config.last_km_col].value
                )

                tech_id = self.get_technic_by_name(technic_name)

                if tech_id:
                    found_emp = self.get_emp_by_name(
                        operator_firstname, operator_lastname
                    )

                    line_id = self.motohour_line.filtered(
                        lambda r: r.technic_id.id == tech_id.id
                    )

                    if line_id.operator_line and found_emp:
                        opertor_line_id = line_id.operator_line.filtered(
                            lambda r: not r.operator_id
                        )
                        if opertor_line_id:
                            opertor_line_id[0].operator_id = found_emp.id
                        line_id._set_operator_odometer()

                else:
                    if technic_name:
                        _logger.info(
                            "-###-Oldoogui technic --####--%s---" % technic_name
                        )

    def action_import(self):
        daily_type = self.env.context.get("daily_type", False)

        cause_obj = self.env["mining.motohours.cause"]
        motohour_line_obj = self.env["mining.motohour.entry.line"]
        employee_obj = self.env["hr.employee"]
        operator_line_obj = self.env["mining.motohour.entry.operator.line"]
        material_obj = self.env["mining.material"]
        import_config = self.env["mining.dispatcher.import.config"].search(
            [("type", "=", "motoh"), ("branch_id", "=", self.branch_id.id)], limit=1
        )
        sheet_day = 0
        if daily_type == "motohour":
            date = self.date
            sheet_day = date.day - 1
            import_data = self.import_data_id[0].datas
            if not import_config:
                raise UserError("Мотоцагийн Тохиргоо олдсонгүй Админд хандана уу")
        elif daily_type == "production":
            import_config = self.env["mining.dispatcher.import.config"].search(
                [("type", "=", "prod"), ("branch_id", "=", self.branch_id.id)], limit=1
            )
            sheet_day = 0
            date = self.date
            sheet_day = date.day - 1
            import_data = self.import_data_production_id[0].datas

        if not import_data:
            raise UserError("Оруулах эксэлээ Импортлох эксел-д хийнэ үү ")

        fileobj = NamedTemporaryFile("w+b")
        fileobj.write(base64.decodebytes(import_data))
        fileobj.seek(0)
        if not os.path.isfile(fileobj.name):
            raise UserError(
                "Алдаа Мэдээллийн файлыг уншихад алдаа гарлаа.\nЗөв файл эсэхийг шалгаад дахин оролдоно уу!"
            )
        book = xlrd.open_workbook(fileobj.name)

        try:
            if daily_type == "motohour":
                sheet = book.sheet_by_index(sheet_day)
            elif daily_type == "production":
                sheet = book.sheet_by_index(sheet_day)

        except:
            raise UserError("Алдаа Sheet -ны дугаар буруу байна.")
        nrows = sheet.nrows

        technic_obj = self.env["technic.equipment"]

        if daily_type == "motohour":
            rc_cause_id = cause_obj.search([("is_middle", "=", True)], limit=1)
            rowi = 3
            if self.shift == "night":
                rowi = self.night_row
            else:
                nrows = self.night_row
            if self.is_fixing:
                self.motohour_line.unlink()
            for item in range(rowi, nrows):
                row = sheet.row(item)
                technic_name = self.get_import_val(
                    "str", row[import_config.technic_name_col].value
                )
                operator_firstname = self.get_import_val(
                    "str", row[import_config.firstname_col].value
                )
                operator_lastname = self.get_import_val(
                    "str", row[import_config.lastname_col].value
                )
                last_odometer_value = self.get_import_val(
                    "float", row[import_config.last_motoh_col].value
                )
                first_odometer_value = self.get_import_val("float", row[8].value)
                _logger.info(
                    "+++++++++++ --####--%s---%s" % (technic_name, last_odometer_value)
                )
                last_km_value = self.get_import_val(
                    "float", row[import_config.last_km_col].value
                )

                operator_firstname = operator_firstname.strip()
                operator_firstname = operator_firstname.replace("-", "")
                operator_lastname = operator_lastname.strip()
                operator_lastname = operator_lastname.replace("-", "")

                tech_id = self.get_technic_by_name(technic_name)

                if tech_id:
                    found_emp = self.get_emp_by_name(
                        operator_firstname, operator_lastname
                    )

                    line_id = self.motohour_line.filtered(
                        lambda r: r.technic_id.id == tech_id.id
                    )
                    if not line_id and last_odometer_value > 0:
                        if self.is_fixing:
                            vals = {
                                "technic_id": tech_id.id,
                                "motohour_id": self.id,
                                "first_odometer_value": first_odometer_value,
                            }
                        else:
                            vals = {
                                "technic_id": tech_id.id,
                                "motohour_id": self.id,
                                "first_odometer_value": tech_id.total_odometer,
                            }
                        line_id = motohour_line_obj.create(vals)

                    if line_id:
                        is_not_rem = False
                        if line_id.motohour_cause_line.filtered(
                            lambda r: r.is_not_remove == True
                        ):
                            is_not_rem = True

                        sum_cause_time = 0
                        not_cause_ids = []
                        yes_repair_not_remove = False
                        if is_not_rem:
                            for ll in line_id.motohour_cause_line.filtered(
                                lambda r: r.is_not_remove == True
                            ):
                                if (
                                    ll.cause_id.calc_actual
                                    or ll.cause_id.calc_production
                                ):
                                    ll.cause_time_minute = 0
                                    ll.is_not_remove = False
                                    not_cause_ids.append(ll.cause_id.name)
                                else:
                                    ll.cause_time_minute = round(ll.diff_time * 60)
                            sum_cause_time = sum(
                                line_id.motohour_cause_line.filtered(
                                    lambda r: r.is_not_remove == True
                                ).mapped("cause_time_minute")
                            )

                        # Baigaa tsaguudiig ustgah
                        if line_id.motohour_cause_line.filtered(
                            lambda r: r.is_not_remove == False
                        ):
                            line_id.motohour_cause_line.filtered(
                                lambda r: r.is_not_remove == False
                            ).unlink()

                        for ll_id in not_cause_ids:
                            self.get_cause_id(ll_id, line_id, 0, True)

                        if line_id.operator_line:
                            line_id.operator_line.unlink()

                        operator_line_obj.create(
                            {
                                "motohour_cause_id": line_id.id,
                                "operator_id": found_emp.id if found_emp else False,
                                "last_odometer_value": last_odometer_value,
                                # 'last_km': last_km_value,
                            }
                        )
                        line_id.last_km = last_km_value
                        for cause_line in import_config.lines:
                            cause_time = self.get_import_val(
                                "int", row[cause_line.col].value
                            )
                            if cause_time > 0:
                                if (
                                    rc_cause_id
                                    and line_id.technic_id.owner_type == "own_asset"
                                    and cause_line.cause_id.is_repair
                                ):
                                    if cause_time >= 3:
                                        default_hour = self.env[
                                            "mining.default.hour"
                                        ].get_default_cause(
                                            line_id.technic_id, line_id.date
                                        )
                                        cause_ilgeeh = rc_cause_id
                                        if default_hour:
                                            cause_ilgeeh = default_hour["cause_id"]

                                        cause_line_id = self.get_cause_id(
                                            cause_ilgeeh.name, line_id, cause_time, True
                                        )
                                        if default_hour and cause_line_id:
                                            cause_line_id.repair_system_id = (
                                                default_hour["repair_system_id"].id
                                            )
                                    else:
                                        self.get_cause_id(
                                            rc_cause_id.name, line_id, cause_time, True
                                        )
                                else:
                                    self.get_cause_id(
                                        cause_line.cause_id.name, line_id, cause_time
                                    )

                else:
                    if technic_name:
                        _logger.info(
                            "-###-Oldoogui technic --####--%s---" % technic_name
                        )
            for item_c1 in self.motohour_line:
                for item_c2 in item_c1.motohour_cause_line:
                    item_c2.time_setting_compute()

        elif daily_type == "production":
            rowi = 3
            ncols = sheet.ncols
            production_line_vals = []
            first_col = 0
            # if self.production_line:
            # 	self.production_line.unlink()
            for item in range(rowi, nrows):
                row = sheet.row(item)
                dump_name = self.get_import_val(
                    "str", row[import_config.technic_name_col].value
                )
                if dump_name:
                    dump_id = self.get_technic_by_name(dump_name)
                    if dump_id:
                        # coli = 21
                        coli = import_config.exca_name_col
                        exc_row_index = import_config.exca_name_row
                        col_pile = import_config.pile_col
                        col_haul = import_config.haul_distance_col
                        row_block = sheet.row(import_config.block_row)
                        row_level = sheet.row(import_config.level_row)
                        pile_id = self.get_pile_by_name(
                            self.get_import_val("str", row[col_pile].value)
                        )
                        haul_value = self.get_import_val("float", row[col_haul].value)

                        exc_row = sheet.row(exc_row_index)

                        for colitem in range(coli, ncols):
                            exc_name = self.get_import_val(
                                "str", exc_row[colitem].value
                            )
                            if exc_name:
                                excavator_id = self.get_technic_by_name(exc_name)
                                if excavator_id:
                                    material_row = sheet.row(exc_row_index)
                                    m_con_lines = import_config.lines
                                    m_con_index = 0
                                    for material in range(
                                        colitem, colitem + len(m_con_lines)
                                    ):
                                        block_id = self.get_block_by_name(
                                            self.get_import_val(
                                                "str", row_block[material].value
                                            )
                                        )
                                        level = self.get_import_val(
                                            "int", row_level[material].value
                                        )

                                        material_id = m_con_lines[
                                            m_con_index
                                        ].material_id
                                        res_count = self.get_import_val(
                                            "int", row[material].value
                                        )

                                        m_con_index += 1
                                        if res_count > 0:
                                            production_line_vals.append(
                                                self.create_production_line(
                                                    dump_id,
                                                    excavator_id,
                                                    material_id,
                                                    res_count,
                                                    block_id,
                                                    level,
                                                    pile_id,
                                                    haul_value,
                                                )
                                            )

                                else:
                                    _logger.info(
                                        "-***********-Oldoogui excavator --*************--%s---"
                                        % exc_name
                                    )
                    else:
                        _logger.info(
                            "-***********-Oldoogui dump --*************--%s---"
                            % dump_name
                        )

            if production_line_vals:
                self.production_line = production_line_vals

    # by Bayasaa Бүх техникийг импортлох
    def import_technic(self):
        obj = self
        daily_ids = self.env["mining.daily.entry"].search(
            [
                ("date", "<", obj.date),
                ("state", "=", "draft"),
                ("branch_id", "=", obj.branch_id.id),
                ("id", "!=", self.id),
            ]
        )
        technic_ids = self.env["technic.equipment"].search(
            [
                ("odometer_unit", "=", "motoh"),
                ("branch_id", "=", obj.branch_id.id),
                ("state", "!=", "draft"),
            ]
        )

        technic_ids = technic_ids.ids
        for item in obj.motohour_line:
            if item.technic_id.id in technic_ids:
                technic_ids.remove(item.technic_id.id)

        for technic in technic_ids:
            tech_id = self.env["technic.equipment"].browse(technic)
            data = {
                "technic_id": tech_id.id,
                "motohour_id": obj.id,
                "last_km": tech_id.total_km,
                "first_odometer_value": tech_id.total_odometer,
            }
            m_line_ids = self.env["mining.motohour.entry.line"].create(data)

    # by Bayasaa Бүх техникийг устгах
    def remove_technic(self):
        obj = self
        # if not obj.motohour_line:
        #     return {}
        montohour_line_ids = []
        montohour_line_ids = obj.motohour_line.filtered(
            lambda r: not r.motohour_cause_line and not r.operator_line
        )
        montohour_line_ids.unlink()

    def remove_technic_force(self):
        obj = self
        montohour_line_ids = []
        for item in obj.motohour_line:
            if item.motohour_cause_line.filtered(lambda r: r.is_not_remove == True):
                continue
            else:
                montohour_line_ids.append(item.id)
        self.env["mining.motohour.entry.line"].browse(montohour_line_ids).unlink()

        for item in self.motohour_line:
            item.unlink()

    def button_dummy(self):
        self.production_line._sum_all()
        return True

    # by Bayasaa Confirm
    def action_to_approved(self):
        obj = self
        if not obj.motohour_line:
            raise UserError(_("Motohour Line Empty Click on Import Technic Button"))

        text = []
        for item in self.motohour_line.mapped("motohour_cause_line").filtered(
            lambda r: r.cause_id.is_middle
        ):
            text.append(item.motohour_cause_id.technic_id.display_name)
        if text:
            text = set(text)
            raise UserError(
                "Дундын шалтгаан байна түүнийгээ солино уу\n%s" % (", ".join(text))
            )

        self.action_to_check()
        for item in obj.production_line:
            if item.body_capacity_m3 == 0:
                raise Warning(
                    (
                        "%s загвар дээр %s багтаамжын (Capacity м3) тохиргоо хийгдээгүй байна! Инженерт хандан уу!"
                        % (item.dump_id.model_id.name, item.material_id.name)
                    )
                )

        for item in obj.motohour_line:
            daily_ids = self.env["mining.daily.entry"].search(
                [
                    ("date", ">", obj.date),
                    ("branch_id", "=", obj.branch_id.id),
                    ("state", "=", "done"),
                ]
            )
            if not daily_ids:
                # item.technic_id._increase_odometer( obj.date, item.last_odometer_value, item.last_km )
                # Amaraa iim bolguulav
                if item.diff_odometer_value > 0:
                    item.technic_id._increase_odometer(
                        obj.date,
                        item.last_odometer_value,
                        item.last_km,
                        item.diff_odometer_value,
                        0,
                        obj.shift,
                    )

        self.write({"state": "approved"})
        return True

    def action_to_check(self):
        obj = self
        if not obj.motohour_line:
            raise UserError(_("Motohour Line Empty Click on Import Technic Button"))
        for item in obj.motohour_line:
            # Eniig bas tur haav TTJV-d
            # if item.production_time>0:
            #     if item.technic_id.technic_type=='excavator':
            #         if not self.env['mining.production.entry.line'].search([('production_id','=',obj.id),('excavator_id','=',item.technic_id.id)]) and not self.env['mining.concentrator.production.line'].search([('mining_concentrator_production_id','in',self.env['mining.concentrator.production'].search([('date','=',obj.date),('branch_id','=',obj.branch_id.id),('shift','=',obj.shift)])),('excavator_id','=',item.technic_id.id)]):
            #             raise UserError(_(u'Алдаа !!!'+unicode(item.technic_id.name)+u' техник ажиласан мөртлөө Бүтээлийн бүртгэлд бүртгэгдээгүй байна'))
            #     if item.technic_id.technic_type=='dump':
            #         if not self.env['mining.production.entry.line'].search([('production_id','=',obj.id),('dump_id','=',item.technic_id.id)]):
            #             raise UserError(_(u'Алдаа !!!'+unicode(item.technic_id.name)+u' техник ажиласан мөртлөө Бүтээлийн бүртгэлд бүртгэгдээгүй байна'))
            if item.work_diff_time != 12.00:
                raise UserError(
                    (
                        "Ээлжийн цагт хүрэхгүй байна !!! "
                        + (item.technic_id.name)
                        + " нийт цаг "
                        + ""
                        + str(item.work_diff_time)
                    )
                )

            if item.first_odometer_value > item.last_odometer_value:
                raise UserError(
                    ("Дууссан мотоцаг зөрүүтэй байна !!! " + (item.technic_id.name))
                )

            # # Eniig bas tur haav TTJV-d
            # if round(item.diff_odometer_value, 1) != round(item.motohour_time, 1):
            #     #     # Мотоцагийн зөрүү Гүйсэн Мотоцаг 2 тэнцүү байх хэрэгтэй
            #     raise UserError(
            #         _(
            #             "Мотоцагийн зөрүү == Гүйсэн Мотоцаг байх ёстой !!!\nТехник "
            #             + (item.technic_id.name)
            #             + " Дууссан мотоцаг болон шалтгаануудын цагаа нягтлана уу !!!"
            #         )
            #     )

            if (round(item.diff_odometer_value, 1) - round(item.motohour_time, 1)) > 0.5:
                #     # Мотоцагийн зөрүү Гүйсэн Мотоцаг 2 тэнцүү байх хэрэгтэй
                raise UserError(
                    _(
                        "Мотоцагийн зөрүү == Гүйсэн Мотоцаг хоёрын зөрүү 0.5 дотор байх ёстой байх ёстой !!!\nТехник "
                        + (item.technic_id.name)
                        + " Дууссан мотоцаг болон шалтгаануудын цагаа нягтлана уу !!!"
                    )
                )

        # Eniig bas tur haav TTJV-d
        # for item in obj.production_line:
        #     if item.sum_m3>0:
        #         if not self.env['mining.motohour.entry.line'].search([('motohour_id','=',obj.id),('technic_id','=',item.dump_id.id)]):
        #             raise UserError(_(u'Алдаа !!!'+unicode(item.dump_id.name)+u' техник бүтээлтэй мөртлөө Мотоцагийн бүртгэлд бүртгэгдээгүй байна'))
        #         if not self.env['mining.motohour.entry.line'].search([('motohour_id','=',obj.id),('technic_id','=',item.excavator_id.id)]):
        #                 raise UserError(_(u'Алдаа !!!'+unicode(item.excavator_id.name)+u' техник бүтээлтэй мөртлөө Мотоцагийн бүртгэлд бүртгэгдээгүй байна'))

    # by Bayasaa Цуцлах
    def action_to_draft(self):
        self.write({"state": "draft"})
        return True

    def get_motohour_js(self):
        result = {
            "mining_mh_causes": [],
            "motohour_line": [],
            "state": self.state,
        }
        mining_mh_causes = []
        for item in self.env["mining.motohours.cause"].search([]):
            mining_mh_causes.append(
                {
                    "name": item.name,
                    "color": item.color,
                    "cause_name": item.cause_name,
                }
            )

        result["mining_mh_causes"] = mining_mh_causes

        mhl = []
        for item in self.motohour_line:
            causes = []

            for res in item.motohour_cause_line:
                causes.append(
                    {
                        "start_time": res.start_time,
                        "r_start_time": res.r_start_time
                        # ,'description':res.work_order_id[1]+' / '+res.job_description
                        ,
                        "diff_time": res.diff_time,
                        "cause": res.cause_id.name,
                        "color": res.color,
                        "line_id": res.id,
                        "cause_name": res.cause_name,
                    }
                )
            mhl.append(
                {
                    "motohour": item.id,
                    "technic_id": item.sudo().technic_id.id,
                    "technic_names": item.sudo().technic_id.name,
                    "last_odometer_value": item.last_odometer_value,
                    "first_odometer_value": item.first_odometer_value,
                    "operator_id": item.operator_names,
                    "work_diff_time": round(item.work_diff_time, 1),
                    "diff_odometer_value": round(item.diff_odometer_value, 1),
                    "production_time": round(item.production_time, 1),
                    "repair_time": round(item.repair_time, 1),
                    "tbbk": round(item.tbbk, 2),
                    "is_tbbk": item.is_tbbk,
                    "work_time": round(item.work_time, 1),
                    "motohour_time": round(item.motohour_time, 1),
                    "causes": causes,
                }
            )
        result["motohour_line"] = mhl
        return result

    def view_line_production(self):
        context = dict(self._context)
        action = {
            "name": "Хүсэлт",
            "view_type": "pivot",
            "view_mode": "pivot",
            "res_model": "mining.production.report",
            "view_id": self.env.ref("mw_mining.view_mining_production_report_pivot").id,
            "domain": [("production_id", "in", self.production_line.ids)],
            "type": "ir.actions.act_window",
            "context": context,
            "target": "current",
        }
        return action

    # by Bayasaa Өдөр шөнөөс хамааруулах ээлж сонгогдох
    _order = "date desc, shift asc"
    _sql_constraints = [
        ("name_uniq", "UNIQUE(date, branch_id, shift)", "Date and Shift must be unique")
    ]


class mining_production_entry_line(models.Model):
    _name = "mining.production.entry.line"
    _description = "Production Entry Line"

    # by Bayasaa тэвшний багтаамж өөрчлөгдөх
    @api.onchange("material_id")
    def on_change_material(self):
        material_obj = self.material_id
        material_type = material_obj.mining_product_type
        if material_obj.mining_product_type == "mineral":
            material_type = False
        self.the_from = False
        self.the_for = False
        self.from_pile = False
        self.from_location = False
        self.for_pile = False
        self.for_location = False
        self.coal_layer = False
        self.is_stone = False
        self.is_sulfur = False
        self.domain_material_type = material_type

    # by Bayasaa
    @api.onchange("the_from")
    def on_change_from(self):
        self.from_pile = False
        self.from_location = False

    # by Bayasaa
    @api.onchange("the_for")
    def on_change_for(self):
        self.for_pile = False
        self.for_location = False

    @api.depends("dump_id", "material_id", "res_count")
    def _sum_all(self):
        for obj in self:
            # if obj.body_capacity_m3 > 0:
            #     continue
            sum_m3 = 0.0
            sum_tn = 0
            capacity_m3 = 0.0
            capacity_tn = 0.0
            mining_technic_setting = self.env["mining.technic.configure"].search(
                [
                    ("technic_setting_id", "=", obj.dump_id.technic_setting_id.id),
                    ("material_id", "=", obj.material_id.id),
                    ("branch_id", "=", obj.production_id.branch_id.id),
                ],
                limit=1,
            )
            capacity = mining_technic_setting

            if capacity:
                capacity_m3 = capacity.body_capacity_m3
                capacity_tn = capacity.body_capacity_tn
            sum_m3 = obj.res_count * obj.body_capacity_m3
            sum_tn = obj.res_count * obj.body_capacity_tn
            obj.body_capacity_m3 = capacity_m3 or obj.body_capacity_m3
            obj.body_capacity_tn = capacity_tn or obj.body_capacity_tn
            obj.sum_m3 = sum_m3
            obj.sum_tn = sum_tn

    production_id = fields.Many2one(
        "mining.daily.entry",
        "Production ID",
        required=True,
        ondelete="cascade",
        index=True,
    )
    date = fields.Date(related="production_id.date", store=True)
    shift = fields.Selection(related="production_id.shift")
    dump_id = fields.Many2one("technic.equipment", "Dump", required=True, index=True)
    material_id = fields.Many2one(
        "mining.material", "Material", required=True, index=True
    )
    domain_material_type = fields.Char("Domain Material", size=100)
    the_from = fields.Selection([("location", "Блок"), ("pile", "Овоолго")], "Аас")
    from_pile = fields.Many2one(
        "mining.pile",
        "Piles",
    )
    from_location = fields.Many2one("mining.location", "Блок")
    the_for = fields.Selection([("location", "Блок"), ("pile", "Овоолго")], "Хүртэл")
    for_pile = fields.Many2one("mining.pile", "Овоолго")
    for_location = fields.Many2one("mining.location", "Блок")
    level = fields.Integer("Level", default=1000)
    res_count = fields.Integer("Ресс")
    excavator_id = fields.Many2one(
        "technic.equipment", "Excavator", required=True, index=True
    )
    body_capacity_m3 = fields.Float(
        compute="_sum_all", string="Capacity м3", store=True
    )
    body_capacity_tn = fields.Float(
        compute="_sum_all", string="Capacity тонн", store=True
    )
    sum_m3 = fields.Float(compute="_sum_all", string="Total м3", store=True)
    sum_tn = fields.Float(compute="_sum_all", string="Total тонн", store=True)
    sum_m3_petram = fields.Float(string="Total м3 Петрам", store=True)
    sum_tn_petram = fields.Float(string="Total тонн Петрам", store=True)
    sum_m3_puu = fields.Float(string="Total м3 Пүү", store=True)
    sum_tn_puu = fields.Float(string="Total тонн Пүү", store=True)
    is_production = fields.Boolean("Productivity", default=True)
    is_stone = fields.Boolean("Чулуутай?", readonly=True)
    is_sulfur = fields.Boolean("Хүхэртэй?", readonly=True)
    coal_layer = fields.Selection(
        [
            ("1", "1"),
            ("2", "2"),
            ("3", "3"),
            ("4", "4"),
            ("5", "5"),
            ("6", "6"),
            ("7", "7"),
            ("8", "8"),
            ("9", "9"),
            ("10", "10"),
        ],
        "Layer",
        readonly=True,
    )
    haul_distance = fields.Float(string="Талын зай", default=0)


# Tehniciin modultai inherit hiij bgaa heseg by Purvee
class MotoHourEntry(models.Model):
    _inherit = "technic.equipment"

    moto_hour_ids = fields.One2many(
        "mining.motohour.entry.line",
        "technic_id",
        string="Moto Hour",
        groups="mw_mining.group_mining_user",
    )
    production_view_ids = fields.One2many(
        "mining.production.entry.line",
        "dump_id",
        string="Dump",
        groups="mw_mining.group_mining_user",
    )
    production_exca_ids = fields.One2many(
        "mining.production.entry.line",
        "excavator_id",
        string="Exca buteel",
        groups="mw_mining.group_mining_user",
    )
    production_count = fields.Integer(
        string="Нийт бүтээл",
        compute="_compute_contract_count",
        groups="mw_mining.group_mining_user",
    )
    res_count = fields.Integer(
        string="Нийт res",
        compute="_compute_contract_count",
        groups="mw_mining.group_mining_user",
    )
    plan_this_year_production = fields.Integer(
        string="Энэ жил төлөвлөгөө бүтээл",
        compute="_compute_contract_count_plan",
        groups="mw_mining.group_mining_user",
    )
    plan_this_year_time = fields.Float(
        string="Энэ жил төлөвлөгөө цаг",
        compute="_compute_contract_count_plan",
        groups="mw_mining.group_mining_user",
    )
    technic_plan_line_ids = fields.One2many(
        "mining.plan.technic.line",
        "technic_id",
        string="Technic",
        groups="mw_mining.group_mining_user",
    )

    # Бүтээлийн хүснэгтийг харуулдаг товчлуурын функц By Purvee
    def see_productions(self):
        action = self.env.ref("mw_mining.action_mining_production_report_tree").read()[
            0
        ]
        action["domain"] = [
            "|",
            ("dump_id", "=", self.id),
            ("excavator_id", "=", self.id),
        ]
        action["context"] = {}
        return action

    def see_plan(self):
        action = self.env.ref("mw_mining.action_mining_plan_technic_line_all").read()[0]
        action["domain"] = [("technic_id", "=", self.id)]
        action["context"] = {"search_default_this_year": True}
        return action

    @api.depends("technic_plan_line_ids")
    def _compute_contract_count_plan(self):
        for item in self.sudo():
            item.plan_this_year_production = sum(
                item.sudo()
                .technic_plan_line_ids.filtered(
                    lambda r: r.date.year == fields.Date.context_today(self).year
                )
                .mapped("production")
            )
            item.plan_this_year_time = sum(
                item.sudo()
                .technic_plan_line_ids.filtered(
                    lambda r: r.date.year == fields.Date.context_today(self).year
                )
                .mapped("run_hour_util")
            )
            print("item.plan_this_year_production", item.plan_this_year_production)
            print("item.plan_this_year_time", item.plan_this_year_time)
            # print (blllblbl)

    # By Purvee
    @api.depends("production_view_ids", "production_exca_ids")
    def _compute_contract_count(self):
        for item in self.sudo():
            item.production_count = sum(
                item.sudo().production_view_ids.mapped("sum_m3")
            ) + sum(item.sudo().production_exca_ids.mapped("sum_m3"))
            item.res_count = sum(
                item.sudo().production_view_ids.mapped("res_count")
            ) + sum(item.sudo().production_exca_ids.mapped("res_count"))


class mining_motohour_entry_line(models.Model):
    _name = "mining.motohour.entry.line"
    _description = "Mining Motohour Entry Line"

    # by Bayasaa Ажилсан цаг
    @api.depends("motohour_cause_line.diff_time", "technic_id")
    def _sum_time(self):
        for obj in self:
            obj.work_diff_time = sum(obj.motohour_cause_line.mapped("diff_time"))
            obj.motohour_time = sum(
                obj.motohour_cause_line.filtered(
                    lambda r: r.cause_id.cause_type.type == "smu"
                ).mapped("diff_time")
            )
            obj.work_time = sum(
                obj.motohour_cause_line.filtered(
                    lambda r: r.cause_id.calc_actual
                ).mapped("diff_time")
            )
            obj.production_time = sum(
                obj.motohour_cause_line.filtered(
                    lambda r: r.cause_id.calc_production
                ).mapped("diff_time")
            )
            obj.repair_time = sum(
                obj.motohour_cause_line.filtered(lambda r: r.cause_id.is_repair).mapped(
                    "diff_time"
                )
            )
            if (
                (
                    obj.sudo().technic_id.is_tbb_mining
                    or obj.sudo().technic_id.technic_setting_id.is_tbb_mining
                )
                and obj.sudo().technic_id.state in ["working", "repairing", "stopped"]
                and obj.sudo().technic_id.owner_type == "own_asset"
            ):
                tbb = (12 - obj.repair_time) * 100 / 12
                obj.tbbk = 0 if tbb < 0 else tbb
                obj.is_tbbk = True
            else:
                obj.tbbk = 0
                obj.is_tbbk = False

    # by Bayasaa Ажилсан цаг
    @api.depends("operator_line", "first_odometer_value")
    def _set_operator_odometer(self):
        for obj in self:
            last_odometer = 0.0
            o_names = ""
            for item in obj.operator_line:
                if item.last_odometer_value > last_odometer:
                    last_odometer = item.last_odometer_value
                if item.operator_id.name:
                    o_names += item.operator_id.name + "\n"
            obj.last_odometer_value = last_odometer
            obj.operator_names = o_names
            obj.diff_odometer_value = last_odometer - obj.first_odometer_value

    motohour_id = fields.Many2one(
        "mining.daily.entry",
        "Motohour ID",
        required=True,
        ondelete="cascade",
        index=True,
    )
    technic_id = fields.Many2one(
        "technic.equipment", "Technic", required=True, readonly=True, index=True
    )
    report_order = fields.Char(
        related="technic_id.report_order", readonly=True, store=True, related_sudo=True
    )
    technic_name = fields.Char(
        related="technic_id.name", store=True, readonly=True, related_sudo=True
    )
    technic_type = fields.Selection(
        TECHNIC_TYPE, store=True, readonly=True, related_sudo=True
    )
    owner_type = fields.Selection(
        OWNER_TYPE, store=True, readonly=True, related_sudo=True
    )
    operator_names = fields.Char(
        string="Operators", compute="_set_operator_odometer", readonly=True, store=True
    )
    first_odometer_value = fields.Float(
        "Мотоцаг Эхэнд", states={"approved": [("readonly", True)]}
    )
    last_odometer_value = fields.Float(
        string="Дууссан Мотоцаг",
        compute="_set_operator_odometer",
        readonly=True,
        store=True,
    )
    diff_odometer_value = fields.Float(
        string="Difference Moto Hours", compute="_set_operator_odometer", store=True
    )
    motohour_cause_line = fields.One2many(
        "mining.motohour.entry.cause.line",
        "motohour_cause_id",
        states={"approved": [("readonly", True)]},
    )
    work_diff_time = fields.Float(
        string="Total time",
        digits=(16, 1),
        compute="_sum_time",
        readonly=True,
        store=True,
    )
    motohour_time = fields.Float(
        string="Зөрүү Гүйсэн Мотоцаг",
        digits=(16, 1),
        compute="_sum_time",
        readonly=True,
        store=True,
    )
    repair_time = fields.Float(
        string="Repair time",
        digits=(16, 1),
        compute="_sum_time",
        readonly=True,
        store=True,
    )
    work_time = fields.Float(
        string="Working time",
        digits=(16, 1),
        compute="_sum_time",
        readonly=True,
        store=True,
    )
    production_time = fields.Float(
        string="Productivity time",
        digits=(16, 1),
        compute="_sum_time",
        readonly=True,
        store=True,
    )
    state = fields.Selection(related="motohour_id.state")
    shift = fields.Selection(related="motohour_id.shift")
    motohour_date = fields.Date(related="motohour_id.date")
    date = fields.Date(related="motohour_id.date", store=True)
    branch_id = fields.Many2one(
        "res.branch", related="motohour_id.branch_id", store=True
    )
    # domain_operator = fields.function(_set_domain_operator, type='many2many', relation='hr.employee', string='Domain Opertator ID'),
    operator_line = fields.One2many(
        "mining.motohour.entry.operator.line",
        "motohour_cause_id",
        states={"approved": [("readonly", True)]},
    )
    is_medium_technic = fields.Boolean("Дундын Техник")
    last_km = fields.Float("Last Км", states={"approved": [("readonly", True)]})
    tbbk = fields.Float("TBBK", compute="_sum_time", store=True)
    is_tbbk = fields.Boolean(string="ТББК-д орох эсэх", compute="_sum_time", store=True)

    _order = (
        "owner_type desc, report_order, technic_name asc, technic_type desc, date desc"
    )

    _sql_constraints = [
        ("last_km_cons", "CHECK(last_km >= 0)", "Error ! Last Km is  >= 0")
    ]


class mining_motohour_entry_operator_line(models.Model):
    _name = "mining.motohour.entry.operator.line"
    _description = "Mining Motohour Opertator Entr Line"

    # by Bayasaa Ажилсан цаг
    @api.depends("motohour_cause_id.first_odometer_value", "last_odometer_value")
    def _set_time(self):
        # for obj in self:
        # obj = entry.motohour_cause_id.operator_line
        for item in self:
            first = item.motohour_cause_id.first_odometer_value
            last = item.last_odometer_value
            obj2 = item.motohour_cause_id.operator_line
            for line in item:
                if first < line.last_odometer_value and line.last_odometer_value < last:
                    first = line.last_odometer_value
            item.o_motohour_time = last - first
            item.o_production_time = 0.0
            item.first_odometer_value = first

    motohour_cause_id = fields.Many2one(
        "mining.motohour.entry.line",
        "Cause ID",
        required=True,
        ondelete="cascade",
        index=True,
    )
    daily_entry_id = fields.Many2one(
        "mining.daily.entry",
        related="motohour_cause_id.motohour_id",
        readonly=True,
        store=True,
        index=True,
    )
    # daily_entry_id = fields.Many2one('mining.daily.entry', compute='_set_daily_entry_id', readonly=True, store=True, index=True)
    operator_id = fields.Many2one("hr.employee", "Operator")
    last_odometer_value = fields.Float("Last Odometer")
    first_odometer_value = fields.Float(
        string="First Odometer", compute="_set_time", readonly=True, store=True
    )
    o_production_time = fields.Float(
        string="Productivity time", compute="_set_time", readonly=True, store=True
    )
    o_motohour_time = fields.Float(
        string="Мотоцаг гүйсэн", compute="_set_time", readonly=True, store=True
    )

    # @api.depends('motohour_cause_id')
    # def _set_daily_entry_id(self):
    #     for item in self:
    #         item.daily_entry_id = item.motohour_cause_id.motohour_id

    _order = "last_odometer_value asc"
    # _sql_constraints = [
    #      ('motohour_time','CHECK(o_motohour_time >= 0)','Error ! Motohour Time is ever >= 0'),
    # ]

    @api.constrains("o_motohour_time")
    def _check_o_motohour_time(self):
        for item in self:
            if item.o_motohour_time < 0:
                raise UserError(
                    "%s Error ! Motohour Time is ever >= 0  %s %s "
                    % (
                        item.motohour_cause_id.technic_id.name,
                        item.last_odometer_value,
                        item.first_odometer_value,
                    )
                )


class mining_motohour_entry_cause_line(models.Model):
    _name = "mining.motohour.entry.cause.line"
    _description = "Mining Motohour Cause Line"

    @api.depends("motohour_cause_id.shift", "start_time")
    def _set_start_time(self):
        for obj in self:
            time = obj.start_time
            if obj.motohour_cause_id.shift == "night" and time < 19:
                time += 24.0
            obj.r_start_time = time

    @api.onchange("cause_id")
    def on_change_cause(self):
        if self.cause_id:
            self.is_repair = self.cause_id.is_repair

    @api.model
    def _default_start_time(self):
        parent_shift = self.env.context.get("parent_shift", False)
        time = 0
        if parent_shift == "day":
            time = 7
        elif parent_shift == "night":
            time = 19
        current_time = datetime.now().astimezone(pytz.timezone(self.env.user.tz))
        time = current_time.hour + current_time.minute/60
        return time

    motohour_cause_id = fields.Many2one(
        "mining.motohour.entry.line", "Cause ID", required=True, ondelete="cascade"
    )
    shift = fields.Selection(related="motohour_cause_id.shift", readonly=True)
    cause_id = fields.Many2one("mining.motohours.cause", "Cause", required=True)
    cause_name = fields.Char(related="cause_id.cause_name", string="Cause name")
    is_medium_technic = fields.Boolean(related="motohour_cause_id.is_medium_technic")
    start_time = fields.Float("Start time", digits=(16, 2), default=_default_start_time)
    r_start_time = fields.Float(
        digits=(16, 2),
        string="Real Start Time",
        compute="_set_start_time",
        readonly=True,
        store=True,
    )
    diff_time = fields.Float(
        "Cause time",
        digits=(16, 2),
        readonly=True,
        compute="time_setting_compute",
        store=True,
    )
    description = fields.Char("Description", size=150)
    work_order_id = fields.Many2one(
        "maintenance.workorder", "Work Order", readonly=True
    )
    location_id = fields.Many2one("mining.location", "Блок")
    # job_description = fields.Char(related='work_order_id.job_description','job_description')
    color = fields.Selection(related="cause_id.color", string="Color")
    is_repair = fields.Boolean(related="cause_id.is_repair", readonly=True)
    percentage = fields.Integer("Percentage", readonly=True, invisible=True)
    cause_time_minute = fields.Float("By Minut", digits=(16, 2))
    repair_system_id = fields.Many2one(
        "maintenance.damaged.type",
        string="Зогссон систем",
        domain="[('parent_id','=',False)]",
        store=True,
    )

    view_cause_ids = fields.Many2many(
        "mining.motohours.cause",
        string="Харагдах шалтгаанууд",
        compute="_compute_is_repair_user",
    )

    @api.depends("cause_id", "start_time", "motohour_cause_id.technic_id")
    def _compute_is_repair_user(self):
        for item in self:
            if self.user_has_groups("mw_mining.group_mining_not_remove_cause"):
                item.view_cause_ids = self.env["mining.motohours.cause"].search(
                    [
                        "|",
                        "|",
                        "|",
                        ("is_repair", "=", True),
                        ("is_middle", "=", True),
                        ("calc_production", "=", True),
                        ("name", "in", ["S1", "S2", "S7", "S9"]),
                    ]
                )
            elif item.motohour_cause_id.technic_id.owner_type in ["rent", "contracted"]:
                item.view_cause_ids = self.env["mining.motohours.cause"].search(
                    ["|", ("is_repair", "!=", True), ("is_repair", "=", True)]
                )
            else:
                item.view_cause_ids = self.env["mining.motohours.cause"].search(
                    [("is_repair", "!=", True)]
                )

    @api.model
    def _default_is_not_remove_group(self):
        if self.user_has_groups("mw_mining.group_mining_not_remove_cause"):
            return True
        else:
            return False

    is_not_remove = fields.Boolean(
        "Устгахгүй цаг", default=_default_is_not_remove_group
    )
    is_not_remove_group = fields.Boolean(
        "Устгахгүй цаг",
        compute="_compute_is_not_remove_group",
        default=_default_is_not_remove_group,
    )

    @api.onchange("cause_id")
    def onchange_cause_id_is_not_remove(self):
        if self.user_has_groups("mw_mining.group_mining_not_remove_cause"):
            if self.cause_id.calc_actual or self.cause_id.calc_production:
                self.is_not_remove = False
            else:
                self.is_not_remove = True

    def _compute_is_not_remove_group(self):
        for item in self:
            if self.user_has_groups("mw_mining.group_mining_not_remove_cause"):
                item.is_not_remove_group = True
            else:
                item.is_not_remove_group = False

    def unlink(self):
        for item in self:
            if (
                not self.user_has_groups("mw_mining.group_mining_not_remove_cause")
                and item.is_not_remove
            ):
                raise UserError("Устгахгүй цагийг УСТГАХ ЭРХТЭЙ ХҮН УСТГАНА!!")
        return super(mining_motohour_entry_cause_line, self).unlink()

    _order = "r_start_time asc, is_not_remove desc, create_date asc"

    @api.onchange("start_time", "motohour_cause_id")
    def check_time_onchange(self):
        obj = self
        if (
            obj.start_time
            and obj.cause_id
            and obj.motohour_cause_id
            and obj.motohour_cause_id.motohour_date
        ):
            st_time = float(obj.start_time)
            hours = int(st_time)
            minutes = int((st_time - hours) * 60)
            now_time = datetime.now(pytz.timezone(self._context.get("tz") or "UTC"))
            if obj.motohour_cause_id.shift == "day" and (7 > st_time or 19 < st_time):
                raise UserError(_("Wrong time Shift is Day 07:00<=time<=19:00 "))
            if obj.motohour_cause_id.shift == "night":
                if 7 >= st_time:
                    st_time += 24
            if obj.motohour_cause_id.shift == "night" and (
                19 > st_time or 31 < st_time
            ):
                raise UserError(_("Wrong time Shift is Night 19:00<=time<=07:00 "))
            # Night shalgah
            # form_date = datetime.strptime(obj.motohour_cause_id.motohour_date+' '+str(hours)+':'+str(minutes)+':00.00', '%Y-%m-%d %H:%M:%S.%f')
            form_date = obj.motohour_cause_id.motohour_date + relativedelta(
                hour=hours, minute=minutes
            )
            # print(obj.motohour_cause_id.motohour_date, form_date)
            # print(form_date, obj.id)
            # print(obj.motohour_cause_id.motohour_cause_line.mapped('id'))
            # print(obj.motohour_cause_id.motohour_cause_line.mapped('start_time'))
            form_date = form_date.replace(tzinfo=pytz.timezone(self._context.get("tz")))
            now_time = now_time.replace(tzinfo=pytz.timezone(self._context.get("tz")))

            if form_date > now_time:
                raise UserError(_("Wrong time Time is not Time > (Now Time) "))
            # for item in obj.motohour_cause_id.motohour_cause_line.filtered(lambda r: r.id != obj.id):
            # 	if item.start_time == obj.start_time:
            # 		raise UserError(_('Wrong time Time is UNIQUE'))
            # self.env.cr.commit()
            # return False
            # i = 0
            # lines = obj.motohour_cause_id.motohour_cause_line
            # for item in lines.filtered(lambda r: r.id != obj.id):
            # 	if obj.id == item.id:
            # 		if i+1<len(lines):
            # 			if obj.cause_id == lines[i+1].cause_id:
            # 				raise UserError(_('Wrong time Шалтгаан дараалж орсон байна '))
            # 				return False
            # 		if i-1>=0:
            # 			if obj.cause_id == lines[i-1].cause_id:
            # 				raise UserError(_('Wrong time Шалтгаан дараалж орсон байна '))
            # 				return False
            # 	i += 1
        # return True

    @api.depends(
        "motohour_cause_id.motohour_cause_line.r_start_time",
        "motohour_cause_id.motohour_cause_line.start_time",
        "start_time",
        "r_start_time",
    )
    def time_setting_compute(self):
        for obj in self:
            i = 0
            if obj.id:
                if obj.motohour_cause_id:
                    lines = obj.motohour_cause_id.motohour_cause_line
                    for item in lines:
                        i += 1
                        if i < len(lines):
                            item.diff_time = (
                                lines[i].r_start_time - lines[i - 1].r_start_time
                            )
                            # super(mining_motohour_entry_cause_line, self).write(cr, uid, item.id,
                            #     {'diff_time':lines[i].r_start_time-lines[i-1].r_start_time}, context)
                        else:
                            now_time = datetime.now(
                                pytz.timezone(self._context.get("tz") or "UTC")
                            )
                            r_shift = "night"
                            r_time = now_time.hour + float(now_time.minute) / 60
                            if r_time >= 7.0 and r_time < 19.0:
                                r_shift = "day"
                            e_time = 19
                            if lines[i - 1].motohour_cause_id.shift == "night":
                                e_time = 31
                            item.diff_time = e_time - lines[i - 1].r_start_time

                    # obj._onchage_cause_time_minute()
                    # super(mining_motohour_entry_cause_line, self).write(cr, uid, item.id,
                    #     {'diff_time':e_time-lines[i-1].r_start_time}, context)
                if not obj.motohour_cause_id:
                    current_time = datetime.now().astimezone(pytz.timezone(self.env.user.tz))
                    if current_time.hour >= 7:
                        obj.diff_time = (current_time.hour - 7) + (current_time.minute/60)
                    elif current_time.hour < 6:
                        obj.diff_time = (current_time.hour + 5) + (current_time.minute/60)
                    elif current_time.hour >= 19:
                        obj.diff_time = (current_time.hour - 19) + (current_time.minute/60)
                    for line in obj.motohour_cause_id.motohour_cause_line.sorted(key=lambda r: r.start_time):
                        line
                else:
                    obj.diff_time = 0
                    # res = obj.motohour_cause_id._sum_time()
            else:
                obj.diff_time = 0
        return True

    # @api.onchange('diff_time')
    # def _onchage_cause_time_minute(self):
    #     for item in self:
    #         item.cause_time_minute = round(item.diff_time*60)

    def _get_time(self, shift, time):
        if shift == "night" and time < 19:
            time += 24.0
        return time

    # def _get_start_time(self, cr, uid, context=None):
    #     now_time = datetime.now(pytz.timezone(self._context.get('tz')))
    #     return now_time.hour + float(now_time.minute)/60
    _order = "r_start_time asc, create_date asc"
    # _defaults = {
    #     'start_time': _get_start_time,
    # }
    _sql_constraints = [
        (
            "percentage",
            "CHECK(percentage >= 0)",
            "Error ! 0 <= percentage is ever <= 100",
        ),
    ]
