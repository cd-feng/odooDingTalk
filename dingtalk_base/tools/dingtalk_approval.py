import logging #line:3:import logging
from odoo import models ,api #line:4:from odoo import models, api
from odoo .exceptions import UserError #line:5:from odoo.exceptions import UserError
from .import dingtalk_api #line:6:from . import dingtalk_api
_O00O00O0OOO000O00 =logging .getLogger (__name__ )#line:8:_logger = logging.getLogger(__name__)
def approval_result (O0OO0OO0OO000OOOO ):#line:11:def approval_result(self):
    ""#line:16:"""
    O00000O000O0000O0 =dingtalk_api .check_dingtalk_authorization ('dingtalk_approval')#line:18:result = dingtalk_api.check_dingtalk_authorization('dingtalk_approval')
    if not O00000O000O0000O0 ['state']:#line:19:if not result['state']:
        raise UserError (O00000O000O0000O0 ['msg'])#line:20:raise UserError(result['msg'])
    O00O000O0000O0000 =O0OO0OO0OO000OOOO .env ['ir.model'].sudo ().search ([('model','=',O0OO0OO0OO000OOOO ._name )]).id #line:22:model_id = self.env['ir.model'].sudo().search([('model', '=', self._name)]).id
    O0O0O0OOO0O00OOO0 =O0OO0OO0OO000OOOO .env ['dingtalk.approval.control'].sudo ().search ([('oa_model_id','=',O00O000O0000O0000 )],limit =1 )#line:23:approval = self.env['dingtalk.approval.control'].sudo().search([('oa_model_id', '=', model_id)], limit=1)
    _O00O00O0OOO000O00 .info ("提交'%s'单据至钉钉进行审批..."%O0O0O0OOO0O00OOO0 .name )#line:24:_logger.info("提交'%s'单据至钉钉进行审批..." % approval.name)
    O00OO0OOO0O0OOOOO =O0O0O0OOO0O00OOO0 .template_id .process_code #line:26:process_code = approval.template_id.process_code
    OO00OOOO00000OOOO ,OOOO0O0OOO000000O =get_originator_user_id (O0OO0OO0OO000OOOO )#line:28:user_id, dept_id = get_originator_user_id(self)
    O00O0OOOO000000OO =get_form_values (O0OO0OO0OO000OOOO ,O0O0O0OOO0O00OOO0 )#line:30:form_values = get_form_values(self, approval)
    _O00O00O0OOO000O00 .info (O00O0OOOO000000OO )#line:31:_logger.info(form_values)
    OOO000OOOO0O00OO0 =dingtalk_api .get_client ()#line:33:client = dingtalk_api.get_client()
    try :#line:34:try:
        OOO0O000OO0O000OO ='topapi/processinstance/create'#line:35:url = 'topapi/processinstance/create'
        O00000O000O0000O0 =OOO000OOOO0O00OO0 .post (OOO0O000OO0O000OO ,{'process_code':O00OO0OOO0O0OOOOO ,'originator_user_id':OO00OOOO00000OOOO ,'dept_id':OOOO0O0OOO000000O ,'form_component_values':O00O0OOOO000000OO })#line:41:})
    except Exception as O00OOO0OO00000OOO :#line:42:except Exception as e:
        raise UserError (O00OOO0OO00000OOO )#line:43:raise UserError(e)
    _O00O00O0OOO000O00 .info (O00000O000O0000O0 )#line:44:_logger.info(result)
    return O00000O000O0000O0 ,O0O0O0OOO0O00OOO0 #line:45:return result, approval
