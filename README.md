# Codex AI Memo Classifier

这个项目实现了一个简洁的 AI 备忘录分类器，能够将非规范化的文本备忘录自动划分到以下类别：

- **电话**：识别通话请求或者包含电话号码的内容。
- **日程**：检测会议、约会、时间地点等安排。
- **提醒事项**：包含待办、需要记住或后续跟进的任务。
- **备忘录**：无法归入以上类别的一般性记录。

## 快速开始

### 安装依赖

项目不依赖第三方库，只需要 Python 3.10 及以上环境即可运行和测试。

### 使用命令行工具

```bash
python -m ai_memo "明天10:00和王经理开会，别忘了带合同"
```

命令会输出分类结果、置信度以及被捕获的详细线索。你也可以通过 `--json` 获取机器可读的输出，或者通过 `--file` 传入多条备忘录。

### Python API

```python
from ai_memo import MemoClassifier

classifier = MemoClassifier()
analysis = classifier.classify("Call John at +1 415 555 0012")
print(analysis.category)
print(analysis.details)
```

## 运行测试

```bash
pytest
```

测试用例覆盖了电话、日程、提醒事项和默认备忘录分类场景。
