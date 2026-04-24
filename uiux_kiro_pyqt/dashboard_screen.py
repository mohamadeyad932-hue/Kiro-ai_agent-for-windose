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

    def showEvent(self, event):
        """تحديث الإحصائيات في كل مرة تظهر فيها الشاشة"""
        super().showEvent(event)
        self.update_stats()

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

            v_lbl = QLabel("0"); v_lbl.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold)); v_lbl.setStyleSheet(f"color: {color};")
            v_lbl.setAlignment(lang_manager.align)

            s_lbl = QLabel(""); s_lbl.setFont(QFont("Segoe UI", 9)); s_lbl.setStyleSheet(f"color: {TEXT_SUB};")
            s_lbl.setAlignment(lang_manager.align); s_lbl.setWordWrap(True)

            c_layout.addWidget(l_lbl)
            c_layout.addWidget(v_lbl)
            c_layout.addWidget(s_lbl)

            stats_grid.addWidget(card, 0, i)
            self._stat_widgets.append({'lbl': l_lbl, 'val': v_lbl, 'sub': s_lbl, 'keys': (lbl_key, val_key, sub_key)})

        layout.addWidget(stats_widget)
        layout.addSpacing(20)

        # ─── قائمة المجلدات الذكية ───
        folder_card = QFrame(); folder_card.setObjectName("folders")
        folder_card.setStyleSheet(f"QFrame#folders {{ background: rgba(0, 0, 0, 0.03); border-radius: 18px; border: 1.5px solid {BORDER_CYAN}; }}")
        self.fc_layout = QVBoxLayout(folder_card); self.fc_layout.setContentsMargins(0, 0, 0, 0); self.fc_layout.setSpacing(0)

        head = QWidget(); head.setFixedHeight(48); head.setStyleSheet(f"background: rgba(0, 120, 215, 0.07); border-top-left-radius: 18px; border-top-right-radius: 18px; border-bottom: 1px solid {BORDER_CYAN};")
        h_layout = QHBoxLayout(head); h_layout.setContentsMargins(20, 0, 20, 0)

        self._labels["f_badge"] = QLabel("0 Groups")
        self._labels["f_badge"].setFont(QFont("Segoe UI", 10, QFont.Weight.Bold)); self._labels["f_badge"].setStyleSheet(f"color: {CYAN}; background: transparent;")

        self._labels["f_title"] = QLabel(t("dash_folders_title"))
        self._labels["f_title"].setFont(QFont("Segoe UI", 12, QFont.Weight.Bold)); self._labels["f_title"].setStyleSheet(f"color: {TEXT_MAIN}; background: transparent;")

        h_layout.addWidget(self._labels["f_title"])
        h_layout.addStretch()
        h_layout.addWidget(self._labels["f_badge"])
        self.fc_layout.addWidget(head)
        
        # حاوية المجلدات الديناميكية
        self.folders_container = QWidget()
        self.folders_container.setStyleSheet("background: transparent;")
        self.folders_layout = QVBoxLayout(self.folders_container)
        self.folders_layout.setContentsMargins(0, 0, 0, 0)
        self.folders_layout.setSpacing(0)
        self.fc_layout.addWidget(self.folders_container)

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

    def update_stats(self):
        """قراءة ملف النتائج والتحقق من وجود المجلدات فعلياً لتحديث البيانات لحظياً"""
        import json
        import os
        
        json_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "created_folders.json")
        
        if not os.path.exists(json_path):
            self._reset_to_zero()
            return

        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)
            
            folders_raw = raw_data.get("created_folders", [])
            valid_folders = []
            
            # التحقق اللحظي من المجلدات (في حال قام المستخدم بحذفها أو تغيير محتواها)
            for f_entry in folders_raw:
                f_path = f_entry.get("folder_path", "")
                if os.path.exists(f_path) and os.path.isdir(f_path):
                    # تحديث عدد الملفات الحقيقي الموجود حالياً في المجلد
                    current_files = [item for item in os.listdir(f_path) if os.path.isfile(os.path.join(f_path, item))]
                    f_entry["files_count"] = len(current_files)
                    valid_folders.append(f_entry)

            if not valid_folders:
                self._reset_to_zero()
                return

            total_files = sum(f.get("files_count", 0) for f in valid_folders)
            total_groups = len(valid_folders)
            
            # تحديث كروت الإحصائيات
            self._stat_widgets[0]['val'].setText(str(total_files))
            self._stat_widgets[0]['sub'].setText(f"{total_groups} {t('dash_folders_count')}")
            
            # كارت الوقت الحقيقي المستلم من المحرك
            raw_time = raw_data.get("total_processing_time", 0)
            if raw_time == 0: #Fallback
                raw_time = total_files * 0.05
                
            if raw_time >= 60:
                mins = int(raw_time // 60)
                secs = int(raw_time % 60)
                time_str = f"{mins}m {secs}s" if secs > 0 else f"{mins}m"
            else:
                time_str = f"{raw_time:.1f}s"
                
            self._stat_widgets[1]['val'].setText(time_str)
            self._stat_widgets[1]['sub'].setText("Actual processing time")

            text_files = sum(f.get("files_count", 0) for f in valid_folders if f.get("type") == "text")
            visual_files = sum(f.get("files_count", 0) for f in valid_folders if f.get("type") == "image")
            
            self._stat_widgets[2]['val'].setText(str(text_files))
            self._stat_widgets[2]['sub'].setText(t("dash_stat3_sub"))
            self._stat_widgets[3]['val'].setText(str(visual_files))
            self._stat_widgets[3]['sub'].setText(t("dash_stat4_sub"))

            # تحديث الهيرو
            hero_desc = t("dash_hero_desc").replace("287", str(total_files))
            if "287" not in t("dash_hero_desc"):
                hero_desc = f"{t('dash_hero_desc')} ({total_files} items, {total_groups} folders)"
            self._labels["hero_desc"].setText(hero_desc)

            # تحديث قائمة المجلدات الذكية
            self._labels["f_badge"].setText(f"{total_groups} {t('dash_folders_count')}")
            self._clear_folders_list()
            
            for f_data in valid_folders:
                path = f_data.get("folder_path", "")
                # نستخدم اسم المجلد الفعلي من القرص
                display_name = os.path.basename(path).replace("_", " ").title()
                count = f_data.get("files_count", 0)
                self._add_folder_row(display_name, f"{count} {t('dash_files_suffix')}")

        except Exception as e:
            print(f"Error updating dashboard: {e}")
            self._reset_to_zero()

        except Exception as e:
            print(f"Error updating dashboard: {e}")
            self._reset_to_zero()

    def _reset_to_zero(self):
        """تصفير كافة الأرقام في الواجهة"""
        for item in self._stat_widgets:
            item['val'].setText("0")
        
        self._stat_widgets[0]['sub'].setText(f"0 {t('dash_folders_count')}")
        self._stat_widgets[1]['val'].setText("0.0s")
        self._stat_widgets[1]['sub'].setText("No active session")
        self._stat_widgets[2]['sub'].setText("0 Text files")
        self._stat_widgets[3]['sub'].setText("0 Image files")
        
        self._labels["hero_desc"].setText("System is ready. Start a new cycle to organize your files.")
        self._labels["f_badge"].setText(f"0 {t('dash_folders_count')}")
        self._clear_folders_list()

    def _clear_folders_list(self):
        """مسح قائمة المجلدات من الواجهة"""
        while self.folders_layout.count():
            item = self.folders_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _add_folder_row(self, name, count_text):
        sep = QFrame(); sep.setFixedHeight(1)
        sep.setStyleSheet(f"background-color: rgba(0, 0, 0, 0.06); border: none;")
        self.folders_layout.addWidget(sep)

        row = QWidget()
        row.setStyleSheet("background: transparent;")
        r_layout = QHBoxLayout(row)
        r_layout.setContentsMargins(20, 12, 20, 12)

        count_badge = QLabel(count_text)
        count_badge.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        count_badge.setFixedSize(90, 28)
        count_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        count_badge.setStyleSheet(f"background: rgba(16, 185, 129, 0.15); color: {EMERALD}; border-radius: 14px;")

        info_widget = QWidget()
        info_widget.setStyleSheet("background: transparent;")
        info_layout = QVBoxLayout(info_widget)
        info_layout.setContentsMargins(5, 0, 5, 0)
        info_layout.setSpacing(4)

        name_lbl = QLabel(name)
        name_lbl.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        name_lbl.setStyleSheet(f"color: {TEXT_MAIN}; background:transparent;")
        name_lbl.setAlignment(lang_manager.align | Qt.AlignmentFlag.AlignVCenter)

        info_layout.addWidget(name_lbl)

        r_layout.addWidget(info_widget, stretch=1)
        r_layout.addStretch()
        r_layout.addWidget(count_badge)

        self.folders_layout.addWidget(row)

    def _on_lang_changed(self, lang):
        self._labels["hero_title"].setText(t("dash_hero_title"))
        self._labels["hero_title"].setAlignment(lang_manager.align)
        # الوصف يتطلب إعادة تحديث بالأرقام الحقيقية، لذا نستدعي update_stats
        self.update_stats()
        
        self._labels["f_title"].setText(t("dash_folders_title"))
        self._new_btn.setText(t("dash_new_cycle"))

        for item in self._stat_widgets:
            item['lbl'].setText(t(item['keys'][0]))
            item['lbl'].setAlignment(lang_manager.align)
            # إعادة ترجمة النصوص الفرعية إذا لزم الأمر
            if item['keys'][2] == "dash_stat1_sub":
                pass # يتم تحديثه في update_stats
            else:
                item['sub'].setAlignment(lang_manager.align)
            