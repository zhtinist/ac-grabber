# AI Copywriter 抢稿助手

通过 Microsoft Edge（CDP 调试模式）自动刷新 [AI Copywriter](https://ai-copywriter.risevideo.ai/distribute) 稿池并领取符合条件的稿件。支持 GUI 与命令行两种运行方式。

## 功能

- 复用本机 Edge 登录状态，无需单独配置 Cookie
- 按公众号筛选，只抢选定账号下的稿子
- 定制稿规则：标题**末尾**括号内为你本人名字时才抢；他人定制稿自动跳过
- 可设置刷新间隔、领取篇数上限
- GUI 一键重启 Edge 调试模式

## 目录结构

```
.
├── ac_grabber/           # 核心逻辑
│   ├── config.py         # 配置读写
│   ├── rules.py          # 定制稿筛选规则
│   ├── browser.py        # Edge CDP 连接与页面操作
│   ├── edge_launcher.py  # Edge 调试模式启动
│   ├── worker.py         # 抢稿主循环
│   └── win32_bg.py       # Windows 后台窗口处理
├── app_gui.py            # GUI 入口
├── grab.py               # 命令行入口
├── run.bat               # 启动命令行抢稿
├── start_edge_debug.bat  # 以调试模式启动 Edge
├── build.bat             # 打包为 exe
├── requirements.txt
├── config.json.example   # 配置模板（复制为 config.json）
└── README.md
```

首次运行会自动生成 `config.json`；也可手动复制 `config.json.example` 并修改。

## 环境要求

- Windows 10/11
- Python 3.10+
- Microsoft Edge

## 安装

```bat
pip install -r requirements.txt
playwright install chromium
```

## 使用步骤

### 方式一：GUI（推荐）

1. 运行 `python app_gui.py`
2. 点击「启动 Edge」，确认稿池页已登录
3. 选择要抢的公众号，设置参数
4. 点击「开始抢稿」

### 方式二：命令行

1. 关闭所有 Edge 窗口
2. 双击 `start_edge_debug.bat`，确认已登录稿池页
3. 双击 `run.bat` 或执行 `python grab.py`
4. 关闭 CMD 窗口即停止

## 定制稿规则

| 标题末尾 | 行为 |
|----------|------|
| 无括号 | 普通稿，可抢 |
| `(你的名字)` | 你的定制稿，可抢 |
| `(其他人名)` | 他人定制稿，跳过 |
| `(9)` 等非汉字 | 可抢 |

标题开头或中间的括号（如「（横屏）」）不影响判断。

## 配置说明

编辑 `config.json`（中文键）：

| 字段 | 说明 |
|------|------|
| 人名 | 定制稿归属名，须与标题末尾括号一致 |
| 抢稿上限 | `0` = 不限篇数 |
| 刷新间隔 | 秒，默认 `0.3`，最小 `0.1` |
| 目标公众号 | 数组，名称须与页面 tag 完全一致 |

可选公众号：`小金AI新科技`、`康健求真`、`大宝说创业`、`AI壹号`、`秦刚·个人IP`、`秦刚头条`

## 打包 exe

```bat
build.bat
```

输出在 `dist/AC抢稿助手.exe`，同目录附带 `start_edge_debug.bat`。

## 注意事项

- Edge 必须以 `--remote-debugging-port=9222` 启动，且同一时间只能有一个 Edge 实例占用该端口
- 抢稿脚本只操作稿池标签页，其他标签页可照常使用
- `config.json` 含个人设置，已在 `.gitignore` 中排除，请勿提交到公开仓库

## 许可

仅供学习与个人使用，请遵守目标网站服务条款。
