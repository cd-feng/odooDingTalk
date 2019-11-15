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
_O0OO000O0OO0O00O0 =logging .getLogger (__name__ )#line:28:_logger = logging.getLogger(__name__)
def get_client ():#line:31:def get_client():
    ""#line:35:"""
    O0OO0O0OOO000O0O0 =request .env ['ir.config_parameter'].sudo ().get_param ('dingtalk_base.dt_corp_id')#line:36:dt_corp_id = request.env['ir.config_parameter'].sudo().get_param('dingtalk_base.dt_corp_id')
    O0OO00OOOOOO00O00 ,OO00OO00000O000OO =_OOOO0OOOO0000O000 ()#line:37:app_key, app_secret = _get_key_and_secrect()
    return AppKeyClient (O0OO0O0OOO000O0O0 ,O0OO00OOOOOO00O00 ,OO00OO00000O000OO ,storage =mem_storage )#line:38:return AppKeyClient(dt_corp_id, app_key, app_secret, storage=mem_storage)
def _OOOO0OOOO0000O000 ():#line:41:def _get_key_and_secrect():
    ""#line:45:"""
    OOOOOOOO0OOOO00O0 =request .env ['ir.config_parameter'].sudo ().get_param ('dingtalk_base.dt_app_key')#line:46:app_key = request.env['ir.config_parameter'].sudo().get_param('dingtalk_base.dt_app_key')
    OO00OOO0OOO000OOO =request .env ['ir.config_parameter'].sudo ().get_param ('dingtalk_base.dt_app_secret')#line:47:app_secret = request.env['ir.config_parameter'].sudo().get_param('dingtalk_base.dt_app_secret')
    if OOOOOOOO0OOOO00O0 and OO00OOO0OOO000OOO :#line:48:if app_key and app_secret:
        return OOOOOOOO0OOOO00O0 .replace (' ',''),OO00OOO0OOO000OOO .replace (' ','')#line:49:return app_key.replace(' ', ''), app_secret.replace(' ', '')
    return '0000','0000'#line:50:return '0000', '0000'
def get_delete_is_synchronous ():#line:53:def get_delete_is_synchronous():
    ""#line:57:"""
    return request .env ['ir.config_parameter'].sudo ().get_param ('dingtalk_base.dt_delete_is_sy')#line:58:return request.env['ir.config_parameter'].sudo().get_param('dingtalk_base.dt_delete_is_sy')
def get_login_id ():#line:61:def get_login_id():
    ""#line:65:"""
    O0OOOOOOOO00O00OO =request .env ['ir.config_parameter'].sudo ().get_param ('dingtalk_base.dt_login_id')#line:66:login_id = request.env['ir.config_parameter'].sudo().get_param('dingtalk_base.dt_login_id')
    if O0OOOOOOOO00O00OO :#line:67:if login_id:
        return O0OOOOOOOO00O00OO .replace (' ','')#line:68:return login_id.replace(' ', '')
    return '0000'#line:69:return '0000'
def get_login_id_and_key ():#line:72:def get_login_id_and_key():
    ""#line:75:"""
    O0000000O0O00OO00 =request .env ['ir.config_parameter'].sudo ().get_param ('dingtalk_base.dt_login_id')#line:76:login_id = request.env['ir.config_parameter'].sudo().get_param('dingtalk_base.dt_login_id')
    OOO00O000OO0OOO00 =request .env ['ir.config_parameter'].sudo ().get_param ('dingtalk_base.dt_login_secret')#line:77:dt_login_secret = request.env['ir.config_parameter'].sudo().get_param('dingtalk_base.dt_login_secret')
    if O0000000O0O00OO00 and OOO00O000OO0OOO00 :#line:78:if login_id and dt_login_secret:
        return O0000000O0O00OO00 .replace (' ',''),OOO00O000OO0OOO00 .replace (' ','')#line:79:return login_id.replace(' ', ''), dt_login_secret.replace(' ', '')
    return '0000','0000'#line:80:return '0000', '0000'
def get_dt_corp_id ():#line:83:def get_dt_corp_id():
    ""#line:86:"""
    OOO00OOO0OO00O00O =request .env ['ir.config_parameter'].sudo ().get_param ('dingtalk_base.dt_corp_id')#line:87:dt_corp_id = request.env['ir.config_parameter'].sudo().get_param('dingtalk_base.dt_corp_id')
    if OOO00OOO0OO00O00O :#line:88:if dt_corp_id:
        return OOO00OOO0OO00O00O .replace (' ','')#line:89:return dt_corp_id.replace(' ', '')
    return '0000'#line:90:return '0000'
