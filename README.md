# AC Grabber

An auto-claiming assistant for AI Copywriter. It drives Microsoft Edge in CDP debugging mode to keep refreshing the [submission pool](https://ai-copywriter.risevideo.ai/distribute) and claims eligible content submissions.

The repository and directory are both named **`ac-grabber`**, matching the Python package `ac_grabber`.

## Features

- Reuses the local Edge login session, so no separate cookie setup is needed
- Filters by WeChat Official Account and only claims submissions under the selected accounts
- Custom-submission rule: a submission is claimed only when the name in the parentheses at the **end** of its title is yours; custom submissions for other people are skipped
- Configurable refresh interval and maximum number of claims
- Runs as a GUI or from the command line

## Project Structure

```
ac-grabber/
├── ac_grabber/           # Core Python package
│   ├── config.py         # Config read/write
│   ├── rules.py          # Custom-submission filtering rules
│   ├── browser.py        # Edge CDP connection and page actions
│   ├── edge_launcher.py  # Launches Edge in debugging mode
│   ├── worker.py         # Main claiming loop
│   └── win32_bg.py       # Windows background-window handling
├── app_gui.py            # GUI entry point
├── grab.py               # CLI entry point
├── start-edge.bat        # Launches Edge in debugging mode
├── run-cli.bat           # Starts the CLI grabber
├── build.bat             # Packages into an .exe
├── requirements.txt
├── config.json.example   # Config template (copy to config.json)
└── README.md
```

`config.json` is generated automatically on the first run. You can also copy `config.json.example` and edit it.

## Requirements

- Windows 10/11
- Python 3.10+
- Microsoft Edge

## Installation

```bat
cd ac-grabber
pip install -r requirements.txt
playwright install chromium
```

## Usage

### GUI (Recommended)

```bat
python app_gui.py
```

1. Click 「启动 Edge」 (Launch Edge) and make sure you are logged in to the submission pool page
2. Select the Official Accounts and enter the name used for custom submissions
3. Click 「开始抢稿」 (Start Grabbing)

### Command Line

1. Close all Edge windows
2. Double-click `start-edge.bat` and make sure you are logged in to the submission pool page
3. Double-click `run-cli.bat`, or run `python grab.py`

## Custom-Submission Rules

| End of title | Behavior |
|----------|------|
| No parentheses | Regular submission, claimable |
| `(your name)` | Your custom submission, claimable |
| `(someone else's name)` | Someone else's custom submission, skipped |
| `(9)` or other non-Chinese-character content | Claimable |

Parentheses at the start or in the middle of a title (such as 「（横屏）」, "landscape") do not affect the decision.

## Configuration

Edit `config.json`. The keys are in Chinese and must stay as they are:

| Key | Description |
|------|------|
| `人名` | Name for custom submissions; must match the name in the parentheses at the end of the title |
| `抢稿上限` | Maximum number of claims; `0` = unlimited |
| `刷新间隔` | Refresh interval in seconds; default `0.3`, minimum `0.1` |
| `目标公众号` | Array of target Official Accounts; names must exactly match the tags on the page |

Available Official Accounts: `小金AI新科技`, `康健求真`, `大宝说创业`, `AI壹号`, `秦刚·个人IP`, `秦刚头条`

## Packaging

```bat
build.bat
```

Output:

- `dist/ac-grabber-gui.exe`
- `dist/start-edge.bat`

## Notes

- Edge must be launched with `--remote-debugging-port=9222`
- The script only operates on the submission pool tab; other tabs can be used normally
- `config.json` contains personal settings and is excluded in `.gitignore`

## License

For learning and personal use only. Please follow the target website's terms of service.

## Author

[Haotian Zhu (zhtinist)](https://github.com/zhtinist)
