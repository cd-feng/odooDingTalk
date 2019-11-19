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
_O0OOO000OOO000000 =logging .getLogger (__name__ )#line:28:_logger = logging.getLogger(__name__)
def get_client ():#line:31:def get_client():
    ""#line:35:"""
    O0OO0OO00O000O0O0 =request .env ['ir.config_parameter'].sudo ().get_param ('dingtalk_base.dt_corp_id')#line:36:dt_corp_id = request.env['ir.config_parameter'].sudo().get_param('dingtalk_base.dt_corp_id')
    O0O00OOOOO00O0OOO ,O000O000O0OOO00OO =_O000000O0OOO0OO00 ()#line:37:app_key, app_secret = _get_key_and_secrect()
    return AppKeyClient (O0OO0OO00O000O0O0 ,O0O00OOOOO00O0OOO ,O000O000O0OOO00OO ,storage =mem_storage )#line:38:return AppKeyClient(dt_corp_id, app_key, app_secret, storage=mem_storage)
def _O000000O0OOO0OO00 ():#line:41:def _get_key_and_secrect():
    ""#line:45:"""
    OOOOOOOO0O00OOOO0 =request .env ['ir.config_parameter'].sudo ().get_param ('dingtalk_base.dt_app_key')#line:46:app_key = request.env['ir.config_parameter'].sudo().get_param('dingtalk_base.dt_app_key')
    OOO000O0O0000O0O0 =request .env ['ir.config_parameter'].sudo ().get_param ('dingtalk_base.dt_app_secret')#line:47:app_secret = request.env['ir.config_parameter'].sudo().get_param('dingtalk_base.dt_app_secret')
    if OOOOOOOO0O00OOOO0 and OOO000O0O0000O0O0 :#line:48:if app_key and app_secret:
        return OOOOOOOO0O00OOOO0 .replace (' ',''),OOO000O0O0000O0O0 .replace (' ','')#line:49:return app_key.replace(' ', ''), app_secret.replace(' ', '')
    return '0000','0000'#line:50:return '0000', '0000'
def get_delete_is_synchronous ():#line:53:def get_delete_is_synchronous():
    ""#line:57:"""
    return request .env ['ir.config_parameter'].sudo ().get_param ('dingtalk_base.dt_delete_is_sy')#line:58:return request.env['ir.config_parameter'].sudo().get_param('dingtalk_base.dt_delete_is_sy')
def get_login_id ():#line:61:def get_login_id():
    ""#line:65:"""
    O0O0OOO000OO0000O =request .env ['ir.config_parameter'].sudo ().get_param ('dingtalk_base.dt_login_id')#line:66:login_id = request.env['ir.config_parameter'].sudo().get_param('dingtalk_base.dt_login_id')
    if O0O0OOO000OO0000O :#line:67:if login_id:
        return O0O0OOO000OO0000O .replace (' ','')#line:68:return login_id.replace(' ', '')
    return '0000'#line:69:return '0000'
def get_login_id_and_key ():#line:72:def get_login_id_and_key():
    ""#line:75:"""
    OO0O00OOO00O00OO0 =request .env ['ir.config_parameter'].sudo ().get_param ('dingtalk_base.dt_login_id')#line:76:login_id = request.env['ir.config_parameter'].sudo().get_param('dingtalk_base.dt_login_id')
    O0O00O00OOO00OOOO =request .env ['ir.config_parameter'].sudo ().get_param ('dingtalk_base.dt_login_secret')#line:77:dt_login_secret = request.env['ir.config_parameter'].sudo().get_param('dingtalk_base.dt_login_secret')
    if OO0O00OOO00O00OO0 and O0O00O00OOO00OOOO :#line:78:if login_id and dt_login_secret:
        return OO0O00OOO00O00OO0 .replace (' ',''),O0O00O00OOO00OOOO .replace (' ','')#line:79:return login_id.replace(' ', ''), dt_login_secret.replace(' ', '')
    return '0000','0000'#line:80:return '0000', '0000'
def get_dt_corp_id ():#line:83:def get_dt_corp_id():
    ""#line:86:"""
    O00O000OOOOO0O0OO =request .env ['ir.config_parameter'].sudo ().get_param ('dingtalk_base.dt_corp_id')#line:87:dt_corp_id = request.env['ir.config_parameter'].sudo().get_param('dingtalk_base.dt_corp_id')
    if O00O000OOOOO0O0OO :#line:88:if dt_corp_id:
        return O00O000OOOOO0O0OO .replace (' ','')#line:89:return dt_corp_id.replace(' ', '')
    return '0000'#line:90:return '0000'
