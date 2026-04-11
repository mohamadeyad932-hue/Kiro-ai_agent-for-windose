"""
Kiro AI - Main Application (PyQt6) - Bilingual
التطبيق الرئيسي مع الشريط الجانبي والتنقل بين الصفحات - ثنائي اللغة
"""
import sys
import os

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                              QHBoxLayout, QPushButton, QLabel, QStackedWidget,
                              QFrame, QGraphicsDropShadowEffect, QGraphicsOpacityEffect)
from PyQt6.QtCore import Qt, QSize, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QColor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from theme import COLORS, WINDOW_WIDTH, WINDOW_HEIGHT, SIDEBAR_WIDTH, GLOBAL_STYLESHEET
from translations import lang_manager, t
from welcome_screen import WelcomeScreen
from config_screen import ConfigScreen
from processing_screen import ProcessingScreen
from dashboard_screen import DashboardScreen
from settings_screen import SettingsScreen
from about_screen import AboutScreen


# ─── ربط أسماء الصفحات بمفاتيح الترجمة ───
PAGE_KEYS = {
    "sp": "page_sp",
    "cf": "page_cf",
    "pr": "page_pr",
    "db": "page_db",
    "st": "page_st",
    "ab": "page_ab",
}

NAV_KEYS = {
    "sp": "nav_sp",
    "cf": "nav_cf",
    "pr": "nav_pr",
    "db": "nav_db",
    "st": "nav_st",
    "ab": "nav_ab",
}


