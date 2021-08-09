let prot = window.location.protocol;
let host = window.location.host;

$(function() {
    dd.ready(function() {
        // 获取CorpId
        var corpId = document.querySelector("#corp-id").innerHTML.trim();
        dd.runtime.permission.requestAuthCode({
            corpId: corpId, // 企业id
            onSuccess: function (result) {
                $("#message-result").html("身份已确认! 正在执行登陆...");
                window.location.replace("/web/dingtalk/auto/login/action?authCode=" + result.code);
            },
            onFail: function(err) {
                $("#message-result").attr("class", "alert alert-danger").html("身份校验失败！原因：" + err);
            }
        });
    });
})
