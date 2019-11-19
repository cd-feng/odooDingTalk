import base64 #line:6:import base64
import hashlib #line:7:import hashlib
import hmac #line:8:import hmac
import json #line:9:import json
import logging #line:10:import logging
import time #line:11:import time
from datetime import datetime ,timedelta #line:12:from datetime import datetime, timedelta
import requests #line:13:import requests
from odoo import fields ,_ #line:14:from odoo import fields, _
from urllib .parse import quote #line:15:from urllib.parse import quote
from odoo .exceptions import ValidationError #line:16:from odoo.exceptions import ValidationError
try :#line:18:try:
    from dingtalk .client import AppKeyClient #line:19:from dingtalk.client import AppKeyClient
    from dingtalk .storage .memorystorage import MemoryStorage #line:20:from dingtalk.storage.memorystorage import MemoryStorage
    from odoo .http import request #line:21:from odoo.http import request
except ImportError as e :#line:22:except ImportError as e:
    logging .info (_ ("-------Import Error-----------------------"))#line:23:logging.info(_("-------Import Error-----------------------"))
    logging .info (_ ("引入钉钉三方SDK出错！请检查是否正确安装SDK！！！"))#line:24:logging.info(_("引入钉钉三方SDK出错！请检查是否正确安装SDK！！！"))
    logging .info (_ ("-------Import Error-----------------------"))#line:25:logging.info(_("-------Import Error-----------------------"))
mem_storage =MemoryStorage ()#line:27:mem_storage = MemoryStorage()
_O0OOOOO0000O0OO0O =logging .getLogger (__name__ )#line:28:_logger = logging.getLogger(__name__)
def get_client ():#line:31:def get_client():
    ""#line:35:"""
    OO00OO00OOOO0000O =request .env ['ir.config_parameter'].sudo ().get_param ('dingtalk_base.dt_corp_id')#line:36:dt_corp_id = request.env['ir.config_parameter'].sudo().get_param('dingtalk_base.dt_corp_id')
    OO00OOO0O0O0O0OO0 ,O00OOOO00O00O0000 =_OO00OOO000000O0OO ()#line:37:app_key, app_secret = _get_key_and_secrect()
    return AppKeyClient (OO00OO00OOOO0000O ,OO00OOO0O0O0O0OO0 ,O00OOOO00O00O0000 ,storage =mem_storage )#line:38:return AppKeyClient(dt_corp_id, app_key, app_secret, storage=mem_storage)
def _OO00OOO000000O0OO ():#line:41:def _get_key_and_secrect():
    ""#line:45:"""
    OOOOOO000000O0OO0 =request .env ['ir.config_parameter'].sudo ().get_param ('dingtalk_base.dt_app_key')#line:46:app_key = request.env['ir.config_parameter'].sudo().get_param('dingtalk_base.dt_app_key')
    OO0OO0O0O00O00O0O =request .env ['ir.config_parameter'].sudo ().get_param ('dingtalk_base.dt_app_secret')#line:47:app_secret = request.env['ir.config_parameter'].sudo().get_param('dingtalk_base.dt_app_secret')
    if OOOOOO000000O0OO0 and OO0OO0O0O00O00O0O :#line:48:if app_key and app_secret:
        return OOOOOO000000O0OO0 .replace (' ',''),OO0OO0O0O00O00O0O .replace (' ','')#line:49:return app_key.replace(' ', ''), app_secret.replace(' ', '')
    return '0000','0000'#line:50:return '0000', '0000'
def get_delete_is_synchronous ():#line:53:def get_delete_is_synchronous():
    ""#line:57:"""
    return request .env ['ir.config_parameter'].sudo ().get_param ('dingtalk_base.dt_delete_is_sy')#line:58:return request.env['ir.config_parameter'].sudo().get_param('dingtalk_base.dt_delete_is_sy')
def get_login_id ():#line:61:def get_login_id():
    ""#line:65:"""
    O0000OO0O0OOO00OO =request .env ['ir.config_parameter'].sudo ().get_param ('dingtalk_base.dt_login_id')#line:66:login_id = request.env['ir.config_parameter'].sudo().get_param('dingtalk_base.dt_login_id')
    if O0000OO0O0OOO00OO :#line:67:if login_id:
        return O0000OO0O0OOO00OO .replace (' ','')#line:68:return login_id.replace(' ', '')
    return '0000'#line:69:return '0000'
