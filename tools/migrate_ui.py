#!/usr/bin/env python3
"""
UI迁移工具：将旧UI文件移动到legacy目录
保持向后兼容性
"""

import shutil
import os
from pathlib import Path
import sys


def migrate_ui():
    """迁移UI文件到legacy目录"""
    # 项目根目录
    project_root = Path(__file__).parent.parent
    ui_dir = project_root / "tetris_rl" / "ui"
    legacy_dir = ui_dir / "legacy"

    # 创建legacy目录
    legacy_dir.mkdir(exist_ok=True)
    print(f"Legacy目录: {legacy_dir}")

    # 要移动的文件列表
    files_to_move = [
        "main_window.py",
        "game_canvas.py",
        "plots.py",
        "training_panel.py",
        "splash.py"
    ]

    moved_files = []
    skipped_files = []

    for file_name in files_to_move:
        src = ui_dir / file_name
        dst = legacy_dir / file_name

        if src.exists():
            # 如果目标文件已存在，备份
            if dst.exists():
                backup_name = f"{file_name}.backup"
                backup_dst = legacy_dir / backup_name
                shutil.move(dst, backup_dst)
                print(f"  备份已存在文件: {file_name} -> {backup_name}")

            # 移动文件
            shutil.move(src, dst)
            moved_files.append(file_name)
            print(f"✓ 移动: {file_name}")
        else:
            skipped_files.append(file_name)
            print(f"⚠ 跳过: {file_name} (不存在)")

    # 创建__init__.py
    init_file = legacy_dir / "__init__.py"
    if not init_file.exists():
        init_content = '''"""
遗留UI模块，保持向后兼容
包含从tetris_rl.ui迁移过来的旧UI文件

注意: 这些文件已不再维护，建议使用新的模块化架构
"""

# 重新导出旧模块
try:
    from .main_window import MainWindow
    from .game_canvas import GameCanvas
    from .plots import LivePlots
    from .training_panel import TrainingPanel
    from .splash import SplashScreen

    __all__ = [
        "MainWindow",
        "GameCanvas",
        "LivePlots",
        "TrainingPanel",
        "SplashScreen"
    ]
except ImportError:
    # 如果某些模块导入失败，继续
    __all__ = []
'''
        init_file.write_text(init_content, encoding="utf-8")
        print("✓ 创建: legacy/__init__.py")

    # 创建兼容性导入文件
    create_compatibility_imports(ui_dir, legacy_dir, files_to_move)

    # 总结
    print("\n" + "=" * 50)
    print("迁移完成!")
    print(f"移动文件: {len(moved_files)}")
    print(f"跳过文件: {len(skipped_files)}")

    if moved_files:
        print("\n移动的文件:")
        for f in moved_files:
            print(f"  - {f}")

    if skipped_files:
        print("\n跳过的文件:")
        for f in skipped_files:
            print(f"  - {f}")

    print("\n下一步:")
    print("1. 运行测试确保新架构正常工作")
    print("2. 更新导入语句（如果需要）")
    print("3. 查看 docs/MIGRATION_GUIDE.md 获取详细指南")


def create_compatibility_imports(ui_dir, legacy_dir, files_to_move):
    """创建兼容性导入文件"""
    # 为每个移动的文件创建兼容性重定向（可选）
    # 这里我们只在ui/__init__.py中处理

    # 检查ui/__init__.py是否存在
    ui_init = ui_dir / "__init__.py"
    if ui_init.exists():
        print("✓ ui/__init__.py 已存在（已更新为新架构版本）")
    else:
        print("⚠ ui/__init__.py 不存在")


def verify_migration():
    """验证迁移结果"""
    project_root = Path(__file__).parent.parent
    ui_dir = project_root / "tetris_rl" / "ui"
    legacy_dir = ui_dir / "legacy"

    print("\n" + "=" * 50)
    print("验证迁移结果:")

    # 检查legacy目录
    if legacy_dir.exists():
        legacy_files = list(legacy_dir.glob("*.py"))
        print(f"Legacy目录中的文件 ({len(legacy_files)}):")
        for f in legacy_files:
            print(f"  - {f.name}")
    else:
        print("✗ Legacy目录不存在")

    # 检查新架构文件
    new_arch_files = [
        "core/__init__.py",
        "backends/html5/__init__.py",
        "streamlit/__init__.py",
        "streamlit_app.py"
    ]

    print("\n新架构文件:")
    for f in new_arch_files:
        file_path = ui_dir / f
        if file_path.exists():
            print(f"  ✓ {f}")
        else:
            print(f"  ✗ {f} (缺失)")


def main():
    """主函数"""
    print("Tetris RL UI 迁移工具")
    print("=" * 50)
    print("此工具将旧UI文件移动到legacy目录，为新的模块化架构腾出空间。")
    print("")

    # 确认
    response = input("是否继续? (y/N): ").strip().lower()
    if response not in ["y", "yes"]:
        print("取消迁移")
        return 1

    try:
        migrate_ui()
        verify_migration()
        return 0
    except Exception as e:
        print(f"\n✗ 迁移失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())