"""
Kiro AI - About Screen (PyQt6) - Bilingual
شاشة عن المشروع
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QFrame, QScrollArea)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from translations import lang_manager, t

# ── لوحة الألوان الموحدة ──────────────────────────────────────────
BG_DEEP     = "#020650"
BG_MID      = "#050F26"
CYAN        = "#00D2FF"
BLUE        = "#1A73E8"
TEXT_MAIN   = "#FFFFFF"
TEXT_SUB    = "#80A0C0"
BORDER_CYAN = "rgba(0, 210, 255, 0.15)"


class AboutScreen(QWidget):
    """شاشة عن المشروع"""

    def __init__(self, on_navigate, parent=None):
        super().__init__(parent)
        self.on_navigate = on_navigate
        self.setStyleSheet("background: transparent;")
        self._labels = {}
        self._build()
        lang_manager.language_changed.connect(self._on_lang_changed)

    def paintEvent(self, event):
        from PyQt6.QtGui import QRadialGradient, QLinearGradient, QPainter, QBrush, QColor
        p = QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing)
        W, H = self.width(), self.height()
        bg = QLinearGradient(0, 0, 0, H)
        bg.setColorAt(0.0, QColor(BG_DEEP)); bg.setColorAt(0.5, QColor(BG_MID)); bg.setColorAt(1.0, QColor(BG_DEEP))
        p.fillRect(self.rect(), QBrush(bg))
        cg = QRadialGradient(W/2, H*0.4, W*0.5)
        cg.setColorAt(0.0, QColor(0, 210, 255, 30)); cg.setColorAt(1.0, QColor(0, 210, 255, 0))
        p.fillRect(self.rect(), QBrush(cg))
        p.end()

    def _build(self):
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("background: transparent; border: none;")

        content = QWidget()
        content.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(content)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(0)

        self._labels["title"] = QLabel(t("about_title"))
        self._labels["title"].setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
        self._labels["title"].setStyleSheet(f"color: {TEXT_MAIN};")
        self._labels["title"].setAlignment(lang_manager.align)
        layout.addWidget(self._labels["title"])
        layout.addSpacing(6)

        self._labels["sub"] = QLabel(t("about_sub"))
        self._labels["sub"].setFont(QFont("Segoe UI", 12))
        self._labels["sub"].setStyleSheet(f"color: {TEXT_SUB};")
        self._labels["sub"].setAlignment(lang_manager.align)
        layout.addWidget(self._labels["sub"])
        layout.addSpacing(30)

        sections = [
            ("about_s1_title", "about_s1_body"),
            ("about_s2_title", "about_s2_body"),
            ("about_s3_title", "about_s3_body"),
        ]
        for title_key, body_key in sections:
            self._section(layout, title_key, body_key)
            layout.addSpacing(15)

        layout.addStretch()

        scroll_area.setWidget(content)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll_area)

    def _section(self, parent_layout, title_key, body_key):
        group = QFrame()
        group.setObjectName("aboutSection")
        group.setStyleSheet(f"QFrame#aboutSection {{ background: rgba(255, 255, 255, 0.04); border-radius: 18px; border: 1px solid {BORDER_CYAN}; }}")
        g_layout = QVBoxLayout(group)
        g_layout.setContentsMargins(0, 0, 0, 0)
        g_layout.setSpacing(0)

        head = QWidget(); head.setFixedHeight(44); head.setStyleSheet(f"background: rgba(0, 210, 255, 0.08); border-top-left-radius: 18px; border-top-right-radius: 18px;")
        h_layout = QHBoxLayout(head); h_layout.setContentsMargins(20, 0, 20, 0)

        h_label = QLabel(t(title_key).upper())
        h_label.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold)); h_label.setStyleSheet(f"color: {CYAN}; background: transparent; letter-spacing: 1px;")
        self._labels[title_key] = h_label

        h_layout.addStretch()
        h_layout.addWidget(h_label)
        g_layout.addWidget(head)

        body_lbl = QLabel(t(body_key)); body_lbl.setFont(QFont("Segoe UI", 11)); body_lbl.setStyleSheet(f"color: {TEXT_SUB}; background: transparent;")
        body_lbl.setAlignment(lang_manager.align); body_lbl.setWordWrap(True); body_lbl.setContentsMargins(20, 16, 20, 20)
        self._labels[body_key] = body_lbl
        g_layout.addWidget(body_lbl)

        parent_layout.addWidget(group)

    def _on_lang_changed(self, lang):
        self._labels["title"].setText(t("about_title"))
        self._labels["title"].setAlignment(lang_manager.align)
        self._labels["sub"].setText(t("about_sub"))
        self._labels["sub"].setAlignment(lang_manager.align)

        sections = [
            ("about_s1_title", "about_s1_body"),
            ("about_s2_title", "about_s2_body"),
            ("about_s3_title", "about_s3_body"),
        ]
        for title_key, body_key in sections:
            if title_key in self._labels:
                self._labels[title_key].setText(t(title_key))
            if body_key in self._labels:
                self._labels[body_key].setText(t(body_key))
                self._labels[body_key].setAlignment(lang_manager.align)
