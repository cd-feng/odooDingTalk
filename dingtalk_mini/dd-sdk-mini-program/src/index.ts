/** 钉钉全局变量 */
declare var dd: any;

export default {
  alert,
  confirm,
  getAuthCode,
  httpRequest,
  redirectTo,
  getSystemInfo,
  getSystemInfoSync,
  createCanvasContext,
  createSelectorQuery,
  showToast,
  showLoading,
  hideLoading,
  showActionSheet,
  uploadFile,
  downloadFile,
  navigateTo,
  navigateBack,
  reLaunch,
  setNavigationBar,
  switchTab,
  datePicker,
  createAnimation,
  hideKeyboard,
  pageScrollTo,
  complexChoose,
  chooseDepartments,
  createGroupChat,
  choosePhonebook,
  chooseExternalUsers,
  editExternalUser,
  chooseUserFromList,
  openLocation,
  setStorage,
  setStorageSync,
  getStorage,
  getStorageSync,
  removeStorage,
  removeStorageSync,
  getNetworkType,
  getClipboard,
  setClipboard,
  vibrate,
  chooseImage,
  previewImage,
  saveImage,
  compressImage,
  getImageInfo,
  getRecorderManager,
  getBackgroundAudioManager,
  chooseVideo,
  createDing,
  callUsers,
  showCallMenu,
  checkBizCall,
  pay,
  saveFileToDingTalk,
  previewFileInDingTalk,
  uploadAttachmentToDingTalk,
  chooseDingTalkDir,
  chooseChatForNormalMsg,
  chooseChat,
  openChatByChatId,
  openChatByUserId,
  connectSocket,
  onSocketOpen,
  offSocketOpen,
  onSocketError,
  offSocketError,
  sendSocketMessage,
  onSocketMessage,
  offSocketMessage,
  closeSocket,
  onSocketClose,
  offSocketClose,
};

/** 毫秒 */
type Millisecond = number;
/** 秒 */
type Second = number;

interface CommonObject {
  [key: string]: string;
}

/**
 * reject 包裹函数, 保证最终处理的为 Error 类型
 * @param r Promise 的 reject 函数
 */
const rejectWarp = (r: (reason?: any) => void) => {
  return (err: unknown) => {
    if (err instanceof Error) {
      r(err);
      return;
    }
    if (typeof err === 'string') {
      r(new Error(err));
      return;
    }
    r(new Error(JSON.stringify(err)));
  };
};

/**
 * 获取钉钉 SDK 相关信息
 * {@link https://ding-doc.dingtalk.com/doc#/dev/xdu3pr 获取基础库版本号}
 */
export function getDingtalkSDK(): {
  /** 是否在钉钉环境下 */
  dd: boolean;
  /** 钉钉小程序平台阶段 */
  stage?: 'v1' | 'v2';
  /** 钉钉 SDK 版本号 */
  version?: string;
} {
  if (typeof dd === 'undefined') {
    return { dd: false };
  }
  if (dd.ExtSDKVersion) {
    return { dd: true, stage: 'v2', version: dd.ExtSDKVersion };
  }
  if (dd.SDKVersion) {
    return { dd: true, stage: 'v1', version: dd.SDKVersion };
  }
  console.error({ dd });
  throw new Error('预期之外的平台');
}

/**
 * 警告框
 * {@link https://ding-doc.dingtalk.com/doc#/dev/ui-feedback 界面=>交互反馈}
 */
export function alert({
  title,
  content,
  buttonText,
}: {
  /** 标题 */
  title: string;
  /** 内容 */
  content: string;
  /** 按钮文字 */
  buttonText?: string;
}) {
  return new Promise((resolve, reject) => {
    dd.alert({
      title,
      content,
      buttonText,
      success: resolve,
      fail: rejectWarp(reject),
    });
  });
}

/**
 * 确认框
 * {@link https://ding-doc.dingtalk.com/doc#/dev/ui-feedback 界面=>交互反馈}
 */
export function confirm(opt: {
  /** confirm 框的标题 */
  title: string;
  /** confirm 框的内容 */
  content: string;
  /** 确认按钮文字 */
  confirmButtonText?: string;
  /** 取消按钮文字 */
  cancelButtonText?: string;
}): Promise<{ confirm: boolean }> {
  return new Promise((resolve, reject) => {
    dd.confirm({
      ...opt,
      success: resolve,
      fail: rejectWarp(reject),
    });
  });
}

/**
 * 显示一个弱提示，可选择多少秒之后消失
 * {@link https://ding-doc.dingtalk.com/doc#/dev/ui-feedback 界面=>交互反馈}
 * @param content 文字内容
 * @param type toast 类型，展示相应图标，默认 none
 * 支持 success / fail / exception / none。其中 exception 类型必须传文字信息
 * @param duration 显示时长，单位为 ms，默认 2000。按系统规范，
 * android只有两种(<=2s >2s)
 */
export function showToast({
  content,
  type = 'none',
  duration = 2000,
}: {
  content?: string;
  type?: 'success' | 'fail' | 'exception' | 'none';
  duration?: Millisecond;
} = {}) {
  return new Promise((resolve, reject) => {
    dd.showToast({
      content,
      type,
      duration,
      success: resolve,
      fail: rejectWarp(reject),
    });
  });
}

/**
 * 显示加载提示
 * {@link https://ding-doc.dingtalk.com/doc#/dev/ui-feedback 界面=>交互反馈}
 * @param content loading的文字内容
 * @param delay 延迟显示，单位 ms，默认 0
 * 如果在此时间之前调用了 dd.hideLoading 则不会显示
 */
export function showLoading({
  content,
  delay = 0,
}: {
  content?: string;
  delay?: Millisecond;
} = {}) {
  return new Promise((resolve, reject) => {
    dd.showLoading({
      content,
      delay,
      success: resolve,
      fail: rejectWarp(reject),
    });
  });
}

/**
 * 隐藏加载提示
 * {@link https://ding-doc.dingtalk.com/doc#/dev/ui-feedback 界面=>交互反馈}
 */
export function hideLoading() {
  return dd.hideLoading();
}

/**
 * 显示操作菜单
 * {@link https://ding-doc.dingtalk.com/doc#/dev/ui-feedback 界面=>交互反馈}
 * @param title 菜单标题
 * @param items 菜单按钮文字数组
 * @param cancelButtonText 取消按钮文案。注：Android平台此字段无效，不会显示取消按钮
 */
export function showActionSheet(opt: {
  title?: string;
  items: Array<string>;
  cancelButtonText?: string;
}): Promise<{
  /** 被点击的按钮的索引，从0开始。点击取消或蒙层时返回 -1 */
  index: number;
}> {
  return new Promise((resolve, reject) => {
    dd.showActionSheet({
      ...opt,
      success: resolve,
      fail: rejectWarp(reject),
    });
  });
}

/**
 * 获取免登 code
 */
export function getAuthCode() {
  return new Promise((resolve, reject) => {
    dd.getAuthCode({
      success(res: any) {
        resolve(res.authCode);
      },
      fail: rejectWarp(reject),
    });
  });
}

