from venv import logger
from odoo.exceptions import UserError
import requests
import json
import time
import base64
import hmac
import hashlib
# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo import _
    
class HrOpenJob(models.Model):
    _inherit = "hr.open.job"

    ad_code = fields.Char(string='Adcode')
    
# get/anket
    def action_fetch_anket_from_zangia(self):
        job_integration = self.env['job.integration'].create({})
        logger.info(f"Raw response from Zangia: {job_integration}")
        if self.ad_code:
            anket_code = self.ad_code  # Replace with your actual field name
        try:
            anket_data = job_integration.get_anket(anket_code)
            logger.info(f"Sending anket_data to {anket_data}")
            self.process_anket_details(anket_data)
        except Exception as e:
            raise UserError(f"Failed to fetch anket from Zangia: {str(e)}")

    def process_anket_details(self, anket_data):
        applicant = self.env['hr.applicant']
        source_id = ''
        source= self.env['utm.source'].search([('name','ilike','Зангиа')],limit=1)
        if source:
            source_id = source.id
        if isinstance(anket_data, dict):
        # Iterate over each record in the dictionary
            for key, anket in anket_data.items():
                educations = []
                experiences =[]
                skills_group5 = []
                skills_group3 = []
                skills_group2 = []
                for education in anket['educations']:
                    name = ''
                    pro = ''
                    degree_mapping = { '1': 'bachelor','2': 'master', '3': 'doctor','4': 't_senior','5': 'senior','6': 'basilar','7': 'basilar','8': 'high'}
                    school_name= self.env['hr.school.name'].search([('name','ilike',education.get("school"))],limit=1)
                    # country_name= self.env['res.country'].search([('name','ilike',education.get("school"))],limit=1)
                    pro_name= self.env['job.name'].search([('name','ilike',education.get("pro"))],limit=1)
                    if school_name:
                        name =school_name.id
                    else:
                        new_school = self.env['hr.school.name'].create({
                            'name':education.get("school")
                        })
                        name = new_school.id
                    if pro_name:
                        pro =pro_name.id
                    else:
                        new_pro = self.env['job.name'].create({
                            'name':education.get("pro")
                        })
                        pro = new_pro.id
                    educations.append((0,0,{
                        'name':name,
                        'honest':education.get("rate"),
                        'job':pro,
                        'education_level':degree_mapping.get(education.get("degree"), ''),
                        # 'start_date':education.get("start"),
                        # 'end_date':education.get("end"),
                        'date_from':education.get("start"),
                        'date_to':education.get("end"),
                    }))
                    
                for experience in anket['experiences']:
                    endon= None
                    if experience.get("endon") == '0000-00-00':
                        endon = None
                    else:
                        endon = experience.get("endon")
                    experiences.append((0,0,{
                        'organization':experience.get("cname"),
                        'job_title':experience.get("pos"),
                        'entered_date':experience.get("starton"),
                        'resigned_date':endon
                    }))
                for skill_group5 in anket['skills']:
                    if skill_group5.get("group") in ('4','5','1'):
                        skills_group5.append((0,0,{
                            'spent_time':skill_group5.get("skill_rate"),
                            'name':skill_group5.get("skill_title"),
                        }))
                for skill_group3 in anket['skills']:
                    software = None
                    if skill_group3.get("group") == '3':
                        software_obj = self.env['software.technic'].search([('name','ilike',skill_group3.get("skill_title"))],limit=1)
                        if software_obj:
                            software = software_obj.id
                        else:
                            new_software = self.env['software.technic'].create({'name':skill_group3.get("skill_title")})
                            software = new_software.id
                        skills_group3.append((0,0,{
                            'name':software,
                            'name_description':skill_group3.get("skill_rate"),
                        }))
                for skill_group2 in anket['skills']:
                    if skill_group2.get("group") == '2':
                        language = None
                        language= self.env['hr.info.language'].search([('name','ilike',skill_group2.get("skill_title"))],limit=1)
                        if language:
                            language = language.id
                        else:
                            new_language = self.env['hr.info.language'].create({
                            'name':education.get("skill_title")})
                            language = new_language.id
                            
                        skills_group2.append((0,0,{
                            'language_name':language,
                            # 'name':skill_group5.get("skill_title"),
                        }))
                logger.info(f"Anket Data: {anket}")
                last_name = anket.get("lname")
                first_name = anket.get("fname")
                if anket.get("marstat") =='1':
                    is_married = True
                else:
                    is_married = False
                if last_name and first_name:
                    full_name = f"{first_name} {last_name}"
                    app_pool = applicant.create({
                        'name': full_name,
                        'family_name': anket.get("fmname"),
                        'last_name': last_name,
                        'partner_name': first_name,
                        'register': anket.get("reg"),
                        # 'image_1920': anket.get("pic"),
                        'introduce': anket.get("bio"),
                        'is_married': is_married,
                        'source_id': source_id,
                        'partner_phone': anket.get("phone1"),
                        'partner_mobile': anket.get("phone2"),
                        'email_from': anket.get("email"),
                        'driver_license': anket.get("drlicense"),
                        'availability': anket.get("availdt"),
                        'applicant_emp_id': self.id,
                        'school_line_ids': educations,
                        'employment_ids': experiences,
                        'degree_ids': skills_group5,
                        'software_skill_line_ids': skills_group3,
                        'language_line_ids': skills_group2,
                        'job_id': self.job_id.id,
                        'is_ita':True
                    })
                    if anket.get("pic"):
                        url = anket.get("pic")
                        url = url.replace('/u/','/r/')
                        result = requests.get(url)
                        # image = False
                        if result.status_code == 200:
                            app_pool.image_1920 = base64.b64encode(result.content).decode('utf-8')
                else:
                    logger.warning(f"Missing required fields in anket data: {anket}")
        else:
             raise UserError("anket_data is not in the expected format. It should be a dictionary with records.")