def timestamp_to_local_date (O000OOO0000000OO0 ):#line:93:def timestamp_to_local_date(time_num):
    ""#line:98:"""
    OOO0O0OO0OO0OOOOO =float (O000OOO0000000OO0 /1000 )#line:99:to_second_timestamp = float(time_num / 1000)  # 毫秒转秒
    OO0O0O000OOOOOOO0 =time .gmtime (OOO0O0OO0OO0OOOOO )#line:100:to_utc_datetime = time.gmtime(to_second_timestamp)  # 将时间戳转换为UTC时区（0时区）的时间元组struct_time
    O00O0O000O0OO0000 =time .strftime ("%Y-%m-%d %H:%M:%S",OO0O0O000OOOOOOO0 )#line:101:to_str_datetime = time.strftime("%Y-%m-%d %H:%M:%S", to_utc_datetime)  # 将时间元组转成指定格式日期字符串
    OO00OO0OO00OO00OO =fields .Datetime .from_string (O00O0O000O0OO0000 )#line:102:to_datetime = fields.Datetime.from_string(to_str_datetime)  # 将字符串转成datetime对象
    OOO00O0OO0000O000 =fields .Datetime .context_timestamp (request ,OO00OO0OO00OO00OO )#line:103:to_local_datetime = fields.Datetime.context_timestamp(request, to_datetime)  # 将原生的datetime值(无时区)转换为具体时区的datetime
    O00O0O000O0OO0000 =fields .Datetime .to_string (OOO00O0OO0000O000 )#line:104:to_str_datetime = fields.Datetime.to_string(to_local_datetime)  # datetime 转成 字符串
    return O00O0O000O0OO0000 #line:105:return to_str_datetime
def datetime_to_stamp (O00OOOOO0O0O0OOO0 ):#line:108:def datetime_to_stamp(time_num):
    ""#line:113:"""
    O000OOOO0O00OOOO0 =fields .Datetime .to_string (O00OOOOO0O0O0OOO0 )#line:114:date_str = fields.Datetime.to_string(time_num)
    O0O0000OOO0OO0000 =time .mktime (time .strptime (O000OOOO0O00OOOO0 ,"%Y-%m-%d %H:%M:%S"))#line:115:date_stamp = time.mktime(time.strptime(date_str, "%Y-%m-%d %H:%M:%S"))
    O0O0000OOO0OO0000 =O0O0000OOO0OO0000 *1000 #line:116:date_stamp = date_stamp * 1000
    return O0O0000OOO0OO0000 #line:117:return date_stamp
def get_user_info_by_code (O000OO0O00O000O00 ):#line:120:def get_user_info_by_code(code):
    ""#line:125:"""
    OO0O0OOOO00O00OO0 ,O00O0O0OO0OOOOOOO =get_login_id_and_key ()#line:126:login_id, login_secret = get_login_id_and_key()
    OO000OOOOOOOO0OO0 =lambda :int (round (time .time ()*1000 ))#line:127:milli_time = lambda: int(round(time.time() * 1000))
    OOOOOOOOOO00O0O0O =str (OO000OOOOOOOO0OO0 ())#line:128:timestamp = str(milli_time())
    OO00OO00O000000OO =hmac .new (O00O0O0OO0OOOOOOO .encode ('utf-8'),OOOOOOOOOO00O0O0O .encode ('utf-8'),hashlib .sha256 ).digest ()#line:129:signature = hmac.new(login_secret.encode('utf-8'), timestamp.encode('utf-8'), hashlib.sha256).digest()
    OO00OO00O000000OO =quote (base64 .b64encode (OO00OO00O000000OO ),'utf-8')#line:130:signature = quote(base64.b64encode(signature), 'utf-8')
    O0OO00O0OOO00OO00 ="sns/getuserinfo_bycode?signature={}&timestamp={}&accessKey={}".format (OO00OO00O000000OO ,OOOOOOOOOO00O0O0O ,OO0O0OOOO00O00OO0 )#line:131:url = "sns/getuserinfo_bycode?signature={}&timestamp={}&accessKey={}".format(signature, timestamp, login_id)
    OOO0O00O0O000OOO0 =get_client ().post (O0OO00O0OOO00OO00 ,{'tmp_auth_code':O000OO0O00O000O00 ,'signature':OO00OO00O000000OO ,'timestamp':OOOOOOOOOO00O0O0O ,'accessKey':OO0O0OOOO00O00OO0 })#line:137:})
    return OOO0O00O0O000OOO0 #line:138:return result
