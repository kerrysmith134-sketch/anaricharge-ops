#!/usr/bin/env python3
"""薄包装：真正的实现随站点仓库走（06-site/anari-new-site/scripts/tools/ci-static-checks.py）。

为什么这样分：CI 在仓库内运行，脚本必须提交进仓库才能被执行；
而运营工作区也常直接调用它做本地验收。只保留一份实现，避免两边漂移。
"""
import os
import runpy
import sys

REPO_IMPL = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                         "06-site", "anari-new-site", "scripts", "tools", "ci-static-checks.py")
if not os.path.exists(REPO_IMPL):
    sys.exit(f"缺少实现：{REPO_IMPL}")
sys.argv[0] = REPO_IMPL
runpy.run_path(REPO_IMPL, run_name="__main__")
