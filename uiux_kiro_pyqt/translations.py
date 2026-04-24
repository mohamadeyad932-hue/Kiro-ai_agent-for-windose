"""
Kiro AI - Translation System
نظام الترجمة ثنائي اللغة (عربي / إنجليزي)
"""
from PyQt6.QtCore import Qt, QObject, pyqtSignal


class LanguageManager(QObject):
    """مدير اللغة المركزي - يبث إشارة عند تغيير اللغة"""
    language_changed = pyqtSignal(str)  # "ar" or "en"

    def __init__(self):
        super().__init__()
        self._lang = "ar"  # اللغة الافتراضية

    @property
    def lang(self):
        return self._lang

    @property
    def is_rtl(self):
        return self._lang == "ar"

    @property
    def direction(self):
        return Qt.LayoutDirection.RightToLeft if self.is_rtl else Qt.LayoutDirection.LeftToRight

    @property
    def align(self):
        """محاذاة النص حسب اللغة.
        مع setLayoutDirection(RTL)، Qt يعكس AlignLeft تلقائياً
        إلى الجهة اليمنى فيزيائياً. لذلك نستخدم AlignLeft دائماً.
        """
        return Qt.AlignmentFlag.AlignLeft

    def set_language(self, lang: str):
        if lang != self._lang:
            self._lang = lang
            self.language_changed.emit(lang)

    def toggle(self):
        self.set_language("en" if self._lang == "ar" else "ar")

    def t(self, key: str) -> str:
        """ترجمة نص حسب المفتاح"""
        return STRINGS.get(key, {}).get(self._lang, key)


# ─── المثيل العام (Singleton) ───
lang_manager = LanguageManager()


def t(key: str) -> str:
    """اختصار للترجمة السريعة"""
    return lang_manager.t(key)


# ═══════════════════════════════════════════════════════════════
#  جميع النصوص في التطبيق
# ═══════════════════════════════════════════════════════════════

