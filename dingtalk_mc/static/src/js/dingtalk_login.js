let prot = window.location.protocol;
let host = window.location.host;

$(function(){
    $("#env_company").append("<option value='no'>请选择您的公司</option>");
    $.ajax({
        async: false,
        url: "/web/dingtalk/mc/get/companys",
        success: function (data) {
            let company_list = data['company_list']
            for(let x=0; x<company_list.length; x++) {
                let company = company_list[x]
                $("#env_company").append("<option value="+company['id']+ ">"+ company['name'] + "</option>")
            }
        },
        dataType:'json'
    });
    $('#env_company').change(function(){
        let company_val = $(this).children('option:selected').val();
        if(company_val === 'no'){
            return false;
        }
        // 加载二维码
        let url_target = get_decode_url(company_val);
        if(url_target){
            console.log(url_target);
            addDDLogin(url_target);
        }
        return false;
    });
});

function addDDLogin(url_target){
    let obj = DDLogin({
        id: "login_container",
        goto: encodeURIComponent(url_target),
        style: "border:none;background-color:#FFFFFF;",
        href: "",
        width: "260",
        height: "300"
    });
    let hanndleMessage = function (event) {
        let origin = event.origin;
        if (origin == "https://login.dingtalk.com") { //判断是否来自ddLogin扫码事件。
            let loginTmpCode = event.data;            //拿到loginTmpCode后就可以在这里构造跳转链接进行跳转了
            console.log(">>>:loginTmpCode", loginTmpCode);
            window.location.href = url_target + "&loginTmpCode=" + loginTmpCode;
        }
    };
    if (typeof window.addEventListener != 'undefined') {
        window.addEventListener('message', hanndleMessage, false);
    } else if (typeof window.attachEvent != 'undefined') {
        window.attachEvent('onmessage', hanndleMessage);
    }
}

/**
 * 获取服务器拼接的访问url
 * @param company_val
 * @returns {string}
 */
function get_decode_url(company_val) {
    let url_target = '';
    $.ajax({
        async: false,
        url: "/web/dingtalk/mc/get_url",
        data: {"local_url": prot + "//" + host, "company_id": company_val},
        success: function (data) {
            if(data.state === false){
                alert(data.error);
                return false;
            }
            url_target = data.encode_url;
        },
        dataType: "json"
    });
    return url_target
}



