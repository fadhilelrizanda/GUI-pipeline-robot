# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main_script.py'],
    pathex=['.'],  # Adjust the path to your project directory if necessary
    binaries=[],
    datas=[],
    hiddenimports=[
        'paramiko', 'picommand', 'cryptography', 'pyasn1', 'bcrypt', 'pynacl',
        'asn1crypto', 'six', 'cffi', 'idna', 'pycparser'
    ],
    hookspath=['./hooks'],  # Specify the hooks directory
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='RobotPipeline',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='RobotPipeline'
)