def get_login_id_and_key ():#line:72:def get_login_id_and_key():
    ""#line:75:"""
    OOOOOO0OO00O0O0OO =request .env ['ir.config_parameter'].sudo ().get_param ('dingtalk_base.dt_login_id')#line:76:login_id = request.env['ir.config_parameter'].sudo().get_param('dingtalk_base.dt_login_id')
    OOOOO0OOO0O00O0O0 =request .env ['ir.config_parameter'].sudo ().get_param ('dingtalk_base.dt_login_secret')#line:77:dt_login_secret = request.env['ir.config_parameter'].sudo().get_param('dingtalk_base.dt_login_secret')
    if OOOOOO0OO00O0O0OO and OOOOO0OOO0O00O0O0 :#line:78:if login_id and dt_login_secret:
        return OOOOOO0OO00O0O0OO .replace (' ',''),OOOOO0OOO0O00O0O0 .replace (' ','')#line:79:return login_id.replace(' ', ''), dt_login_secret.replace(' ', '')
    return '0000','0000'#line:80:return '0000', '0000'
def get_dt_corp_id ():#line:83:def get_dt_corp_id():
    ""#line:86:"""
    OOO000OOO0O00O00O =request .env ['ir.config_parameter'].sudo ().get_param ('dingtalk_base.dt_corp_id')#line:87:dt_corp_id = request.env['ir.config_parameter'].sudo().get_param('dingtalk_base.dt_corp_id')
    if OOO000OOO0O00O00O :#line:88:if dt_corp_id:
        return OOO000OOO0O00O00O .replace (' ','')#line:89:return dt_corp_id.replace(' ', '')
    return '0000'#line:90:return '0000'
def get_serial_number ():#line:93:def get_serial_number():
    ""#line:96:"""
    O0OO00O00O00OO0O0 =request .env ['ir.config_parameter'].sudo ().get_param ('dingtalk_base.dt_serial_number')#line:97:dt_serial_number = request.env['ir.config_parameter'].sudo().get_param('dingtalk_base.dt_serial_number')
    if O0OO00O00O00OO0O0 :#line:98:if dt_serial_number:
        return O0OO00O00O00OO0O0 .replace (' ','')#line:99:return dt_serial_number.replace(' ', '')
    return False #line:100:return False
def timestamp_to_local_date (O0O0OO00O0O0O0O0O ):#line:103:def timestamp_to_local_date(time_num):
    ""#line:108:"""
    O00O00O00O00OOOO0 =float (O0O0OO00O0O0O0O0O /1000 )#line:109:to_second_timestamp = float(time_num / 1000)  # 毫秒转秒
    O00OO0O0O0OO00OOO =time .gmtime (O00O00O00O00OOOO0 )#line:110:to_utc_datetime = time.gmtime(to_second_timestamp)  # 将时间戳转换为UTC时区（0时区）的时间元组struct_time
    O00000OO00OO00000 =time .strftime ("%Y-%m-%d %H:%M:%S",O00OO0O0O0OO00OOO )#line:111:to_str_datetime = time.strftime("%Y-%m-%d %H:%M:%S", to_utc_datetime)  # 将时间元组转成指定格式日期字符串
    O00O00O0OOOO00OO0 =fields .Datetime .from_string (O00000OO00OO00000 )#line:112:to_datetime = fields.Datetime.from_string(to_str_datetime)  # 将字符串转成datetime对象
    OOOOO0OO0O000OOOO =fields .Datetime .context_timestamp (request ,O00O00O0OOOO00OO0 )#line:113:to_local_datetime = fields.Datetime.context_timestamp(request, to_datetime)  # 将原生的datetime值(无时区)转换为具体时区的datetime
    O00000OO00OO00000 =fields .Datetime .to_string (OOOOO0OO0O000OOOO )#line:114:to_str_datetime = fields.Datetime.to_string(to_local_datetime)  # datetime 转成 字符串
    return O00000OO00OO00000 #line:115:return to_str_datetime
def datetime_to_stamp (O00000OOO0000O0OO ):#line:118:def datetime_to_stamp(time_num):
    ""#line:123:"""
    O000O0O0OO000OOOO =fields .Datetime .to_string (O00000OOO0000O0OO )#line:124:date_str = fields.Datetime.to_string(time_num)
    O00000000OO000OO0 =time .mktime (time .strptime (O000O0O0OO000OOOO ,"%Y-%m-%d %H:%M:%S"))#line:125:date_stamp = time.mktime(time.strptime(date_str, "%Y-%m-%d %H:%M:%S"))
    O00000000OO000OO0 =O00000000OO000OO0 *1000 #line:126:date_stamp = date_stamp * 1000
    return int (O00000000OO000OO0 )#line:127:return int(date_stamp)