/**
 * 发送网络请求
 * {@link https://opendocs.alipay.com/mini/00hxw8}
 * 钉钉小程序暂时不支持 my.request, 目前使用 dd.httpRequest 替代.
 */
export const request = httpRequest;

/**
 * httpRequest 支持的请求方法
 */
export type HttpRequestMethod = 'GET' | 'POST';

/**
 * httpRequest 返回信息格式转换
 */
export type HttpRequestResFormat = 'json' | 'text' | 'base64';

/**
 * 发送网络请求
 * {@link https://ding-doc.dingtalk.com/doc#/dev/httprequest 网络=>发送网络请求}
 * @param url 目标服务器url
 * @param headers 设置请求的 HTTP 头
 * 默认 {'Content-Type': 'application/x-www-form-urlencoded'}
 * @param method 默认 GET，目前文档只说了支持 GET，POST
 * @param dataType 默认 JSON
 * @param timeout HTTP 请求超时时间, 默认 30,000 毫秒
 * @param data  请求参数
 */
export function httpRequest(opt: {
  url: string;
  method?: HttpRequestMethod;
  dataType?: HttpRequestResFormat;
  timeout?: Millisecond;
  headers?: any;
  data?: CommonObject | string;
}) {
  let { headers = {}, data, ...rest } = opt;
  if (!headers['Content-Type']) {
    headers['Content-Type'] = 'application/json';
    if (typeof data !== 'string') {
      data = JSON.stringify(data);
    }
  }
  return new Promise((resolve, reject) => {
    dd.httpRequest({
      headers,
      data,
      success: (res: {
        data: string | object;
        status: number;
        headers: object;
      }) => {
        res.headers = getHeaders(res.headers);
        resolve(res);
      },
      fail: rejectWarp(reject),
      ...rest,
    });
  });
}

/**
 * 上传本地资源到开发者服务器
 * {@link https://ding-doc.dingtalk.com/doc#/dev/frd69q 网络=>上传下载}
 * @param url 开发者服务器地址
 * @param filePath 要上传文件资源的本地定位符
 * @param fileName 文件名，即对应的 key,
 * 开发者在服务器端通过这个 key 可以获取到文件二进制内容
 * @param fileType 文件类型，image / video
 * @param header HTTP 请求 Header
 * @param formData HTTP 请求中其他额外的 form 数据
 */
export function uploadFile(opt: {
  url: string;
  filePath: string;
  fileName: string;
  fileType: string;
  header?: any;
  formData?: any;
}): Promise<{
  /** 服务器返回的数据 */
  data: string;
  /**  HTTP 状态码 */
  statusCode: string;
  /** 服务器返回的 header */
  header: any;
}> {
  return new Promise((resolve, reject) => {
    dd.uploadFile({
      ...opt,
      success: resolve,
      fail: rejectWarp(reject),
    });
  });
}

/**
 * 下载文件资源到本地
 * {@link https://ding-doc.dingtalk.com/doc#/dev/frd69q 网络=>上传下载}
 * @param url 下载文件地址
 * @param header HTTP 请求 Header
 */
export function downloadFile(opt: {
  url: string;
  header?: any;
}): Promise<string> {
  return new Promise((resolve, reject) => {
    dd.downloadFile({
      ...opt,
      success(res: any) {
        resolve(res.filePath);
      },
      fail: rejectWarp(reject),
    });
  });
}

/**
 * 专为处理钉钉 httpRequest 问题
 */
function getHeaders(origin: any) {
  if (Array.isArray(origin)) {
    const obj = {};
    for (const v of origin) {
      Object.assign(obj, v);
    }
    return obj;
  }
  return origin;
}

/**
 * 获取系统信息
 * {@link https://ding-doc.dingtalk.com/doc#/dev/system-info 设备=>系统信息}.
 */
export function getSystemInfo(): Promise<{
  /** 手机型号 */
  model: string;
  /** 设备像素比 */
  pixelRatio: number;
  /** 窗口宽度 */
  windowWidth: number;
  /** 窗口高度 */
  windowHeight: number;
  /** 钉钉设置的语言 */
  language: string;
  /** 钉钉版本号 */
  version: string;
  /** 设备磁盘容量 */
  storage: string;
  /** 当前电量百分比 */
  currentBattery: string;
  /** 系统版本 */
  system: string;
  /** 系统名：Android，iOS */
  platform: string;
  /** 屏幕宽度 */
  screenWidth: number;
  /** 屏幕高度 */
  screenHeight: number;
  /** 手机品牌 */
  brand: string;
  /** 用户设置字体大小 */
  fontSizeSetting: string;
}> {
  return new Promise((resolve, reject) => {
    dd.getSystemInfo({
      success(res: any) {
        resolve(res);
      },
      fail: rejectWarp(reject),
    });
  });
}

/**
 * 获取系统信息
 * 返回值同 getSystemInfo success 回调参数
 * {@link https://ding-doc.dingtalk.com/doc#/dev/system-info 设备=>系统信息}.
 */
export function getSystemInfoSync() {
  return dd.getSystemInfoSync();
}

/**
 * 创建 canvas 绘图上下文
 * {@link https://ding-doc.dingtalk.com/doc#/dev/ui-canvas 界面=>画布}.
 * @param canvasId 定义在 上的 id
 */
export function createCanvasContext(canvasId: string) {
  return dd.createCanvasContext(canvasId);
}

interface RectInfo {
  x: number;
  y: number;
  width: number;
  height: number;
  top: number;
  right: number;
  bottom: number;
  left: number;
}

type SelectorQueryInfo =
  | null
  | RectInfo
  | RectInfo[]
  | { scrollTop: number; scrollLeft: number }
  | { width: number; height: number };

interface SelectorQuery {
  /** 选择当前第一个匹配选择器的节点 */
  select: (id: string) => SelectorQuery;
  /** 选择所有匹配选择器的节点 */
  selectAll: (id: string) => SelectorQuery;
  /** 选择窗口对象 */
  selectViewport: () => SelectorQuery;
  /** 位置信息 将当前选择节点的信息放入查询结果 */
  boundingClientRect: () => SelectorQuery;
  /** 滚动信息 将当前选择节点的信息放入查询结果 */
  scrollOffset: () => SelectorQuery;
  exec: (callback: (data: SelectorQueryInfo[]) => void) => void;
}

/**
 * 获取一个节点查询对象 SelectorQuery
 * {@link https://ding-doc.dingtalk.com/doc#/dev/selector-query 界面=>节点查询}.
 */
export function createSelectorQuery(): SelectorQuery {
  return dd.createSelectorQuery();
}

/**
 * 关闭当前页面，跳转到应用内的某个指定页面
 * @param url 需要跳转的应用内非 tabBar 的目标页面路径,路径后可以带参数。
 * 参数规则如下：路径与参数之间使用?分隔，参数键与参数值用=相连，不同参数必须用&分隔；
 * 如path?key1=value1&key2=value2
 */
export function redirectTo(url: string) {
  return new Promise((resolve, reject) => {
    dd.redirectTo({
      url,
      success: resolve,
      fail: rejectWarp(reject),
    });
  });
}

