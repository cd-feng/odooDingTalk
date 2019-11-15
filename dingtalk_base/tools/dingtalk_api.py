import base64 #line:6
import hashlib #line:7
import hmac #line:8
import json #line:9
import logging #line:10
import time #line:11
from datetime import datetime ,timedelta #line:12
import requests #line:13
from odoo import fields ,_ #line:14
from urllib .parse import quote #line:15
from odoo .exceptions import ValidationError #line:16
try :#line:18
    from dingtalk .client import AppKeyClient #line:19
    from dingtalk .storage .memorystorage import MemoryStorage #line:20
    from odoo .http import request #line:21
except ImportError as e :#line:22
    logging .info (_ ("-------Import Error-----------------------"))#line:23
    logging .info (_ ("引入钉钉三方SDK出错！请检查是否正确安装SDK！！！"))#line:24
    logging .info (_ ("-------Import Error-----------------------"))#line:25
mem_storage =MemoryStorage ()#line:27
_O0O00000O0OO0O000 =logging .getLogger (__name__ )#line:28
def get_client ():#line:31
    ""#line:35
    OO0OO0OOOOO000O00 =request .env ['ir.config_parameter'].sudo ().get_param ('dingtalk_base.dt_corp_id')#line:36
    O0O0O00000O00O0O0 ,O0OO0O00OO0000O00 =_O00OO00O0O000O00O ()#line:37
    return AppKeyClient (OO0OO0OOOOO000O00 ,O0O0O00000O00O0O0 ,O0OO0O00OO0000O00 ,storage =mem_storage )#line:38
def _O00OO00O0O000O00O ():#line:41
    ""#line:45
    OOOO0000000OOOO0O =request .env ['ir.config_parameter'].sudo ().get_param ('dingtalk_base.dt_app_key')#line:46
    OO0000O0O0OO00O0O =request .env ['ir.config_parameter'].sudo ().get_param ('dingtalk_base.dt_app_secret')#line:47
    if OOOO0000000OOOO0O and OO0000O0O0OO00O0O :#line:48
        return OOOO0000000OOOO0O .replace (' ',''),OO0000O0O0OO00O0O .replace (' ','')#line:49
    return '0000','0000'#line:50
def get_delete_is_synchronous ():#line:53
    ""#line:57
    return request .env ['ir.config_parameter'].sudo ().get_param ('dingtalk_base.dt_delete_is_sy')#line:58
def get_login_id ():#line:61
    ""#line:65
    O00OOO00OOOOO0O00 =request .env ['ir.config_parameter'].sudo ().get_param ('dingtalk_base.dt_login_id')#line:66
    if O00OOO00OOOOO0O00 :#line:67
        return O00OOO00OOOOO0O00 .replace (' ','')#line:68
    return '0000'#line:69
def get_login_id_and_key ():#line:72
    ""#line:75
    O0000O0O0OO0OO0O0 =request .env ['ir.config_parameter'].sudo ().get_param ('dingtalk_base.dt_login_id')#line:76
    O00OO00O0OO0O00O0 =request .env ['ir.config_parameter'].sudo ().get_param ('dingtalk_base.dt_login_secret')#line:77
    if O0000O0O0OO0OO0O0 and O00OO00O0OO0O00O0 :#line:78
        return O0000O0O0OO0OO0O0 .replace (' ',''),O00OO00O0OO0O00O0 .replace (' ','')#line:79
    return '0000','0000'#line:80
def get_dt_corp_id ():#line:83
    ""#line:86
    O0O0O0OO00O0OOO00 =request .env ['ir.config_parameter'].sudo ().get_param ('dingtalk_base.dt_corp_id')#line:87
    if O0O0O0OO00O0OOO00 :#line:88
        return O0O0O0OO00O0OOO00 .replace (' ','')#line:89
    return '0000'#line:90