def get_serial_number ():#line:93:def get_serial_number():
    ""#line:96:"""
    OOOOOO0OOOO0O0OO0 =request .env ['ir.config_parameter'].sudo ().get_param ('dingtalk_base.dt_serial_number')#line:97:dt_serial_number = request.env['ir.config_parameter'].sudo().get_param('dingtalk_base.dt_serial_number')
    if OOOOOO0OOOO0O0OO0 :#line:98:if dt_serial_number:
        return OOOOOO0OOOO0O0OO0 .replace (' ','')#line:99:return dt_serial_number.replace(' ', '')
    return False #line:100:return False
def timestamp_to_local_date (OO0O0OOO000000OO0 ):#line:103:def timestamp_to_local_date(time_num):
    ""#line:108:"""
    O0O00O00000000OOO =float (OO0O0OOO000000OO0 /1000 )#line:109:to_second_timestamp = float(time_num / 1000)  # 毫秒转秒
    O0O0O0O00OO0O0000 =time .gmtime (O0O00O00000000OOO )#line:110:to_utc_datetime = time.gmtime(to_second_timestamp)  # 将时间戳转换为UTC时区（0时区）的时间元组struct_time
    O00OO000OOO0000O0 =time .strftime ("%Y-%m-%d %H:%M:%S",O0O0O0O00OO0O0000 )#line:111:to_str_datetime = time.strftime("%Y-%m-%d %H:%M:%S", to_utc_datetime)  # 将时间元组转成指定格式日期字符串
    OOOOOOOO00000O0O0 =fields .Datetime .from_string (O00OO000OOO0000O0 )#line:112:to_datetime = fields.Datetime.from_string(to_str_datetime)  # 将字符串转成datetime对象
    OOO00OOOO0O00OO0O =fields .Datetime .context_timestamp (request ,OOOOOOOO00000O0O0 )#line:113:to_local_datetime = fields.Datetime.context_timestamp(request, to_datetime)  # 将原生的datetime值(无时区)转换为具体时区的datetime
    O00OO000OOO0000O0 =fields .Datetime .to_string (OOO00OOOO0O00OO0O )#line:114:to_str_datetime = fields.Datetime.to_string(to_local_datetime)  # datetime 转成 字符串
    return O00OO000OOO0000O0 #line:115:return to_str_datetime
def datetime_to_stamp (O0OO0000O000OO00O ):#line:118:def datetime_to_stamp(time_num):
    ""#line:123:"""
    OO0OO00OO0O00O0OO =fields .Datetime .to_string (O0OO0000O000OO00O )#line:124:date_str = fields.Datetime.to_string(time_num)
    O0O0OO00O0O0OOO0O =time .mktime (time .strptime (OO0OO00OO0O00O0OO ,"%Y-%m-%d %H:%M:%S"))#line:125:date_stamp = time.mktime(time.strptime(date_str, "%Y-%m-%d %H:%M:%S"))
    O0O0OO00O0O0OOO0O =O0O0OO00O0O0OOO0O *1000 #line:126:date_stamp = date_stamp * 1000
    return int (O0O0OO00O0O0OOO0O )#line:127:return int(date_stamp)