def _OO0OOO0O00OO00O0O (OOOOO0O00000O000O ):#line:48:def _commit_dingtalk_approval(self):
    ""#line:53:"""
    OOOOO0O00000O000O .ensure_one ()#line:54:self.ensure_one()
    OO0OOOOO0O0O00000 ,O000OOOO0OO00O0O0 =approval_result (OOOOO0O00000O000O )#line:55:result, approval = approval_result(self)
    if OO0OOOOO0O0O00000 .get ('errcode')!=0 :#line:56:if result.get('errcode') != 0:
        raise UserError ('提交审批实例失败，失败原因:{}'.format (OO0OOOOO0O0O00000 .get ('errmsg')))#line:57:raise UserError('提交审批实例失败，失败原因:{}'.format(result.get('errmsg')))
    OO0O00OO00OO0OO0O =OOOOO0O00000O000O ._name .replace ('.','_')#line:58:model_name = self._name.replace('.', '_')
    OO0O0O0OOO0OO0000 ="""UPDATE {} 
                SET 
                    dd_approval_state='{}', 
                    dd_doc_state='{}', 
                    dd_process_instance='{}' 
                WHERE 
                    id={}""".format (OO0O00OO00OO0OO0O ,'approval','等待审批',OO0OOOOO0O0O00000 .get ('process_instance_id'),OOOOO0O00000O000O .id )#line:65:id={}""".format(model_name, 'approval', '等待审批', result.get('process_instance_id'), self.id)
    OOOOO0O00000O000O ._cr .execute (OO0O0O0OOO0OO0000 )#line:66:self._cr.execute(sql)
    if O000OOOO0OO00O0O0 .approval_start_function :#line:68:if approval.approval_start_function:
        for O0000OOOO00O0O0OO in O000OOOO0OO00O0O0 .approval_start_function .split (','):#line:69:for method in approval.approval_start_function.split(','):
            try :#line:70:try:
                getattr (OOOOO0O00000O000O ,O0000OOOO00O0O0OO )()#line:71:getattr(self, method)()
            except Exception as OOO00000O00OO0O0O :#line:72:except Exception as e:
                _O00O00O0OOO000O00 .info (OOO00000O00OO0O0O )#line:73:_logger.info(e)
    OOOOO0O00000O000O .message_post (body =u"提交钉钉成功，请等待审批人进行审批！",message_type ='notification')#line:74:self.message_post(body=u"提交钉钉成功，请等待审批人进行审批！", message_type='notification')
    return True #line:75:return True