def list_cut (OO00O0OOO00000OO0 ,O00000O000O0O000O ):#line:141:def list_cut(mylist, limit):
    ""#line:147:"""
    OO000000000OOOO0O =len (OO00O0OOO00000OO0 )#line:148:length = len(mylist)
    OOO0000OO0OO0000O =[OO00O0OOO00000OO0 [O0O00OOOOOO0O00OO :O0O00OOOOOO0O00OO +O00000O000O0O000O ]for O0O00OOOOOO0O00OO in range (0 ,OO000000000OOOO0O ,O00000O000O0O000O )]#line:149:cut_list = [mylist[i:i + limit] for i in range(0, length, limit)]
    return OOO0000OO0OO0000O #line:150:return cut_list
def day_cut (OO0O00OO00000O0O0 ,OO000O0OO00000OO0 ,O00O0OOO00OO0000O ):#line:153:def day_cut(begin_time, end_time, days):
    ""#line:160:"""
    O0O000OOOOO0O0O00 =[]#line:161:cut_day = []
    OO0O00OO00000O0O0 =datetime .strptime (str (OO0O00OO00000O0O0 ),"%Y-%m-%d")#line:162:begin_time = datetime.strptime(str(begin_time), "%Y-%m-%d")
    OO000O0OO00000OO0 =datetime .strptime (str (OO000O0OO00000OO0 ),"%Y-%m-%d")#line:163:end_time = datetime.strptime(str(end_time), "%Y-%m-%d")
    OO0OO0000OOO0OO00 =timedelta (days =O00O0OOO00OO0000O )#line:164:delta = timedelta(days=days)
    O00OO00O0OOOO00OO =OO0O00OO00000O0O0 #line:165:t1 = begin_time
    while O00OO00O0OOOO00OO <=OO000O0OO00000OO0 :#line:166:while t1 <= end_time:
        if OO000O0OO00000OO0 <O00OO00O0OOOO00OO +OO0OO0000OOO0OO00 :#line:167:if end_time < t1 + delta:
            O000O0OO0000O00OO =OO000O0OO00000OO0 #line:168:t2 = end_time
        else :#line:169:else:
            O000O0OO0000O00OO =O00OO00O0OOOO00OO +OO0OO0000OOO0OO00 #line:170:t2 = t1 + delta
        O0OOO0OO0OOOO000O =O00OO00O0OOOO00OO .strftime ("%Y-%m-%d %H:%M:%S")#line:171:t1_str = t1.strftime("%Y-%m-%d %H:%M:%S")
        OO000OO0000OO0O00 =O000O0OO0000O00OO .strftime ("%Y-%m-%d %H:%M:%S")#line:172:t2_str = t2.strftime("%Y-%m-%d %H:%M:%S")
        O0O000OOOOO0O0O00 .append ([O0OOO0OO0OOOO000O ,OO000OO0000OO0O00 ])#line:173:cut_day.append([t1_str, t2_str])
        O00OO00O0OOOO00OO =O000O0OO0000O00OO +timedelta (seconds =1 )#line:174:t1 = t2 + timedelta(seconds=1)
    return O0O000OOOOO0O0O00 #line:175:return cut_day
