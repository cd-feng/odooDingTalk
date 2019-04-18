# Odoo平台集成钉钉应用

**前言**：

> 本应用主要基于OdooERP开发，支持社区版和企业版，当前版本仅支持12版本，github地址： https://github.com/suxuefeng20/odooDinDin  可自行下载后根据实际情况进行增加完善和调整功能。
>
> 在使用本模块前，请先将钉钉中你创建的E应用或微应用权限放开和配置出口ip，得到钉钉应用的 **AppKey**和 **AppSecret**， 至于钉钉后台中的配置请参照：https://open-doc.dingtalk.com/microapp/bgb96b

至v1.5版本开始，将依赖OA协同办公模块，地址： [oa协同办公](https://github.com/suxuefeng20/Odoo12-OA)

博客地址： https://sxfblog.com/index.php/archives/371.html

主要功能：**

- 基础配置  (v1.0)

- 系统参数列表   

  > 存放钉钉提供的外部接口地址和token值等 (v1.0)

- 手动/自动同步基础信息   (v1.0)

  > 手动从钉钉中同步用户、部门、联系人等信息，若需要自动同步，则需要按照下面提供的自动参数列表进行配置

- 通讯录管理(用户、部门、联系人) (v1.0)

  > 可实现在odoo中创建、删除、修改（员工、部门、联系人）时，自动将信息传递至钉钉，做到实时将odoo的信息与钉钉同步；该功能需在设置项中灵活开启。

- 消息通知(v1.1)

  > 1. **工作通知消息**：是以企业工作通知会话中某个微应用的名义通知到员工个人，例如审批通知、任务通知、工作项通知等。
  > 2. **群消息**：向钉钉群发送消息，仅限企业内部开发使用。
  > 3. **普通消息**：员工个人在使用应用时，通过界面操作的方式把消息发送到群里或其他人，例如发送日志的场景。

- 公告(v1.2)

  > 获取用户公告数据

- 日志(v1.3)

- 签到(v1.3)

- 考勤(v1.4)

- 待办事项(v1.5)

- 审批(v2.0)

- 智能人事(v2.0)

- 钉钉运动(v1.5)



**自动同步参数设置列表****或使用钉钉回调实时更新**

| 动作名称       | 模型                          | Python代码                                                   |
| :------------- | ----------------------------- | :----------------------------------------------------------- |
| 同步用户       | dindin.synchronous.employee   | env['dindin.synchronous.employee'].start_synchronous_employee() |
| 同步部门       | dindin.synchronous.department | env['dindin.synchronous.department'].start_synchronous_department() |
| 同步联系人标签 | dindin.synchronous.extcontact | env['dindin.synchronous.extcontact'].start_synchronous_category() |
| 同步联系人列表 | dindin.synchronous.extcontact | env['dindin.synchronous.extcontact'].start_synchronous_partner |
|                |                               |                                                              |

### 常见问题：

- **钉钉扫码登录后会报错：Internal Server Error**

> 1.一般这样的问题不是程序出错，请检查钉钉->设置中的扫码登录AppId、扫码登录appsecret。
>
> 2.检查钉钉后台中的。移动接入应用并配置好回调地址(即odoo地址) http://ip:port/web/action_login
>
> Ip:port为对应的IP地址和端口    /web/action_login 为回调函数。

- **仪表盘：获取公告失败,详情为:无效的USERID、代审批数、公告数**

  > 这个错误通常情况是在刚安装完成时出现的，但不影响使用，安装完成后在设置->钉钉设置中，配置好钉钉API应用信息。手动或自动同步钉钉上的员工数据到odoo中后就不会出现这样的问题

- **拉取考勤组成员的时候提示： 考勤组有更新,请先拉取最新的考勤组!**

  > 那就点击 拉取考勤组成员 旁的 拉取考勤组即可

- **考勤组成员列表无法更新**

  > 钉钉未提供odoo上更新考勤成员的api。故无法自动推送到钉钉服务器

-  **协同办公 提交审批后，已通过钉钉审批单odoo中未更新状态**

> 1. 检查odoo钉钉中的审批模板是否存在
>
> 2. 检查odoo钉钉中审批单据关联是否正确
>
> 3. 重要： 钉钉回调管理是否配置正确并已注册
>
>    满足以上三点即可正常使用审批同步

- **财务审批中的表单需要自动生成凭证(日记账分录)，则需要配置凭证模板，位置：协同办公->设置->凭证模板**

  **若看不到的请检查权限**



