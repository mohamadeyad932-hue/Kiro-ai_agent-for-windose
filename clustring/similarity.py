import os
import sys
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import AgglomerativeClustering

# ─── 1. استيراد المتجهات وحساب التشابه ───
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from text_file_prossing.desktop_vectors import desktop_vectors

file_names = list(desktop_vectors.keys())
vectors = list(desktop_vectors.values())

# حساب التشابه الجيبي
similarity_matrix = cosine_similarity(vectors)

# ─── 2. مرحلة التجميع (Clustering) ───
# الخوارزمية تحتاج إلى "مسافة" وليس "تشابه". 
# المسافة ببساطة هي: 1 ناقص التشابه. (تشابه 95% يعني مسافة 0.05)
distance_matrix = 1 - similarity_matrix

# تأمين الأرقام لتجنب أي أخطاء عشرية صغيرة جداً (قيم سالبة وهمية)
distance_matrix = np.clip(distance_matrix, 0, 1)

# ⚙️ إعداد حساسية الفرز (هذا هو الرقم السحري الذي يمكنك تعديله)
# 0.05 تعني أننا نطلب تشابهاً بنسبة 95% على الأقل لجمع الملفات
# إذا تم جمع ملفات غير متشابهة، قم بتقليل الرقم إلى 0.03 (أي 97%)
# إذا تم فصل ملفات متشابهة، قم بزيادة الرقم إلى 0.08 (أي 92%)
THRESHOLD = 0.01

clustering_model = AgglomerativeClustering(
    n_clusters=None, 
    metric='precomputed', 
    linkage='average', 
    distance_threshold=THRESHOLD
)

# إعطاء كل ملف رقم المجلد الخاص به
labels = clustering_model.fit_predict(distance_matrix)

# ─── 3. عرض النتائج ───
print(f"تم فرز الملفات إلى {len(set(labels))} مجلدات مختلفة (عتبة التشابه: {100 - (THRESHOLD*100)}%):\n")

# ترتيب الملفات في قاموس لتسهيل الطباعة
clusters = {}
for file_name, label in zip(file_names, labels):
    if label not in clusters:
        clusters[label] = []
    clusters[label].append(file_name)

# طباعة كل مجلد والملفات التي بداخله
for cluster_id, files in sorted(clusters.items()):
    print(f"📁 المجلد رقم {cluster_id + 1} (يحتوي على {len(files)} ملف):")
    for f in files:
        print(f"   - {f}")
    print("-" * 45)