def timestamp_to_local_date (OOOO00OO0OOO0O00O ):#line:93
    ""#line:98
    O0OOO0OO0O0OO0O00 =float (OOOO00OO0OOO0O00O /1000 )#line:99
    OOO0OOO00O00O00OO =time .gmtime (O0OOO0OO0O0OO0O00 )#line:100
    O0O0O0O0O0OO00O00 =time .strftime ("%Y-%m-%d %H:%M:%S",OOO0OOO00O00O00OO )#line:101
    O0O0O0O00000000O0 =fields .Datetime .from_string (O0O0O0O0O0OO00O00 )#line:102
    OO0OO0OO0O000O000 =fields .Datetime .context_timestamp (request ,O0O0O0O00000000O0 )#line:103
    O0O0O0O0O0OO00O00 =fields .Datetime .to_string (OO0OO0OO0O000O000 )#line:104
    return O0O0O0O0O0OO00O00 #line:105
def datetime_to_stamp (O0O00O00O000O0O00 ):#line:108
    ""#line:113
    O00OO000O00000O0O =fields .Datetime .to_string (O0O00O00O000O0O00 )#line:114
    O0OOO0O0000OOOOO0 =time .mktime (time .strptime (O00OO000O00000O0O ,"%Y-%m-%d %H:%M:%S"))#line:115
    O0OOO0O0000OOOOO0 =O0OOO0O0000OOOOO0 *1000 #line:116
    return O0OOO0O0000OOOOO0 #line:117
def get_user_info_by_code (O00OOOO000OOO00OO ):#line:120
    ""#line:125
    OO0O0O0OO0O00O0OO ,O0O000O00OOO0O000 =get_login_id_and_key ()#line:126
    O0OO00OO0000O0000 =lambda :int (round (time .time ()*1000 ))#line:127
    O0O0OOOO00O000OO0 =str (O0OO00OO0000O0000 ())#line:128
    O0O0OO00O0000OOO0 =hmac .new (O0O000O00OOO0O000 .encode ('utf-8'),O0O0OOOO00O000OO0 .encode ('utf-8'),hashlib .sha256 ).digest ()#line:129
    O0O0OO00O0000OOO0 =quote (base64 .b64encode (O0O0OO00O0000OOO0 ),'utf-8')#line:130
    OOOO00O00O00OOO00 ="sns/getuserinfo_bycode?signature={}&timestamp={}&accessKey={}".format (O0O0OO00O0000OOO0 ,O0O0OOOO00O000OO0 ,OO0O0O0OO0O00O0OO )#line:131
    OOOOO0OO0O00000OO =get_client ().post (OOOO00O00O00OOO00 ,{'tmp_auth_code':O00OOOO000OOO00OO ,'signature':O0O0OO00O0000OOO0 ,'timestamp':O0O0OOOO00O000OO0 ,'accessKey':OO0O0O0OO0O00O0OO })#line:137
    return OOOOO0OO0O00000OO #line:138
def list_cut (O0OO00OOOO00O00O0 ,O0O0O0O0O0000O000 ):#line:141
    ""#line:147
    O0OOOOOOOO000O00O =len (O0OO00OOOO00O00O0 )#line:148
    OOOO000OOO0O00OOO =[O0OO00OOOO00O00O0 [OO00OO000OO00OO0O :OO00OO000OO00OO0O +O0O0O0O0O0000O000 ]for OO00OO000OO00OO0O in range (0 ,O0OOOOOOOO000O00O ,O0O0O0O0O0000O000 )]#line:149
    return OOOO000OOO0O00OOO #line:150
