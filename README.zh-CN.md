# Open Startup Radar｜开放式 AI 创业雷达

**追踪 AI 创业公司发生了什么变化，并保留每条信号的来源。**

[直接体验在线演示](https://jinfengkj-byte.github.io/open-startup-radar/)（虚构数据，无需注册）

输入研究主题、公开 RSS/Atom 订阅源和可选的公司关注名单，工具会收集并去重带链接的条目，在本地保存历史，显示本次新发现与已见过的信号，输出网页、Markdown 和 JSON。可选的模型分析只使用本次收集到的证据。

## 一分钟体验

需要 Python 3.10 或更新版本。依次运行：

```powershell
git clone https://github.com/jinfengkj-byte/open-startup-radar.git
cd open-startup-radar
python -m pip install -e .
startup-radar demo --output output
startup-radar serve --output output
```

浏览器打开 `http://127.0.0.1:8000/`。演示数据是虚构的，不需要网络或密钥。再次运行演示命令，新发现数量会从 4 变成 0，说明本地历史追踪生效。

## 真实订阅源

```powershell
startup-radar scan --config config.example.json --output output
```

修改 `config.example.json` 中的主题、订阅源和公司名单。结果保存在 `output/index.html`、`output/report.md`、`output/report.json`；`output/history.sqlite` 保存已见过的链接。网页可以直接双击打开。

模型分析是**自选功能**，只有显式加上 `--ai` 才会调用 API，可能产生费用。需要自行提供 `OPENAI_API_KEY`。模型引用必须来自本次收集的原始链接，但仍需人工核查结论。当前公司匹配和分类采用透明的文本规则，不能保证新闻真实性，也不推断未披露的融资金额或估值。

英文主页包含完整配置、架构和贡献说明：[README.md](README.md)。