# send/job
    def action_send_job_to_zangia(self):
        data = {
            "job": {
                "title": self.job_name,
                "desc":self.job_id.role,
                "requires":self.job_id.needs,
                "more": '',
                "location": self.location,
                "awh": self.work_type,
                "prolvl": self.level,
                "branch": 26,
                "profession": 1401,
                "salary": self.salary_type,
                "slchangeable":'',
                "addr": 1,
                "contact":1,
            }
        }
        job_integration = self.env['job.integration'].create({})
        try:
            if not self.ad_code:
                response=job_integration.post_job(data)
                anket_code = response.get("ad_code")  # Extract ad_code from the response
                logger.info(f"Job sent successfully. Received ad_code: {anket_code}")
                self.ad_code = anket_code
                return {
                    'type': 'ir.actions.client',
                    'tag': 'reload',
                }
            else:
                raise UserError("Зар тавигдсан байна.")
        except Exception as e:
            raise UserError(f"Failed to send job to Zangia: {str(e)}")
        
class JobIntegration(models.Model):
    _name = 'job.integration'
    _description = 'Job Integration'
        
    api_code = fields.Char("API Code", required=True,default='2954238185')
    secret = fields.Char("Secret", required=True,default='2n7wsbyp1y8mvlqxfw61fo8rw6wa1skufs53vasu38zv0wculgd4o13bnouq8ue3wb5wc1wyx3sady0t')
    # api_code = '2954238185'
    # secret = '2n7wsbyp1y8mvlqxfw61fo8rw6wa1skufs53vasu38zv0wculgd4o13bnouq8ue3wb5wc1wyx3sady0t' 
    stamp = fields.Char('stamp',default=str(int(time.time())))
    useragent = fields.Char('useragent',default='BiznetworkAuth [https://www.biznetwork.mn]')
    
    def generate_token(self):
        key = f'{self.useragent}|{self.stamp}'
        message = f'{self.api_code}:{self.secret}'.encode()
        hmac_digest = hmac.new(key.encode(), message, hashlib.sha1).digest()
        token = base64.b64encode(hmac_digest).decode()
        return token
    
    def post_job(self, job_data):
        url = "https://api.zangia.mn/send/job"
        headers = {
            "Content-Type": "application/json",
            'User-Agent': self.useragent,
        }
        token = self.generate_token()

        post_data = {
            "api_code": self.api_code,
            "secret": self.secret,
            "token": token,
            "stamp": self.stamp,
            **job_data,
        }
        session = requests.Session()
        response = session.post(url, headers=headers, json=post_data)
        logger.info(f"Sending request to {url}")
        logger.info(f"Request headers: {headers}")
        logger.info(f"Request data: {json.dumps(post_data)}")
        logger.info(f"Response status code: {response.status_code}")
        logger.info(f"Response content: {response.text}")
        
        if response.status_code != 200:
            raise UserError(f"Failed to send job to Zangia: {response.status_code} - {response.text}")

        return response.json()
    
    def get_anket(self, anket_code):
        url = f"https://api.zangia.mn/get/ankets?adcode={anket_code}"
        headers = {
            "Content-Type": "application/json",
            "User-Agent": self.useragent,
        }
        token = self.generate_token()
        params = {
            "api_code": self.api_code,
            "token": token,
            "stamp": self.stamp,
        }
        try:
            session = requests.Session()
            response = session.get(url, headers=headers, params=params)
            logger.info(f"Sending request to {url}")
            logger.info(f"Request headers: {headers}")
            logger.info(f"Request data: {json.dumps(params)}")
            logger.info(f"Response status code: {response.status_code}")
            logger.info(f"Response content: {response.text}")
            if response.status_code != 200:
                raise Exception(f"HTTP Error: {response.status_code} - {response.text}")
            
            return response.json()

        except requests.RequestException as e:
            raise UserError(f"Failed to fetch anket from Zangia: {str(e)}")
        

