#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR/get token/fetch_token"

echo "=========================================="
echo "      Easy_Cidaren macOS Token 抓取工具    "
echo "=========================================="
echo "1. 正在启动系统代理与 mitmdump..."
echo "2. 请在电脑端微信将 https://app.vocabgo.com/student/ 发送到任意聊天框并点击打开"
echo "3. 捕获到 Token 后会自动保存到 token.txt"
echo "=========================================="
export PATH="$DIR/.venv/bin:$PATH"
"$DIR/.venv/bin/python" main.py
