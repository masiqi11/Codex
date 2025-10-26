# Codex AI Memo Parser

本项目提供了一个基于 OpenAI 大模型的备忘录解析组件，专门面向 iOS 端的提醒与日程场景。通过调用聊天模型生成结构化 JSON，可以轻松在 Swift / SwiftUI 中渲染分类、摘要以及后续动作。

## 功能特性

- ✅ 使用 OpenAI 大模型理解自然语言备忘录（中文、英文皆可）。
- ✅ 返回统一的结构化结果：`category`、`confidence`、`summary`、`actionItems`。
- ✅ 适合在 iOS 端直接序列化为 `Codable` 对象或通知内容。
- ✅ 提供命令行和 Python API，两者均支持配置模型与 API Key。

## 快速开始

### 1. 准备环境

项目仅依赖 Python 3.10+ 标准库，无需额外第三方包。

### 2. 交互式应用

运行下面的命令即可启动一个交互式控制台 App，直接在程序里输入 OpenAI API Key、选择模型并填写备忘录：

```bash
python -m ai_memo
```

应用会依次询问：

1. **OpenAI API Key**：直接在提示中粘贴即可，无需提前设置环境变量。
2. **模型选择**：按回车使用默认的 `gpt-4o-mini`，也可以输入其他模型名。
3. **备忘录内容**：逐条输入自然语言备忘录，输出会给出类别、摘要、置信度及后续行动。输入 `:config` 可随时重新设置 API Key 和模型，直接回车退出程序。

### 3. Python API

```python
from ai_memo import MemoParser

parser = MemoParser(api_key="YOUR_OPENAI_API_KEY")
result = parser.classify("周五下午提醒我提交 App Store 审核")
print(result.to_ios_payload())
# {"category": "reminder", "confidence": 0.87, ...}
```

可以将 `result.to_ios_payload()` 的返回值编码成 JSON，并在 Swift 中解码为：

```swift
struct MemoPayload: Codable {
    let category: String
    let confidence: Double
    let summary: String
    let actionItems: [String]
}
```

随后即可在通知、Widget 或者 Core Data 中使用。

## 自定义

- **模型选择**：初始化 `MemoParser` 时传入 `model="gpt-4o"` 等即可切换不同模型。
- **本地化**：`classify` 方法默认使用 `zh-CN` 输出，传入 `locale="en-US"` 等即可改变语言。
- **错误处理**：`MemoParser` 会在网络异常或 OpenAI API 返回错误时抛出 `OpenAIRequestError`，方便你在应用中统一提示。

## 运行测试

```bash
pytest
```

测试通过模拟 OpenAI 响应验证了请求结构、解析逻辑以及错误场景，确保在没有真实网络的情况下也能放心开发。
