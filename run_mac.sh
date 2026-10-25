#!/bin/bash
# Easy_Cidaren macOS 一键启动脚本
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo "=========================================="
echo "         Easy_Cidaren macOS 启动器         "
echo "=========================================="

if [ ! -d ".venv" ]; then
    echo "未检测到虚拟环境 .venv，正在使用 Python 3.12 创建..."
    if command -v uv &> /dev/null; then
        uv venv .venv --python 3.12
        uv pip install -r requirements.txt --python .venv/bin/python
    else
        python3 -m venv .venv
        source .venv/bin/activate
        pip install -r requirements.txt
    fi
fi

export PATH="$DIR/.venv/bin:$PATH"

echo "正在启动 Easy_Cidaren GUI..."
"$DIR/.venv/bin/python" "$DIR/main.py"