Model =models .Model #line:78:Model = models.Model
setattr (Model ,'commit_dingtalk_approval',_OO0OOO0O00OO00O0O )#line:79:setattr(Model, 'commit_dingtalk_approval', _commit_dingtalk_approval)
def get_form_values (O0O00OO0O0O000000 ,OO00O0OO000O00O00 ):#line:82:def get_form_values(self, approval):
    ""#line:88:"""
    OO00O0000O0O0000O =list ()#line:89:fcv_list = list()
    for O0O0O0OOOOOO00OO0 in OO00O0OO000O00O00 .line_ids :#line:90:for line in approval.line_ids:
        if O0O0O0OOOOOO00OO0 .ttype =='many2one':#line:92:if line.ttype == 'many2one':
            O0O000OO000O00O00 =O0O00OO0O0O000000 [O0O0O0OOOOOO00OO0 .field_id .name ]#line:93:ding_field = self[line.field_id.name]
            if O0O0O0OOOOOO00OO0 .is_dd_id :#line:94:if line.is_dd_id:
                OO00O0000O0O0000O .append ({'name':O0O0O0OOOOOO00OO0 .dd_field ,'value':[O0O000OO000O00O00 .ding_id ]})#line:95:fcv_list.append({'name': line.dd_field, 'value': [ding_field.ding_id]})
            else :#line:96:else:
                OO00O0000O0O0000O .append ({'name':O0O0O0OOOOOO00OO0 .dd_field ,'value':O0O000OO000O00O00 .name })#line:97:fcv_list.append({'name': line.dd_field, 'value': ding_field.name})
        elif O0O0O0OOOOOO00OO0 .ttype =='many2many':#line:99:elif line.ttype == 'many2many':
            OO0OOOOOOOOO0OOO0 =O0O00OO0O0O000000 [O0O0O0OOOOOO00OO0 .field_id .name ]#line:100:many_models = self[line.field_id.name]
            OO00000000OO00O00 =list ()#line:101:line_list = list()
            for O00O0OO0OOO0OO00O in OO0OOOOOOOOO0OOO0 :#line:102:for many_model in many_models:
                if O0O0O0OOOOOO00OO0 .is_dd_id :#line:104:if line.is_dd_id:
                    OO00000000OO00O00 .append (O00O0OO0OOO0OO00O .ding_id )#line:105:line_list.append(many_model.ding_id)
                else :#line:106:else:
                    OO00000000OO00O00 .append (O00O0OO0OOO0OO00O .name )#line:107:line_list.append(many_model.name)
            OO00O0000O0O0000O .append ({'name':O0O0O0OOOOOO00OO0 .dd_field ,'value':OO00000000OO00O00 })#line:108:fcv_list.append({'name': line.dd_field, 'value': line_list})
        elif O0O0O0OOOOOO00OO0 .ttype =='date':#line:110:elif line.ttype == 'date':
            OO00O0000O0O0000O .append ({'name':O0O0O0OOOOOO00OO0 .dd_field ,'value':O0O00OO0O0O000000 [O0O0O0OOOOOO00OO0 .field_id .name ].strftime ('%Y-%m-%d')})#line:111:fcv_list.append({'name': line.dd_field, 'value': self[line.field_id.name].strftime('%Y-%m-%d')})
        elif O0O0O0OOOOOO00OO0 .ttype =='datetime':#line:113:elif line.ttype == 'datetime':
            OO00O0000O0O0000O .append ({'name':O0O0O0OOOOOO00OO0 .dd_field ,'value':O0O00OO0O0O000000 [O0O0O0OOOOOO00OO0 .field_id .name ].strftime ('%Y-%m-%d %H:%M')})#line:114:fcv_list.append({'name': line.dd_field, 'value': self[line.field_id.name].strftime('%Y-%m-%d %H:%M')})
        elif O0O0O0OOOOOO00OO0 .ttype in ['char','text','integer','float','monetary','selection']:#line:116:elif line.ttype in ['char', 'text', 'integer', 'float', 'monetary', 'selection']:
            OO00O0000O0O0000O .append ({'name':O0O0O0OOOOOO00OO0 .dd_field ,'value':O0O00OO0O0O000000 [O0O0O0OOOOOO00OO0 .field_id .name ]})#line:117:fcv_list.append({'name': line.dd_field, 'value': self[line.field_id.name]})
        elif O0O0O0OOOOOO00OO0 .ttype =='one2many':#line:119:elif line.ttype == 'one2many':
            O00OOOO00O00O00O0 =O0O00OO0O0O000000 [O0O0O0OOOOOO00OO0 .field_id .name ]#line:120:model_lines = self[line.field_id.name]
            OOO0O0O0000OOO000 =list ()#line:121:fcv_line = list()   # 子表容器列表
            for O0OOOOO00OOOOOOO0 in O00OOOO00O00O00O0 :#line:122:for model_line in model_lines:      # 遍历对象示例列表
                O0O0OO0OOO0O000O0 =list ()#line:123:fcv_line_list = list()
                for OO00OO0OO00000OOO in O0O0O0OOOOOO00OO0 .list_ids :#line:124:for list_id in line.list_ids:   # 遍历配置项中的字段列表字段
                    if OO00OO0OO00000OOO .field_id .ttype =='many2one':#line:126:if list_id.field_id.ttype == 'many2one':
                        O0O0OOOO00OOO00OO =O0OOOOO00OOOOOOO0 [OO00OO0OO00000OOO .field_id .name ]#line:127:list_ding_field = model_line[list_id.field_id.name]
                        if OO00OO0OO00000OOO .is_dd_id :#line:128:if list_id.is_dd_id:
                            O0O0OO0OOO0O000O0 .append ({'name':OO00OO0OO00000OOO .dd_field ,'value':[O0O0OOOO00OOO00OO .ding_id ]})#line:129:fcv_line_list.append({'name': list_id.dd_field, 'value': [list_ding_field.ding_id]})
                        else :#line:130:else:
                            O0O0OO0OOO0O000O0 .append ({'name':OO00OO0OO00000OOO .dd_field ,'value':O0O0OOOO00OOO00OO .name_get ()})#line:131:fcv_line_list.append({'name': list_id.dd_field, 'value': list_ding_field.name_get()})
                    elif OO00OO0OO00000OOO .field_id .ttype =='many2many':#line:133:elif list_id.field_id.ttype == 'many2many':
                        OOO0O00O0OOOOO000 =O0OOOOO00OOOOOOO0 [OO00OO0OO00000OOO .field_id .name ]#line:134:list_id_models = model_line[list_id.field_id.name]
                        OO0O00O0OO0O0OOO0 =list ()#line:135:field_list = list()
                        for OO0O00O0OOO0OOO00 in OOO0O00O0OOOOO000 :#line:136:for list_id_model in list_id_models:
                            if OO00OO0OO00000OOO .is_dd_id :#line:138:if list_id.is_dd_id:
                                OO0O00O0OO0O0OOO0 .append (OO0O00O0OOO0OOO00 .ding_id )#line:139:field_list.append(list_id_model.ding_id)
                            else :#line:140:else:
                                OO0O00O0OO0O0OOO0 .append (OO0O00O0OOO0OOO00 .name )#line:141:field_list.append(list_id_model.name)
                        O0O0OO0OOO0O000O0 .append ({'name':OO00OO0OO00000OOO .dd_field ,'value':OO0O00O0OO0O0OOO0 })#line:142:fcv_line_list.append({'name': list_id.dd_field, 'value': field_list})
                    elif OO00OO0OO00000OOO .field_id .ttype =='date':#line:144:elif list_id.field_id.ttype == 'date':
                        O0O0OO0OOO0O000O0 .append ({'name':OO00OO0OO00000OOO .dd_field ,'value':O0OOOOO00OOOOOOO0 [OO00OO0OO00000OOO .field_id .name ].strftime ('%Y-%m-%d')})#line:145:fcv_line_list.append({'name': list_id.dd_field, 'value': model_line[list_id.field_id.name].strftime('%Y-%m-%d')})
                    elif OO00OO0OO00000OOO .field_id .ttype =='datetime':#line:147:elif list_id.field_id.ttype == 'datetime':
                        O0O0OO0OOO0O000O0 .append ({'name':OO00OO0OO00000OOO .dd_field ,'value':O0OOOOO00OOOOOOO0 [OO00OO0OO00000OOO .field_id .name ].strftime ('%Y-%m-%d %H:%M')})#line:148:fcv_line_list.append({'name': list_id.dd_field, 'value': model_line[list_id.field_id.name].strftime('%Y-%m-%d %H:%M')})
                    elif OO00OO0OO00000OOO .field_id .ttype in ['char','text','integer','float','monetary','selection']:#line:150:elif list_id.field_id.ttype in ['char', 'text', 'integer', 'float', 'monetary', 'selection']:
                        O0O0OO0OOO0O000O0 .append ({'name':OO00OO0OO00000OOO .dd_field ,'value':O0OOOOO00OOOOOOO0 [OO00OO0OO00000OOO .field_id .name ]})#line:151:fcv_line_list.append({'name': list_id.dd_field, 'value': model_line[list_id.field_id.name]})
                OOO0O0O0000OOO000 .append (O0O0OO0OOO0O000O0 )#line:152:fcv_line.append(fcv_line_list)
            OO00O0000O0O0000O .append ({'name':O0O0O0OOOOOO00OO0 .dd_field ,'value':OOO0O0O0000OOO000 })#line:153:fcv_list.append({'name': line.dd_field, 'value': fcv_line})
    return OO00O0000O0O0000O #line:154:return fcv_list