class SidebarButton(QPushButton):
    """زر تنقل في الشريط الجانبي"""
    def __init__(self, icon_text, nav_key, page_id, on_click, parent=None):
        super().__init__(parent)
        self.page_id = page_id
        self.icon_text = icon_text
        self.nav_key = nav_key
        self._update_text()
        self.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(42)
        self.clicked.connect(lambda: on_click(page_id))
        self.set_inactive()
        lang_manager.language_changed.connect(self._on_lang_changed)

    def _update_text(self):
        text = t(self.nav_key)
        if lang_manager.is_rtl:
            self.setText(f"{text}   {self.icon_text}")
        else:
            self.setText(f"{self.icon_text}   {text}")

    def set_active(self):
        align = "right" if lang_manager.is_rtl else "left"
        pad = "padding-right" if lang_manager.is_rtl else "padding-left"
        self.setStyleSheet(f"""
            QPushButton {{
                background: rgba(0, 210, 255, 0.12);
                color: {COLORS['violet_d']};
                border-radius: 10px;
                text-align: {align};
                {pad}: 15px;
                border: none;
            }}
        """)

    def set_inactive(self):
        align = "right" if lang_manager.is_rtl else "left"
        pad = "padding-right" if lang_manager.is_rtl else "padding-left"
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {COLORS['ink3']};
                border-radius: 10px;
                text-align: {align};
                {pad}: 15px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: rgba(255, 255, 255, 0.05);
            }}
        """)

    def _on_lang_changed(self, lang):
        self._update_text()
        # Re-apply active/inactive style to fix text-align direction
        # We check by color if active
        if COLORS['violet_dim'] in self.styleSheet():
            self.set_active()
        else:
            self.set_inactive()


class KiroApp(QMainWindow):
    """التطبيق الرئيسي - Kiro AI"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle(t("app_title"))
        self.resize(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.setMinimumSize(900, 600)

        self.current_page = "sp"
        self.nav_history = []  # سجل التنقل
        self.sidebar_visible = False
        self.nav_buttons = {}
        self.screens = {}
        self._labels = {}

        self._build_ui()
        self.navigate("sp")

        lang_manager.language_changed.connect(self._on_lang_changed)

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        outer_layout = QVBoxLayout(central)
        outer_layout.setContentsMargins(15, 2, 15, 12)  # تقليل الهامش العلوي لرفع قسم العنوان
        outer_layout.setSpacing(0)

        # ─── شريط العنوان العلوي ───
        self.titlebar = QFrame()
        self.titlebar.setObjectName("titlebar")
        self.titlebar.setFixedHeight(42)
        self.titlebar.setStyleSheet(f"""
            QFrame#titlebar {{
                background-color: {COLORS['panel']};
                border-top-left-radius: 14px;
                border-top-right-radius: 14px;
                border: 1px solid {COLORS['border']};
                border-bottom: none;
            }}
        """)
        tb_layout = QHBoxLayout(self.titlebar)
        tb_layout.setContentsMargins(15, 0, 15, 0)

        self._labels["tb_title"] = QLabel(t("terminal_title"))
        self._labels["tb_title"].setFont(QFont("Segoe UI", 10))
        self._labels["tb_title"].setStyleSheet(f"color: {COLORS['ink4']};")
        self._labels["tb_title"].setAlignment(Qt.AlignmentFlag.AlignCenter)

        tb_layout.addWidget(self._labels["tb_title"], stretch=1)

        outer_layout.addWidget(self.titlebar)
        
        # إخفاء الهيدر في شاشة الترحيب بشكل افتراضي
        self.titlebar.hide()

        # ─── الحاوية الوسطى ───
        body = QWidget()
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        # ─── المنطقة الرئيسية ───
        main_frame = QFrame()
        main_frame.setObjectName("mainFrame")
        main_frame.setStyleSheet(f"""
            QFrame#mainFrame {{
                background-color: transparent;
                border-bottom-left-radius: 14px;
                border: 1px solid {COLORS['border']};
                border-top: none;
            }}
        """)
        main_layout = QVBoxLayout(main_frame)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ─── شريط التنقل العلوي ───
        self.topbar = QFrame()
        self.topbar.setObjectName("topbar")
        self.topbar.setFixedHeight(56)
        self.topbar.setStyleSheet(f"""
            QFrame#topbar {{
                background-color: transparent;
                border-bottom: 1px solid {COLORS['border']};
            }}
        """)
        topbar_layout = QHBoxLayout(self.topbar)
        topbar_layout.setContentsMargins(20, 0, 20, 0)

        # شارة الإصدار
        self._labels["version"] = QLabel(t("version"))
        self._labels["version"].setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self._labels["version"].setFixedSize(110, 28)
        self._labels["version"].setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._labels["version"].setStyleSheet(f"""
            background-color: rgba(255, 255, 255, 0.08);
            color: {COLORS['violet_d']};
            border-radius: 14px;
            border: 1px solid rgba(0, 210, 255, 0.2);
        """)

        # ─── زر تبديل اللغة ───
        self.lang_btn = QPushButton(t("lang_btn"))
        self.lang_btn.setFixedSize(36, 36)
        self.lang_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.lang_btn.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        self.lang_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(0, 210, 255, 0.15);
                color: {COLORS['violet_d']};
                border: 1px solid rgba(0, 210, 255, 0.3);
                border-radius: 10px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['violet_d']};
                color: {COLORS['white']};
            }}
        """)
        self.lang_btn.setToolTip("Switch Language / تبديل اللغة")
        self.lang_btn.clicked.connect(lang_manager.toggle)

        # زر القائمة
        self.menu_btn = QPushButton("☰")
        self.menu_btn.setFixedSize(34, 34)
        self.menu_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.menu_btn.setFont(QFont("Segoe UI", 14))
        self.menu_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(255,255,255,0.05);
                color: {COLORS['ink']};
                border: 1px solid {COLORS['border']};
                border-radius: 10px;
            }}
            QPushButton:hover {{
                background-color: rgba(0, 210, 255, 0.1);
                color: {COLORS['violet_d']};
            }}
        """)
        self.menu_btn.clicked.connect(self._toggle_sidebar)

        # ─── زر العودة ───
        self.back_btn = QPushButton(t("back_btn"))
        self.back_btn.setFixedSize(34, 34)
        self.back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.back_btn.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        self.back_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(255,255,255,0.05);
                color: {COLORS['ink']};
                border: 1px solid {COLORS['border']};
                border-radius: 10px;
            }}
            QPushButton:hover {{
                background-color: rgba(0, 210, 255, 0.1);
                border: 1px solid {COLORS['violet_d']};
            }}
        """)
        self.back_btn.setToolTip("Back / رجوع")
        self.back_btn.clicked.connect(self._go_back)
        self.back_btn.hide()

        topbar_layout.addWidget(self._labels["version"])
        topbar_layout.addSpacing(8)
        topbar_layout.addWidget(self.lang_btn)
        topbar_layout.addStretch()
        topbar_layout.addWidget(self.back_btn)
        topbar_layout.addSpacing(4)
        topbar_layout.addWidget(self.menu_btn)

        main_layout.addWidget(self.topbar)
        self.topbar.hide() # إخفاء توب بار في البداية لشاشة الترحيب

        # ─── حاوية الصفحات ───
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setStyleSheet(f"background-color: {COLORS['panel']};")
        main_layout.addWidget(self.stacked_widget)

        # ─── إنشاء الصفحات ───
        screen_map = {
            "sp": lambda: WelcomeScreen(self.navigate),
            "cf": lambda: ConfigScreen(self.navigate),
            "pr": lambda: ProcessingScreen(self.navigate),
            "db": lambda: DashboardScreen(self.navigate),
            "st": lambda: SettingsScreen(self.navigate),
            "ab": lambda: AboutScreen(self.navigate),
        }
        for page_id, creator in screen_map.items():
            screen = creator()
            self.screens[page_id] = screen
            self.stacked_widget.addWidget(screen)

        body_layout.addWidget(main_frame, stretch=1)

        # ─── الشريط الجانبي ───
        self.sidebar = QFrame()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(SIDEBAR_WIDTH)
        self.sidebar.setStyleSheet(f"""
            QFrame#sidebar {{
                background-color: {COLORS['panel']};
                border-bottom-right-radius: 14px;
                border: 1px solid {COLORS['border']};
                border-top: none;
                border-left: none;
            }}
        """)
        self._build_sidebar()

        body_layout.addWidget(self.sidebar)
        self.sidebar.hide()

        outer_layout.addWidget(body, stretch=1)

    def _build_sidebar(self):
        layout = QVBoxLayout(self.sidebar)
        layout.setContentsMargins(12, 2, 12, 16)
        layout.setSpacing(4)

        # ─── الشعار ───
        header = QHBoxLayout()
        header.setAlignment(lang_manager.align)

        titles = QVBoxLayout()
        titles.setSpacing(0)
        self._labels["brand"] = QLabel(t("sidebar_brand"))
        self._labels["brand"].setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))
        self._labels["brand"].setStyleSheet(f"color: {COLORS['ink']};")
        self._labels["brand"].setAlignment(lang_manager.align)

        self._labels["brand_sub"] = QLabel(t("sidebar_subtitle"))
        self._labels["brand_sub"].setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self._labels["brand_sub"].setStyleSheet(f"color: {COLORS['cyan']};")
        self._labels["brand_sub"].setAlignment(lang_manager.align)

        titles.addWidget(self._labels["brand"])
        titles.addWidget(self._labels["brand_sub"])

        logo = QLabel("◈")
        logo.setFixedSize(42, 42)
        logo.setFont(QFont("Segoe UI", 18))
        logo.setStyleSheet(f"background-color: {COLORS['violet_d']}; color: white; border-radius: 14px;")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        header.addLayout(titles)
        header.addSpacing(10)
        header.addWidget(logo)
        layout.addLayout(header)
        layout.addSpacing(4)

        div = QFrame()
        div.setFixedHeight(1)
        div.setStyleSheet(f"background-color: {COLORS['border']};")
        layout.addWidget(div)
        layout.addSpacing(16)

        # ─── Category 1 ───
        self._labels["cat1"] = QLabel(t("sidebar_cat1"))
        self._labels["cat1"].setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self._labels["cat1"].setStyleSheet(f"color: {COLORS['ink4']};")
        self._labels["cat1"].setAlignment(lang_manager.align)
        layout.addWidget(self._labels["cat1"])
        layout.addSpacing(8)

        self._add_nav_btn("🏠", "nav_sp", "sp", layout)
        self._add_nav_btn("✏️", "nav_cf", "cf", layout)
        self._add_nav_btn("⏱️", "nav_pr", "pr", layout)
        self._add_nav_btn("📊", "nav_db", "db", layout)

        layout.addSpacing(16)

        self._labels["cat2"] = QLabel(t("sidebar_cat2"))
        self._labels["cat2"].setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self._labels["cat2"].setStyleSheet(f"color: {COLORS['ink4']};")
        self._labels["cat2"].setAlignment(lang_manager.align)
        layout.addWidget(self._labels["cat2"])
        layout.addSpacing(8)

        self._add_nav_btn("⚙️", "nav_st", "st", layout)
        self._add_nav_btn("ℹ️", "nav_ab", "ab", layout)

        layout.addStretch()

        div2 = QFrame()
        div2.setFixedHeight(1)
        div2.setStyleSheet(f"background-color: {COLORS['border']};")
        layout.addWidget(div2)
        layout.addSpacing(12)

        # ─── حالة النظام ───
        status_box = QFrame()
        status_box.setObjectName("statusBox")
        status_box.setStyleSheet(f"QFrame#statusBox {{ background-color: {COLORS['emerald_dim']}; border-radius: 12px; }}")
        sb_layout = QHBoxLayout(status_box)
        sb_layout.setContentsMargins(12, 10, 12, 10)
        sb_layout.setAlignment(lang_manager.align)

        st_text = QVBoxLayout()
        st_text.setSpacing(2)

        self._labels["status1"] = QLabel(t("sidebar_status1"))
        self._labels["status1"].setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self._labels["status1"].setStyleSheet(f"color: {COLORS['emerald']}; background: transparent;")
        self._labels["status1"].setAlignment(lang_manager.align)

        self._labels["status2"] = QLabel(t("sidebar_status2"))
        self._labels["status2"].setFont(QFont("Segoe UI", 8))
        self._labels["status2"].setStyleSheet(f"color: {COLORS['ink4']}; background: transparent;")
        self._labels["status2"].setAlignment(lang_manager.align)

        st_text.addWidget(self._labels["status1"])
        st_text.addWidget(self._labels["status2"])

        dot = QFrame()
        dot.setFixedSize(10, 10)
        dot.setStyleSheet(f"background-color: {COLORS['emerald']}; border-radius: 5px;")

        sb_layout.addLayout(st_text)
        sb_layout.addSpacing(8)
        sb_layout.addWidget(dot)

        layout.addWidget(status_box)

    def _add_nav_btn(self, icon, nav_key, pid, layout):
        btn = SidebarButton(icon, nav_key, pid, self.navigate)
        self.nav_buttons[pid] = btn
        layout.addWidget(btn)

    def navigate(self, page_id, **kwargs):
        # حفظ الصفحة الحالية في السجل قبل التنقل
        if self.current_page != page_id:
            self.nav_history.append(self.current_page)

        self.current_page = page_id

        if page_id in self.screens:
            self.stacked_widget.setCurrentWidget(self.screens[page_id])

        # إظهار/إخفاء شريط العنوان العلوي
        if page_id == "sp":
            self.topbar.hide()
            self.titlebar.hide()
        else:
            self.topbar.show()
            self.titlebar.show()

        # إظهار/إخفاء زر العودة والقائمة الجانبية
        if page_id == "sp" or len(self.nav_history) == 0:
            self.back_btn.hide()
            self.menu_btn.hide()  # إخفاء أيقونة القائمة الجانبية من شاشة الترحيب
        else:
            self.back_btn.show()
            self.menu_btn.show()

        for pid, btn in self.nav_buttons.items():
            if pid == page_id:
                btn.set_active()
            else:
                btn.set_inactive()

        if page_id == "sp":
            self.sidebar.hide()
            self.sidebar_visible = False
            self.findChild(QFrame, "mainFrame").setStyleSheet(f"QFrame#mainFrame {{ background: transparent; border-bottom-left-radius: 14px; border-bottom-right-radius: 14px; border: 1px solid {COLORS['border']}; border-top: none; }}")
        elif not self.sidebar_visible:
            self.sidebar.show()
            self.sidebar_visible = True
            self.findChild(QFrame, "mainFrame").setStyleSheet(f"QFrame#mainFrame {{ background: transparent; border-bottom-left-radius: 14px; border: 1px solid {COLORS['border']}; border-top: none; border-right: none; }}")

        if page_id == "pr" and kwargs.get("start_processing"):
            self.screens["pr"].start_processing()

    def _toggle_sidebar(self):
        if self.sidebar_visible:
            self.sidebar.hide()
            self.sidebar_visible = False
            self.findChild(QFrame, "mainFrame").setStyleSheet(f"QFrame#mainFrame {{ background: transparent; border-bottom-left-radius: 14px; border-bottom-right-radius: 14px; border: 1px solid {COLORS['border']}; border-top: none; }}")
        else:
            self.sidebar.show()
            self.sidebar_visible = True
            self.findChild(QFrame, "mainFrame").setStyleSheet(f"QFrame#mainFrame {{ background: transparent; border-bottom-left-radius: 14px; border: 1px solid {COLORS['border']}; border-top: none; border-right: none; }}")

    def _go_back(self):
        """العودة للصفحة السابقة"""
        if self.nav_history:
            prev = self.nav_history.pop()
            # نمنع navigate من إضافة الصفحة الحالية مرة أخرى
            self.current_page = prev
            if prev in self.screens:
                self.stacked_widget.setCurrentWidget(self.screens[prev])

            for pid, btn in self.nav_buttons.items():
                if pid == prev:
                    btn.set_active()
                else:
                    btn.set_inactive()

            # إظهار/إخفاء الشريط العلوي والعودة
            if prev == "sp":
                self.topbar.hide()
                self.titlebar.hide()
            else:
                self.topbar.show()
                self.titlebar.show()

            if prev == "sp" or len(self.nav_history) == 0:
                self.back_btn.hide()
                self.menu_btn.hide()
            else:
                self.back_btn.show()
                self.menu_btn.show()

            # إظهار/إخفاء الشريط الجانبي
            if prev == "sp":
                self.sidebar.hide()
                self.sidebar_visible = False
                self.findChild(QFrame, "mainFrame").setStyleSheet(f"QFrame#mainFrame {{ background: transparent; border-bottom-left-radius: 14px; border-bottom-right-radius: 14px; border: 1px solid {COLORS['border']}; border-top: none; }}")
            elif not self.sidebar_visible:
                self.sidebar.show()
                self.sidebar_visible = True
                self.findChild(QFrame, "mainFrame").setStyleSheet(f"QFrame#mainFrame {{ background: transparent; border-bottom-left-radius: 14px; border: 1px solid {COLORS['border']}; border-top: none; border-right: none; }}")

    def _on_lang_changed(self, lang):
        """تحديث كل النصوص عند تغيير اللغة"""
        QApplication.instance().setLayoutDirection(lang_manager.direction)

        self.setWindowTitle(t("app_title"))
        self.lang_btn.setText(t("lang_btn"))
        self.back_btn.setText(t("back_btn"))

        self._labels["cat1"].setText(t("sidebar_cat1"))
        self._labels["cat1"].setAlignment(lang_manager.align)
        self._labels["cat2"].setText(t("sidebar_cat2"))
        self._labels["cat2"].setAlignment(lang_manager.align)
        self._labels["status1"].setText(t("sidebar_status1"))
        self._labels["status1"].setAlignment(lang_manager.align)
        self._labels["status2"].setText(t("sidebar_status2"))
        self._labels["status2"].setAlignment(lang_manager.align)
        self._labels["brand"].setAlignment(lang_manager.align)
        self._labels["brand_sub"].setAlignment(lang_manager.align)


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(GLOBAL_STYLESHEET)
    app.setLayoutDirection(lang_manager.direction)

    window = KiroApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