/**
 * 保留当前页面，跳转到应用内的某个指定页面，可以使用 dd.navigateBack 返回到原来页面。
 * 注意：页面最大深度为5，即可连续调用 5 次 navigateTo
 * {@ink https://ding-doc.dingtalk.com/doc#/dev/ui-navigate 界面=>导航栏}
 * @param url 需要跳转的应用内非 tabBar 的目标页面路径 ,路径后可以带参数。
 * 参数规则如下：路径与参数之间使用?分隔，参数键与参数值用=相连，不同参数必须用&分隔；
 * 如 path?key1=value1&key2=value2
 */
export function navigateTo(url: string) {
  return new Promise((resolve, reject) => {
    dd.navigateTo({
      url,
      success: resolve,
      fail: rejectWarp(reject),
    });
  });
}

/**
 * 关闭当前页面，返回上一级或多级页面。
 * 可通过 getCurrentPages 获取当前的页面栈信息，决定需要返回几层。
 * {@ink https://ding-doc.dingtalk.com/doc#/dev/ui-navigate 界面=>导航栏}
 * @param delta 默认值1，返回的页面数，
 * 如果 delta 大于现有打开的页面数，则返回到当前页面栈最顶部的页
 */
export function navigateBack(delta = 1) {
  return new Promise((resolve, reject) => {
    dd.navigateBack({
      delta,
      success: resolve,
      fail: rejectWarp(reject),
    });
  });
}

/**
 * 关闭当前所有页面，跳转到应用内的某个指定页面。
 * {@ink https://ding-doc.dingtalk.com/doc#/dev/ui-navigate 界面=>导航栏}
 * @param url 页面路径。如果页面不为 tabbar 页面则路径后可以带参数。
 * 参数规则如下：路径与参数之间使用?分隔，参数键与参数值用=相连，不同参数必须用&分隔；
 * 如path?key1=value1&key2=value2
 */
export function reLaunch(url: string) {
  return new Promise((resolve, reject) => {
    dd.reLaunch({
      url,
      success: resolve,
      fail: rejectWarp(reject),
    });
  });
}

/**
 * 设置导航栏文字及样式
 * {@ink https://ding-doc.dingtalk.com/doc#/dev/ui-navigate 界面=>导航栏}
 * @param title 导航栏标题
 * @param backgroundColor 导航栏背景色，支持十六进制颜色值
 * @param reset 是否重置导航栏为钉钉默认配色，默认 false
 */
export function setNavigationBar({
  title,
  backgroundColor,
  reset = false,
}: {
  title?: string;
  backgroundColor?: string;
  reset?: boolean;
} = {}) {
  return new Promise((resolve, reject) => {
    dd.setNavigationBar({
      title,
      backgroundColor,
      reset,
      success: resolve,
      fail: rejectWarp(reject),
    });
  });
}

/**
 * 跳转到指定 tabBar 页面，并关闭其他所有非 tabBar 页面。
 * {@link https://ding-doc.dingtalk.com/doc#/dev/ui-tabbar 界面=>TabBar}
 * @param url 跳转的 tabBar 页面的路径（需在 app.json 的 tabBar 字段定义的页面）。
 * 注意：路径后不能带参数
 */
export function switchTab(url: string) {
  return new Promise((resolve, reject) => {
    dd.switchTab({
      url,
      success: resolve,
      fail: rejectWarp(reject),
    });
  });
}

/**
 * 打开日期选择列表
 * {@link https://ding-doc.dingtalk.com/doc#/dev/ui-date 界面=>选择日期}
 * @param format 返回的日期格式， 1.yyy-MM-dd（默认） 2.HH:mm
 *  3.yyyy-MM-dd HH:mm 4.yyyy-MM
 * @param currentDate 初始选择的日期时间，默认当前时间
 */
export function datePicker(opt: {
  format?: string;
  currentDate?: string;
}): Promise<string> {
  return new Promise((resolve, reject) => {
    dd.datePicker({
      ...opt,
      success(res: any) {
        resolve(res.data);
      },
      fail: rejectWarp(reject),
    });
  });
}

/**
 * 下拉刷新操作
 * {@link https://ding-doc.dingtalk.com/doc#/dev/pulldown 界面=>下拉刷新}
 * 在 Page 中自定义 onPullDownRefresh 函数，可以监听该页面用户的下拉刷新事件。
 * 需要在页面对应的 .json 配置文件中配置 "pullRefresh": true 选项，
 * 才能开启下拉刷新事件。
 */
export function onPullDownRefresh() {
  console.log('onPullDownRefresh', new Date());
}

/**
 * 停止当前页面的下拉刷新
 * {@link https://ding-doc.dingtalk.com/doc#/dev/pulldown 界面=>下拉刷新}
 * 当处理完数据刷新后，调用 dd.stopPullDownRefresh 可以停止当前页面的下拉刷新。
 */
export function stopPullDownRefresh() {
  return dd.stopPullDownRefresh();
}

/**
 * 创建动画实例animation。调用实例的方法来描述动画，
 * 最后通过动画实例的export方法将动画数据导出并传递给组件的animation属性
 * {@link https://ding-doc.dingtalk.com/doc#/dev/ui-animation 界面=>动画}
 * @param duration 动画的持续时间，单位 ms，默认值 400
 * @param timeFunction 定义动画的效果，默认值"linear"，
 * 有效值："linear","ease","ease-in","ease-in-out","ease-out",
 * "step-start","step-end"
 * @param delay 动画延迟时间，单位 ms，默认值 0
 * @param transformOrigin 设置transform-origin，默认值 "50"
 */
export function createAnimation({
  duration = 400,
  timeFunction = 'linear',
  delay = 0,
  transformOrigin = '50',
}: {
  duration?: Millisecond;
  timeFunction?:
    | 'linear'
    | 'ease'
    | 'ease-in'
    | 'ease-in-out'
    | 'ease-out'
    | 'step-start'
    | 'step-end';
  delay?: Millisecond;
  transformOrigin?: string;
} = {}) {
  return dd.createAnimation({
    duration,
    timeFunction,
    delay,
    transformOrigin,
  });
}

/**
 * 监听键盘弹起事件，并返回键盘高度
 * 键盘高度可以在回调参数的data.height参数中取到，单位为px。
 * 需要在page中设置该回调。
 * 调用 onKeyboardShow()
 */

/**
 * 监听键盘收起事件。
 * 需要在page中设置该回调。
 * 调用 onKeyboardHide()
 */

/**
 * 隐藏键盘
 * {@link https://ding-doc.dingtalk.com/doc#/dev/ui-hidekeyboard 界面=>键盘}
 */
export function hideKeyboard() {
  return dd.hideKeyboard();
}

/**
 * 滚动到页面的目标位置
 * {@link https://ding-doc.dingtalk.com/doc#/dev/scroll 界面=>滚动}
 * @param scrollTop 滚动到页面的目标位置，单位 px
 */
export function pageScrollTo(scrollTop: number) {
  return dd.pageScrollTo({
    scrollTop,
  });
}

