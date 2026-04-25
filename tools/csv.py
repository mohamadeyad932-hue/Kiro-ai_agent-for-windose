"""
diagnose_csv.py — سكربت تشخيصي لفحص محتوى الـ CSV ومسارات الصور
شغّله مرة واحدة لمعرفة المشكلة الحقيقية
"""
import os
import csv
import sys
sys.stdout.reconfigure(encoding="utf-8")

CSV_PATH = r"C:\Kiro-Project\metadata\ground_truth.csv"

print("=" * 70)
print("فحص ملف الـ CSV")
print("=" * 70)

with open(CSV_PATH, "r", encoding="utf-8-sig") as f:
    first_line = f.readline()

delimiter = ";" if first_line.count(";") > first_line.count(",") else ","
print(f"الفاصل: '{delimiter}'")

with open(CSV_PATH, "r", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f, delimiter=delimiter)
    rows   = [{k.strip(): v.strip() for k, v in row.items()} for row in reader]

print(f"عدد السجلات: {len(rows)}")
print()

# اطبع أول 5 صفوف كاملة
print("─── أول 5 صفوف في الـ CSV ───")
for i, row in enumerate(rows[:5]):
    print(f"\nصف {i+1}:")
    for k, v in row.items():
        print(f"  {k!r:25} → {v!r}")

print()

# افحص Full_Path مباشرة
full_path_col = "Full_Path"
if full_path_col in rows[0]:
    print("─── فحص أول 5 مسارات Full_Path ───")
    for row in rows[:5]:
        p = row.get(full_path_col, "").strip()
        exists = os.path.isfile(p)
        print(f"  {'✅' if exists else '❌'} {p}")

    print()
    # جرّب تصحيح المسار بتغيير الجزء الأول
    sample_path = rows[0].get(full_path_col, "")
    if sample_path:
        parts = sample_path.replace("\\", "/").split("/")
        print(f"─── تحليل المسار ───")
        print(f"  المسار الكامل : {sample_path}")
        print(f"  اسم الملف فقط : {os.path.basename(sample_path)}")
        print(f"  المجلد الأب   : {os.path.dirname(sample_path)}")

print()
print("─── الأقراص والمجلدات الموجودة ───")
for drive in ["C:\\", "D:\\", "E:\\"]:
    if os.path.exists(drive):
        print(f"  {drive} موجود")

kiro = r"C:\Kiro-Project"
if os.path.isdir(kiro):
    print(f"\n  محتوى {kiro}:")
    for item in os.listdir(kiro):
        full = os.path.join(kiro, item)
        kind = "📁" if os.path.isdir(full) else "📄"
        print(f"    {kind} {item}")

    archive = os.path.join(kiro, "archive")
    if os.path.isdir(archive):
        print(f"\n  محتوى {archive}:")
        for item in os.listdir(archive):
            full = os.path.join(archive, item)
            kind = "📁" if os.path.isdir(full) else "📄"
            print(f"    {kind} {item}")