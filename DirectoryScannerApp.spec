# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['DirectoryScannerApp.py'],
    pathex=['G:\\Python_Code\\DirectoryScannerApp'],
    binaries=[],
    datas=[
        ('icon.ico', '.'),
        ('static', 'static'),
    ],
    hiddenimports=[
        'PySide6.QtCore',
        'PySide6.QtGui', 
        'PySide6.QtWidgets',
        'PySide6.QtSql',
        'PySide6.QtNetwork',
        'pypinyin',
        'sqlite3',
        'hashlib',
        'json',
        'urllib',
        'http.server',
        'socketserver',
        'threading',
        'concurrent.futures',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'torch',
        'torchvision', 
        'torchaudio',
        'tensorflow',
        'tensorflow_core',
        'cupy',
        'Cython',
        'matplotlib',
        'numpy',
        'PIL',
        'cv2',
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='DirectoryScannerApp',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='DirectoryScannerApp',
)