def day_cut (O00000O0O0OO00OOO ,O00O0O0OOO0O000OO ,O000O00OOO00000O0 ):#line:153
    ""#line:160
    O00O00OO0OO0OO000 =[]#line:161
    O00000O0O0OO00OOO =datetime .strptime (str (O00000O0O0OO00OOO ),"%Y-%m-%d")#line:162
    O00O0O0OOO0O000OO =datetime .strptime (str (O00O0O0OOO0O000OO ),"%Y-%m-%d")#line:163
    O00O0O0O0000O0OO0 =timedelta (days =O000O00OOO00000O0 )#line:164
    OO0OO0OOO0000OOO0 =O00000O0O0OO00OOO #line:165
    while OO0OO0OOO0000OOO0 <=O00O0O0OOO0O000OO :#line:166
        if O00O0O0OOO0O000OO <OO0OO0OOO0000OOO0 +O00O0O0O0000O0OO0 :#line:167
            O000OO00O0O0O0OO0 =O00O0O0OOO0O000OO #line:168
        else :#line:169
            O000OO00O0O0O0OO0 =OO0OO0OOO0000OOO0 +O00O0O0O0000O0OO0 #line:170
        O0O000000000OOOOO =OO0OO0OOO0000OOO0 .strftime ("%Y-%m-%d %H:%M:%S")#line:171
        O0OOO0O0O0OOOOOO0 =O000OO00O0O0O0OO0 .strftime ("%Y-%m-%d %H:%M:%S")#line:172
        O00O00OO0OO0OO000 .append ([O0O000000000OOOOO ,O0OOO0O0O0OOOOOO0 ])#line:173
        OO0OO0OOO0000OOO0 =O000OO00O0O0O0OO0 +timedelta (seconds =1 )#line:174
    return O00O00OO0OO0OO000 #line:175
def check_dingtalk_authorization (O0O0OOOOOO0OOO0OO ):#line:178
    ""#line:182
    OOO000O0OO000O0OO =request .env ['ir.config_parameter'].sudo ().get_param ('dingtalk_base.dt_serial_number')#line:183
    if not OOO000O0OO000O0OO :#line:184
        return {'state':False ,'msg':"抱歉：由于您钉钉配置项中的授权许可号为正确生成或不存在，系统已阻止本功能!"}#line:185
    O0O000O00O00O0000 ="http://111.231.208.155:8099"#line:186
    O00O0O0000OO00O00 ={'code':OOO000O0OO000O0OO ,'domain':request .httprequest .host_url ,'model':O0O0OOOOOO0OOO0OO }#line:187
    try :#line:188
        OOOOO0O000000OOOO =requests .get (url =O0O000O00O00O0000 ,params =O00O0O0000OO00O00 ,timeout =5 )#line:189
        OOOOO0O000000OOOO =json .loads (OOOOO0O000000OOOO .text )#line:190
        if OOOOO0O000000OOOO ['model_state']:#line:191
            return {'state':True ,'msg':OOOOO0O000000OOOO ['msg']}#line:192
        else :#line:193
            return {'state':False ,'msg':"抱歉：授权许可号无效或已过期，请购买授权后再使用，谢谢。 *_*!"}#line:194
    except Exception as OOOOOO000OO0000O0 :#line:195
        return {'state':False ,'msg':"抱歉：服务端的网络链接异常或超时，请确保网络通畅！若不是网络问题，请反馈给开发者。 *_*!"}#line:196

def check_dt_serial_number (O00OOOO0O0OO00000 ):#line:199
    ""#line:204
    if O00OOOO0O0OO00000 =='check_model':#line:205
        O0OO0O0000000O000 =check_dingtalk_authorization ("check_model")#line:206
        return O0OO0O0000000O000 ['msg']#line:207
