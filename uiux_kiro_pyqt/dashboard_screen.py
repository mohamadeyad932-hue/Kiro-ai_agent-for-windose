"""
Kiro AI - Dashboard Screen (PyQt6) - Bilingual
شاشة لوحة التحكم والنتائج
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QPushButton, QFrame, QScrollArea, QGridLayout,
                              QProgressBar, QGraphicsDropShadowEffect)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor
from translations import lang_manager, t

from theme import (
    BG_DEEP, BG_MID, CYAN, BLUE, VIOLET, EMERALD, AMBER,
    TEXT_MAIN, TEXT_SUB, GLASS, BORDER_CYAN
)


class DashboardScreen(QWidget):
    """شاشة النتائج - إحصائيات + قائمة المجلدات الذكية"""

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

        # ─── بطاقة النجاح (Hero) ───
        hero = QFrame(); hero.setObjectName("hero")
        hero.setStyleSheet(f"QFrame#hero {{ background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 rgba(0, 120, 215, 0.08), stop:1 rgba(0, 120, 215, 0.04)); border-radius: 20px; border: 1.5px solid {BORDER_CYAN}; }}")
        hero_layout = QHBoxLayout(hero); hero_layout.setContentsMargins(20, 20, 20, 20); hero_layout.setSpacing(15)

        icon_frame = QLabel("✓")
        icon_frame.setFixedSize(60, 60); icon_frame.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_frame.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
        icon_frame.setStyleSheet(f"background: rgba(76, 194, 255, 0.15); color: {CYAN}; border: 1.5px solid {CYAN}; border-radius: 30px;")

        msg_widget = QWidget(); msg_widget.setStyleSheet("background: transparent;")
        msg_layout = QVBoxLayout(msg_widget); msg_layout.setContentsMargins(0, 0, 0, 0); msg_layout.setSpacing(4)

        self._labels["hero_title"] = QLabel(t("dash_hero_title"))
        self._labels["hero_title"].setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        self._labels["hero_title"].setStyleSheet(f"color: {TEXT_MAIN};")
        self._labels["hero_title"].setAlignment(lang_manager.align)

        self._labels["hero_desc"] = QLabel(t("dash_hero_desc"))
        self._labels["hero_desc"].setFont(QFont("Segoe UI", 11))
        self._labels["hero_desc"].setStyleSheet(f"color: {TEXT_SUB};")
        self._labels["hero_desc"].setAlignment(lang_manager.align)
        self._labels["hero_desc"].setWordWrap(True)

        msg_layout.addWidget(self._labels["hero_title"])
        msg_layout.addWidget(self._labels["hero_desc"])
        
        # Qt's layoutDirection handles mirroring automatically
        hero_layout.addWidget(msg_widget, stretch=1)
        hero_layout.addSpacing(10)
        hero_layout.addWidget(icon_frame)
        
        layout.addWidget(hero)
        layout.addSpacing(25)

        # ─── الإحصائيات ───
        stats_widget = QWidget()
        stats_widget.setStyleSheet("background: transparent;")
        stats_grid = QGridLayout(stats_widget)
        stats_grid.setSpacing(12)
        stats_grid.setContentsMargins(0, 0, 0, 0)

        stat_keys = [
            ("dash_stat1_label", "dash_stat1_value", VIOLET, "dash_stat1_sub"),
            ("dash_stat2_label", "dash_stat2_value", EMERALD, "dash_stat2_sub"),
            ("dash_stat3_label", "dash_stat3_value", CYAN, "dash_stat3_sub"),
            ("dash_stat4_label", "dash_stat4_value", AMBER, "dash_stat4_sub"),
        ]
        self._stat_widgets = []
        for i, (lbl_key, val_key, color, sub_key) in enumerate(stat_keys):
            card = QFrame(); card.setObjectName(f"stat{i}")
            card.setStyleSheet(f"QFrame#stat{i} {{ background: rgba(0, 0, 0, 0.04); border-radius: 16px; border: 1px solid rgba(0, 0, 0, 0.1); }}")
            c_layout = QVBoxLayout(card); c_layout.setContentsMargins(16, 16, 16, 16); c_layout.setSpacing(2)

            l_lbl = QLabel(t(lbl_key)); l_lbl.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold)); l_lbl.setStyleSheet(f"color: {TEXT_SUB};")
            l_lbl.setAlignment(lang_manager.align)

            v_lbl = QLabel(t(val_key)); v_lbl.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold)); v_lbl.setStyleSheet(f"color: {color};")
            v_lbl.setAlignment(lang_manager.align)

            s_lbl = QLabel(t(sub_key)); s_lbl.setFont(QFont("Segoe UI", 9)); s_lbl.setStyleSheet(f"color: {TEXT_SUB};")
            s_lbl.setAlignment(lang_manager.align); s_lbl.setWordWrap(True)

            c_layout.addWidget(l_lbl)
            c_layout.addWidget(v_lbl)
            c_layout.addWidget(s_lbl)

            # Qt handles grid mirroring via layoutDirection
            stats_grid.addWidget(card, 0, i)
            self._stat_widgets.append((lbl_key, l_lbl, val_key, v_lbl, sub_key, s_lbl))

        layout.addWidget(stats_widget)
        layout.addSpacing(20)

        # ─── قائمة المجلدات الذكية ───
        folder_card = QFrame(); folder_card.setObjectName("folders")
        folder_card.setStyleSheet(f"QFrame#folders {{ background: rgba(0, 0, 0, 0.03); border-radius: 18px; border: 1.5px solid {BORDER_CYAN}; }}")
        self.fc_layout = QVBoxLayout(folder_card); self.fc_layout.setContentsMargins(0, 0, 0, 0); self.fc_layout.setSpacing(0)

        head = QWidget(); head.setFixedHeight(48); head.setStyleSheet(f"background: rgba(0, 120, 215, 0.07); border-top-left-radius: 18px; border-top-right-radius: 18px; border-bottom: 1px solid {BORDER_CYAN};")
        h_layout = QHBoxLayout(head); h_layout.setContentsMargins(20, 0, 20, 0)

        self._labels["f_badge"] = QLabel(t("dash_folders_count"))
        self._labels["f_badge"].setFont(QFont("Segoe UI", 10, QFont.Weight.Bold)); self._labels["f_badge"].setStyleSheet(f"color: {CYAN}; background: transparent;")

        self._labels["f_title"] = QLabel(t("dash_folders_title"))
        self._labels["f_title"].setFont(QFont("Segoe UI", 12, QFont.Weight.Bold)); self._labels["f_title"].setStyleSheet(f"color: {TEXT_MAIN}; background: transparent;")

        # Qt's layoutDirection handles mirroring automatically
        h_layout.addWidget(self._labels["f_title"])
        h_layout.addStretch()
        h_layout.addWidget(self._labels["f_badge"])
        self.fc_layout.addWidget(head)

        self._folder_keys = [
            ("dash_folder1", 55, VIOLET, "dash_folder1_count"),
            ("dash_folder2", 42, EMERALD, "dash_folder2_count"),
            ("dash_folder3", 78, AMBER, "dash_folder3_count"),
        ]
        self._folder_labels = []
        for name_key, pct, color, count_key in self._folder_keys:
            name_lbl, count_lbl = self._folder_row(self.fc_layout, name_key, pct, color, count_key)
            self._folder_labels.append((name_key, name_lbl, count_key, count_lbl))

        layout.addWidget(folder_card)
        layout.addSpacing(15)

        # ─── زر البدء من جديد ───
        self._new_btn = QPushButton(t("dash_new_cycle"))
        self._new_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._new_btn.setFixedHeight(56)
        self._new_btn.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        self._new_btn.setStyleSheet(f"QPushButton {{ background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 {CYAN},stop:1 {BLUE}); color: {BG_DEEP}; border-radius: 14px; border: none; }} QPushButton:hover {{ background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #33ffcc,stop:1 #33ccff); }}")
        self._new_btn.clicked.connect(lambda: self.on_navigate("sp"))
        layout.addWidget(self._new_btn)
        layout.addStretch()

        scroll_area.setWidget(content)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll_area)

    def _folder_row(self, parent_layout, name_key, pct, color, count_key):
        sep = QFrame(); sep.setFixedHeight(1)
        sep.setStyleSheet(f"background-color: rgba(0, 0, 0, 0.06); border: none;")
        parent_layout.addWidget(sep)

        row = QWidget()
        row.setStyleSheet("background: transparent;")
        r_layout = QHBoxLayout(row)
        r_layout.setContentsMargins(20, 12, 20, 12)

        count_badge = QLabel(t(count_key))
        count_badge.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        count_badge.setFixedSize(74, 28)
        count_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        count_badge.setStyleSheet(f"background: rgba(16, 185, 129, 0.15); color: {EMERALD}; border-radius: 14px;")



        info_widget = QWidget()
        info_widget.setStyleSheet("background: transparent;")
        info_layout = QVBoxLayout(info_widget)
        info_layout.setContentsMargins(5, 0, 5, 0)
        info_layout.setSpacing(4)

        name_lbl = QLabel(t(name_key))
        name_lbl.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        name_lbl.setStyleSheet(f"color: {TEXT_MAIN}; background:transparent;")
        name_lbl.setAlignment(lang_manager.align | Qt.AlignmentFlag.AlignVCenter)

        prog_widget = QWidget()
        prog_widget.setStyleSheet("background: transparent;")
        prog_layout = QHBoxLayout(prog_widget)
        prog_layout.setContentsMargins(0, 0, 0, 0)
        prog_layout.setSpacing(6)

        pct_lbl = QLabel(f"{pct}%")
        pct_lbl.setFont(QFont("Consolas", 9, QFont.Weight.Bold))
        pct_lbl.setStyleSheet(f"color: {TEXT_SUB};")

        prog_bar = QProgressBar()
        prog_bar.setFixedSize(120, 6)
        prog_bar.setRange(0, 100)
        prog_bar.setValue(pct)
        prog_bar.setTextVisible(False)
        prog_bar.setStyleSheet(f"QProgressBar {{ background: rgba(0, 0, 0, 0.08); border-radius: 3px; border: none; }} QProgressBar::chunk {{ background: {color}; border-radius: 3px; }}")

        prog_layout.addWidget(pct_lbl)
        prog_layout.addWidget(prog_bar)
        prog_layout.addStretch()

        info_layout.addWidget(name_lbl)
        info_layout.addWidget(prog_widget)

        # Qt's layoutDirection handles mirroring automatically
        r_layout.addWidget(info_widget, stretch=1)
        r_layout.addStretch()
        r_layout.addWidget(count_badge)

        parent_layout.addWidget(row)
        return name_lbl, count_badge

    def _on_lang_changed(self, lang):
        self._labels["hero_title"].setText(t("dash_hero_title"))
        self._labels["hero_title"].setAlignment(lang_manager.align)
        self._labels["hero_desc"].setText(t("dash_hero_desc"))
        self._labels["hero_desc"].setAlignment(lang_manager.align)
        self._labels["f_badge"].setText(t("dash_folders_count"))
        self._labels["f_title"].setText(t("dash_folders_title"))
        self._new_btn.setText(t("dash_new_cycle"))

        for lbl_key, l_lbl, val_key, v_lbl, sub_key, s_lbl in self._stat_widgets:
            l_lbl.setText(t(lbl_key))
            l_lbl.setAlignment(lang_manager.align)
            s_lbl.setText(t(sub_key))
            s_lbl.setAlignment(lang_manager.align)

        for name_key, name_lbl, count_key, count_lbl in self._folder_labels:
            name_lbl.setText(t(name_key))
            name_lbl.setAlignment(lang_manager.align)
            count_lbl.setText(t(count_key))