def get_user_info_by_code (OO00O0OOOOO0O000O ):#line:130:def get_user_info_by_code(code):
    ""#line:135:"""
    OOOO0O0OOOOO000OO ,OO000OOO0O0OOOO0O =get_login_id_and_key ()#line:136:login_id, login_secret = get_login_id_and_key()
    OO000OO000O0OO0O0 =lambda :int (round (time .time ()*1000 ))#line:137:milli_time = lambda: int(round(time.time() * 1000))
    O0O00O0OO0OOOO00O =str (OO000OO000O0OO0O0 ())#line:138:timestamp = str(milli_time())
    OOOOOOO00O0OO0O00 =hmac .new (OO000OOO0O0OOOO0O .encode ('utf-8'),O0O00O0OO0OOOO00O .encode ('utf-8'),hashlib .sha256 ).digest ()#line:139:signature = hmac.new(login_secret.encode('utf-8'), timestamp.encode('utf-8'), hashlib.sha256).digest()
    OOOOOOO00O0OO0O00 =quote (base64 .b64encode (OOOOOOO00O0OO0O00 ),'utf-8')#line:140:signature = quote(base64.b64encode(signature), 'utf-8')
    OO0OO00O00O00O0O0 ="sns/getuserinfo_bycode?signature={}&timestamp={}&accessKey={}".format (OOOOOOO00O0OO0O00 ,O0O00O0OO0OOOO00O ,OOOO0O0OOOOO000OO )#line:141:url = "sns/getuserinfo_bycode?signature={}&timestamp={}&accessKey={}".format(signature, timestamp, login_id)
    OOO00000O00OOO0OO =get_client ().post (OO0OO00O00O00O0O0 ,{'tmp_auth_code':OO00O0OOOOO0O000O ,'signature':OOOOOOO00O0OO0O00 ,'timestamp':O0O00O0OO0OOOO00O ,'accessKey':OOOO0O0OOOOO000OO })#line:147:})
    return OOO00000O00OOO0OO #line:148:return result
def list_cut (OO0OO0000O00O0O0O ,O00O00OOOO0O00000 ):#line:151:def list_cut(mylist, limit):
    ""#line:157:"""
    O0O00000OOOO0OOO0 =len (OO0OO0000O00O0O0O )#line:158:length = len(mylist)
    OOOO0000OOO00O0O0 =[OO0OO0000O00O0O0O [OO0OO000O0O0OO000 :OO0OO000O0O0OO000 +O00O00OOOO0O00000 ]for OO0OO000O0O0OO000 in range (0 ,O0O00000OOOO0OOO0 ,O00O00OOOO0O00000 )]#line:159:cut_list = [mylist[i:i + limit] for i in range(0, length, limit)]
    return OOOO0000OOO00O0O0 #line:160:return cut_list
def day_cut (O0000OOO00OOO0OOO ,OOO000OOOO00OOOOO ,O00OOOO0O00O0O000 ):#line:163:def day_cut(begin_time, end_time, days):
    ""#line:170:"""
    OOOOOO0O00O00OO0O =[]#line:171:cut_day = []
    O0000OOO00OOO0OOO =datetime .strptime (str (O0000OOO00OOO0OOO ),"%Y-%m-%d")#line:172:begin_time = datetime.strptime(str(begin_time), "%Y-%m-%d")
    OOO000OOOO00OOOOO =datetime .strptime (str (OOO000OOOO00OOOOO ),"%Y-%m-%d")#line:173:end_time = datetime.strptime(str(end_time), "%Y-%m-%d")
    O0OO000O0O0OOO0O0 =timedelta (days =O00OOOO0O00O0O000 )#line:174:delta = timedelta(days=days)
    OO0000000OO00000O =O0000OOO00OOO0OOO #line:175:t1 = begin_time
    while OO0000000OO00000O <=OOO000OOOO00OOOOO :#line:176:while t1 <= end_time:
        if OOO000OOOO00OOOOO <OO0000000OO00000O +O0OO000O0O0OOO0O0 :#line:177:if end_time < t1 + delta:
            O00000OO00O0000OO =OOO000OOOO00OOOOO #line:178:t2 = end_time
        else :#line:179:else:
            O00000OO00O0000OO =OO0000000OO00000O +O0OO000O0O0OOO0O0 #line:180:t2 = t1 + delta
        O0O0O0OO0O00O0OO0 =OO0000000OO00000O .strftime ("%Y-%m-%d %H:%M:%S")#line:181:t1_str = t1.strftime("%Y-%m-%d %H:%M:%S")
        O00OO0O0OO0OO0OOO =O00000OO00O0000OO .strftime ("%Y-%m-%d %H:%M:%S")#line:182:t2_str = t2.strftime("%Y-%m-%d %H:%M:%S")
        OOOOOO0O00O00OO0O .append ([O0O0O0OO0O00O0OO0 ,O00OO0O0OO0OO0OOO ])#line:183:cut_day.append([t1_str, t2_str])
        OO0000000OO00000O =O00000OO00O0000OO +timedelta (seconds =1 )#line:184:t1 = t2 + timedelta(seconds=1)
    return OOOOOO0O00O00OO0O #line:185:return cut_day