def setup_approval_state_fields (OOO0000OO00O000O0 ):#line:210
    ""#line:215
    def O000O0O00O000O0OO (OOO00O00OOO0O0OOO ,O0OOOO0OO0OO0OO00 ):#line:216
        if OOO00O00OOO0O0OOO not in OOO0000OO00O000O0 ._fields :#line:217
            OOO0000OO00O000O0 ._add_field (OOO00O00OOO0O0OOO ,O0OOOO0OO0OO0OO00 )#line:218
    OOO0000OO00O000O0 ._cr .execute ("SELECT COUNT(*) FROM pg_class WHERE relname = 'dingtalk_approval_control'")#line:219
    O0O00O0OO0OOOO0OO =OOO0000OO00O000O0 ._cr .fetchall ()#line:220
    if O0O00O0OO0OOOO0OO [0 ][0 ]>0 :#line:221
        OOO0000OO00O000O0 ._cr .execute ("""SELECT im.model 
                FROM dingtalk_approval_control dac 
                JOIN ir_model im 
                     ON dac.oa_model_id = im.id 
                WHERE im.model = '%s'
                """%OOO0000OO00O000O0 ._name )#line:228
        OOO0OOO00000O000O =OOO0000OO00O000O0 ._cr .fetchall ()#line:229
        if len (OOO0OOO00000O000O )!=0 :#line:230
            O000O0O00O000O0OO ('dd_doc_state',fields .Char (string =u'审批描述'))#line:231
            O000O0O00O000O0OO ('dd_approval_state',fields .Selection (string =u'审批状态',selection =[('draft','草稿'),('approval','审批中'),('stop','审批结束')],default ='draft'))#line:232
            O000O0O00O000O0OO ('dd_approval_result',fields .Selection (string =u'审批结果',selection =[('load','等待'),('agree','同意'),('refuse','拒绝'),('redirect','转交')],default ='load'))#line:234
            O000O0O00O000O0OO ('dd_process_instance',fields .Char (string ='钉钉审批实例id'))#line:235
    return True #line:236
def dingtalk_approval_write (O000OOO00O0O0OO00 ,OO0O00O0O000O00OO ):#line:239
    ""#line:240
    OOOO000OO00OOOO00 =O000OOO00O0O0OO00 .env .get ('dingtalk.approval.control')#line:241
    if OOOO000OO00OOOO00 is None :#line:242
        return #line:243
    if len (OO0O00O0O000O00OO .keys ())==1 and list (OO0O00O0O000O00OO .keys ())[0 ]=='message_follower_ids':#line:245
        return #line:246
    for OOOO0O0O000O0O00O in O000OOO00O0O0OO00 :#line:247
        O0OO00OOOOOOO0000 =O000OOO00O0O0OO00 .env ['ir.model'].sudo ().search ([('model','=',OOOO0O0O000O0O00O ._name )]).id #line:248
        OOOOOOO0OOO0O0O00 =OOOO000OO00OOOO00 .sudo ().search ([('oa_model_id','=',O0OO00OOOOOOO0000 )])#line:249
        if not OOOOOOO0OOO0O0O00 :#line:250
            continue #line:251
        if OOOO0O0O000O0O00O .dd_approval_state =='approval':#line:252
            raise ValidationError (u'注意：单据审批中，不允许进行修改。 *_*!!')#line:254
        elif OOOO0O0O000O0O00O .dd_approval_state =='stop':#line:255
            if OOOOOOO0OOO0O0O00 [0 ].ftype =='oa':#line:257
                raise ValidationError (u'注意：单据已审批完成，不允许进行修改。 *_*!!')#line:258
    return True #line:259
def dingtalk_approval_unlink (O0000O00O000O0OO0 ):#line:262
    ""#line:263
    OOO0O00OO000O000O =O0000O00O000O0OO0 .env .get ('dingtalk.approval.control')#line:264
    if OOO0O00OO000O000O is None :#line:265
        return #line:266
    for OOOOO0OOO0OO0OOOO in O0000O00O000O0OO0 :#line:267
        O000O0000OOOO0O0O =O0000O00O000O0OO0 .env ['ir.model'].sudo ().search ([('model','=',OOOOO0OOO0OO0OOOO ._name )]).id #line:268
        O00O0OOOO0OOOOO0O =OOO0O00OO000O000O .sudo ().search ([('oa_model_id','=',O000O0000OOOO0O0O )])#line:269
        if not O00O0OOOO0OOOOO0O :#line:270
            continue #line:271
        if OOOOO0OOO0OO0OOOO .dd_approval_state !='draft':#line:272
            raise ValidationError (u'注意：非草稿单据不允许删除。 *_*!!')#line:273
    return True #line:274
