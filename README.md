# AC Grabber

AI Copywriter 自动抢稿助手 — 通过 Microsoft Edge（CDP 调试模式）刷新 [稿池页面](https://ai-copywriter.risevideo.ai/distribute) 并领取符合条件的稿件。

仓库名与目录名均为 **`ac-grabber`**，与 Python 包 `ac_grabber` 对应。

## 功能

- 复用本机 Edge 登录状态，无需单独配置 Cookie
- 按公众号筛选，只抢选定账号下的稿子
- 定制稿规则：标题**末尾**括号内为你本人名字时才抢；他人定制稿自动跳过
- 可设置刷新间隔、领取篇数上限
- GUI 与命令行两种运行方式

## 目录结构

```
ac-grabber/
├── ac_grabber/           # 核心 Python 包
│   ├── config.py         # 配置读写
│   ├── rules.py          # 定制稿筛选规则
│   ├── browser.py        # Edge CDP 连接与页面操作
│   ├── edge_launcher.py  # Edge 调试模式启动
│   ├── worker.py         # 抢稿主循环
│   └── win32_bg.py       # Windows 后台窗口处理
├── app_gui.py            # GUI 入口
├── grab.py               # 命令行入口
├── start-edge.bat        # 以调试模式启动 Edge
├── run-cli.bat           # 启动命令行抢稿
├── build.bat             # 打包为 exe
├── requirements.txt
├── config.json.example   # 配置模板（复制为 config.json）
└── README.md
```

首次运行会自动生成 `config.json`；也可复制 `config.json.example` 并修改。

## 环境要求

- Windows 10/11
- Python 3.10+
- Microsoft Edge

## 安装

```bat
cd ac-grabber
pip install -r requirements.txt
playwright install chromium
```

## 使用步骤

### GUI（推荐）

```bat
python app_gui.py
```

1. 点击「启动 Edge」，确认稿池页已登录
2. 选择公众号、填写定制稿归属名
3. 点击「开始抢稿」

### 命令行

1. 关闭所有 Edge 窗口
2. 双击 `start-edge.bat`，确认已登录稿池页
3. 双击 `run-cli.bat` 或执行 `python grab.py`

## 定制稿规则

| 标题末尾 | 行为 |
|----------|------|
| 无括号 | 普通稿，可抢 |
| `(你的名字)` | 你的定制稿，可抢 |
| `(其他人名)` | 他人定制稿，跳过 |
| `(9)` 等非汉字 | 可抢 |

标题开头或中间的括号（如「（横屏）」）不影响判断。

## 配置

编辑 `config.json`：

| 字段 | 说明 |
|------|------|
| 人名 | 定制稿归属名，须与标题末尾括号一致 |
| 抢稿上限 | `0` = 不限篇数 |
| 刷新间隔 | 秒，默认 `0.3`，最小 `0.1` |
| 目标公众号 | 数组，名称须与页面 tag 完全一致 |

可选公众号：`小金AI新科技`、`康健求真`、`大宝说创业`、`AI壹号`、`秦刚·个人IP`、`秦刚头条`

## 打包

```bat
build.bat
```

输出：

- `dist/ac-grabber-gui.exe`
- `dist/start-edge.bat`

## 注意事项

- Edge 须以 `--remote-debugging-port=9222` 启动
- 抢稿脚本只操作稿池标签页，其他标签页可照常使用
- `config.json` 含个人设置，已在 `.gitignore` 中排除

## 许可

仅供学习与个人使用，请遵守目标网站服务条款。

## Author

[朱昊天 (zhtinist)](https://github.com/zhtinist)
