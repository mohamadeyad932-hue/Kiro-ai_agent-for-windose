"""
Kiro AI - Configuration Screen (PyQt6) - Bilingual
شاشة التهيئة واختيار المسارات وأنواع البيانات
"""
import sys
import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QFrame, QScrollArea, QGridLayout,
                             QGraphicsDropShadowEffect, QApplication,
                             QLineEdit, QFileDialog, QMessageBox)
from PyQt6.QtCore import Qt, pyqtProperty, QPropertyAnimation, pyqtSignal, QEasingCurve
from PyQt6.QtGui import QFont, QColor, QPainter, QBrush
from translations import lang_manager, t

from theme import (
    BG_DEEP, BG_MID, CYAN, BLUE, VIOLET,
    TEXT_MAIN, TEXT_SUB, GLASS, BORDER_CYAN, ModernDialog
)


class ToggleSwitch(QWidget):
    """زر تبديل (Toggle Switch) مع أنيميشن"""
    toggled = pyqtSignal(bool)

    def __init__(self, checked=False, parent=None):
        super().__init__(parent)
        self.setFixedSize(44, 24)
        self._checked = checked
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._position = 22.0 if checked else 2.0
        self.anim = QPropertyAnimation(self, b"position")
        self.anim.setEasingCurve(QEasingCurve.Type.InOutCirc)
        self.anim.setDuration(200)

    @pyqtProperty(float)
    def position(self):
        return self._position

    @position.setter
    def position(self, pos):
        self._position = pos
        self.update()

    @property
    def checked(self):
        return self._checked

    def mousePressEvent(self, event):
        self._checked = not self._checked
        self.anim.setStartValue(self._position)
        self.anim.setEndValue(22.0 if self._checked else 2.0)
        self.anim.start()
        self.toggled.emit(self._checked)

    def paintEvent(self, event):
        p = QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        # خلفية الزر
        bg_color = QColor(CYAN) if self._checked else QColor(0, 0, 0, 40)
        p.setBrush(QBrush(bg_color))
        p.drawRoundedRect(0, 0, 44, 24, 12, 12)
        # المقبض
        p.setBrush(QBrush(QColor("white")))
        p.drawEllipse(int(self._position), 2, 20, 20)
        p.end()


class ToggleRow(QWidget):
    """صف واحد بمفتاح تبديل"""
    def __init__(self, title_key, subtitle_key, default_on=False, parent=None):
        super().__init__(parent)
        self.title_key = title_key
        self.subtitle_key = subtitle_key
        self.setStyleSheet("background: transparent;")
        self._build(default_on)
        lang_manager.language_changed.connect(self._on_lang_changed)

    def _build(self, default_on):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0); layout.setSpacing(0)

        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(16, 12, 16, 12)

        text_widget = QWidget()
        text_layout = QVBoxLayout(text_widget)
        text_layout.setContentsMargins(0, 0, 0, 0); text_layout.setSpacing(2)

        self.t_lbl = QLabel(t(self.title_key))
        self.t_lbl.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.t_lbl.setStyleSheet(f"color: {TEXT_MAIN}; background: transparent;")
        self.t_lbl.setAlignment(lang_manager.align)
        text_layout.addWidget(self.t_lbl)

        self.s_lbl = QLabel(t(self.subtitle_key))
        self.s_lbl.setFont(QFont("Segoe UI", 9))
        self.s_lbl.setStyleSheet(f"color: {TEXT_SUB}; background: transparent;")
        self.s_lbl.setAlignment(lang_manager.align)
        text_layout.addWidget(self.s_lbl)

        self.switch = ToggleSwitch(default_on)

        # Qt's layoutDirection handles mirroring automatically
        row_layout.addWidget(text_widget)
        row_layout.addStretch()
        row_layout.addWidget(self.switch)

        layout.addWidget(row_widget)
        
        # فاصل داكن رقيق
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background-color: rgba(0, 0, 0, 0.08); border: none;")
        layout.addWidget(sep)

    def _on_lang_changed(self, lang):
        self.t_lbl.setText(t(self.title_key))
        self.s_lbl.setText(t(self.subtitle_key))
        self.t_lbl.setAlignment(lang_manager.align)
        self.s_lbl.setAlignment(lang_manager.align)