def check_dingtalk_authorization (OOO000OOOOOO00OOO ):#line:188:def check_dingtalk_authorization(model_name):
    ""#line:192:"""
    OO000OOO00OO000O0 =get_dt_corp_id ()#line:193:serial_number = get_dt_corp_id()
    if not OO000OOO00OO000O0 :#line:194:if not serial_number:
        return False #line:195:return False
    OOO000000OO0O0O0O ="http://111.231.208.155:8099"#line:196:service_url = "http://111.231.208.155:8099"
    try :#line:197:try:
        O00O0O00OO0O0O0OO =requests .get (url =OOO000000OO0O0O0O ,params ={'code':OO000OOO00OO000O0 ,'domain':request .httprequest .host_url ,'model':OOO000OOOOOO00OOO },timeout =5 )#line:198:result = requests.get(url=service_url, params={'code': serial_number, 'domain': request.httprequest.host_url, 'model': model_name}, timeout=5)
        O00O0O00OO0O0O0OO =json .loads (O00O0O00OO0O0O0OO .text )#line:199:result = json.loads(result.text)
        if O00O0O00OO0O0O0OO ['model_state']:#line:200:if result['model_state']:
            return {'state':True ,'msg':O00O0O00OO0O0O0OO ['msg']}#line:201:return {'state': True, 'msg': result['msg']}
        else :#line:202:else:
            return {'state':False ,'msg':O00O0O00OO0O0O0OO ['msg']}#line:203:return {'state': False, 'msg': result['msg']}
    except Exception as O0O0O000000OO0000 :#line:204:except Exception as e:
        return {'state':False ,'msg':str (O0O0O000000OO0000 )}#line:205:return {'state': False, 'msg': str(e)}
def check_dt_serial_number (O000O0O00000O0OOO ):#line:208:def check_dt_serial_number(check_model):
    ""#line:213:"""
    if O000O0O00000O0OOO =='check_model':#line:214:if check_model == 'check_model':
        O000O0OOOO00OO0OO =check_dingtalk_authorization ("check_model")#line:215:result = check_dingtalk_authorization("check_model")
        return O000O0OOOO00OO0OO ['msg']#line:216:return result['msg']
def setup_approval_state_fields (OO00OOOO00OO00O0O ):#line:219:def setup_approval_state_fields(self):
    ""#line:224:"""
    def O0O0OO0O0000O00O0 (OOO0OO0OOO0000000 ,OOO00O0OO0OO00O0O ):#line:225:def add(name, field):
        if OOO0OO0OOO0000000 not in OO00OOOO00OO00O0O ._fields :#line:226:if name not in self._fields:
            OO00OOOO00OO00O0O ._add_field (OOO0OO0OOO0000000 ,OOO00O0OO0OO00O0O )#line:227:self._add_field(name, field)
    OO00OOOO00OO00O0O ._cr .execute ("SELECT COUNT(*) FROM pg_class WHERE relname = 'dingtalk_approval_control'")#line:228:self._cr.execute("SELECT COUNT(*) FROM pg_class WHERE relname = 'dingtalk_approval_control'")
    O0O000O000O000O0O =OO00OOOO00OO00O0O ._cr .fetchall ()#line:229:table = self._cr.fetchall()
    if O0O000O000O000O0O [0 ][0 ]>0 :#line:230:if table[0][0] > 0:
        OO00OOOO00OO00O0O ._cr .execute ("""SELECT im.model 
                FROM dingtalk_approval_control dac 
                JOIN ir_model im 
                     ON dac.oa_model_id = im.id 
                WHERE im.model = '%s'
                """%OO00OOOO00OO00O0O ._name )#line:237:""" % self._name)
        O00O000OO0O0O0O0O =OO00OOOO00OO00O0O ._cr .fetchall ()#line:238:res = self._cr.fetchall()
        if len (O00O000OO0O0O0O0O )!=0 :#line:239:if len(res) != 0:
            O0O0OO0O0000O00O0 ('dd_doc_state',fields .Char (string =u'审批描述'))#line:240:add('dd_doc_state', fields.Char(string=u'审批描述'))
            O0O0OO0O0000O00O0 ('dd_approval_state',fields .Selection (string =u'审批状态',selection =[('draft','草稿'),('approval','审批中'),('stop','审批结束')],default ='draft'))#line:241:add('dd_approval_state', fields.Selection(string=u'审批状态', selection=[('draft', '草稿'), ('approval', '审批中'), ('stop', '审批结束')], default='draft'))
            O0O0OO0O0000O00O0 ('dd_approval_result',fields .Selection (string =u'审批结果',selection =[('load','等待'),('agree','同意'),('refuse','拒绝'),('redirect','转交')],default ='load'))#line:243:default='load'))
            O0O0OO0O0000O00O0 ('dd_process_instance',fields .Char (string ='钉钉审批实例id'))#line:244:add('dd_process_instance', fields.Char(string='钉钉审批实例id'))
    return True #line:245:return True