def check_dingtalk_authorization (OOOO00OO000OO0000 ):#line:179:def check_dingtalk_authorization(model_name):
    ""#line:183:"""
    OOO0OO00O0O00OOO0 =request .env ['ir.config_parameter'].sudo ().get_param ('dingtalk_base.dt_serial_number')#line:184:dt_serial_number = request.env['ir.config_parameter'].sudo().get_param('dingtalk_base.dt_serial_number')
    if not OOO0OO00O0O00OOO0 :#line:185:if not dt_serial_number:
        return {'state':False ,'msg':"抱歉：由于您钉钉配置项中的授权许可号为正确生成或不存在，系统已阻止本功能!"}#line:186:return {'state': False, 'msg': "抱歉：由于您钉钉配置项中的授权许可号为正确生成或不存在，系统已阻止本功能!"}
    OOO0O0OOOO000O000 ="http://111.231.208.155:8099"#line:187:service_url = "http://111.231.208.155:8099"
    O000O0O0OO0O0OO0O ={'code':OOO0OO00O0O00OOO0 ,'domain':request .httprequest .host_url ,'model':OOOO00OO000OO0000 }#line:188:data = {'code': dt_serial_number, 'domain': request.httprequest.host_url, 'model': model_name}
    try :#line:189:try:
        OOO0OOOOO0000OO00 =requests .get (url =OOO0O0OOOO000O000 ,params =O000O0O0OO0O0OO0O ,timeout =5 )#line:190:result = requests.get(url=service_url, params=data, timeout=5)
        print (OOO0OOOOO0000OO00 )#line:191:print(result)
        OOO0OOOOO0000OO00 =json .loads (OOO0OOOOO0000OO00 .text )#line:192:result = json.loads(result.text)
        if OOO0OOOOO0000OO00 ['model_state']:#line:193:if result['model_state']:
            return {'state':True ,'msg':OOO0OOOOO0000OO00 ['msg']}#line:194:return {'state': True, 'msg': result['msg']}
        else :#line:195:else:
            return {'state':False ,'msg':"抱歉：授权许可号无效或已过期，请购买授权后再使用，谢谢。 *_*!"}#line:196:return {'state': False, 'msg': "抱歉：授权许可号无效或已过期，请购买授权后再使用，谢谢。 *_*!"}
    except Exception as O000O000OOOOO000O :#line:197:except Exception as e:
        return {'state':False ,'msg':"抱歉：服务端的网络链接异常或超时，请确保网络通畅！若不是网络问题，请反馈给开发者。 *_*!"}#line:198:return {'state': False, 'msg': "抱歉：服务端的网络链接异常或超时，请确保网络通畅！若不是网络问题，请反馈给开发者。 *_*!"}
def check_dt_serial_number (OOOOO00O0OOO000O0 ):#line:201:def check_dt_serial_number(check_model):
    ""#line:206:"""
    if OOOOO00O0OOO000O0 =='check_model':#line:207:if check_model == 'check_model':
        O0O0OO0OOO00O00O0 =check_dingtalk_authorization ("check_model")#line:208:result = check_dingtalk_authorization("check_model")
        return O0O0OO0OOO00O00O0 ['msg']#line:209:return result['msg']
def setup_approval_state_fields (OOO0OOO00O00O00O0 ):#line:212:def setup_approval_state_fields(self):
    ""#line:217:"""
    def OO0000OOOO00000O0 (O000O0O0O0O0000OO ,OOO0OOO00O000O00O ):#line:218:def add(name, field):
        if O000O0O0O0O0000OO not in OOO0OOO00O00O00O0 ._fields :#line:219:if name not in self._fields:
            OOO0OOO00O00O00O0 ._add_field (O000O0O0O0O0000OO ,OOO0OOO00O000O00O )#line:220:self._add_field(name, field)
    OOO0OOO00O00O00O0 ._cr .execute ("SELECT COUNT(*) FROM pg_class WHERE relname = 'dingtalk_approval_control'")#line:221:self._cr.execute("SELECT COUNT(*) FROM pg_class WHERE relname = 'dingtalk_approval_control'")
    O0000O0O000O000O0 =OOO0OOO00O00O00O0 ._cr .fetchall ()#line:222:table = self._cr.fetchall()
    if O0000O0O000O000O0 [0 ][0 ]>0 :#line:223:if table[0][0] > 0:
        OOO0OOO00O00O00O0 ._cr .execute ("""SELECT im.model 
                FROM dingtalk_approval_control dac 
                JOIN ir_model im 
                     ON dac.oa_model_id = im.id 
                WHERE im.model = '%s'
                """%OOO0OOO00O00O00O0 ._name )#line:230:""" % self._name)
        OOO000000O00O0000 =OOO0OOO00O00O00O0 ._cr .fetchall ()#line:231:res = self._cr.fetchall()
        if len (OOO000000O00O0000 )!=0 :#line:232:if len(res) != 0:
            OO0000OOOO00000O0 ('dd_doc_state',fields .Char (string =u'审批描述'))#line:233:add('dd_doc_state', fields.Char(string=u'审批描述'))
            OO0000OOOO00000O0 ('dd_approval_state',fields .Selection (string =u'审批状态',selection =[('draft','草稿'),('approval','审批中'),('stop','审批结束')],default ='draft'))#line:234:add('dd_approval_state', fields.Selection(string=u'审批状态', selection=[('draft', '草稿'), ('approval', '审批中'), ('stop', '审批结束')], default='draft'))
            OO0000OOOO00000O0 ('dd_approval_result',fields .Selection (string =u'审批结果',selection =[('load','等待'),('agree','同意'),('refuse','拒绝'),('redirect','转交')],default ='load'))#line:236:default='load'))
            OO0000OOOO00000O0 ('dd_process_instance',fields .Char (string ='钉钉审批实例id'))#line:237:add('dd_process_instance', fields.Char(string='钉钉审批实例id'))
    return True #line:238:return True
