# build.spec
import os

from PyInstaller.building.build_main import Analysis, PYZ, EXE, COLLECT
from PyInstaller.utils.hooks import (
    collect_data_files,
    collect_dynamic_libs,
    collect_submodules,
    copy_metadata,
)

block_cipher = None

# 1. collect package assets
uiautomator2_datas = collect_data_files("uiautomator2")
webview_datas = collect_data_files("webview")
pythonnet_datas = collect_data_files("pythonnet")
clr_loader_datas = collect_data_files("clr_loader")

package_metadata = (
    copy_metadata("pywebview")
    + copy_metadata("pythonnet")
    + copy_metadata("clr_loader")
)

pythonnet_binaries = collect_dynamic_libs("pythonnet")

extra_hiddenimports = (
    collect_submodules("pythonnet")
    + collect_submodules("clr_loader")
)

# 2. Your project data. Do not copy Python bytecode or excluded source files.
def collect_project_data(source_dir, destination_dir, excluded_files=()):
    excluded = {os.path.normcase(os.path.normpath(path)) for path in excluded_files}
    collected = []

    for root, dirs, files in os.walk(source_dir):
        dirs[:] = [directory for directory in dirs if directory != '__pycache__']
        for filename in files:
            source_path = os.path.join(root, filename)
            relative_path = os.path.relpath(source_path, source_dir)
            if os.path.normcase(os.path.normpath(relative_path)) in excluded:
                continue
            collected.append((source_path, os.path.join(destination_dir, relative_path)))
    return collected


# 3. Your project data
project_datas = [
    ('templates', 'templates'),
    ('static', 'static'),
    ('Trust', 'Trust'),
    ('blueprints', 'blueprints'),
] + collect_project_data(
    'Boost',
    'Boost',
    excluded_files=('fast_seeding.py',),
)

# 4. Merge data
datas = (
    uiautomator2_datas
    + webview_datas
    + pythonnet_datas
    + clr_loader_datas
    + package_metadata
    + project_datas
)


a = Analysis(
    ['app.py'],
    pathex=['.'],
    binaries=[
        ('adb/windows/adb.exe', 'adb/windows'),
        ('adb/windows/AdbWinApi.dll', 'adb/windows'),
        ('adb/windows/AdbWinUsbApi.dll', 'adb/windows'),
        *pythonnet_binaries,
    ],
    datas=datas,
    hiddenimports=[
        # APScheduler
        'apscheduler.triggers.cron',
        'apscheduler.triggers.date',
        'apscheduler.triggers.interval',
        'apscheduler.executors.pool',
        'apscheduler.executors.base',
        'apscheduler.jobstores.memory',
        'apscheduler.jobstores.base',

        # Google
        'google.oauth2.service_account',
        'google.auth.transport.requests',
        'googleapiclient.discovery',
        'gspread',

        # Flask
        'flask',
        'werkzeug.utils',
        'werkzeug.serving',

        # multiprocessing
        'multiprocessing.spawn',
        'multiprocessing.forkserver',

        # your modules
        'Boost.worker',
        'Boost.worker_seeding',
        'Boost.Tool',
        'Trust.trust',

         # PyWebView
        'webview',
        'webview.platforms',
        'webview.platforms.edgechromium',
        'webview.platforms.winforms',
        *extra_hiddenimports,
    ],
    hookspath=[],
    runtime_hooks=[],
    # Must stay excluded: it is neither copied as project data nor analyzed as a module.
    excludes=['Boost.fast_seeding', 'fast_seeding'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='T1kTool',
    debug=False,
    strip=False,
    upx=False,
    console=False,
    icon='static/icon.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    name='T1kTool',
)