def get_user_info_by_code (OO00O0O000O0OO000 ):#line:130:def get_user_info_by_code(code):
    ""#line:135:"""
    O00O0OO0O0O00OO00 ,OO00OOOO0O00000OO =get_login_id_and_key ()#line:136:login_id, login_secret = get_login_id_and_key()
    O00O0OO00O00OOO00 =lambda :int (round (time .time ()*1000 ))#line:137:milli_time = lambda: int(round(time.time() * 1000))
    O0O000O0000OOO0OO =str (O00O0OO00O00OOO00 ())#line:138:timestamp = str(milli_time())
    O00000O0000OOO0O0 =hmac .new (OO00OOOO0O00000OO .encode ('utf-8'),O0O000O0000OOO0OO .encode ('utf-8'),hashlib .sha256 ).digest ()#line:139:signature = hmac.new(login_secret.encode('utf-8'), timestamp.encode('utf-8'), hashlib.sha256).digest()
    O00000O0000OOO0O0 =quote (base64 .b64encode (O00000O0000OOO0O0 ),'utf-8')#line:140:signature = quote(base64.b64encode(signature), 'utf-8')
    O00O0OOOOO00O0OOO ="sns/getuserinfo_bycode?signature={}&timestamp={}&accessKey={}".format (O00000O0000OOO0O0 ,O0O000O0000OOO0OO ,O00O0OO0O0O00OO00 )#line:141:url = "sns/getuserinfo_bycode?signature={}&timestamp={}&accessKey={}".format(signature, timestamp, login_id)
    O0OO0OOOOOO00OOOO =get_client ().post (O00O0OOOOO00O0OOO ,{'tmp_auth_code':OO00O0O000O0OO000 ,'signature':O00000O0000OOO0O0 ,'timestamp':O0O000O0000OOO0OO ,'accessKey':O00O0OO0O0O00OO00 })#line:147:})
    return O0OO0OOOOOO00OOOO #line:148:return result
def list_cut (OO0O00O0OO0000OOO ,OO000O0OOO0O0O00O ):#line:151:def list_cut(mylist, limit):
    ""#line:157:"""
    OOO0OOO00O00O00O0 =len (OO0O00O0OO0000OOO )#line:158:length = len(mylist)
    OO0O0OOOOO0OO00OO =[OO0O00O0OO0000OOO [O0OO00OOO00OOOO0O :O0OO00OOO00OOOO0O +OO000O0OOO0O0O00O ]for O0OO00OOO00OOOO0O in range (0 ,OOO0OOO00O00O00O0 ,OO000O0OOO0O0O00O )]#line:159:cut_list = [mylist[i:i + limit] for i in range(0, length, limit)]
    return OO0O0OOOOO0OO00OO #line:160:return cut_list
def day_cut (OOO000O00OOOO0OOO ,OOO0O0000000OOO00 ,O000O000O00OOO0OO ):#line:163:def day_cut(begin_time, end_time, days):
    ""#line:170:"""
    O0O0O0O0O0O00O000 =[]#line:171:cut_day = []
    OOO000O00OOOO0OOO =datetime .strptime (str (OOO000O00OOOO0OOO ),"%Y-%m-%d")#line:172:begin_time = datetime.strptime(str(begin_time), "%Y-%m-%d")
    OOO0O0000000OOO00 =datetime .strptime (str (OOO0O0000000OOO00 ),"%Y-%m-%d")#line:173:end_time = datetime.strptime(str(end_time), "%Y-%m-%d")
    O0O0O0OOO0O000O0O =timedelta (days =O000O000O00OOO0OO )#line:174:delta = timedelta(days=days)
    O0OOO0000O0OOO000 =OOO000O00OOOO0OOO #line:175:t1 = begin_time
    while O0OOO0000O0OOO000 <=OOO0O0000000OOO00 :#line:176:while t1 <= end_time:
        if OOO0O0000000OOO00 <O0OOO0000O0OOO000 +O0O0O0OOO0O000O0O :#line:177:if end_time < t1 + delta:
            O000OO0000OOOOO0O =OOO0O0000000OOO00 #line:178:t2 = end_time
        else :#line:179:else:
            O000OO0000OOOOO0O =O0OOO0000O0OOO000 +O0O0O0OOO0O000O0O #line:180:t2 = t1 + delta
        O0O00OO000O00OO0O =O0OOO0000O0OOO000 .strftime ("%Y-%m-%d %H:%M:%S")#line:181:t1_str = t1.strftime("%Y-%m-%d %H:%M:%S")
        OOO0OOO0O000OO00O =O000OO0000OOOOO0O .strftime ("%Y-%m-%d %H:%M:%S")#line:182:t2_str = t2.strftime("%Y-%m-%d %H:%M:%S")
        O0O0O0O0O0O00O000 .append ([O0O00OO000O00OO0O ,OOO0OOO0O000OO00O ])#line:183:cut_day.append([t1_str, t2_str])
        O0OOO0000O0OOO000 =O000OO0000OOOOO0O +timedelta (seconds =1 )#line:184:t1 = t2 + timedelta(seconds=1)
    return O0O0O0O0O0O00O000 #line:185:return cut_day