class FolderSelectionRow(QWidget):
    """صف اختيار المجلد المخصص"""
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)
        
        self.lbl = QLabel(t("config_paths_title"))
        self.lbl.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.lbl.setStyleSheet(f"color: {TEXT_MAIN}; background: transparent;")
        self.lbl.setAlignment(lang_manager.align)
        
        row = QHBoxLayout()
        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText("Enter folder path / أدخل مسار المجلد...")
        self.path_input.setStyleSheet(f"background: rgba(0,0,0,0.04); color: {TEXT_MAIN}; border: 1.5px solid {BORDER_CYAN}; border-radius: 8px; padding: 8px;")
        
        self.browse_btn = QPushButton("📁")
        self.browse_btn.setFixedSize(40, 36)
        self.browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.browse_btn.setStyleSheet(f"QPushButton {{ background: {BLUE}; color: white; border-radius: 8px; font-size: 16px; }} QPushButton:hover {{ background: {CYAN}; }}")
        self.browse_btn.clicked.connect(self._browse)
        
        row.addWidget(self.path_input)
        row.addWidget(self.browse_btn)
        
        layout.addWidget(self.lbl)
        layout.addLayout(row)

        lang_manager.language_changed.connect(self._on_lang_changed)

    def _browse(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Select Folder")
        if dir_path:
            self.path_input.setText(os.path.normpath(dir_path))

    def _on_lang_changed(self, lang):
        self.lbl.setText(t("config_paths_title"))
        self.lbl.setAlignment(lang_manager.align)


class ConfigScreen(QWidget):
    """شاشة التهيئة - تحديد المسارات وأنواع البيانات"""
    def __init__(self, on_navigate=None, parent=None):
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
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(0)

        # ─── العنوان ───
        self._labels["title"] = QLabel(t("config_title"))
        self._labels["title"].setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
        self._labels["title"].setStyleSheet(f"color: {TEXT_MAIN};")
        self._labels["title"].setAlignment(lang_manager.align)
        layout.addWidget(self._labels["title"])
        layout.addSpacing(6)

        self._labels["sub"] = QLabel(t("config_sub"))
        self._labels["sub"].setFont(QFont("Segoe UI", 11))
        self._labels["sub"].setStyleSheet(f"color: {TEXT_SUB};")
        self._labels["sub"].setAlignment(lang_manager.align)
        layout.addWidget(self._labels["sub"])
        layout.addSpacing(30)

        # ─── البطاقتين العلويتين ───
        cards_widget = QWidget()
        cards_grid = QGridLayout(cards_widget)
        cards_grid.setSpacing(15)
        cards_grid.setContentsMargins(0, 0, 0, 0)

        self._path_card_lbl, path_card = self._create_card("config_paths_title")
        pc_layout = path_card.layout()
        self.folder_selector = FolderSelectionRow()
        pc_layout.addWidget(self.folder_selector)
        
        self.toggle_desktop = ToggleRow("config_desktop", "config_desktop_sub", False)
        self.toggle_downloads = ToggleRow("config_downloads", "config_downloads_sub", False)
        self.toggle_documents = ToggleRow("config_documents", "config_documents_sub", False)
        
        pc_layout.addWidget(self.toggle_desktop)
        pc_layout.addWidget(self.toggle_downloads)
        pc_layout.addWidget(self.toggle_documents)
        
        pc_layout.addStretch()
        cards_grid.addWidget(path_card, 0, 0)

        self._type_card_lbl, type_card = self._create_card("config_types_title")
        tc_layout = type_card.layout()
        self.toggle_text = ToggleRow("config_text_data", "config_text_data_sub", True)
        self.toggle_visual = ToggleRow("config_visual_data", "config_visual_data_sub", True)
        tc_layout.addWidget(self.toggle_text)
        tc_layout.addWidget(self.toggle_visual)

        cards_grid.addWidget(type_card, 0, 1)

        layout.addWidget(cards_widget)
        layout.addSpacing(30)

        # ─── زر التشغيل ───
        self._start_btn = QPushButton(t("config_start_btn"))
        self._start_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._start_btn.setFixedHeight(56)
        self._start_btn.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self._start_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 {CYAN},stop:1 {BLUE});
                color: {BG_DEEP};
                border-radius: 10px; border: none;
            }}
            QPushButton:hover {{ background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #33ffcc,stop:1 #33ccff); }}
        """)
        self._start_btn.clicked.connect(self._start)
        layout.addWidget(self._start_btn)
        layout.addStretch()

        scroll_area.setWidget(content)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll_area)

    def _create_card(self, title_key):
        card = QFrame()
        card.setStyleSheet(f"""
            .QFrame {{
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 rgba(0,0,0,0.04), stop:1 rgba(0,0,0,0.01));
                border-radius: 18px;
                border: 1.5px solid {BORDER_CYAN};
                border-top: 1px solid rgba(0, 0, 0, 0.08);
            }}
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(0)

        header = QWidget()
        header.setFixedHeight(40)
        header.setStyleSheet("background: transparent; border: none;")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(16, 8, 16, 8)

        dot = QFrame()
        dot.setFixedSize(6, 6)
        dot.setStyleSheet(f"background-color: {CYAN}; border-radius: 3px;")

        lbl = QLabel(t(title_key).upper())
        lbl.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        lbl.setStyleSheet(f"color: {CYAN}; letter-spacing: 1px;")

        # Qt's layoutDirection handles mirroring automatically
        h_layout.addWidget(dot)
        h_layout.addSpacing(6)
        h_layout.addWidget(lbl)
        h_layout.addStretch()

        card_layout.addWidget(header)
        return lbl, card

    def _on_lang_changed(self, lang):
        self._labels["title"].setText(t("config_title"))
        self._labels["title"].setAlignment(lang_manager.align)
        self._labels["sub"].setText(t("config_sub"))
        self._labels["sub"].setAlignment(lang_manager.align)
        self._start_btn.setText(t("config_start_btn"))
        self._path_card_lbl.setText(t("config_paths_title"))
        self._type_card_lbl.setText(t("config_types_title"))

    def _start(self):
        path = self.folder_selector.path_input.text().strip()
        use_desktop = self.toggle_desktop.switch.checked
        use_downloads = self.toggle_downloads.switch.checked
        use_documents = self.toggle_documents.switch.checked
        
        if not path and not any([use_desktop, use_downloads, use_documents]):
            ModernDialog(t("err_path_title"), t("err_path_missing"), self).exec()
            return
            
        if path and not os.path.exists(path):
            ModernDialog(t("err_path_title"), t("err_path_invalid"), self).exec()
            return
            
        target_paths = []
        if path: target_paths.append(os.path.normpath(path))
        if use_desktop: target_paths.append(os.path.normpath(os.path.expanduser("~/Desktop")))
        if use_downloads: target_paths.append(os.path.normpath(os.path.expanduser("~/Downloads")))
        if use_documents: target_paths.append(os.path.normpath(os.path.expanduser("~/Documents")))

        # تحديد الوضع (Mode)
        is_text = self.toggle_text.switch.checked
        is_visual = self.toggle_visual.switch.checked
        
        mode = "all"
        if is_text and not is_visual: mode = "text"
        elif is_visual and not is_text: mode = "images"
        elif not is_text and not is_visual:
            ModernDialog(t("err_path_title"), t("err_type_missing"), self).exec()
            return

        if self.on_navigate:
            self.on_navigate("pr", start_processing=True, target_paths=target_paths, mode=mode)