/**
 * 获取用户当前的地理位置信息
 * {@link https://ding-doc.dingtalk.com/doc#/dev/location 位置}
 * @param cacheTimeout 钉钉客户端经纬度定位缓存过期时间，单位秒。默认 30s。
 * 使用缓存会加快定位速度，缓存过期会重新定位。
 * @param type 0：获取经纬度； 1：默认，获取经纬度和详细到区县级别的逆地理编码数据
 */
export function getLocation({
  cacheTimeout = 30,
  type,
}: {
  cacheTimeout?: Number;
  type?: number;
} = {}): Promise<{
  /** 经度 */
  longitude: string;
  /** 纬度 */
  latitude: string;
  /** 精确度，单位 米 */
  accuracy: string;
  /** 省份(type>0生效) */
  province: string;
  /** 城市(type>0生效) */
  city: string;
  /** 格式化地址，如：北京市朝阳区南磨房镇北京国家广告产业园区(type>0生效) */
  address: string;
}> {
  return new Promise((resolve, reject) => {
    dd.getLocation({
      cacheTimeout,
      type,
      success(res: any) {
        resolve(res);
      },
      fail: rejectWarp(reject),
    });
  });
}

/**
 * 使用内置地图查看位置
 * {@link https://ding-doc.dingtalk.com/doc#/dev/location 位置}
 * @param longitude 经度
 * @param latitude 纬度
 * @param name 位置名称
 * @param address 地址的详细说明
 * @param scale 缩放比例，范围 3~19，默认为 15
 */
export function openLocation({
  longitude,
  latitude,
  name,
  address,
  scale = 15,
}: {
  longitude: string;
  latitude: string;
  name: string;
  address: string;
  scale?: number;
}) {
  return new Promise((resolve, reject) => {
    dd.openLocation({
      longitude,
      latitude,
      name,
      address,
      scale,
      success: resolve,
      fail: rejectWarp(reject),
    });
  });
}

/**
 * 调用扫一扫功能
 * {@link https://ding-doc.dingtalk.com/doc#/dev/vglq4x 开放接口=>扫码}
 * @param type 扫码样式(默认 qr)：1, qr，扫码框样式为二维码扫码框
 * 2.bar，扫码样式为条形码扫码框
 */
export function scan(
  type = 'qr'
): Promise<{
  /** 扫码所得数据 */
  code: string;
  /** 扫描二维码时返回二维码数据 */
  qrCode: string;
  /** 扫描条形码时返回条形码数据 */
  barCode: string;
}> {
  return new Promise((resolve, reject) => {
    dd.scan({
      type,
      success(res: any) {
        resolve(res);
      },
      fail: rejectWarp(reject),
    });
  });
}

/**
 * 通讯录选人===>选人和部门
 * {@link https://ding-doc.dingtalk.com/doc#/dev/yskexi 开放接口=>通讯录选人}
 * @param title 标题
 * @param multiple 是否多选
 * @param limitTips 超过限定人数返回提示
 * @param maxUsers 	最大可选人数
 * @param pickedUsers 已选用户，值为userId列表
 * @param pickedDepartments 已选部门
 * @param disabledUsers 不可选用户，值为userId列表
 * @param disabledDepartments 不可选部门
 * @param requiredUsers 必选用户（不可取消选中状态），值为userId列表
 * @param requiredDepartments 必选部门（不可取消选中状态）
 * @param permissionType 选人权限，目前只有GLOBAL这个参数
 * @param responseUserOnly true：返回人员信息 false：返回人员和部门信息
 * @param startWithDepartmentId 仅支持0和-1两个值： 0表示从企业最上层开始；
 *  -1表示从自己部门开始，为-1时仅在Android端生效
 */
export function complexChoose(opt: {
  title: string;
  multiple: boolean;
  limitTips: string;
  maxUsers: number;
  pickedUsers: Array<string>;
  pickedDepartments: Array<string>;
  disabledUsers: Array<string>;
  disabledDepartments: Array<string>;
  requiredUsers: Array<string>;
  requiredDepartments: Array<string>;
  permissionType: string;
  responseUserOnly: boolean;
  startWithDepartmentId: number;
}): Promise<{
  /** 选择人数 */
  selectedCount: number;
  /** 返回选人的列表，列表中的对象包含name（用户名），avatar（用户头像），
   * userId（用户工号）三个字段 */
  users: Array<object>;
  /**  返回已选部门列表，列表中每个对象包含id（部门id）、name（部门名称）、
   * count（部门人数） */
  departments: Array<object>;
}> {
  return new Promise((resolve, reject) => {
    dd.complexChoose({
      ...opt,
      success(res: any) {
        resolve(res);
      },
      fail: rejectWarp(reject),
    });
  });
}

/**
 * 通讯录选人===>选择部门信息
 * {@link https://ding-doc.dingtalk.com/doc#/dev/yskexi 开放接口=>通讯录选人}
 * @param title 标题
 * @param multiple 是否多选
 * @param limitTips 超过限定人数返回提示
 * @param maxDepartments 	最大可选部门数
 * @param pickedDepartments 已选部门
 * @param disabledDepartments 不可选部门
 * @param requiredDepartments 必选部门（不可取消选中状态）
 * @param permissionType 选人权限，目前只有GLOBAL这个参数
 */
export function chooseDepartments(opt: {
  title: string;
  multiple: boolean;
  limitTips: string;
  maxDepartments: number;
  pickedDepartments: Array<string>;
  disabledDepartments: Array<string>;
  requiredDepartments: Array<string>;
  permissionType: string;
}): Promise<{
  /** 选择人数 */
  userCount: number;
  /** 选择的部门数 */
  departmentsCount: number;
  /** 返回已选部门列表，
   * 列表中每个对象包含id（部门id）、name（部门名称）、number（部门人数） */
  departments: Array<object>;
}> {
  return new Promise((resolve, reject) => {
    dd.chooseDepartments({
      ...opt,
      success(res: any) {
        resolve(res);
      },
      fail: rejectWarp(reject),
    });
  });
}

/**
 * 通讯录选人===>创建企业群聊天
 * {@link https://ding-doc.dingtalk.com/doc#/dev/yskexi 开放接口=>通讯录选人}
 * @param users 默认选中的userId列表
 */
export function createGroupChat(users: Array<string>): Promise<Array<string>> {
  return new Promise((resolve, reject) => {
    dd.createGroupChat({
      users,
      success(res: any) {
        resolve(res.id);
      },
      fail: rejectWarp(reject),
    });
  });
}

/**
 * 通讯录选人===>选取手机通讯录
 * {@link https://ding-doc.dingtalk.com/doc#/dev/yskexi 开放接口=>通讯录选人}
 * @param title 如果你需要修改选人页面的title，可以在这里赋值
 * @param multiple 是否多选： true多选，false单选； 默认true
 * @param maxUsers 人数限制，当multiple为true才生效，可选范围1-1500
 * @param limitTips 超过人数限制的提示语可以用这个字段自定义
 */
