#!/usr/bin/env python3
"""
实时查看日志工具
"""
import os
import sys
import time
from pathlib import Path

def tail_file(filepath, n=50):
    """显示文件最后 n 行"""
    if not os.path.exists(filepath):
        print(f"日志文件不存在: {filepath}")
        return []

    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        return lines[-n:]

def watch_logs():
    """实时监控所有日志文件"""
    log_dir = Path("logs")

    log_files = {
        "Audio Service": log_dir / "audio_service.log",
        "VAD": log_dir / "vad.log",
        "Transcriber": log_dir / "transcriber.log"
    }

    print("=" * 80)
    print("ClassAudio 日志监控")
    print("=" * 80)
    print()

    # 显示每个日志的最后几行
    for name, filepath in log_files.items():
        print(f"\n{'=' * 40}")
        print(f"{name} - {filepath}")
        print('=' * 40)

        lines = tail_file(filepath, n=20)
        if lines:
            for line in lines:
                print(line.rstrip())
        else:
            print("(无内容)")

    print("\n" + "=" * 80)
    print("按 Ctrl+C 退出")
    print("=" * 80)

    # 持续监控（实时显示新增内容）
    file_positions = {}
    for name, filepath in log_files.items():
        if filepath.exists():
            with open(filepath, 'r', encoding='utf-8') as f:
                f.seek(0, 2)  # 移到文件末尾
                file_positions[str(filepath)] = f.tell()
        else:
            file_positions[str(filepath)] = 0

    try:
        while True:
            time.sleep(0.5)

            for name, filepath in log_files.items():
                if not filepath.exists():
                    continue

                with open(filepath, 'r', encoding='utf-8') as f:
                    pos = file_positions[str(filepath)]
                    f.seek(pos)
                    new_lines = f.readlines()

                    if new_lines:
                        print(f"\n[{name}]")
                        for line in new_lines:
                            print(line.rstrip())

                        file_positions[str(filepath)] = f.tell()

    except KeyboardInterrupt:
        print("\n\n日志监控已停止")

if __name__ == "__main__":
    watch_logs()