def check_dingtalk_authorization (O0OO0OO00OO000OO0 ):#line:188:def check_dingtalk_authorization(model_name):
    ""#line:192:"""
    OO0OO000OO0OO00OO =get_serial_number ()#line:193:serial_number = get_serial_number()
    if not OO0OO000OO0OO00OO :#line:194:if not serial_number:
        return False #line:195:return False
    O0O0O0O0OO00OOOOO ="http://111.231.208.155:8099"#line:196:service_url = "http://111.231.208.155:8099"
    try :#line:197:try:
        OO000OOOOO0OO0O00 =requests .get (url =O0O0O0O0OO00OOOOO ,params ={'code':OO0OO000OO0OO00OO ,'domain':request .httprequest .host_url ,'model':O0OO0OO00OO000OO0 },timeout =5 )#line:198:result = requests.get(url=service_url, params={'code': serial_number, 'domain': request.httprequest.host_url, 'model': model_name}, timeout=5)
        OO000OOOOO0OO0O00 =json .loads (OO000OOOOO0OO0O00 .text )#line:199:result = json.loads(result.text)
        if OO000OOOOO0OO0O00 ['model_state']:#line:200:if result['model_state']:
            return {'state':True ,'msg':OO000OOOOO0OO0O00 ['msg']}#line:201:return {'state': True, 'msg': result['msg']}
        else :#line:202:else:
            return {'state':False ,'msg':OO000OOOOO0OO0O00 ['msg']}#line:203:return {'state': False, 'msg': result['msg']}
    except Exception as OO0OOOO000000OOOO :#line:204:except Exception as e:
        return {'state':False ,'msg':str (OO0OOOO000000OOOO )}#line:205:return {'state': False, 'msg': str(e)}
def check_dt_serial_number (O000OO00O000OOOO0 ):#line:208:def check_dt_serial_number(check_model):
    ""#line:213:"""
    if O000OO00O000OOOO0 =='check_model':#line:214:if check_model == 'check_model':
        OOO000OO0OOO0O000 =check_dingtalk_authorization ("check_model")#line:215:result = check_dingtalk_authorization("check_model")
        return OOO000OO0OOO0O000 ['msg']#line:216:return result['msg']
def setup_approval_state_fields (O000OO0000OOO0O0O ):#line:219:def setup_approval_state_fields(self):
    ""#line:224:"""
    def O0OOO00000O000000 (O0OO00O0O0O00O000 ,O0OOOO0000O0000O0 ):#line:225:def add(name, field):
        if O0OO00O0O0O00O000 not in O000OO0000OOO0O0O ._fields :#line:226:if name not in self._fields:
            O000OO0000OOO0O0O ._add_field (O0OO00O0O0O00O000 ,O0OOOO0000O0000O0 )#line:227:self._add_field(name, field)
    O000OO0000OOO0O0O ._cr .execute ("SELECT COUNT(*) FROM pg_class WHERE relname = 'dingtalk_approval_control'")#line:228:self._cr.execute("SELECT COUNT(*) FROM pg_class WHERE relname = 'dingtalk_approval_control'")
    OO0O0O0OO00O0O00O =O000OO0000OOO0O0O ._cr .fetchall ()#line:229:table = self._cr.fetchall()
    if OO0O0O0OO00O0O00O [0 ][0 ]>0 :#line:230:if table[0][0] > 0:
        O000OO0000OOO0O0O ._cr .execute ("""SELECT im.model 
                FROM dingtalk_approval_control dac 
                JOIN ir_model im 
                     ON dac.oa_model_id = im.id 
                WHERE im.model = '%s'
                """%O000OO0000OOO0O0O ._name )#line:237:""" % self._name)
        O0O00O00000OOO0O0 =O000OO0000OOO0O0O ._cr .fetchall ()#line:238:res = self._cr.fetchall()
        if len (O0O00O00000OOO0O0 )!=0 :#line:239:if len(res) != 0:
            O0OOO00000O000000 ('dd_doc_state',fields .Char (string =u'审批描述'))#line:240:add('dd_doc_state', fields.Char(string=u'审批描述'))
            O0OOO00000O000000 ('dd_approval_state',fields .Selection (string =u'审批状态',selection =[('draft','草稿'),('approval','审批中'),('stop','审批结束')],default ='draft'))#line:241:add('dd_approval_state', fields.Selection(string=u'审批状态', selection=[('draft', '草稿'), ('approval', '审批中'), ('stop', '审批结束')], default='draft'))
            O0OOO00000O000000 ('dd_approval_result',fields .Selection (string =u'审批结果',selection =[('load','等待'),('agree','同意'),('refuse','拒绝'),('redirect','转交')],default ='load'))#line:243:default='load'))
            O0OOO00000O000000 ('dd_process_instance',fields .Char (string ='钉钉审批实例id'))#line:244:add('dd_process_instance', fields.Char(string='钉钉审批实例id'))
    return True #line:245:return True
