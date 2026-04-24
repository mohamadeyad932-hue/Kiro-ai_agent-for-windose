"""
Kiro AI - Settings Screen (PyQt6) - Bilingual
شاشة الإعدادات وتخصيص النظام
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QFrame, QScrollArea)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPainter, QBrush, QColor
from translations import lang_manager, t

from theme import (
    BG_DEEP, BG_MID, CYAN, BLUE, EMERALD,
    TEXT_MAIN, TEXT_SUB, BORDER_CYAN
)


class ToggleSwitchSettings(QWidget):
    def __init__(self, checked=False, parent=None):
        super().__init__(parent)
        self.setFixedSize(44, 24)
        self._checked = checked
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def mousePressEvent(self, event):
        self._checked = not self._checked
        self.update()

    def paintEvent(self, event):
        p = QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        bg_color = QColor(CYAN) if self._checked else QColor(255, 255, 255, 30)
        p.setBrush(QBrush(bg_color))
        p.drawRoundedRect(0, 0, 44, 24, 12, 12)
        knob_x = 22 if self._checked else 2
        p.setBrush(QBrush(QColor(TEXT_MAIN)))
        p.drawEllipse(knob_x, 2, 20, 20)
        p.end()


class SettingsScreen(QWidget):
    """شاشة إعدادات النظام"""

    def __init__(self, on_navigate, parent=None):
        super().__init__(parent)
        self.on_navigate = on_navigate
        self.setStyleSheet("background: transparent;")
        self._labels = {}
        self._build()
        lang_manager.language_changed.connect(self._on_lang_changed)

    def paintEvent(self, event):
        from theme import paint_bg
        paint_bg(self)

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

        self._labels["title"] = QLabel(t("settings_title"))
        self._labels["title"].setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
        self._labels["title"].setStyleSheet(f"color: {TEXT_MAIN};")
        self._labels["title"].setAlignment(lang_manager.align)
        layout.addWidget(self._labels["title"])
        layout.addSpacing(6)

        self._labels["sub"] = QLabel(t("settings_sub"))
        self._labels["sub"].setFont(QFont("Segoe UI", 12))
        self._labels["sub"].setStyleSheet(f"color: {TEXT_SUB};")
        self._labels["sub"].setAlignment(lang_manager.align)
        layout.addWidget(self._labels["sub"])
        layout.addSpacing(30)

        # ─── مجموعة 1 ───
        self._build_group(layout, "settings_group1", [
            ("settings_nlp", "settings_nlp_sub", "badge", "settings_active"),
            ("settings_cv", "settings_cv_sub", "badge", "settings_active"),
            ("settings_gpu", "settings_gpu_sub", "toggle", True),
        ])
        layout.addSpacing(15)



        layout.addStretch()

        scroll_area.setWidget(content)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll_area)

    def _build_group(self, parent_layout, title_key, items):
        group = QFrame(); group.setObjectName("settingsGroup")
        group.setStyleSheet(f"QFrame#settingsGroup {{ background: rgba(255, 255, 255, 0.04); border-radius: 18px; border: 1px solid {BORDER_CYAN}; }}")
        g_layout = QVBoxLayout(group); g_layout.setContentsMargins(0, 0, 0, 0); g_layout.setSpacing(0)

        head = QWidget(); head.setFixedHeight(44); head.setStyleSheet(f"background: rgba(76, 194, 255, 0.08); border-top-left-radius: 18px; border-top-right-radius: 18px;")
        h_layout = QHBoxLayout(head); h_layout.setContentsMargins(20, 0, 20, 0)

        h_label = QLabel(t(title_key).upper())
        h_label.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold)); h_label.setStyleSheet(f"color: {CYAN}; background: transparent; letter-spacing: 1px;")
        self._labels[title_key] = h_label

        # Qt's layoutDirection handles mirroring automatically
        h_layout.addWidget(h_label)
        h_layout.addStretch()
        g_layout.addWidget(head)

        for i, item in enumerate(items):
            name_key, desc_key, ctrl_type, ctrl_val = item

            row = QWidget()
            row.setStyleSheet("background: transparent;")
            r_layout = QHBoxLayout(row)
            r_layout.setContentsMargins(20, 12, 20, 12)

            # ── عمود النص ──
            text_widget = QWidget()
            text_widget.setStyleSheet("background: transparent;")
            t_layout = QVBoxLayout(text_widget)
            t_layout.setContentsMargins(0, 0, 0, 0)
            t_layout.setSpacing(2)

            n_lbl = QLabel(t(name_key))
            n_lbl.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
            n_lbl.setStyleSheet(f"color: {TEXT_MAIN};")
            n_lbl.setAlignment(lang_manager.align)

            d_lbl = QLabel(t(desc_key))
            d_lbl.setFont(QFont("Segoe UI", 10))
            d_lbl.setStyleSheet(f"color: {TEXT_SUB};")
            d_lbl.setAlignment(lang_manager.align)
            d_lbl.setWordWrap(True)

            t_layout.addWidget(n_lbl)
            t_layout.addWidget(d_lbl)

            # ── عنصر التحكم ──
            ctrl_widget = None
            if ctrl_type == "toggle":
                ctrl_widget = ToggleSwitchSettings(ctrl_val)
            elif ctrl_type == "badge":
                badge = QLabel(t(ctrl_val))
                badge.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
                badge.setFixedSize(84, 26)
                badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
                badge.setStyleSheet(f"background: rgba(16, 185, 129, 0.15); color: {EMERALD}; border-radius: 13px;")
                ctrl_widget = badge
                self._labels[f"badge_{name_key}"] = badge
            elif ctrl_type == "badge_cyan":
                badge = QLabel(t(ctrl_val))
                badge.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
                badge.setFixedSize(110, 26)
                badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
                badge.setStyleSheet(f"background: rgba(76, 194, 255, 0.15); color: {CYAN}; border-radius: 13px;")
                ctrl_widget = badge
                self._labels[f"badge_{name_key}"] = badge

            # Qt's layoutDirection handles mirroring automatically
            r_layout.addWidget(text_widget)
            r_layout.addStretch()
            if ctrl_widget:
                r_layout.addWidget(ctrl_widget)

            self._labels[name_key] = n_lbl
            self._labels[desc_key] = d_lbl

            g_layout.addWidget(row)

            if i < len(items) - 1:
                sep = QFrame()
                sep.setFixedHeight(1)
                sep.setStyleSheet(f"background-color: rgba(255,255,255,0.05); margin-left: 20px; margin-right: 20px;")
                g_layout.addWidget(sep)

        parent_layout.addWidget(group)

    def _on_lang_changed(self, lang):
        self._labels["title"].setText(t("settings_title"))
        self._labels["title"].setAlignment(lang_manager.align)
        self._labels["sub"].setText(t("settings_sub"))
        self._labels["sub"].setAlignment(lang_manager.align)

        keys_to_update = [
            "settings_group1",
            "settings_nlp", "settings_nlp_sub",
            "settings_cv", "settings_cv_sub",
            "settings_gpu", "settings_gpu_sub",
        ]
        for key in keys_to_update:
            if key in self._labels:
                self._labels[key].setText(t(key))
                if hasattr(self._labels[key], 'setAlignment'):
                    self._labels[key].setAlignment(lang_manager.align)