class BizApiException(Exception):
    pass

# class BizApi:
#     API_HOST = 'https://api.zangia.mn'
#     API_PORT = ''
#     URLSEP = '/'
#     USERAGENT = 'BiznetworkAuth [https://www.biznetwork.mn]'

#     def __init__(self):
#         self.token = ''
#         self.version = '1.0'
#         self.code = ''
#         self.secret = ''
#         self.callback = ''
#         self.params = {}
#         self.path = ''
#         self.method = 'POST'
#         self.headers = {}
#         self.gzip_encoding = False
#         self.response_format = 'json'
#         self.response_text = ''

#     def init(self, code, secret):
#         if secret is None:
#             raise BizApiException('API secret is empty')
#         if code is None:
#             raise BizApiException('API code is empty')
#         return self.code(code).secret(secret)

#     def new_anket(self, code=''):
#         return self.api('/get/ankets', {'adcode': code})

#     def post_job(self, data):
#         if not data or not isinstance(data, dict):
#             raise BizApiException('Job data is wrong')
#         return self.api('/send/job', {'job': data})

#     def update_job(self, data, code):
#         if not code:
#             raise BizApiException('Job code is missing')
#         if not data or not isinstance(data, dict):
#             self.post_job(data)
#         data['edit'] = code
#         return self.post_job(data)

#     def options(self, code):
#         return self.api('/get/options', {'optioncode': code})

#     def profession(self, branch, type=1):
#         if type not in [1, 2]:
#             raise BizApiException(f'Wrong parameter [{type}]. 1-CV мэргэжлүүд, 2-Ажлын байрны мэргэжил')
#         return self.api('/get/options', {'optioncode': f'pfs{type}', 'branch': branch})

#     def address_phone(self, only=None, via='html'):
#         if only in ['html', 'json']:
#             via = only
#             only = None
#         return self.api('/get/addrphone', {'only': only, 'via': via})

#     def resp(self):
#         return self.response_text

#     def response(self):
#         return self.parse_json() if self.response_format == 'json' else self.parse_xml()

#     def format(self, s=None):
#         if s is None:
#             return self.response_format
#         s = s.lower()
#         if s not in ['json', 'xml']:
#             s = 'json'
#         self.params['format'] = s
#         self.response_format = s
#         return self

#     def code(self, s_code=None):
#         if s_code is None:
#             return self.code
#         self.code = s_code
#         return self.set_param('api_code', s_code)

#     def secret(self, s_secret=None):
#         if s_secret is None:
#             return self.secret
#         self.secret = s_secret
#         return self

#     def callback(self, s_callback=None):
#         if s_callback is None:
#             return self.callback
#         self.callback = s_callback
#         return self.set_param('callback', s_callback)

#     def gzip(self, b=None):
#         if b is None:
#             return self.gzip_encoding
#         self.gzip_encoding = b
#         return self

#     def set_param(self, key, value):
#         self.params[key] = value
#         return self

#     def set_params(self, params):
#         for key, value in params.items():
#             self.set_param(key, value)
#         return self

#     def get_param(self, key):
#         return self.params.get(key)

#     def get_params(self):
#         return self.params

#     def remove_param(self, key):
#         if key in self.params:
#             del self.params[key]
#         return self

#     def remove_params(self, keys):
#         if isinstance(keys, str):
#             keys = keys.split(',')
#         for key in keys:
#             self.remove_param(key)
#         return self