export function choosePhonebook({
  title,
  multiple = true,
  limitTips,
  maxUsers,
}: {
  title: string;
  multiple?: boolean;
  limitTips: string;
  maxUsers: number;
}): Promise<
  [
    {
      /** 姓名 */
      name: string;
      /** 头像图片id，可能为空 */
      avatar: string;
      /** 用户手机号 */
      mobile: string;
    }
  ]
> {
  return new Promise((resolve, reject) => {
    dd.choosePhonebook({
      title,
      multiple,
      limitTips,
      maxUsers,
      success(res: any) {
        resolve(res);
      },
      fail: rejectWarp(reject),
    });
  });
}

/**
 * 通讯录选人===>选择外部联系人
 * {@link https://ding-doc.dingtalk.com/doc#/dev/yskexi 开放接口=>通讯录选人}
 * @param title 选择联系人标题
 * @param multiple 是否多选： true多选，false单选； 默认true
 * @param maxUsers 最多选择的人数
 * @param limitTips 限制选择人数，0为不限制
 * @param pickedUsers 默认选中的人，值为userId列表。注意:已选中可以取消
 * @param disabledUsers 不能选的人，值为userId列表
 * @param requiredUsers 默认选中且不可取消选中状态的人，值为userId列表
 */
export function chooseExternalUsers({
  title,
  multiple = true,
  limitTips,
  maxUsers,
  pickedUsers,
  disabledUsers,
  requiredUsers,
}: {
  title: string;
  multiple?: boolean;
  limitTips: string;
  maxUsers: number;
  pickedUsers: Array<string>;
  disabledUsers: Array<string>;
  requiredUsers: Array<string>;
}): Promise<
  [
    {
      /** 姓名 */
      name: string;
      /** 头像图片url，可能为空 */
      avatar: string;
      /** 用户id */
      userId: string;
      /** 公司名字 */
      orgName: string;
    }
  ]
> {
  return new Promise((resolve, reject) => {
    dd.chooseExternalUsers({
      title,
      multiple,
      limitTips,
      maxUsers,
      pickedUsers,
      disabledUsers,
      requiredUsers,
      success(res: any) {
        resolve(res);
      },
      fail: rejectWarp(reject),
    });
  });
}

/**
 * 通讯录选人===>编辑外部联系人
 * {@link https://ding-doc.dingtalk.com/doc#/dev/yskexi 开放接口=>通讯录选人}
 * @param title 标题
 * @param emplId 需要编辑的员工id，不填，则为新增外部联系人
 * @param name 需要新增的外部联系人的名字
 * @param mobile 需要预填的手机号
 * @param companyName 需要预填的公司名
 * @param deptName 预填部门名字
 * @param job 预填职位
 * @param remark 备注信息
 */
export function editExternalUser(opt: {
  title: string;
  emplId: string;
  name: string;
  mobile: string;
  companyName: string;
  deptName: string;
  job: string;
  remark: string;
}): Promise<{
  /** 需要编辑的员工id，不填，则为新增外部联系人 */
  userId: string;
  /** 需要新增的外部联系人的名字，emplID为空时生效 */
  name: string;
  /** 需要预填的手机号，emplID为空时生效 */
  mobile: string;
  /** 需要预填的公司名，emplID为空时生效 */
  companyName: string;
  /** 预填部门名字，emplID为空时生效 */
  deptName: string;
  /** 预填职位，emplID为空时生效 */
  job: string;
  /** 备注信息，emplId为空时生效 */
  remark: string;
}> {
  return new Promise((resolve, reject) => {
    dd.editExternalUser({
      ...opt,
      success(res: any) {
        resolve(res);
      },
      fail: rejectWarp(reject),
    });
  });
}

/**
 * 通讯录选人===>单选自定义联系人
 * {@link https://ding-doc.dingtalk.com/doc#/dev/yskexi 开放接口=>通讯录选人}
 * @param title 标题
 * @param users 一组员工userId
 * @param isShowCompanyName 是否显示公司名称
 * @param disabledUsers 不能选择的人；PC端不支持此参数
 */
export function chooseUserFromList({
  title,
  users,
  isShowCompanyName = false,
  disabledUsers,
}: {
  title: string;
  users: Array<string>;
  isShowCompanyName?: boolean;
  disabledUsers: Array<string>;
}): Promise<
  [
    {
      /** 姓名 */
      name: string;
      /** 头像图片url，可能为空 */
      avatar: string;
      /** 即员工userid */
      userId: string;
    }
  ]
> {
  return new Promise((resolve, reject) => {
    dd.chooseUserFromList({
      title,
      users,
      isShowCompanyName,
      disabledUsers,
      success(res: any) {
        resolve(res);
      },
      fail: rejectWarp(reject),
    });
  });
}

/**
 * 将数据存储在本地缓存中指定的 key 中，会覆盖掉原来该 key 对应的数据
 * {@link https://ding-doc.dingtalk.com/doc#/dev/storage 缓存}
 * @param key 缓存数据的key
 * @param data 要缓存的数据
 */
export function setStorage(opt: { key: string; data: object | string }) {
  return new Promise((resolve, reject) => {
    dd.setStorage({
      ...opt,
      success: resolve,
      fail: rejectWarp(reject),
    });
  });
}

/**
 * 同步将数据存储在本地缓存中指定的 key 中
 * 同步数据IO操作可能会影响小程序流畅度，建议使用异步接口，或谨慎处理调用异常
 * {@link https://ding-doc.dingtalk.com/doc#/dev/storage 缓存}
 * @param key 缓存数据的key
 * @param data 要缓存的数据
 */
export function setStorageSync(opt: { key: string; data: object | string }) {
  return dd.setStorageSync(opt);
}

/**
 * 获取缓存数据
 * {@link https://ding-doc.dingtalk.com/doc#/dev/storage 缓存}
 * @param key 要缓存的数据
 */
export function getStorage(key: string): Promise<object | string> {
  return new Promise((resolve, reject) => {
    dd.getStorage({
      key,
      success(res: any) {
        resolve(res.data);
      },
      fail: rejectWarp(reject),
    });
  });
}

/**
 * 同步获取缓存数据
 * 同步数据IO操作可能会影响小程序流畅度，建议使用异步接口，或谨慎处理调用异常
 * {@link https://ding-doc.dingtalk.com/doc#/dev/storage 缓存}
 * @param key 缓存数据的key
 */
export function getStorageSync(key: string) {
  return dd.getStorageSync({ key });
}

/**
 * 删除缓存数据
 * {@link https://ding-doc.dingtalk.com/doc#/dev/storage 缓存}
 * @param key 缓存数据的key
 */
export function removeStorage(key: string) {
  return new Promise((resolve, reject) => {
    dd.removeStorage({
      key,
      success: resolve,
      fail: rejectWarp(reject),
    });
  });
}

/**
 * 同步删除缓存数据
 * 同步数据IO操作可能会影响小程序流畅度，建议使用异步接口，或谨慎处理调用异常
 * {@link https://ding-doc.dingtalk.com/doc#/dev/storage 缓存}
 * @param key 缓存数据的key
 */
export function removeStorageSync(key: string) {
  return dd.removeStorageSync({
    key,
  });
}