def get_originator_user_id (O00OO00OOOOOOOO00 ):#line:157:def get_originator_user_id(self):
    ""#line:162:"""
    OO00OOO00O00O0O00 =O00OO00OOOOOOOO00 .env ['hr.employee'].search ([('user_id','=',O00OO00OOOOOOOO00 .env .user .id )],limit =1 )#line:163:emp = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)], limit=1)
    if not OO00OOO00O00O0O00 :#line:164:if not emp:
        raise UserError ("当前登录用户无对应员工，请使用员工账号登录系统再发起审批。  *_*!!")#line:165:raise UserError("当前登录用户无对应员工，请使用员工账号登录系统再发起审批。  *_*!!")
    if not OO00OOO00O00O0O00 .ding_id :#line:166:if not emp.ding_id:
        raise UserError ("当前员工{}不存在钉钉ID，请使用钉钉下的员工进行提交,或则先将员工上传至钉钉后在操作。  *_*!!".format (OO00OOO00O00O0O00 .name ))#line:167:raise UserError("当前员工{}不存在钉钉ID，请使用钉钉下的员工进行提交,或则先将员工上传至钉钉后在操作。  *_*!!".format(emp.name))
    if not OO00OOO00O00O0O00 .department_id :#line:168:if not emp.department_id:
        raise UserError ("当前员工{}不存在钉钉部门，请维护后再发起审批。  *_*!!".format (OO00OOO00O00O0O00 .name ))#line:169:raise UserError("当前员工{}不存在钉钉部门，请维护后再发起审批。  *_*!!".format(emp.name))
    if not OO00OOO00O00O0O00 .department_id .ding_id :#line:170:if not emp.department_id.ding_id:
        raise UserError ("当前员工{}的部门{}不存在钉钉ID，请注意更正。  *_*!!".format (OO00OOO00O00O0O00 .name ,OO00OOO00O00O0O00 .department_id .name ))#line:171:raise UserError("当前员工{}的部门{}不存在钉钉ID，请注意更正。  *_*!!".format(emp.name, emp.department_id.name))
    return OO00OOO00O00O0O00 .ding_id ,OO00OOO00O00O0O00 .department_id .ding_id #line:172:return emp.ding_id, emp.department_id.ding_id
