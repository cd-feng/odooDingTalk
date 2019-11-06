window.onload = function () {
    var ua = window.navigator.userAgent.toLowerCase();
// 检测UA
    if (ua.match(/DingTalk/i) == "dingtalk") {
        // 获取CorpId
        var corpId = document.querySelector("#corp-id").innerHTML.trim();
        // 调用钉钉JSAPI
        dd.runtime.permission.requestAuthCode({
            corpId,
            onSuccess: function (result) {
                window.location.replace("/web/dingtalk/auto/login/action?authCode=" + result.code);
            },
            onFail: function (err) {
                alert("系统错误，请使用账号密码登陆。");
                window.location.replace("/web/login");
            }
        })
    } else {
        window.location.replace("/web/login");
    }
}