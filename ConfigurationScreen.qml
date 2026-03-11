import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Item {
    id: configRoot
    width: parent ? parent.width : 1280
    height: parent ? parent.height : 820

    property var dirChecks: [true, false, false]
    property bool anyDirSelected: dirChecks[0] || dirChecks[1] || dirChecks[2]

    Flickable {
        anchors.fill: parent
        contentHeight: outerCol.implicitHeight + 100
        clip: true
        boundsBehavior: Flickable.StopAtBounds

        ColumnLayout {
            id: outerCol
            anchors { top: parent.top; left: parent.left; right: parent.right; margins: 50; topMargin: 50 }
            spacing: 35

            // ── Header ────────────────────────────────────────────────────
            RowLayout {
                Layout.fillWidth: true; spacing: 20

                Rectangle {
                    width: 48; height: 48; radius: 24
                    color: backMouse.containsMouse ? "#C0DCE8" : "#D5EAF2"
                    border.color: "#90C8DE"; border.width: 1
                    Behavior on color { ColorAnimation { duration: 150 } }
                    Text { anchors.centerIn: parent; text: "→"; font.pixelSize: 24; color: "#334155" }
                    MouseArea {
                        id: backMouse; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                        onClicked: if (typeof kiroBackend !== "undefined") kiroBackend.currentScreen = "WelcomeScreen.qml"
                    }
                }

                ColumnLayout {
                    spacing: 5
                    Text { text: "تكوين إعدادات التنظيم"; font.pixelSize: 34; font.weight: Font.Bold; font.family: "Segoe UI"; color: "#0F172A" }
                    Text { text: "اختر المجلدات المستهدفة وأنواع الملفات المراد معالجتها"; font.pixelSize: 16; font.family: "Segoe UI"; color: "#64748B" }
                }
            }

            // ── Section 1: Directories ────────────────────────────────────
            Rectangle {
                Layout.fillWidth: true; height: dirSection.implicitHeight + 60
                radius: 20; color: "#C8E0F0F5"
                border.color: "#80A8D0E5"; border.width: 1
                
                Rectangle { anchors.centerIn: parent; width: parent.width; height: parent.height; anchors.verticalCenterOffset: 10; radius: 20; color: "#1A5090B0"; z: -1 }

                ColumnLayout {
                    id: dirSection
                    anchors { left: parent.left; right: parent.right; top: parent.top; margins: 30 }
                    spacing: 24

                    RowLayout {
                        spacing: 12
                        Rectangle { width: 5; height: 26; radius: 2.5; color: "#3B82F6" }
                        Text { text: "1. تحديد المجلدات"; font.pixelSize: 20; font.weight: Font.Bold; font.family: "Segoe UI"; color: "#1E293B" }
                    }

                    GridLayout {
                        columns: 3; columnSpacing: 18; Layout.fillWidth: true

                        Repeater {
                            model: [
                                { icon: "💻", desc: "سطح المكتب", borderHover: "#3B82F6", bgActive: "#EFF6FF" },
                                { icon: "📥", desc: "التنزيلات", borderHover: "#8B5CF6", bgActive: "#F5F3FF" },
                                { icon: "📂", desc: "المستندات", borderHover: "#EC4899", bgActive: "#FDF2F8" }
                            ]
                            delegate: Rectangle {
                                id: dirCard
                                property bool isChecked: configRoot.dirChecks[index]
                                Layout.fillWidth: true; height: 120; radius: 18
                                color: isChecked ? modelData.bgActive : (dirMouse.containsMouse ? "#D8EDF5" : "#E0F0F8")
                                border.color: isChecked ? modelData.borderHover : (dirMouse.containsMouse ? "#90C8DE" : "#A0D0E5")
                                border.width: isChecked ? 2 : 1
                                Behavior on color { ColorAnimation { duration: 200 } }
                                Behavior on border.color { ColorAnimation { duration: 200 } }

                                scale: dirMouse.pressed ? 0.96 : 1.0
                                Behavior on scale { NumberAnimation { duration: 150 } }

                                ColumnLayout {
                                    anchors.centerIn: parent; spacing: 12
                                    Text { Layout.alignment: Qt.AlignHCenter; text: modelData.icon; font.pixelSize: 34 }
                                    Text { Layout.alignment: Qt.AlignHCenter; text: modelData.desc; font.pixelSize: 16; font.weight: Font.DemiBold; font.family: "Segoe UI"; color: isChecked ? "#0F172A" : "#475569" }
                                }

                                Rectangle {
                                    visible: dirCard.isChecked
                                    width: 26; height: 26; radius: 13
                                    anchors { top: parent.top; right: parent.right; margins: 12 }
                                    color: modelData.borderHover
                                    Text { anchors.centerIn: parent; text: "✓"; font.pixelSize: 14; font.weight: Font.Bold; color: "white" }
                                }

                                MouseArea {
                                    id: dirMouse; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                                    onClicked: {
                                        var a = [configRoot.dirChecks[0], configRoot.dirChecks[1], configRoot.dirChecks[2]]
                                        a[index] = !a[index]
                                        configRoot.dirChecks = a
                                    }
                                }
                            }
                        }
                    }
                }
            }

            // ── Section 2: File Types ─────────────────────────────────────
            Rectangle {
                Layout.fillWidth: true; height: ftSection.implicitHeight + 60
                radius: 20; color: "#C8E0F0F5"
                border.color: "#80A8D0E5"; border.width: 1
                Rectangle { anchors.centerIn: parent; width: parent.width; height: parent.height; anchors.verticalCenterOffset: 10; radius: 20; color: "#1A5090B0"; z: -1 }

                ColumnLayout {
                    id: ftSection
                    anchors { left: parent.left; right: parent.right; top: parent.top; margins: 30 }
                    spacing: 24

                    RowLayout {
                        spacing: 12
                        Rectangle { width: 5; height: 26; radius: 2.5; color: "#8B5CF6" }
                        Text { text: "2. أنواع الملفات"; font.pixelSize: 20; font.weight: Font.Bold; font.family: "Segoe UI"; color: "#1E293B" }
                    }

                    Rectangle {
                        Layout.fillWidth: true; height: 66; radius: 16
                        color: masterSwitch.checked ? "#D5ECF5" : "#E0F0F8"
                        border.color: masterSwitch.checked ? "#90C8DE" : "#A0D0E5"; border.width: 1
                        RowLayout {
                            anchors { verticalCenter: parent.verticalCenter; left: parent.left; right: parent.right; margins: 22 }
                            Text { text: "معالجة جميع الأنواع المتوفرة"; font.pixelSize: 16; font.weight: Font.DemiBold; font.family: "Segoe UI"; color: "#334155"; Layout.fillWidth: true }
                            Switch {
                                id: masterSwitch; checked: true
                                onToggled: { textSwitch.checked = checked; imageSwitch.checked = checked }
                            }
                        }
                    }

                    GridLayout {
                        columns: 2; columnSpacing: 18; rowSpacing: 18; Layout.fillWidth: true

                        // Text card
                        Rectangle {
                            Layout.fillWidth: true; height: 86; radius: 16
                            color: textSwitch.checked ? "#E8E5FF" : "#E0F0F8"
                            border.color: textSwitch.checked ? "#8B5CF6" : "#E2E8F0"; border.width: 1
                            RowLayout {
                                anchors { left: parent.left; right: parent.right; verticalCenter: parent.verticalCenter; margins: 20 }
                                spacing: 18
                                Rectangle {
                                    width: 52; height: 52; radius: 14; color: "#EDE9FE"
                                    Text { anchors.centerIn: parent; text: "📄"; font.pixelSize: 24 }
                                }
                                ColumnLayout {
                                    spacing: 4; Layout.fillWidth: true
                                    Text { text: "المستندات النصية"; font.pixelSize: 16; font.weight: Font.Bold; font.family: "Segoe UI"; color: "#1E293B" }
                                    Text { text: ".txt, .pdf, .docx"; font.pixelSize: 13; font.family: "Segoe UI"; color: "#64748B" }
                                }
                                Switch { id: textSwitch; checked: true; onToggled: masterSwitch.checked = (checked && imageSwitch.checked) }
                            }
                        }

                        // Image card
                        Rectangle {
                            Layout.fillWidth: true; height: 86; radius: 16
                            color: textSwitch.checked ? "#E8E5FF" : "#E0F0F8"
                            border.color: textSwitch.checked ? "#8B5CF6" : "#E2E8F0"; border.width: 1
                            RowLayout {
                                anchors { left: parent.left; right: parent.right; verticalCenter: parent.verticalCenter; margins: 20 }
                                spacing: 18
                                Rectangle {
                                    width: 52; height: 52; radius: 14; color: "#EDE9FE"
                                    Text { anchors.centerIn: parent; text: "🖼️"; font.pixelSize: 24 }
                                }
                                ColumnLayout {
                                    spacing: 4; Layout.fillWidth: true
                                    Text { text: "الصور والوسائط"; font.pixelSize: 16; font.weight: Font.Bold; font.family: "Segoe UI"; color: "#1E293B" }
                                    Text { text: ".jpg, .png, .gif"; font.pixelSize: 13; font.family: "Segoe UI"; color: "#64748B" }
                                }
                                Switch { id: imageSwitch; checked: true; onToggled: masterSwitch.checked = (textSwitch.checked && checked) }
                            }
                        }
                    }
                }
            }

            // ── Warning ───────────────────────────────────────────────────
            Rectangle {
                Layout.fillWidth: true; height: 56; radius: 14
                color: "#FEF2F2"; border.color: "#FCA5A5"; border.width: 1
                visible: !configRoot.anyDirSelected
                RowLayout {
                    anchors { left: parent.left; right: parent.right; verticalCenter: parent.verticalCenter; margins: 20 }
                    Text { text: "⚠️"; font.pixelSize: 18 }
                    Text { text: "يمكنك المتابعة بدون مجلدات لتجربة النظام، أو اختيار مجلد"; font.pixelSize: 15; font.weight: Font.Bold; font.family: "Segoe UI"; color: "#B91C1C"; Layout.fillWidth: true }
                }
            }

            // ── Start button ──────────────────────────────────────────────
            Rectangle {
                Layout.alignment: Qt.AlignHCenter
                Layout.preferredWidth: 320; Layout.preferredHeight: 64; Layout.bottomMargin: 30
                radius: 32
                opacity: 1.0 // دائمًا ظاهر
                Behavior on opacity { NumberAnimation { duration: 250 } }

                gradient: Gradient {
                    orientation: Gradient.Horizontal
                    GradientStop { position: 0.0; color: startMouse.containsMouse ? "#2563EB" : "#3B82F6" }
                    GradientStop { position: 1.0; color: startMouse.containsMouse ? "#4F46E5" : "#6366F1" }
                }

                scale: startMouse.pressed ? 0.95 : 1.0
                Behavior on scale { NumberAnimation { duration: 150 } }

                Rectangle { anchors.centerIn: parent; width: parent.width; height: parent.height; anchors.verticalCenterOffset: 8; radius: 32; color: "#3B82F6"; opacity: startMouse.containsMouse ? 0.3 : 0.15; z: -1 }

                RowLayout {
                    anchors.centerIn: parent; spacing: 12
                    Text { text: "🚀"; font.pixelSize: 22 }
                    Text { text: "تفعيل التنظيم الذكي"; font.pixelSize: 19; font.weight: Font.Bold; font.family: "Segoe UI"; color: "white" }
                }

                MouseArea {
                    id: startMouse; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                    onClicked: {
                        var dirs = []
                        if (configRoot.dirChecks[0]) dirs.push("Desktop")
                        if (configRoot.dirChecks[1]) dirs.push("Downloads")
                        if (configRoot.dirChecks[2]) dirs.push("Documents")
                        
                        // Default to Desktop if none selected just for UI showcase
                        if (dirs.length === 0) dirs.push("Default_Demo")

                        if (typeof kiroBackend !== "undefined") kiroBackend.startOrganizing(dirs, textSwitch.checked, imageSwitch.checked)
                    }
                }
            }
        }
    }

    Component.onCompleted: { configRoot.opacity = 0; entAnim.start() }
    NumberAnimation { id: entAnim; target: configRoot; property: "opacity"; from: 0; to: 1; duration: 450; easing.type: Easing.OutCubic }
}