/**
 * 获取网络状态
 * {@link https://ding-doc.dingtalk.com/doc#/dev/network-type 网络状态}
 */
export function getNetworkType(): Promise<{
  /** 网络是否可用 */
  networkAvailable: boolean;
  /** 网络类型值 UNKNOWN / NOTREACHABLE / WIFI / 3G / 2G / 4G / WWAN */
  networkType: string;
}> {
  return new Promise((resolve, reject) => {
    dd.getNetworkType({
      success(res: any) {
        resolve(res);
      },
      fail: rejectWarp(reject),
    });
  });
}

/**
 * 剪切板功能
 * {@link https://ding-doc.dingtalk.com/doc#/dev/clipboard 剪切板}
 */
export function getClipboard(): Promise<string> {
  return new Promise((resolve, reject) => {
    dd.getClipboard({
      success(res: any) {
        resolve(res.text);
      },
      fail: rejectWarp(reject),
    });
  });
}

/**
 * 设置剪切板数据
 * {@link https://ding-doc.dingtalk.com/doc#/dev/clipboard 剪切板}
 * @param text 剪切板数据
 */
export function setClipboard(text: string) {
  return new Promise((resolve, reject) => {
    dd.setClipboard({
      text,
      success: resolve,
      fail: rejectWarp(reject),
    });
  });
}

/**
 * 调用震动功能
 * {@link https://ding-doc.dingtalk.com/doc#/dev/vibrate 震动}
 */
export function vibrate() {
  return new Promise((resolve, reject) => {
    dd.vibrate({
      success: resolve,
      fail: rejectWarp(reject),
    });
  });
}

/**
 * 选择图片
 * {@link https://ding-doc.dingtalk.com/doc#/dev/media-image 多媒体=>图片}
 * @param count 最大可选照片数，默认1张
 * @param sourceType 相册选取或者拍照，默认 ['camera','album']
 */
export function chooseImage({
  count = 1,
  sourceType = ['camera', 'album'],
}: {
  count?: number;
  sourceType?: Array<string>;
} = {}): Promise<Array<string>> {
  return new Promise((resolve, reject) => {
    dd.chooseImage({
      count,
      sourceType,
      success(res: any) {
        resolve(res.filePaths);
      },
      fail: rejectWarp(reject),
    });
  });
}

/**
 * 预览图片
 * {@link https://ding-doc.dingtalk.com/doc#/dev/media-image 多媒体=>图片}
 * @param urls 要预览的图片链接列表
 * @param current 当前显示图片索引，默认 0
 */
export function previewImage({
  urls,
  current = 0,
}: {
  urls: Array<any>;
  current?: number;
}) {
  return new Promise((resolve, reject) => {
    dd.previewImage({
      urls,
      current,
      success: resolve,
      fail: rejectWarp(reject),
    });
  });
}

/**
 * 保存在线、本地临时或者永久地址图片到手机相册
 * {@link https://ding-doc.dingtalk.com/doc#/dev/media-image 多媒体=>图片}
 * @param url 要保存的图片地址
 */
export function saveImage(url: string) {
  return new Promise((resolve, reject) => {
    dd.saveImage({
      url,
      success: resolve,
      fail: rejectWarp(reject),
    });
  });
}

/**
 * 压缩图片
 * {@link https://ding-doc.dingtalk.com/doc#/dev/media-image 多媒体=>图片}
 * @param filePaths 要压缩的图片地址数组
 * @param compressLevel 压缩级别，支持 0 ~ 4 的整数，默认 4。
 * compressLevel	说明 0 低质量 1	中等质量 2	高质量 3	不压缩 4	根据网络适应
 */
export function compressImage({
  filePaths,
  compressLevel = 4,
}: {
  filePaths: Array<string>;
  compressLevel?: number;
}): Promise<Array<string>> {
  return new Promise((resolve, reject) => {
    dd.compressImage({
      filePaths,
      compressLevel,
      success(res: any) {
        resolve(res.filePaths);
      },
      fail: rejectWarp(reject),
    });
  });
}

/**
 * 获取图片信息
 * {@link https://ding-doc.dingtalk.com/doc#/dev/media-image 多媒体=>图片}
 * @param src 图片路径，目前支持：
 */
export function getImageInfo(
  src: string
): Promise<{
  /** 图片宽度（单位px） */
  width: number;
  /** 图片高度（单位px） */
  height: number;
  /** 图片本地路径 */
  path: string;
}> {
  return new Promise((resolve, reject) => {
    dd.getImageInfo({
      src,
      succrss(res: any) {
        resolve(res);
      },
      fail: rejectWarp(reject),
    });
  });
}

/**
 * 获取当前小程序全局唯一的录音管理器 recordManager
 * {@link https://ding-doc.dingtalk.com/doc#/dev/vw45p8 录音管理}
 */
export function getRecorderManager() {
  return dd.getRecorderManager();
}

/**
 * 背景音频管理 获取当前小程序全局唯一的背景音频管理 backgroundAudioManager。
 * 当小程序切入后台时，音频可以背景播放。
 * {@link https://ding-doc.dingtalk.com/doc#/dev/ag4x5f 背景音频管理}
 */
export function getBackgroundAudioManager() {
  return dd.getBackgroundAudioManager();
}

/**
 * 拍摄视频或从手机相册中选视频
 * {@link https://ding-doc.dingtalk.com/doc#/dev/wsm3ig 视频}
 * @param sourceType 视频来源
 * @param maxDuration 最长视频拍摄事件，单位为秒
 */
export function chooseVideo({
  sourceType = ['album', 'camera'],
  maxDuration = 60,
}: {
  sourceType?: Array<string>;
  maxDuration?: Second;
} = {}): Promise<{
  /** 视频临时文件路径 */
  filePath: string;
  /** 视频时间长度 */
  duration: Second;
  /** 视频数据大小 */
  size: number;
  /** 视频高度 */
  height: number;
  /** 视频宽度 */
  width: number;
}> {
  return new Promise((resolve, reject) => {
    dd.chooseVideo({
      sourceType,
      maxDuration,
      success(res: any) {
        resolve(res);
      },
      fail: rejectWarp(reject),
    });
  });
}

/**
 * 分享
 * {@link https://ding-doc.dingtalk.com/doc#/dev/share-app 分享}
 * 调用onShareAppMessage()
 * 返回一个object
 * {title 自定义分享标题; desc 自定义分享描述; path 自定义分享页面的路径}，
 * path中的自定义参数可在小程序生命周期的onLoad方法中获取（参数传递遵循http get的传参规则）;
 * imageUrl 自定义分享图片(只支持网络图片路径}fallbackUrl 可降级 H5 URL，仅适用于企业应用。
 * 当前钉钉桌面客户端不支持打开企业类小程序，配置此设置后，
 * 在桌面端访问此企业应用时，会打开fallbackUrl配置的H5 URL。
 */