def dingtalk_approval_write (OOO0OOO00OOO0OO00 ,O0OOO000000OOO00O ):#line:248:def dingtalk_approval_write(self, vals):
    ""#line:249:"""不允许单据修改"""
    O0OO00000O0000000 =OOO0OOO00OOO0OO00 .env .get ('dingtalk.approval.control')#line:250:res_state_obj = self.env.get('dingtalk.approval.control')
    if O0OO00000O0000000 is None :#line:251:if res_state_obj is None:
        return #line:252:return
    if len (O0OOO000000OOO00O .keys ())==1 and list (O0OOO000000OOO00O .keys ())[0 ]=='message_follower_ids':#line:254:if len(vals.keys()) == 1 and list(vals.keys())[0] == 'message_follower_ids':
        return #line:255:return
    for O00O0OOOO00OO0OO0 in OOO0OOO00OOO0OO00 :#line:256:for res in self:
        O0O000OO0O0000OOO =OOO0OOO00OOO0OO00 .env ['ir.model'].sudo ().search ([('model','=',O00O0OOOO00OO0OO0 ._name )]).id #line:257:model_id = self.env['ir.model'].sudo().search([('model', '=', res._name)]).id
        OOO0000O0O0O000OO =O0OO00000O0000000 .sudo ().search ([('oa_model_id','=',O0O000OO0O0000OOO )])#line:258:flows = res_state_obj.sudo().search([('oa_model_id', '=', model_id)])
        if not OOO0000O0O0O000OO :#line:259:if not flows:
            continue #line:260:continue
        if O00O0OOOO00OO0OO0 .dd_approval_state =='approval':#line:261:if res.dd_approval_state == 'approval':
            raise ValidationError (u'注意：单据审批中，不允许进行修改。 *_*!!')#line:263:raise ValidationError(u'注意：单据审批中，不允许进行修改。 *_*!!')
        elif O00O0OOOO00OO0OO0 .dd_approval_state =='stop':#line:264:elif res.dd_approval_state == 'stop':
            if OOO0000O0O0O000OO [0 ].ftype =='oa':#line:266:if flows[0].ftype == 'oa':
                raise ValidationError (u'注意：单据已审批完成，不允许进行修改。 *_*!!')#line:267:raise ValidationError(u'注意：单据已审批完成，不允许进行修改。 *_*!!')
    return True #line:268:return True
def dingtalk_approval_unlink (OO0OOOO00OO0OOOO0 ):#line:271:def dingtalk_approval_unlink(self):
    ""#line:272:"""非草稿单据不允许删除"""
    OOO00O00OO0O00O0O =OO0OOOO00OO0OOOO0 .env .get ('dingtalk.approval.control')#line:273:res_state_obj = self.env.get('dingtalk.approval.control')
    if OOO00O00OO0O00O0O is None :#line:274:if res_state_obj is None:
        return #line:275:return
    for OO00O0OOOO0000000 in OO0OOOO00OO0OOOO0 :#line:276:for res in self:
        OOO0OO0O000000O0O =OO0OOOO00OO0OOOO0 .env ['ir.model'].sudo ().search ([('model','=',OO00O0OOOO0000000 ._name )]).id #line:277:model_id = self.env['ir.model'].sudo().search([('model', '=', res._name)]).id
        O00O000OOO0O00OOO =OOO00O00OO0O00O0O .sudo ().search ([('oa_model_id','=',OOO0OO0O000000O0O )])#line:278:flows = res_state_obj.sudo().search([('oa_model_id', '=', model_id)])
        if not O00O000OOO0O00OOO :#line:279:if not flows:
            continue #line:280:continue
        if OO00O0OOOO0000000 .dd_approval_state !='draft':#line:281:if res.dd_approval_state != 'draft':
            raise ValidationError (u'注意：非草稿单据不允许删除。 *_*!!')#line:282:raise ValidationError(u'注意：非草稿单据不允许删除。 *_*!!')
    return True #line:283:return True