STRINGS = {
    # ─── عام ───
    "app_title": {
        "ar": "Kiro AI - مساعد الملفات الذكي",
        "en": "Kiro AI - Smart File Assistant",
    },
    "terminal_title": {
        "ar": "Kiro AI Core Terminal",
        "en": "Kiro AI Core Terminal",
    },
    "version": {
        "ar": "Kiro AI v2.5.0",
        "en": "Kiro AI v2.5.0",
    },
    "lang_btn": {
        "ar": "EN",
        "en": "ع",
    },
    "back_btn": {
        "ar": "→",
        "en": "←",
    },

    # ─── أسماء الصفحات ───
    "page_sp": {"ar": "نظام الترحيب", "en": "Welcome"},
    "page_cf": {"ar": "التهيئة", "en": "Configuration"},
    "page_pr": {"ar": "نواة التنظيم", "en": "Processing"},
    "page_db": {"ar": "التحليل والنتائج", "en": "Analytics"},
    "page_st": {"ar": "إعدادات النظام", "en": "Settings"},
    "page_ab": {"ar": "عن المشروع", "en": "About"},

    # ─── الشريط الجانبي ───
    "sidebar_brand": {"ar": "Kiro AI", "en": "Kiro AI"},
    "sidebar_subtitle": {"ar": "Neural Organizer", "en": "Neural Organizer"},
    "sidebar_cat1": {"ar": "الوحدات النشطة", "en": "Active Modules"},
    "sidebar_cat2": {"ar": "بروتوكولات أخرى", "en": "Other Protocols"},
    "sidebar_status1": {"ar": "الشبكة العصبية مستقرة", "en": "Neural network stable"},
    "sidebar_status2": {"ar": "جاهز لاستقبال الأوامر", "en": "Ready for commands"},

    "nav_sp": {"ar": "نظام الترحيب", "en": "Welcome"},
    "nav_cf": {"ar": "التهيئة", "en": "Config"},
    "nav_pr": {"ar": "نواة التنظيم", "en": "Processing"},
    "nav_db": {"ar": "التحليل والنتائج", "en": "Analytics"},
    "nav_st": {"ar": "إعدادات النظام", "en": "Settings"},
    "nav_ab": {"ar": "عن المشروع", "en": "About"},

    # ─── شاشة الترحيب ───
    "welcome_badge": {
        "ar": "معالجة محلية 100% | آمن",
        "en": "100% Local Processing | Secure",
    },
    "welcome_title": {
        "ar": "مرحباً بك في وحدة Kiro AI",
        "en": "Welcome to Kiro AI",
    },
    "welcome_desc": {
        "ar": "نظام ذكاء اصطناعي متقدم مصمم لقراءة، تحليل، وهيكلة بياناتك المبعثرة\nفي ثوانٍ معدودة. لا تدخل بشري مطلوب.",
        "en": "An advanced AI system designed to read, analyze, and organize\nyour scattered data in seconds. No human intervention needed.",
    },
    "welcome_btn": {
        "ar": "  تهيئة النظام الآن  ▶",
        "en": "▶  Initialize System Now",
    },
    "feat1_title": {"ar": "تشفير وخصوصية", "en": "Encryption & Privacy"},
    "feat1_desc": {
        "ar": "الخوارزمية تعمل محلياً على\nنواتك. لا اتصال خارجي.",
        "en": "Algorithm runs locally on\nyour device. No external connection.",
    },
    "feat2_title": {"ar": "شبكة عصبية دقيقة", "en": "Precise Neural Network"},
    "feat2_desc": {
        "ar": "يفهم النصوص والصور\nويصنفها كعقل بشري رقمي.",
        "en": "Understands text and images\nclassifying them like a digital brain.",
    },
    "feat3_title": {"ar": "سرعة فائقة", "en": "Ultra Speed"},
    "feat3_desc": {
        "ar": "مزامنة وهيكلة آلاف الملفات\nخلال أجزاء من الثانية.",
        "en": "Sync and organize thousands\nof files in milliseconds.",
    },

    # ─── شاشة التهيئة ───
    "config_title": {"ar": "إحداثيات المعالجة", "en": "Processing Coordinates"},
    "config_sub": {
        "ar": "حدد مسارات البيانات التي تريد أن تحللها الشبكة العصبية.",
        "en": "Select the data paths you want the neural network to analyze.",
    },
    "config_paths_title": {"ar": "نقاط الإدخال (المسارات)", "en": "Input Points (Paths)"},
    "config_desktop": {"ar": "سطح المكتب", "en": "Desktop"},
    "config_desktop_sub": {"ar": "الواجهة الرئيسية للنظام", "en": "Main system interface"},
    "config_downloads": {"ar": "عقدة التنزيلات", "en": "Downloads"},
    "config_downloads_sub": {"ar": "البيانات الواردة حديثاً", "en": "Recently received data"},
    "config_documents": {"ar": "أرشيف المستندات", "en": "Document Archive"},
    "config_documents_sub": {"ar": "السجلات والملفات النصية", "en": "Records and text files"},
    "config_types_title": {"ar": "أنواع البيانات المستهدفة", "en": "Target Data Types"},
    "config_text_data": {"ar": "البيانات النصية (PDF, DOCX)", "en": "Text Data (PDF, DOCX)"},
    "config_text_data_sub": {"ar": "يتطلب تفعيل وحدة معالجة اللغات", "en": "Requires NLP module activation"},
    "config_visual_data": {"ar": "البيانات البصرية", "en": "Visual Data"},
    "config_visual_data_sub": {"ar": "تحليل الصور عبر الرؤية الحاسوبية", "en": "Image analysis via Computer Vision"},
    "config_tables": {"ar": "الجداول وقواعد البيانات", "en": "Tables & Databases"},
    "config_tables_sub": {"ar": "استخراج الأنماط من Excel", "en": "Extract patterns from Excel"},
    "config_slider_title": {"ar": "دقة وعمق الفرز", "en": "Sorting Depth & Accuracy"},
    "config_slider_deep": {"ar": "سريع وسطحي", "en": "Fast & Shallow"},
    "config_slider_fast": {"ar": "بطيء وعميق", "en": "Slow & Deep"},
    "config_start_btn": {"ar": "  ▶  تشغيل وحدة المعالجة", "en": "▶  Start Processing Unit"},

    # ─── شاشة المعالجة ───
 
    # رسائل المراحل
    "phase1_title": {"ar": "جاري العمل...", "en": "Working..."},
    "phase1_sub": {"ar": "يتم الآن تحليل ومعالجة البيانات عبر المحرك العصبوني", "en": "Analyzing and processing data via neural engine"},
    "phase2_title": {"ar": "Kiro يقوم بالتحليل العصبوني...", "en": "Kiro performing neural analysis..."},
    "phase2_sub": {"ar": "نماذج الذكاء الاصطناعي تقرأ وتفهم المحتوى", "en": "AI models reading and understanding content"},
    "phase3_title": {"ar": "Kiro يهيكل البيانات...", "en": "Kiro structuring data..."},
    "phase3_sub": {"ar": "توليد المجلدات الذكية ونقل الكيانات إليها", "en": "Generating smart folders and moving entities"},
    "phase4_title": {"ar": "اكتملت الدورة بنجاح", "en": "Cycle completed successfully"},
    "phase4_sub": {"ar": "النظام الآن مهيأ ومستقر", "en": "System is now configured and stable"},

    # ─── شاشة لوحة التحكم ───
    "dash_hero_title": {"ar": "تم تنظيم بياناتك بنجاح", "en": "Data Organized Successfully"},
    "dash_hero_desc": {"ar": "قام Kiro AI بتحليل بياناتك وتصنيفها في مسارات عصبونية ذكية.", "en": "Kiro AI analyzed your data and classified it into smart neural pathways."},
    "dash_stat1_label": {"ar": "كيانات معالجة", "en": "Processed Entities"},
    "dash_stat1_value": {"ar": "287", "en": "287"},
    "dash_stat1_sub": {"ar": "موزعة في 3 عقد رئيسية", "en": "Distributed in 3 main nodes"},
    "dash_stat2_label": {"ar": "وقت المعالجة", "en": "Processing Time"},
    "dash_stat2_value": {"ar": "0.8s", "en": "0.8s"},
    "dash_stat2_sub": {"ar": "فائق السرعة (وفر ~12 دقيقة)", "en": "Ultra fast (saved ~12 minutes)"},
    "dash_stat3_label": {"ar": "بيانات نصية", "en": "Text Data"},
    "dash_stat3_value": {"ar": "172", "en": "172"},
    "dash_stat3_sub": {"ar": "تم تحليل محتواها وفهمها", "en": "Content analyzed and understood"},
    "dash_stat4_label": {"ar": "بيانات بصرية", "en": "Visual Data"},
    "dash_stat4_value": {"ar": "115", "en": "115"},
    "dash_stat4_sub": {"ar": "تم التعرف على عناصرها", "en": "Elements identified"},
    "dash_folders_title": {"ar": "العقد التنظيمية (المجلدات الذكية)", "en": "Smart Folders (Organization Nodes)"},
    "dash_files_suffix": {"ar": "ملفات", "en": "files"},
    "dash_folders_count": {"ar": "مجلدات", "en": "Folders"},
    "dash_folder1": {"ar": "مستندات قانونية وإدارية", "en": "Legal & Administrative Docs"},
    "dash_folder3_count": {"ar": "82 ملف", "en": "82 files"},
    "dash_new_cycle": {"ar": "← بدء دورة معالجة جديدة", "en": "Start New Processing Cycle →"},

    # ─── شاشة الإعدادات ───
    "settings_title": {"ar": "لوحة التحكم المركزية", "en": "Central Control Panel"},
    "settings_sub": {"ar": "تخصيص بارامترات نموذج الذكاء الاصطناعي", "en": "Customize AI model parameters"},
    "settings_group1": {"ar": "ميزات النموذج الأساسية", "en": "Core Model Features"},
    "settings_nlp": {"ar": "معالجة اللغات الطبيعية (NLP)", "en": "Natural Language Processing (NLP)"},
    "settings_nlp_sub": {"ar": "تفعيل قراءة النصوص واستنباط المعاني العميقة وتصنيفها.", "en": "Enable text reading, deep meaning extraction and classification."},
    "settings_cv": {"ar": "الرؤية الحاسوبية (Computer Vision)", "en": "Computer Vision"},
    "settings_cv_sub": {"ar": "تحليل البيكسلات لفهم محتوى الصور والمخططات.", "en": "Pixel analysis to understand images and diagrams."},
    "settings_gpu": {"ar": "استهلاك الأجهزة (Hardware Acceleration)", "en": "Hardware Acceleration"},
    "settings_gpu_sub": {"ar": "استخدام المعالج الرسومي (GPU) لتسريع الفرز.", "en": "Use GPU to accelerate sorting."},
    "settings_group2": {"ar": "الذاكرة الذكية", "en": "Smart Memory"},
    "settings_learning": {"ar": "التعلم المستمر", "en": "Continuous Learning"},
    "settings_learning_sub": {"ar": "يسمح للنموذج بدراسة تفضيلاتك في التنظيم ليصبح أكثر ذكاءً.", "en": "Allows the model to study your preferences to become smarter."},
    "settings_threads": {"ar": "تخصيص الموارد", "en": "Resource Allocation"},
    "settings_threads_sub": {"ar": "عدد المسارات المعالجة في وقت واحد.", "en": "Number of paths processed simultaneously."},
    "settings_active": {"ar": "● Active", "en": "● Active"},
    "settings_thread_count": {"ar": "Thread Count: 8", "en": "Thread Count: 8"},

    # ─── شاشة عن المشروع ───
    "about_title": {"ar": "عن مشروع Kiro AI", "en": "About Kiro AI"},
    "about_sub": {"ar": "تعرف على العقل الإلكتروني وراء هذه المنصة.", "en": "Learn about the electronic brain behind this platform."},
    "about_s1_title": {"ar": "ما هو Kiro AI؟", "en": "What is Kiro AI?"},
    "about_s1_body": {
        "ar": "مشروع Kiro AI هو مساعد تنظيم ذكي يعتمد على خوارزميات التعلم الآلي لترتيب الفوضى الرقمية في جهازك. صُمم للمحترفين والطلاب الذين يمتلكون مئات أو آلاف الملفات المبعثرة، حيث يقوم بقراءتها، تحليل نوعها ومحتواها (عبر معالجة اللغات الطبيعية للوصف، والرؤية الحاسوبية للصور)، ثم نقلها آلياً إلى مجلدات ذكية ذات سياق موحد.",
        "en": "Kiro AI is a smart organizer that uses machine learning algorithms to sort digital chaos on your device. Designed for professionals and students with hundreds or thousands of scattered files, it reads, analyzes content type (via NLP for text and Computer Vision for images), then automatically moves them into smart contextual folders.",
    },
    "about_s2_title": {"ar": "كيف تعمل الخوارزمية؟", "en": "How does the algorithm work?"},
    "about_s2_body": {
        "ar": "1. المسح السطحي: يبحث النظام عن الكيانات (الملفات) غير المنظمة في مسارات يتم تحديدها مسبقاً (مثل التنزيلات أو سطح المكتب).\n\n2. التحليل العصبوني (Deep Analysis): بدلاً من الاعتماد على صيغة الملف فقط، يقرأ الذكاء الاصطناعي محتوى الملف لفهم سياقه (هل هو تقرير عمل؟ صورة عائلية؟ فاتورة مالية؟).\n\n3. إعادة الهيكلة: بناءً على \"المجموعات\" التي يكتشفها، يقوم بإنشاء عقد تنظيمية ونقل الكيانات إليها بسرعة فائقة.",
        "en": "1. Surface Scan: The system searches for unorganized entities (files) in pre-defined paths (like Downloads or Desktop).\n\n2. Deep Analysis: Instead of relying on file format alone, the AI reads file content to understand its context (is it a work report? family photo? financial invoice?).\n\n3. Restructuring: Based on the discovered \"clusters\", it creates organizational nodes and moves entities to them at ultra speed.",
    },
    "about_s3_title": {"ar": "الخصوصية والأمان", "en": "Privacy & Security"},
    "about_s3_body": {
        "ar": "الخصوصية هي جوهر Kiro AI. تم بناء النماذج العصبونية لتعمل بشكل محلي (Local Processing) تماماً على عتاد جهازك، مما يعني أن ملفاتك الشخصية، تقاريرك، وصورك لا تُرفع أبداً إلى أي سحابة خارجية أو خوادم طرف ثالث. كل المعالجة تتم داخل جهازك.",
        "en": "Privacy is at the core of Kiro AI. Neural models are built to run entirely locally on your hardware, meaning your personal files, reports, and photos are never uploaded to any external cloud or third-party servers. All processing happens on your device.",
    },
    # ─── رسائل الخطأ ───
    "err_path_title": {"ar": "خطأ في المسار", "en": "Path Error"},
    "err_path_missing": {
        "ar": "الرجاء إدخال مسار المجلد أو تفعيل أحد المجلدات الافتراضية (سطح المكتب، التنزيلات، المستندات)!",
        "en": "Please enter a folder path or enable one of the default folders (Desktop, Downloads, Documents)!",
    },
    "err_path_invalid": {
        "ar": "المجلد المحدد غير موجود، يرجى التأكد من المسار!",
        "en": "The specified folder does not exist, please check the path!",
    },
}