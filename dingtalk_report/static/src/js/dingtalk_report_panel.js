odoo.define('dingtalk.report.panel.client', function (require) {
"use strict";

    var AbstractAction = require('web.AbstractAction');
    var core = require('web.core');

    var DingtalkReportPanel = AbstractAction.extend({
        template: 'dingtalk_report.DingtalkReportPanelTemplate',
        // 初始化
        init: function (parent, action) {
            this._super(parent, action);
            this.url = action.params.url;
        },

        start: function () {
            this._super();
            this.get_dingtalk_report_count();
            this.get_employee_report_count();
            // this.get_employee_report_footer();
        },

        get_dingtalk_report_count: function(){
            let self = this;
            this._rpc({
                model: 'dingtalk.report.report',
                method: 'get_report_count',
                args: [],
            }).then(function (result) {
                self.set_report_count(result);
            })
        },

        set_report_count: function(result){
            let myChart = echarts.init(self.$('#dingtalk_report_count_div')[0], 'light');
            let option = {
                title : {
                    text: '按类型统计数量',
                    subtext: '饼图',
                    x:'center'
                },
                tooltip : {
                    trigger: 'item',
                    formatter: "{a} <br/>{b} : {c} ({d}%)"
                },
                legend: {
                    orient: 'vertical',
                    left: 'left',
                    data: result.category_list
                },
                series : [
                    {
                        name: '日志数量',
                        type: 'pie',
                        radius : '55%',
                        center: ['50%', '60%'],
                        data: result.category_dict,
                        itemStyle: {
                            emphasis: {
                                shadowBlur: 10,
                                shadowOffsetX: 0,
                                shadowColor: 'rgba(0, 0, 0, 0.5)'
                            }
                        }
                    }
                ]
            };
            myChart.setOption(option);

        },

        get_employee_report_count: function () {
            let self = this;
            this._rpc({
                model: 'dingtalk.report.report',
                method: 'get_employee_report_count',
                args: [],
            }).then(function (result) {
                console.log(result);
                self.set_employee_count(result);
            })
        },

        set_employee_count: function(result){
            let self = this;
            let myChart = echarts.init(self.$('#dingtalk_report_emp_count_div')[0], 'light');
            let dataAxis = result.emp_list;
            let data = result.emp_conut;
            let yMax = result.sum_count;
            let dataShadow = [];

            for (let i = 0; i < data.length; i++) {
                dataShadow.push(yMax);
            }
            let option = {
                title: {
                    text: '按员工分类统计日志数',
                    subtext: '点击柱子或者两指在触屏上滑动能够自动缩放~'
                },
                xAxis: {
                    data: dataAxis,
                    axisLabel: {
                        inside: true,
                        textStyle: {
                            color: 'red'
                        }
                    },
                    axisTick: {
                        show: false
                    },
                    axisLine: {
                        show: false
                    },
                    z: 10
                },
                yAxis: {
                    axisLine: {
                        show: false
                    },
                    axisTick: {
                        show: false
                    },
                    axisLabel: {
                        textStyle: {
                            color: '#999'
                        }
                    }
                },
                dataZoom: [
                    {
                        type: 'inside'
                    }
                ],
                series: [
                    {
                        type: 'bar',
                        itemStyle: {
                            normal: {color: 'rgba(0,0,0,0.05)'}
                        },
                        barGap:'-100%',
                        barCategoryGap:'40%',
                        data: dataShadow,
                        animation: false
                    },
                    {
                        type: 'bar',
                        itemStyle: {
                            normal: {
                                color: new echarts.graphic.LinearGradient(
                                    0, 0, 0, 1,
                                    [
                                        {offset: 0, color: '#83bff6'},
                                        {offset: 0.5, color: '#188df0'},
                                        {offset: 1, color: '#188df0'}
                                    ]
                                )
                            },
                            emphasis: {
                                color: new echarts.graphic.LinearGradient(
                                    0, 0, 0, 1,
                                    [
                                        {offset: 0, color: '#2378f7'},
                                        {offset: 0.7, color: '#2378f7'},
                                        {offset: 1, color: '#83bff6'}
                                    ]
                                )
                            }
                        },
                        data: data
                    }
                ]
            };

            let zoomSize = 6;
            myChart.on('click', function (params) {
                console.log(dataAxis[Math.max(params.dataIndex - zoomSize / 2, 0)]);
                myChart.dispatchAction({
                    type: 'dataZoom',
                    startValue: dataAxis[Math.max(params.dataIndex - zoomSize / 2, 0)],
                    endValue: dataAxis[Math.min(params.dataIndex + zoomSize / 2, data.length - 1)]
                });
            });
            myChart.setOption(option);
        },
        
        get_employee_report_footer: function () {
            let self = this;
            this._rpc({
                model: 'dingtalk.report.report',
                method: 'get_report_count',
                args: [],
            }).then(function (result) {
                self.set_employee_report_footer(result);
            })
        },
        
        set_employee_report_footer: function (result) {
            let myChart = echarts.init(self.$('#dingtalk_report_footer_div')[0], 'light');
            let option = {
                title: {
                    text: '多雷达图'
                },
                tooltip: {
                    trigger: 'axis'
                },
                legend: {
                    x: 'center',
                    data:['某软件','某主食手机','某水果手机','降水量','蒸发量']
                },
                radar: [
                    {
                        indicator: [
                            {text: '品牌', max: 100},
                            {text: '内容', max: 100},
                            {text: '可用性', max: 100},
                            {text: '功能', max: 100}
                        ],
                        center: ['25%','40%'],
                        radius: 80
                    },
                    {
                        indicator: [
                            {text: '外观', max: 100},
                            {text: '拍照', max: 100},
                            {text: '系统', max: 100},
                            {text: '性能', max: 100},
                            {text: '屏幕', max: 100}
                        ],
                        radius: 80,
                        center: ['50%','60%'],
                    },
                    {
                        indicator: (function (){
                            var res = [];
                            for (var i = 1; i <= 12; i++) {
                                res.push({text:i+'月',max:100});
                            }
                            return res;
                        })(),
                        center: ['75%','40%'],
                        radius: 80
                    }
                ],
                series: [
                    {
                        type: 'radar',
                         tooltip: {
                            trigger: 'item'
                        },
                        itemStyle: {normal: {areaStyle: {type: 'default'}}},
                        data: [
                            {
                                value: [60,73,85,40],
                                name: '某软件'
                            }
                        ]
                    },
                    {
                        type: 'radar',
                        radarIndex: 1,
                        data: [
                            {
                                value: [85, 90, 90, 95, 95],
                                name: '某主食手机'
                            },
                            {
                                value: [95, 80, 95, 90, 93],
                                name: '某水果手机'
                            }
                        ]
                    },
                    {
                        type: 'radar',
                        radarIndex: 2,
                        itemStyle: {normal: {areaStyle: {type: 'default'}}},
                        data: [
                            {
                                name: '降水量',
                                value: [2.6, 5.9, 9.0, 26.4, 28.7, 70.7, 75.6, 82.2, 48.7, 18.8, 6.0, 2.3],
                            },
                            {
                                name:'蒸发量',
                                value:[2.0, 4.9, 7.0, 23.2, 25.6, 76.7, 35.6, 62.2, 32.6, 20.0, 6.4, 3.3]
                            }
                        ]
                    }
                ]
            };
            myChart.setOption(option);
        }
    });

    core.action_registry.add('dingtalk_report_panel', DingtalkReportPanel);
    return DingtalkReportPanel;
});
