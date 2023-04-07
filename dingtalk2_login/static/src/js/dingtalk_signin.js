
$(function() {

    // dd.ready参数为回调函数，在环境准备就绪时触发，jsapi的调用需要保证在该回调函数触发后调用，否则无效。
    dd.ready(function() {
        // 获取CorpId
        let corpId = document.querySelector("#corp-id").innerHTML.trim();
        dd.runtime.permission.requestAuthCode({
            corpId: corpId,
            onSuccess: function (result) {
                $("#message-result").html("身份已确认! 正在执行登陆...");
                window.location.replace(`/dingtalk/signin/action?authCode=${result.code}&corpId=${corpId}`);
            },
            onFail: function(err) {
                $("#message-result").attr("class", "alert alert-danger").html("身份校验失败！原因：" + err);
            }
        });

    });
})
