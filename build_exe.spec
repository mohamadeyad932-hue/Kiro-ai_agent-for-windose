# -*- mode: python ; coding: utf-8 -*-
"""
Kiro AI - PyInstaller Build Spec (المطور والمحدث)
═══════════════════════════════════════════════
تم إصلاح مشاكل الانهيار ونقص ملفات PyTorch الديناميكية
التشغيل: pyinstaller build_exe.spec
"""

import os
import sys
import glob

PROJECT_ROOT = os.path.dirname(os.path.abspath(SPEC))

# ─── مساعد: جمع ملفات .pyc من مجلد معين ───
def collect_pyc(dir_name, dest):
    """جمع ملفات .pyc المُجمَّعة من مجلد"""
    full = os.path.join(PROJECT_ROOT, dir_name)
    pairs = []
    for f in glob.glob(os.path.join(full, '*.pyc')):
        pairs.append((f, dest))
    return pairs

# ─── ملفات البيانات ───
datas = [
    # واجهة المستخدم (تبقى .py لأنها مُدمجة في الـ exe عبر Analysis)
    (os.path.join(PROJECT_ROOT, 'uiux_kiro_pyqt', '*.py'),      'uiux_kiro_pyqt'),
    (os.path.join(PROJECT_ROOT, 'uiux_kiro_pyqt', 'icons'),     'uiux_kiro_pyqt/icons'),

    # نماذج الذكاء الاصطناعي
    (os.path.join(PROJECT_ROOT, 'models'),                        'models'),
]

# ─── صورة الخلفية ───
for img in ['Picture1.png', 'Gemini_Generated_Image_rrv8szrrv8szrrv8.png']:
    p = os.path.join(PROJECT_ROOT, 'uiux_kiro_pyqt', img)
    if os.path.exists(p):
        datas.append((p, 'uiux_kiro_pyqt'))

# ─── إضافة السكربتات المُجمَّعة (.pyc) بدل .py ───
script_dirs = {
    'Processing text files':                          'Processing text files',
    'Processing image':                               'Processing image',
    'clustring_files':                                'clustring_files',
    'clustring_imge':                                 'clustring_imge',
    'creat folders for flie_text  and name':          'creat folders for flie_text  and name',
    'creat folders for image and name':               'creat folders for image and name',
    'dawnload_models':                                'dawnload_models',
}

for src_dir, dest_dir in script_dirs.items():
    datas.extend(collect_pyc(src_dir, dest_dir))

# run_project.pyc في المجلد الرئيسي
rp_pyc = os.path.join(PROJECT_ROOT, 'run_project.pyc')
if os.path.exists(rp_pyc):
    datas.append((rp_pyc, '.'))
else:
    datas.append((os.path.join(PROJECT_ROOT, 'run_project.py'), '.'))

from PyInstaller.utils.hooks import collect_submodules

# ─── الاستيرادات المخفية (Hidden Imports) ───
hiddenimports = [
    'PyQt6.QtWidgets', 'PyQt6.QtCore', 'PyQt6.QtGui', 'PyQt6.sip',
    'fitz', 'docx', 'PIL', 'PIL.Image',
    'imagehash', 'pywt',
    'sklearn', 'sklearn.cluster',
    'numpy', 'scipy', 'pandas',
    'json', 'tempfile', 'argparse', 'shutil',
    'sentence_transformers',
    'encodings', 'encodings.utf_8', 'encodings.ascii',
    'encodings.latin_1', 'encodings.cp1252',
    'theme', 'translations', 'welcome_screen',
    'config_screen', 'processing_screen',
    'dashboard_screen', 'settings_screen', 'about_screen',
    
    # 🌟 [إصلاح] استدعاء ملفات الـ RPC المفقودة في نظام المجموعات
    'torch.distributed.rpc',
    
    # 🌟 [إصلاح] استدعاء ملفات الـ Dynamo Polyfills المفقودة لتشغيل CLIPProcessor بأمان
    'torch._dynamo.polyfills.fx',
    'torch._dynamo.polyfills.builtins',
    'torch._dynamo.polyfills.itertools',
    'torch._dynamo.polyfills.os',
    'torch._dynamo.polyfills.sys',
]

# ⚠️ [تنبيه هامن جداً] تم تعطيل السطر التالي لمنع انهيار الذاكرة العشوائية (Access Violation)
# hiddenimports += collect_submodules('torch')

# تضمين باقي المكتبات الفرعية الضرورية الأخرى
hiddenimports += collect_submodules('torchvision')
hiddenimports += collect_submodules('transformers')
hiddenimports += collect_submodules('sentence_transformers')
hiddenimports += collect_submodules('sklearn')

# ─── أيقونة التطبيق ───
icon_path = os.path.join(PROJECT_ROOT, 'uiux_kiro_pyqt', 'icons', 'kiro_icon.ico')
if not os.path.exists(icon_path):
    icon_path = None

# ═══════════════════════════════════════════════
a = Analysis(
    [os.path.join(PROJECT_ROOT, 'uiux_kiro_pyqt', 'main.py')],
    pathex=[PROJECT_ROOT, os.path.join(PROJECT_ROOT, 'uiux_kiro_pyqt')],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib', 'tkinter', 'setuptools', 'pip', 'wheel',
        # منع الملف الدقيق الذي يفجر ويقطع عملية البناء
        'torch.distributed.algorithms._optimizer_overlap',
        'triton', 'tensorboard', 'numba',
        'IPython', 'colorama', 'networkx'
    ],
    noarchive=True,
    optimize=0,
)

pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz, a.scripts, [],
    exclude_binaries=True,
    name='KiroAI',
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
    icon=icon_path,
)

coll = COLLECT(
    exe, a.binaries, a.datas,
    strip=False, upx=False, upx_exclude=[],
    name='KiroAI',
)