#     def parse_headers(self, string):
#         headers = {}
#         for line in string.split('\r\n'):
#             if ':' in line:
#                 key, value = line.split(':', 1)
#                 key = key.replace('-', '_').lower()
#                 headers[key] = value.strip()
#         return headers

#     def set_header(self, key, value):
#         self.headers[key] = value
#         return self

#     def remove_header(self, key):
#         if key in self.headers:
#             del self.headers[key]
#         return self

#     def set_headers(self, headers):
#         for key, value in headers.items():
#             self.set_header(key, value)
#         return self

#     def get_header(self, key):
#         return self.headers.get(key)

#     def get_headers(self):
#         return self.headers

#     def headers(self):
#         return [f'{key}: {value}' for key, value in self.headers.items()]

#     def extend_params(self, params):
#         for key, value in params.items():
#             if key not in self.params:
#                 self.params[key] = value
#         return self

    

#     def build_uri_params(self, params=None):
#         if params is None:
#             params = self.params
#         sorted_params = {k: v for k, v in sorted(params.items())}
#         return '&'.join(f'{self.encode_uri(k)}={self.encode_uri(v)}' for k, v in sorted_params.items())

#     def from_uri_params(self, query):
#         if not query:
#             return {}
#         result = {}
#         for param in query.split('&'):
#             key, val = param.split('=', 1)
#             key, val = self.decode_uri(key), self.decode_uri(val)
#             if key in result:
#                 if isinstance(result[key], list):
#                     result[key].append(val)
#                 else:
#                     result[key] = [result[key], val]
#             else:
#                 result[key] = val
#         return result

#     def method(self, s=None):
#         if s is None:
#             return self.method
#         self.method = s
#         return self

#     def post(self):
#         self.method = 'POST'
#         return self.request()

#     def get(self):
#         self.method = 'GET'
#         return self.request()

#     def encode_uri(self, mixed):
#         if isinstance(mixed, dict):
#             return {self.encode_uri(k): self.encode_uri(v) for k, v in mixed.items()}
#         return requests.utils.quote(str(mixed), safe='')

#     def decode_uri(self, mixed):
#         if isinstance(mixed, dict):
#             return {self.decode_uri(k): self.decode_uri(v) for k, v in mixed.items()}
#         return requests.utils.unquote(mixed)

#     def encode_data(self, data):
#         return json.dumps(data)

#     def decode_data(self, data, as_array=False):
#         return json.loads(data) if as_array else json.loads(data)

#     def make_uri(self):
#         return f"{self.API_HOST}{f':{self.API_PORT}' if self.API_PORT and self.API_PORT != 80 else ''}{self.URLSEP}{self.version}{self.URLSEP}{self.path}{'?' + self.build_uri_params() if self.method == 'GET' else ''}"

#     def request(self):
#         if not self.code:
#             raise BizApiException('Missing API code')
#         if not self.secret:
#             raise BizApiException('Missing API secret')
#         self.generate_token(f"{self.USERAGENT}|{int(time.time())}").set_param('stamp', int(time.time()))

#         headers = {
#             'Accept': 'application/json',
#             'User-Agent': self.USERAGENT,
#             **self.headers
#         }
#         if self.gzip_encoding:
#             headers['Accept-Encoding'] = 'gzip'

#         if self.method == 'POST':
#             response = requests.post(self.make_uri(), headers=headers, data=self.build_uri_params())
#         else:
#             response = requests.get(self.make_uri(), headers=headers)

#         if response.status_code != 200:
#             raise BizApiException(f"HTTP Error: {response.status_code}")

#         self.response_text = response.text
#         self.set_headers(self.parse_headers(response.headers))
#         return self.response()

#     def parse_json(self):
#         return self.decode_data(self.response_text, True)

#     def _to_arr(self, data, stack, value):
#         if stack:
#             key = stack.pop(0)
#             if key not in data:
#                 data[key] = {}
#             self._to_arr(data[key], stack, value)
#         else:
#             data = value

#     def parse_xml(self):
#         tree = ET.ElementTree(ET.fromstring(self.response_text))
#         root = tree.getroot()
#         return {elem.tag: elem.text for elem in root}

# # Example usage
# api = BizApi()
# api.init('your_code', 'your_secret')
# try:
#     response = api.new_anket('some_code')
#     print(response)
# except BizApiException as e:
#     print(f"Error: {str(e)}")

