from odoo import fields, models, _


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    school_line_ids = fields.One2many(
        'hr.school', 'employee_id', string='Төгссөн сургууль', tracking=True, copy=True)
    course_line_ids = fields.One2many(
        'hr.course', 'employee_id', string='Курс Дамжаа', tracking=True, copy=True)
    degree_line_ids = fields.One2many(
        'hr.degree', 'employee_id', string='Олон улсын мэргэжлийн, болон спортын зэрэг цол', tracking=True, copy=True)
    language_line_ids = fields.One2many(
        'hr.language', 'employee_id', string='Гадаад хэлний мэдлэг', tracking=True, copy=True)
    software_skill_line_ids = fields.One2many(
        'hr.software.skill', 'employee_id', string='Програмын ур чадвар', tracking=True, copy=True)
    other_skill_line_ids = fields.One2many(
        'hr.other.skill', 'employee_id', string='Нэмэлт ур чадвар', tracking=True, copy=True)

class HrCourse(models.Model):
    _name = 'hr.course'
    _description = 'course'

    employee_id = fields.Many2one('hr.employee', 'Employee')
    name = fields.Char('Сургалтын агуулга')
    country_id = fields.Many2one('res.country', 'Улс')
    date = fields.Date('Огноо')
    year = fields.Char('Он')
    organization_name = fields.Char('Сургагч байгууллага')
    train_time = fields.Char('Үргэлжилсэн хугацаа')
    sertificate = fields.Char('Сертификат')
    attach = fields.Binary('Сертификат')
    job = fields.Char('Чиглэл')


class HrSchoolName(models.Model):
    _name = 'hr.school.name'
    _description = 'school name'

    name = fields.Char(string='Сургуулийн нэр')


class JobName(models.Model):
    _name = 'job.name'
    _description = 'job name'

    name = fields.Char(string='Мэргэжил')
    code = fields.Char(string='Код')
    index_name = fields.Char(string='Мэргэжлийн индексийн нэр')
    index = fields.Char(string='БСШУСЯ-ны баталсан одоо мөрдөж буй мэргэжлийн индекс')

class HrSchool(models.Model):
    _name = 'hr.school'
    _description = 'school'

    employee_id = fields.Many2one('hr.employee', 'Employee')
    name = fields.Many2one('hr.school.name', string='Сургуулийн нэр')
    country_id = fields.Many2one('res.country', 'Улс')
    start_date = fields.Date('Элссэн огноо')
    end_date = fields.Date('Төгссөн огноо')
    date_from = fields.Char('Элссэн он')
    date_to = fields.Char('Төгссөн он')
    job = fields.Many2one('job.name', string='Эзэмшсэн мэргэжил')
    honest = fields.Float('Голч оноо')
    education_level = fields.Selection([('basilar', 'Суурь боловсрол'), ('t_senior', 'Тусгай дунд'), ('senior', 'Бүрэн дунд боловсрол'), ('high', 'Дээд боловсрол'),
                                        ('bachelor', 'Бакалавр'), ('master', 'Магистр'), ('doctor', 'Доктор'), ('professor', 'Профессор')], 'Эрдмийн зэрэг')
    state = fields.Selection(
        [('end', 'Төгссөн'), ('study', 'Суралцаж байгаа'), ('other', 'Бусад')], 'Төлөв')
    attach = fields.Binary('Сертификат')
    is_foreign = fields.Boolean('Гадаад сургууль эсэх')


class HrDegreeName(models.Model):
    _name = 'hr.degree.name'
    _description = 'degree name'

    name = fields.Char('Чиглэл')


class HrDegree(models.Model):
    _name = 'hr.degree'
    _description = 'degree'

    employee_id = fields.Many2one('hr.employee', 'Employee')
    direction = fields.Many2one('hr.degree.name', 'Чиглэл')
    name = fields.Char('Нэр')
    date = fields.Char('Огноо')


class HrEduLanguage(models.Model):
    _name = 'hr.info.language'
    _description = 'Info Language'

    name = fields.Char(string='Name')


class HrLanguage(models.Model):
    _name = 'hr.language'
    _description = 'Employee language'

    language_name = fields.Many2one('hr.info.language', string='Хэл')
    listening_skill = fields.Selection([('5', u'Маш сайн'), ('4', u'Сайн'), (
        '3', u'Дунд'), ('2', u'Тааруу'), ('1', u'Хангалтгүй')], 'Сонсох чадвар')
    speaking_skill = fields.Selection([('5', u'Маш сайн'), ('4', u'Сайн'), (
        '3', u'Дунд'), ('2', u'Тааруу'), ('1', u'Хангалтгүй')], 'Ярих чадвар')
    reading_skill = fields.Selection([('5', u'Маш сайн'), ('4', u'Сайн'), (
        '3', u'Дунд'), ('2', u'Тааруу'), ('1', u'Хангалтгүй')], 'Унших чадвар')
    writing_skill = fields.Selection([('5', u'Маш сайн'), ('4', u'Сайн'), (
        '3', u'Дунд'), ('2', u'Тааруу'), ('1', u'Хангалтгүй')], 'Бичих чадвар')
    employee_id = fields.Many2one('hr.employee', string='Employee')


class SoftwareTechnic(models.Model):
    _name = 'software.technic'
    _description = 'Software Technic'

    name = fields.Char(string='Name')


class HrSoftwareSkill(models.Model):
    _name = 'hr.software.skill'
    _description = 'Employee software skill'

    name = fields.Many2one('software.technic', string='Ур чадвар')
    name_description = fields.Char(string='Тайлбар', size=128)
    software_level = fields.Selection([('middle', u'Анхан шатны'), (
        'good', u'Хэрэглээний'), ('excellent', u'Бүрэн эзэмшсэн')], string='Түвшин')
    employee_id = fields.Many2one('hr.employee', string='Employee')


class OtherTechnic(models.Model):
    _name = 'other.technic'
    _description = 'other Technic'

    name = fields.Char(string='Name')


class HrOtherSkill(models.Model):
    _name = 'hr.other.skill'
    _description = 'Employee other skill'

    name = fields.Many2one('other.technic', string='Ур чадвар')
    name_description = fields.Char(string='Тайлбар', size=128)
    level = fields.Selection(
        [('middle', u'Анхан'), ('good', u'Дунд'), ('excellent', u'Ахисан')], string='Түвшин')
    employee_id = fields.Many2one('hr.employee', string='Employee')
