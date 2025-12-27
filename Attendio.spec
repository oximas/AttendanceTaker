# -*- mode: python ; coding: utf-8 -*-
"""
AttendanceTracker.spec
PyInstaller specification file for AttendanceTracker.
"""

import os
from PyInstaller.utils.hooks import collect_data_files

# Collect MTCNN and Keras-FaceNet data files
mtcnn_datas = collect_data_files('mtcnn')
keras_facenet_datas = collect_data_files('keras_facenet')

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('settings_template.json', '.'),
    ] + mtcnn_datas + keras_facenet_datas,  # ADD THIS LINE - includes model weights
    hiddenimports=[
        'tensorflow',
        'keras_facenet',
        'mtcnn',
        'mtcnn.assets',  # ADD THIS - critical for MTCNN
        'cv2',
        'numpy',
        'PIL',
        'openpyxl',
        'sklearn',
        'sklearn.utils._weight_vector',
        'sklearn.metrics.pairwise',  # ADD THIS - needed for cosine_similarity
        'gdown',
        'tqdm',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name='AttendanceTracker',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # Set to True to see console for debugging
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='logo.ico' if os.path.exists('logo.ico') else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='AttendanceTracker',
)