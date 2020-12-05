# dd-sdk-mini-program [![npm version](https://img.shields.io/npm/v/@zsqk/dd-sdk-mini-program.svg?style=flat)](https://www.npmjs.com/package/@zsqk/dd-sdk-mini-program)

钉钉小程序 JSAPI SDK.

## 简介

特点:

- Promise 封装.
- 错误总是 Error 类型.
- TypeScript 类型提示.
- 没有依赖.
- 总是最新.
  (针对钉钉小程序内部 dd 的封装, 会随 dd 的变动而变, 旧版本没有意义.)

## 开发

### 安装依赖

```sh
npm i
```

### 编辑器

- 需要 ESLint
- 可选 Prettier

### 全局变量 dd & my

阿里系小程序通用 API 列表:
<https://docs.alipay.com/mini/multi-platform/common>

钉钉小程序 JSAPI 文档:
<https://ding-doc.dingtalk.com/doc#/dev/httprequest>
