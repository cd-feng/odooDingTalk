odoo.define('union_pay_search_bank_card_info', function (require) {
    "use strict";

    let AbstractAction = require('web.AbstractAction');
    let core = require('web.core');
    let QWeb = core.qweb;
    var rpc = require('web.rpc');

    let CustomPageDemo = AbstractAction.extend({
        template: 'UnionPaySearchBankCardInfo',
        events: {'click #search': '_onSubmitClick'},

        _onSubmitClick: function (e) {
            let self = this;
            let cardNo = self.$el.find('#cardNo').val();
            if (cardNo == null || cardNo == undefined || cardNo == '') {
                self.do_warn('警告', '银行卡号不能为空!');
                return false;
            }
            this.searchBankCardInfo(cardNo);
        },
        searchBankCardInfo: function (cardNo) {
            let self = this;
            var def = rpc.query({
                model: 'union.pay.search.bank.card.info',
                method: 'search_bank_card_info',
                args: [cardNo],
            }).then(function (data) {
                // Result
                console.log(data)
                self.setSearchResult(data)
            });
        },

        setSearchResult: function (result_data) {
            let self = this;
            self.$el.find('#issNm').html(result_data.issNm);
            self.$el.find('#cardMedia').html(result_data.cardMedia);
            self.$el.find('#cardLvl').html(result_data.cardLvl);
            self.$el.find('#cardClass').html(result_data.cardClass);
            self.$el.find('#issInsId').html(result_data.issInsId);
            self.$el.find('#hdqrsInsCnNm').html(result_data.hdqrsInsCnNm);
            self.$el.find('#cardProd').html(result_data.cardProd);
            self.$el.find('#issAbbr').html(result_data.issAbbr);
            self.$el.find('#cardCata').html(result_data.cardCata);
            self.$el.find('#cardAttr').html(result_data.cardAttr);
            self.$el.find('#hdqrsInsCnAbbr').html(result_data.hdqrsInsCnAbbr);
            self.$el.find('#cardBrand').html(result_data.cardBrand);
        }
    });


    core.action_registry.add('union_pay_search_bank_card_info', CustomPageDemo);
    return CustomPageDemo;
});