def dingtalk_approval_write (O0O000OOOO0O00O0O ,O0000O000O000OOO0 ):#line:248:def dingtalk_approval_write(self, vals):
    ""#line:249:"""不允许单据修改"""
    O000O0OO0OO00O0O0 =O0O000OOOO0O00O0O .env .get ('dingtalk.approval.control')#line:250:res_state_obj = self.env.get('dingtalk.approval.control')
    if O000O0OO0OO00O0O0 is None :#line:251:if res_state_obj is None:
        return #line:252:return
    if len (O0000O000O000OOO0 .keys ())==1 and list (O0000O000O000OOO0 .keys ())[0 ]=='message_follower_ids':#line:254:if len(vals.keys()) == 1 and list(vals.keys())[0] == 'message_follower_ids':
        return #line:255:return
    for OOOOO0OO0O0O00O0O in O0O000OOOO0O00O0O :#line:256:for res in self:
        O0OO00OO0O000OO0O =O0O000OOOO0O00O0O .env ['ir.model'].sudo ().search ([('model','=',OOOOO0OO0O0O00O0O ._name )]).id #line:257:model_id = self.env['ir.model'].sudo().search([('model', '=', res._name)]).id
        O0O0O00000O0O00OO =O000O0OO0OO00O0O0 .sudo ().search ([('oa_model_id','=',O0OO00OO0O000OO0O )])#line:258:flows = res_state_obj.sudo().search([('oa_model_id', '=', model_id)])
        if not O0O0O00000O0O00OO :#line:259:if not flows:
            continue #line:260:continue
        if OOOOO0OO0O0O00O0O .dd_approval_state =='approval':#line:261:if res.dd_approval_state == 'approval':
            raise ValidationError (u'注意：单据审批中，不允许进行修改。 *_*!!')#line:263:raise ValidationError(u'注意：单据审批中，不允许进行修改。 *_*!!')
        elif OOOOO0OO0O0O00O0O .dd_approval_state =='stop':#line:264:elif res.dd_approval_state == 'stop':
            if O0O0O00000O0O00OO [0 ].ftype =='oa':#line:266:if flows[0].ftype == 'oa':
                raise ValidationError (u'注意：单据已审批完成，不允许进行修改。 *_*!!')#line:267:raise ValidationError(u'注意：单据已审批完成，不允许进行修改。 *_*!!')
    return True #line:268:return True
def dingtalk_approval_unlink (OOO000OOO00OO0000 ):#line:271:def dingtalk_approval_unlink(self):
    ""#line:272:"""非草稿单据不允许删除"""
    O00O000000OOO00O0 =OOO000OOO00OO0000 .env .get ('dingtalk.approval.control')#line:273:res_state_obj = self.env.get('dingtalk.approval.control')
    if O00O000000OOO00O0 is None :#line:274:if res_state_obj is None:
        return #line:275:return
    for OOO0000000O000000 in OOO000OOO00OO0000 :#line:276:for res in self:
        O00OOOO0OOO000OO0 =OOO000OOO00OO0000 .env ['ir.model'].sudo ().search ([('model','=',OOO0000000O000000 ._name )]).id #line:277:model_id = self.env['ir.model'].sudo().search([('model', '=', res._name)]).id
        O0OO00OOO0O0OOO0O =O00O000000OOO00O0 .sudo ().search ([('oa_model_id','=',O00OOOO0OOO000OO0 )])#line:278:flows = res_state_obj.sudo().search([('oa_model_id', '=', model_id)])
        if not O0OO00OOO0O0OOO0O :#line:279:if not flows:
            continue #line:280:continue
        if OOO0000000O000000 .dd_approval_state !='draft':#line:281:if res.dd_approval_state != 'draft':
            raise ValidationError (u'注意：非草稿单据不允许删除。 *_*!!')#line:282:raise ValidationError(u'注意：非草稿单据不允许删除。 *_*!!')
    return True #line:283:return True