/**
 * 发钉接口支持唤起DING、任务、日程等创建界面，
 * 目前发钉只支持客户端发钉，不支持直接通过服务端发钉。
 * {@link https://ding-doc.dingtalk.com/doc#/dev/raeos8 Ding}
 * @param users 用户列表，员工userid
 * @param corpId 企业corpId
 * @param alertType 钉提醒类型 0：电话, 1：短信, 2：应用内
 * @param alertDate 钉提醒时间；非必填
 * @param type Number为整数，钉类型 1：image 2：link
 * @param attachment 附件信息
 * @param text 消息体
 * @param bizType 0：通知DING，1：任务，2：日程
 * @param taskInfo 任务信息
 * @param confInfo 日程信息
 */
export function createDing(opt: {
  users: Array<string>;
  corpId: string;
  alertType: number;
  alertDate: object;
  type: number;
  attachment?: object;
  text?: string;
  bizType?: number;
  taskInfo?: object;
  confInfo?: object;
}): Promise<{
  /** 发送的DING消息的id */
  dingId: string;
  /** 发送的DING消息的文本内容 */
  text: string;
  /** 发送消息是否成功，true|false */
  result: boolean;
}> {
  return new Promise((resolve, reject) => {
    dd.createDing({
      ...opt,
      success(res: any) {
        resolve(res);
      },
      fail: rejectWarp(reject),
    });
  });
}

/**
 * 拨打钉钉电话
 * {@link https://ding-doc.dingtalk.com/doc#/dev/gr5lv4 电话}
 * @param users 用户列表，工号
 */
export function callUsers(users: Array<string>) {
  return new Promise((resolve, reject) => {
    dd.callUsers({
      users,
      success: resolve,
      fail: rejectWarp(reject),
    });
  });
}

/**
 * 唤起拨打电话菜单
 * {@link https://ding-doc.dingtalk.com/doc#/dev/gr5lv4 电话}
 * @param phoneNumber 期望拨打的电话号码
 * @param code 国家代号，中国是+86
 * @param showDingCall 是否显示钉钉电话
 */
export function showCallMenu(opt: {
  phoneNumber: string;
  code: string;
  showDingCall: boolean;
}) {
  return new Promise((resolve, reject) => {
    dd.showCallMenu({
      ...opt,
      success: resolve,
      fail: rejectWarp(reject),
    });
  });
}

/**
 * 检查某企业办公电话开通状态
 * {@link https://ding-doc.dingtalk.com/doc#/dev/gr5lv4 电话}
 * @param corpId 被检测企业的corpId
 */
export function checkBizCall(corpId: string): Promise<boolean> {
  return new Promise((resolve, reject) => {
    dd.checkBizCall({
      corpId,
      success(res: any) {
        resolve(res.isSupport);
      },
      fail: rejectWarp(reject),
    });
  });
}

/**
 * 支付接口
 * {@link https://ding-doc.dingtalk.com/doc#/dev/bkgshb 支付}
 * @param info 需要构建的订单信息
 * info 参考支付宝文档：
 * https://doc.open.alipay.com/doc2/detail.htm?treeId=59&articleId=103663&docType=1
 */
export function pay(
  info: string
): Promise<{
  /** 保留参数，一般无内容 */
  memo: string;
  /** 本次操作返回的结果数据 */
  result: string;
  /** 本次操作的状态返回值，标识本次调用的结果 参考：
   * https://doc.open.alipay.com/doc2/detail.htm?treeId=59&articleId=103671&docType=1
   */
  resultStatus: string;
}> {
  return new Promise((resolve, reject) => {
    dd.pay({
      info,
      success(res: any) {
        resolve(res);
      },
      fail: rejectWarp(reject),
    });
  });
}

/**
 * 转存文件到钉盘
 * {@link https://ding-doc.dingtalk.com/doc#/dev/hu8d2w 钉盘}
 * @param url 文件在第三方服务器上的url地址或通过提交文件上传事务、单步文件上传获取到的media_id
 * @param name 文件保存的名字
 */
export function saveFileToDingTalk(opt: {
  url: string;
  name: string;
}): Promise<
  [
    {
      /** 空间id */
      spaceId: string;
      /** 文件id */
      fileId: string;
      /** 文件名 */
      fileName: string;
      /** 文件大小 */
      fileSize: number;
      /** 文件类型 */
      fileType: string;
    }
  ]
> {
  return new Promise((resolve, reject) => {
    dd.saveFileToDingTalk({
      ...opt,
      success(res: any) {
        resolve(res.data);
      },
      fail: rejectWarp(reject),
    });
  });
}

/**
 * 钉盘文件预览
 * {@link https://ding-doc.dingtalk.com/doc#/dev/hu8d2w 钉盘}
 * @param spaceId 空间ID
 * @param fileId 文件ID
 * @param fileName 文件名称
 * @param fileSize 文件大小，字节数
 * @param fileType 文件扩展名
 */
export function previewFileInDingTalk(opt: {
  spaceId: string;
  fileId: string;
  fileName: string;
  fileSize: number;
  fileType: string;
}) {
  return dd.previewFileInDingTalk({ ...opt });
}

/**
 * 上传附件到钉盘/从钉盘选择文件
 * {@link https://ding-doc.dingtalk.com/doc#/dev/hu8d2w 钉盘}
 * @param types 支持上传附件的文件类型，至少一个；Android&iOS：
 * 最多支持四种类型["photo","camera","file","space"]；
 * PC端：最多支持["photo","file","space"]
 * @param image types这个数组里有photo、camera参数需要构建这个数据
 * @param compress 是否压缩，默认为true
 * @param multiple 是否多选，默认为false
 * @param max 最多选择的图片数目，最多支持9张
 * @param isCopy 1复制，0不复制(PC端不支持此参数)
 * @param spaceId 企业自定义空间
 * @param space types这个数组里有space参数需要构建这个数据
 * @param file types这个数组里有file参数需要构建这个数据
 */
export function uploadAttachmentToDingTalk({
  types,
  image,
  compress = true,
  multiple = false,
  max,
  isCopy,
  spaceId,
  space,
  file,
}: {
  types: Array<string>;
  image: object;
  compress?: boolean;
  multiple?: boolean;
  max: number;
  isCopy: number;
  spaceId: string;
  space: Object;
  file: Object;
}): Promise<{
  /** 支持上传附件的类型，目前有photo、camera、file、space */
  type: string;
  /** 文件上传成功后的数据信息 */
  data: Array<object>;
  /** 目标空间id */
  spaceId: string;
  /** 文件id */
  fileId: string;
  /** 文件名称 */
  fileName: string;
  /** 文件类型 */
  fileType: string;
  /** 文件大小 */
  fileSize: string;
}> {
  return new Promise((resolve, reject) => {
    dd.uploadAttachmentToDingTalk({
      types,
      image,
      compress,
      multiple,
      max,
      isCopy,
      spaceId,
      space,
      file,
      success(res: any) {
        resolve(res);
      },
      fail: rejectWarp(reject),
    });
  });
}

/**
 * 选取钉盘目录
 * 唤起钉盘选择器， 从用户当前的企业空间或个人空间选择一个目录， 用以保存文件等操作。
 * {@link https://ding-doc.dingtalk.com/doc#/dev/hu8d2w 钉盘}
 */