def _O000O0000OOOOOO0O (O000O0O0OOOO0OOO0 ):#line:175:def _restart_commit_approval(self):
    ""#line:180:"""
    O000O0O0OOOO0OOO0 .ensure_one ()#line:181:self.ensure_one()
    OOOOOO000O0O0O000 ,OOO0O0OOOOOO0O0O0 =approval_result (O000O0O0OOOO0OOO0 )#line:182:result, approval = approval_result(self)
    if OOOOOO000O0O0O000 .get ('errcode')!=0 :#line:183:if result.get('errcode') != 0:
        raise UserError ('重新提交失败，失败原因:{}'.format (OOOOOO000O0O0O000 .get ('errmsg')))#line:184:raise UserError('重新提交失败，失败原因:{}'.format(result.get('errmsg')))
    O0OOO0OOO0OOOO000 =O000O0O0OOOO0OOO0 ._name .replace ('.','_')#line:185:model_name = self._name.replace('.', '_')
    O000OO0O00O0OOOOO ="""UPDATE {} 
             SET 
                 dd_approval_state='{}', 
                 dd_doc_state='{}', 
                 dd_approval_result='load', 
                 dd_process_instance='{}' 
             WHERE 
                 id={}""".format (O0OOO0OOO0OOOO000 ,'approval','重新提交审批',OOOOOO000O0O0O000 .get ('process_instance_id'),O000O0O0OOOO0OOO0 .id )#line:193:id={}""".format(model_name, 'approval', '重新提交审批', result.get('process_instance_id'), self.id)
    O000O0O0OOOO0OOO0 ._cr .execute (O000OO0O00O0OOOOO )#line:194:self._cr.execute(sql)
    O000O0O0OOOO0OOO0 .message_post (body =u"已重新提交，请等待审批人审批！",message_type ='notification')#line:195:self.message_post(body=u"已重新提交，请等待审批人审批！", message_type='notification')
    return True #line:196:return True
setattr (Model ,'restart_commit_approval',_O000O0000OOOOOO0O )#line:199:setattr(Model, 'restart_commit_approval', _restart_commit_approval)
