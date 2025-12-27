# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all
from PyInstaller.utils.hooks import copy_metadata

datas = []
binaries = []
hiddenimports = ['tensorflow', 'tensorflow.python', 'tensorflow.python.ops', 'keras_facenet', 'mtcnn', 'mtcnn.assets', 'cv2', 'numpy', 'PIL', 'PIL._tkinter_finder', 'openpyxl', 'openpyxl.cell._writer', 'sklearn', 'sklearn.utils._weight_vector', 'sklearn.neighbors._typedefs', 'sklearn.utils._typedefs', 'sklearn.metrics.pairwise', 'gdown', 'tqdm', 'queue', 'logging.handlers']
datas += copy_metadata('tensorflow')
datas += copy_metadata('keras-facenet')
datas += copy_metadata('mtcnn')
tmp_ret = collect_all('tensorflow')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('keras_facenet')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('mtcnn')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [('v', None, 'OPTION')],
    exclude_binaries=True,
    name='Attendio',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['logo.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='Attendio',
)
