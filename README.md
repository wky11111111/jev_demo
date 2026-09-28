# Jev × OpenRouter：工单判断台 Demo

这是一个可现场操作的本地网页 Demo。输入一条工单后，它把内容发给 OpenRouter 上的 Jev 1.13，在同一次请求中做三个判断：

- **Choice**：工单应该交给哪个团队？
- **Noul**：客户是否明确要求退款？
- **Score**：问题对主要业务流程的影响有多大？

网页服务端和命令行版本都只用 Python 标准库，不需要安装第三方包。浏览器不会接触 API Key；Key 只由本机 Python 服务读取。

## 1. 创建 OpenRouter API Key

登录 OpenRouter，在 Dashboard 创建 API Key，并确认账号可以调用付费模型。Key 由你的 OpenRouter 账号提供，不需要 TypeSafe 账号。

## 2. 在 PowerShell 打开 Demo 文件夹

进入解压或保存 Demo 文件的目录，然后确认 Python 已安装：

```powershell
python --version
```

脚本支持 Python 3.9 或更高版本，不需要安装依赖。

## 3. 在当前 PowerShell 窗口设置 Key

```powershell
$env:OPENROUTER_API_KEY = "sk-or-v1-粘贴你自己的密钥"
```

Key 仅保存在当前 PowerShell 窗口的环境变量中，不会写入代码文件。不要把真实 Key 放进文档、PPT 或聊天消息。

## 4. 启动网页 Demo

```powershell
python .\server.py
```

打开终端显示的本地地址：

```text
http://127.0.0.1:8765
```

页面提供三条预置工单，也可以直接编辑文本。点击“运行 Jev 判断”后，服务端实际请求：

```text
POST https://openrouter.ai/api/alpha/decisions
model = typesafe/jev-1.13
```

注意这里是 OpenRouter 的 **Decisions API**。Jev 不使用常见聊天接口 `/api/v1/chat/completions`。请求体由 `model`、`state` 和 `questions` 构成，页面提供的 API 示例也使用这个专用端点。

停止服务时回到 PowerShell 按 `Ctrl+C`。演示内容会发送至 OpenRouter 处理，请使用虚构工单，不要输入真实客户隐私。

## 5. 现场演示顺序

先让大家看输入工单，再观察 Choice 的团队判断及候选概率、Noul 的退款意图概率、Score 的严重度分数与分布。接着换一条“支付故障”或“无法登录”的工单，看看同一组问题如何用于不同输入。页面也能展开查看 OpenRouter 返回的原始 JSON。

这个 Demo 只展示模型判断，不会执行退款、自动派单或修改业务数据。

## 命令行版本（可选）

如果想看最精简的 API 调用流程，可以运行：

```powershell
python .\main.py
```

## API 参考

- [OpenRouter Jev 1.13 页面与 API 示例](https://openrouter.ai/typesafe/jev-1.13?view=api)
- [OpenRouter 的 Jev 入门讲解](https://openrouter.ai/blog/insights/what-is-jev/)
- [TypeSafe 文档：Choice、Score 和 Noul](https://docs.typesafe.ai/introduction)

文中演示文本与结果示例只用于测试调用。OpenRouter 的请求会把输入文本发送给模型服务，分享或公开演示时使用虚构文本即可。
