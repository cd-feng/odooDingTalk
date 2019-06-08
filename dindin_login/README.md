# 钉钉免登、扫码登录功能说明

## 扫码登录

1. 登录钉钉开发者后台，在移动接入作用中，新建一个`登录`应用
2. 填写基本信息，其中回调域名格式为：

``` http://ip:port/web/action_login ```  
> ip为域名，port为端口，/web/action_login为固定格式

### 免登设置：

- 需要到钉钉开发平台配置H5微应用，创建应用>应用信息>查看详情>修改应用首页地址为：

``` http://ip:port/dingding/auto/login/in  ```

>  /dingding/auto/login/in 为固定格式