def dingtalk_approval_write (OO0OOOO000O00OOO0 ,O0OOOOO00OO00O0OO ):#line:241:def dingtalk_approval_write(self, vals):
    ""#line:242:"""不允许单据修改"""
    O00OOO000O00OO0O0 =OO0OOOO000O00OOO0 .env .get ('dingtalk.approval.control')#line:243:res_state_obj = self.env.get('dingtalk.approval.control')
    if O00OOO000O00OO0O0 is None :#line:244:if res_state_obj is None:
        return #line:245:return
    if len (O0OOOOO00OO00O0OO .keys ())==1 and list (O0OOOOO00OO00O0OO .keys ())[0 ]=='message_follower_ids':#line:247:if len(vals.keys()) == 1 and list(vals.keys())[0] == 'message_follower_ids':
        return #line:248:return
    for O00O0OO000O00O0OO in OO0OOOO000O00OOO0 :#line:249:for res in self:
        OOO0OO0O0O0O0000O =OO0OOOO000O00OOO0 .env ['ir.model'].sudo ().search ([('model','=',O00O0OO000O00O0OO ._name )]).id #line:250:model_id = self.env['ir.model'].sudo().search([('model', '=', res._name)]).id
        OOOOOOO0OO0OOO00O =O00OOO000O00OO0O0 .sudo ().search ([('oa_model_id','=',OOO0OO0O0O0O0000O )])#line:251:flows = res_state_obj.sudo().search([('oa_model_id', '=', model_id)])
        if not OOOOOOO0OO0OOO00O :#line:252:if not flows:
            continue #line:253:continue
        if O00O0OO000O00O0OO .dd_approval_state =='approval':#line:254:if res.dd_approval_state == 'approval':
            raise ValidationError (u'注意：单据审批中，不允许进行修改。 *_*!!')#line:256:raise ValidationError(u'注意：单据审批中，不允许进行修改。 *_*!!')
        elif O00O0OO000O00O0OO .dd_approval_state =='stop':#line:257:elif res.dd_approval_state == 'stop':
            if OOOOOOO0OO0OOO00O [0 ].ftype =='oa':#line:259:if flows[0].ftype == 'oa':
                raise ValidationError (u'注意：单据已审批完成，不允许进行修改。 *_*!!')#line:260:raise ValidationError(u'注意：单据已审批完成，不允许进行修改。 *_*!!')
    return True #line:261:return True
def dingtalk_approval_unlink (O0OO0OO000OOO00O0 ):#line:264:def dingtalk_approval_unlink(self):
    ""#line:265:"""非草稿单据不允许删除"""
    OO0OO000OOOOO0OO0 =O0OO0OO000OOO00O0 .env .get ('dingtalk.approval.control')#line:266:res_state_obj = self.env.get('dingtalk.approval.control')
    if OO0OO000OOOOO0OO0 is None :#line:267:if res_state_obj is None:
        return #line:268:return
    for O0O00OOOOO00OO0O0 in O0OO0OO000OOO00O0 :#line:269:for res in self:
        OOOO0OO00000000OO =O0OO0OO000OOO00O0 .env ['ir.model'].sudo ().search ([('model','=',O0O00OOOOO00OO0O0 ._name )]).id #line:270:model_id = self.env['ir.model'].sudo().search([('model', '=', res._name)]).id
        OOOOO0OOO0O0O0OO0 =OO0OO000OOOOO0OO0 .sudo ().search ([('oa_model_id','=',OOOO0OO00000000OO )])#line:271:flows = res_state_obj.sudo().search([('oa_model_id', '=', model_id)])
        if not OOOOO0OOO0O0O0OO0 :#line:272:if not flows:
            continue #line:273:continue
        if O0O00OOOOO00OO0O0 .dd_approval_state !='draft':#line:274:if res.dd_approval_state != 'draft':
            raise ValidationError (u'注意：非草稿单据不允许删除。 *_*!!')#line:275:raise ValidationError(u'注意：非草稿单据不允许删除。 *_*!!')
    return True #line:276:return True