export function chooseDingTalkDir(): Promise<{
  /** 被选中文件夹所在的钉盘空间id */
  spaceId: string;
  /** 被选中的文件夹路径， 例如“/测试/测试子目录/” */
  path: string;
  /** 被选中的文件夹id */
  dirId: string;
}> {
  return new Promise((resolve, reject) => {
    dd.chooseDingTalkDir({
      success(res: any) {
        resolve(res);
      },
      fail: rejectWarp(reject),
    });
  });
}

/**
 * 获取会话信息
 * {@link https://ding-doc.dingtalk.com/doc#/dev/epcw4e 会话}
 * @param isConfirm 是否弹出确认窗口，默认为true
 */
export function chooseChatForNormalMsg(
  isConfirm = true
): Promise<{
  /**  会话id
   * （该cid和服务端开发文档-普通会话消息接口配合使用，而且只能使用一次，之后将失效）
   */
  cid: string;
  /**  会话标题 */
  title: string;
}> {
  return new Promise((resolve, reject) => {
    dd.chooseChatForNormalMsg({
      isConfirm,
      success(res: any) {
        resolve(res);
      },
      fail: rejectWarp(reject),
    });
  });
}

/**
 * 选择会话
 * {@link https://ding-doc.dingtalk.com/doc#/dev/epcw4e 会话}
 * @param isAllowCreateGroup 是否允许创建会话
 * @param filterNotOwnerGroup 是否限制为自己创建的会话
 */
export function chooseChat(opt: {
  isAllowCreateGroup: boolean;
  filterNotOwnerGroup: boolean;
}): Promise<{
  /** 会话id（该会话cid永久有效） */
  chatId: string;
  /** 会话标题 */
  title: string;
}> {
  return new Promise((resolve, reject) => {
    dd.chooseChat({
      ...opt,
      success(res: any) {
        resolve(res);
      },
      fail: rejectWarp(reject),
    });
  });
}

/**
 * 根据chatId跳转到对应会话
 * {@link https://ding-doc.dingtalk.com/doc#/dev/epcw4e 会话}
 * @param chatId 会话ID
 */
export function openChatByChatId(chatId: string) {
  return new Promise((resolve, reject) => {
    dd.openChatByChatId({
      chatId,
      success: resolve,
      fail: rejectWarp(reject),
    });
  });
}

/**
 * 打开与某个用户的聊天页面（单聊会话）
 * {@link https://ding-doc.dingtalk.com/doc#/dev/epcw4e 会话}
 * @param userId 用户工号
 */
export function openChatByUserId(userId: string) {
  return new Promise((resolve, reject) => {
    dd.openChatByUserId({
      userId,
      success: resolve,
      fail: rejectWarp(reject),
    });
  });
}

/**
 * 创建一个 WebSocket 的连接；一个钉钉小程序同时只能保留一个 WebSocket 连接，
 * 如果当前已存在 WebSocket 连接，会自动关闭该连接，并重新创建一个新的 WebSocket 连接。
 * {@link https://ding-doc.dingtalk.com/doc#/dev/ywpb29 webSocket}
 * @param url 目标服务器url
 * @param data 请求的参数
 * @param header 设置请求的头部
 */
export function connectSocket(opt: {
  url: string;
  data?: object;
  header?: object;
}) {
  return new Promise((resolve, reject) => {
    dd.connectSocket({
      ...opt,
      success: resolve,
      fail: rejectWarp(reject),
    });
  });
}

/**
 * 监听WebSocket连接打开事件
 * {@link https://ding-doc.dingtalk.com/doc#/dev/ywpb29 webSocket}
 * @fun WebSocket 连接打开事件的回调函数
 */
export function onSocketOpen(fun: Function) {
  return Promise.resolve(dd.onSocketOpen(fun));
}

/**
 * 取消监听WebSocket连接打开事件。
 * {@link https://ding-doc.dingtalk.com/doc#/dev/ywpb29 webSocket}
 * @fun 回调函数
 */
export function offSocketOpen(fun: Function) {
  return Promise.resolve(dd.offSocketOpen(fun));
}

/**
 * 监听WebSocket错误。
 * {@link https://ding-doc.dingtalk.com/doc#/dev/ywpb29 webSocket}
 * @fun WebSocket 错误事件的回调函数
 */
export function onSocketError(fun: Function) {
  return Promise.resolve(dd.onSocketError(fun));
}

/**
 * 取消监听WebSocket错误。
 * {@link https://ding-doc.dingtalk.com/doc#/dev/ywpb29 webSocket}
 * @fun 回调函数
 */
export function offSocketError(fun: Function) {
  return Promise.resolve(dd.offSocketError(fun));
}

/**
 * 通过 WebSocket 连接发送数据，需要先使用上述介绍的dd.connectSocket发起连接，
 * 再使用dd.onSocketsOpen回调之后再发送数据
 * {@link https://ding-doc.dingtalk.com/doc#/dev/ywpb29 webSocket}
 * @param data 需要发送的内容：普通的文本内容 String 或者经 base64 编码后的 String
 * @param isBuffer 如果需要发送二进制数据，
 * 需要将入参数据经 base64 编码成 String 后赋值 data，
 * 同时将此字段设置为true，否则如果是普通的文本内容 String，不需要设置此字段
 */
export function sendSocketMessage(opt: { data: string; isBuffer?: boolean }) {
  return new Promise((resolve, reject) => {
    dd.sendSocketMessage({
      ...opt,
      success: resolve,
      fail: rejectWarp(reject),
    });
  });
}

/**
 * 监听WebSocket接受到服务器的消息事件。
 * {@link https://ding-doc.dingtalk.com/doc#/dev/ywpb29 webSocket}
 * @fun WebSocket 接受到服务器的消息事件的回调函数
 */
export function onSocketMessage(fun: Function) {
  return Promise.resolve(dd.onSocketMessage(fun));
}

/**
 * 取消监听WebSocket接受到服务器的消息事件。
 * {@link https://ding-doc.dingtalk.com/doc#/dev/ywpb29 webSocket}
 */
export function offSocketMessage() {
  return dd.offSocketMessage();
}

/**
 * 取消监听WebSocket接受到服务器的消息事件。
 * {@link https://ding-doc.dingtalk.com/doc#/dev/ywpb29 webSocket}
 */
export function closeSocket() {
  return new Promise((resolve, reject) => {
    dd.closeSocket({
      success: resolve,
      fail: rejectWarp(reject),
    });
  });
}

/**
 * 取消监听WebSocket接受到服务器的消息事件。
 * {@link https://ding-doc.dingtalk.com/doc#/dev/ywpb29 webSocket}
 * @fun WebSocket 连接关闭事件的回调函数
 */
export function onSocketClose(fun: Function) {
  return Promise.resolve(dd.onSocketClose(fun));
}

/**
 * 取消监听WebSocket关闭。
 * {@link https://ding-doc.dingtalk.com/doc#/dev/ywpb29 webSocket}
 */
export function offSocketClose() {
  return dd.offSocketClose();
}
