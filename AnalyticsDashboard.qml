import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Item {
    id: dashRoot
    width: parent ? parent.width : 1280
    height: parent ? parent.height : 820

    property int animTotal:  0
    property int animTime:   0
    property int animText:   0
    property int animImages: 0

    Timer {
        id: counterTimer
        interval: 30
        repeat: true
        property int tick: 0
        property int steps: 40
        onTriggered: {
            tick++
            var p = tick / steps
            var eq = 1 - Math.pow(1 - p, 4)
            if (typeof kiroBackend !== "undefined") {
                dashRoot.animTotal  = Math.round(kiroBackend.totalFiles * eq)
                dashRoot.animTime   = Math.round(kiroBackend.timeSaved * eq)
                dashRoot.animText   = Math.round(kiroBackend.textCount * eq)
                dashRoot.animImages = Math.round(kiroBackend.imageCount * eq)
            } else {
                dashRoot.animTotal = Math.round(340 * eq)
                dashRoot.animTime = Math.round(12 * eq)
                dashRoot.animText = Math.round(200 * eq)
                dashRoot.animImages = Math.round(140 * eq)
            }
            if (tick >= steps) stop()
        }
    }

    Connections {
        target: typeof kiroBackend !== "undefined" ? kiroBackend : null
        function onStatsUpdated() { counterTimer.tick = 0; counterTimer.start() }
    }

    Component.onCompleted: {
        counterTimer.tick = 0
        counterTimer.start()
        dashRoot.opacity = 0
        entAnim.start()
    }

    Flickable {
        anchors.fill: parent
        contentHeight: mainCol.implicitHeight + 80
        clip: true
        boundsBehavior: Flickable.StopAtBounds

        ColumnLayout {
            id: mainCol
            anchors.top: parent.top
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.margins: 50
            anchors.topMargin: 45
            spacing: 30

            // ── Header ──────────────────────────────
            RowLayout {
                Layout.fillWidth: true
                spacing: 18

                Rectangle {
                    width: 48; height: 48; radius: 24
                    color: backM.containsMouse ? "#C0DCE8" : "#D5EAF2"
                    border.color: "#90C8DE"; border.width: 1
                    Behavior on color { ColorAnimation { duration: 150 } }
                    Text {
                        anchors.centerIn: parent
                        text: "→"
                        font.pixelSize: 22
                        font.weight: Font.Bold
                        color: "#334155"
                    }
                    MouseArea {
                        id: backM
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: {
                            if (typeof kiroBackend !== "undefined")
                                kiroBackend.currentScreen = "WelcomeScreen.qml"
                        }
                    }
                }

                ColumnLayout {
                    spacing: 4
                    Layout.fillWidth: true
                    Text {
                        text: "📊  لوحة التحليلات والنتائج"
                        font.pixelSize: 30
                        font.weight: Font.Bold
                        font.family: "Segoe UI"
                        color: "#0F172A"
                    }
                    Text {
                        text: "ملخص شامل لعملية التنظيم الذكي"
                        font.pixelSize: 15
                        font.family: "Segoe UI"
                        color: "#64748B"
                    }
                }
            }

            // ── Success Banner ──────────────────────────────────────────────
            Rectangle {
                Layout.fillWidth: true
                height: 60
                radius: 16
                color: "#ECFDF5"
                border.color: "#6EE7B7"
                border.width: 1

                RowLayout {
                    anchors.left: parent.left
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.leftMargin: 20
                    spacing: 14

                    Rectangle {
                        width: 34; height: 34; radius: 17
                        color: "#10B981"
                        Text {
                            anchors.centerIn: parent
                            text: "✓"
                            font.pixelSize: 18
                            font.weight: Font.Bold
                            color: "white"
                        }
                    }
                    Text {
                        text: "تم تنظيم ملفاتك بنجاح تام! إليك ملخص النتائج أدناه."
                        font.pixelSize: 16
                        font.weight: Font.Bold
                        font.family: "Segoe UI"
                        color: "#065F46"
                    }
                }
            }

            // ── KPI Cards Row ──────────────────────────────
            RowLayout {
                Layout.fillWidth: true
                spacing: 20

                // Card 1: Total Files
                Rectangle {
                    Layout.fillWidth: true
                    height: 130
                    radius: 18
                    color: "#D8EEF6"
                    border.color: "#90C8DE"
                    border.width: 1

                    // Shadow
                    Rectangle {
                        anchors.centerIn: parent
                        anchors.verticalCenterOffset: 5
                        width: parent.width
                        height: parent.height
                        radius: 18
                        color: "black"
                        opacity: 0.03
                        z: -1
                    }

                    Rectangle {
                        width: 5; height: 45; radius: 2.5
                        anchors.left: parent.left
                        anchors.verticalCenter: parent.verticalCenter
                        color: "#6366F1"
                    }

                    ColumnLayout {
                        anchors.left: parent.left
                        anchors.verticalCenter: parent.verticalCenter
                        anchors.leftMargin: 22
                        spacing: 6

                        RowLayout {
                            spacing: 10
                            Rectangle {
                                width: 36; height: 36; radius: 10
                                color: "#EEF2FF"
                                Text { anchors.centerIn: parent; text: "🗂️"; font.pixelSize: 18 }
                            }
                            Text { text: "إجمالي الملفات"; font.pixelSize: 14; font.family: "Segoe UI"; color: "#64748B" }
                        }
                        RowLayout {
                            spacing: 6
                            Text {
                                text: dashRoot.animTotal.toString()
                                font.pixelSize: 38
                                font.weight: Font.ExtraBold
                                font.family: "Segoe UI"
                                color: "#6366F1"
                            }
                            Text {
                                text: "ملف"
                                font.pixelSize: 14
                                font.family: "Segoe UI"
                                color: "#94A3B8"
                                Layout.alignment: Qt.AlignBottom
                                Layout.bottomMargin: 6
                            }
                        }
                    }
                }

                // Card 2: Time Saved
                Rectangle {
                    Layout.fillWidth: true
                    height: 130
                    radius: 18
                    color: "#D8EEF6"
                    border.color: "#90C8DE"
                    border.width: 1

                    Rectangle {
                        anchors.centerIn: parent
                        anchors.verticalCenterOffset: 5
                        width: parent.width; height: parent.height
                        radius: 18; color: "black"; opacity: 0.03; z: -1
                    }

                    Rectangle {
                        width: 5; height: 45; radius: 2.5
                        anchors.left: parent.left
                        anchors.verticalCenter: parent.verticalCenter
                        color: "#10B981"
                    }

                    ColumnLayout {
                        anchors.left: parent.left
                        anchors.verticalCenter: parent.verticalCenter
                        anchors.leftMargin: 22
                        spacing: 6

                        RowLayout {
                            spacing: 10
                            Rectangle {
                                width: 36; height: 36; radius: 10
                                color: "#ECFDF5"
                                Text { anchors.centerIn: parent; text: "⚡"; font.pixelSize: 18 }
                            }
                            Text { text: "الوقت المُوفّر"; font.pixelSize: 14; font.family: "Segoe UI"; color: "#64748B" }
                        }
                        RowLayout {
                            spacing: 6
                            Text {
                                text: dashRoot.animTime.toString()
                                font.pixelSize: 38
                                font.weight: Font.ExtraBold
                                font.family: "Segoe UI"
                                color: "#10B981"
                            }
                            Text {
                                text: "دقيقة"
                                font.pixelSize: 14
                                font.family: "Segoe UI"
                                color: "#94A3B8"
                                Layout.alignment: Qt.AlignBottom
                                Layout.bottomMargin: 6
                            }
                        }
                    }
                }

                // Card 3: Text Files
                Rectangle {
                    Layout.fillWidth: true
                    height: 130
                    radius: 18
                    color: "#D8EEF6"
                    border.color: "#90C8DE"
                    border.width: 1

                    Rectangle {
                        anchors.centerIn: parent
                        anchors.verticalCenterOffset: 5
                        width: parent.width; height: parent.height
                        radius: 18; color: "black"; opacity: 0.03; z: -1
                    }

                    Rectangle {
                        width: 5; height: 45; radius: 2.5
                        anchors.left: parent.left
                        anchors.verticalCenter: parent.verticalCenter
                        color: "#3B82F6"
                    }

                    ColumnLayout {
                        anchors.left: parent.left
                        anchors.verticalCenter: parent.verticalCenter
                        anchors.leftMargin: 22
                        spacing: 6

                        RowLayout {
                            spacing: 10
                            Rectangle {
                                width: 36; height: 36; radius: 10
                                color: "#EFF6FF"
                                Text { anchors.centerIn: parent; text: "📄"; font.pixelSize: 18 }
                            }
                            Text { text: "المستندات"; font.pixelSize: 14; font.family: "Segoe UI"; color: "#64748B" }
                        }
                        RowLayout {
                            spacing: 6
                            Text {
                                text: dashRoot.animText.toString()
                                font.pixelSize: 38
                                font.weight: Font.ExtraBold
                                font.family: "Segoe UI"
                                color: "#3B82F6"
                            }
                            Text {
                                text: "نص"
                                font.pixelSize: 14
                                font.family: "Segoe UI"
                                color: "#94A3B8"
                                Layout.alignment: Qt.AlignBottom
                                Layout.bottomMargin: 6
                            }
                        }
                    }
                }

                // Card 4: Images
                Rectangle {
                    Layout.fillWidth: true
                    height: 130
                    radius: 18
                    color: "#D8EEF6"
                    border.color: "#90C8DE"
                    border.width: 1

                    Rectangle {
                        anchors.centerIn: parent
                        anchors.verticalCenterOffset: 5
                        width: parent.width; height: parent.height
                        radius: 18; color: "black"; opacity: 0.03; z: -1
                    }

                    Rectangle {
                        width: 5; height: 45; radius: 2.5
                        anchors.left: parent.left
                        anchors.verticalCenter: parent.verticalCenter
                        color: "#EC4899"
                    }

                    ColumnLayout {
                        anchors.left: parent.left
                        anchors.verticalCenter: parent.verticalCenter
                        anchors.leftMargin: 22
                        spacing: 6

                        RowLayout {
                            spacing: 10
                            Rectangle {
                                width: 36; height: 36; radius: 10
                                color: "#FDF2F8"
                                Text { anchors.centerIn: parent; text: "🖼️"; font.pixelSize: 18 }
                            }
                            Text { text: "الصور"; font.pixelSize: 14; font.family: "Segoe UI"; color: "#64748B" }
                        }
                        RowLayout {
                            spacing: 6
                            Text {
                                text: dashRoot.animImages.toString()
                                font.pixelSize: 38
                                font.weight: Font.ExtraBold
                                font.family: "Segoe UI"
                                color: "#EC4899"
                            }
                            Text {
                                text: "صورة"
                                font.pixelSize: 14
                                font.family: "Segoe UI"
                                color: "#94A3B8"
                                Layout.alignment: Qt.AlignBottom
                                Layout.bottomMargin: 6
                            }
                        }
                    }
                }
            }

            // ── Charts Row ──────────────────────────────
            RowLayout {
                Layout.fillWidth: true
                spacing: 24
                Layout.preferredHeight: 300

                // Distribution Chart
                Rectangle {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    radius: 20
                    color: "#D8EEF6"
                    border.color: "#90C8DE"
                    border.width: 1

                    Rectangle {
                        anchors.centerIn: parent
                        anchors.verticalCenterOffset: 5
                        width: parent.width; height: parent.height
                        radius: 20; color: "black"; opacity: 0.03; z: -1
                    }

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 28
                        spacing: 20

                        Text {
                            text: "📈  توزيع أنواع الملفات"
                            font.pixelSize: 18
                            font.weight: Font.Bold
                            font.family: "Segoe UI"
                            color: "#1E293B"
                        }

                        Item {
                            id: distItem
                            Layout.fillWidth: true
                            Layout.fillHeight: true

                            property int tC: typeof kiroBackend !== "undefined" ? kiroBackend.textCount : 50
                            property int iC: typeof kiroBackend !== "undefined" ? kiroBackend.imageCount : 50
                            property real total: tC + iC
                            property real textPct: total > 0 ? (tC / total) * 100 : 50
                            property real imgPct: total > 0 ? (iC / total) * 100 : 50

                            ColumnLayout {
                                anchors.centerIn: parent
                                spacing: 30
                                width: parent.width * 0.85

                                RowLayout {
                                    Layout.alignment: Qt.AlignHCenter
                                    spacing: 50

                                    ColumnLayout {
                                        spacing: 4
                                        Text {
                                            Layout.alignment: Qt.AlignHCenter
                                            text: Math.round(distItem.textPct).toString() + "%"
                                            font.pixelSize: 42
                                            font.weight: Font.ExtraBold
                                            font.family: "Segoe UI"
                                            color: "#3B82F6"
                                        }
                                        Text {
                                            Layout.alignment: Qt.AlignHCenter
                                            text: "مستندات نصية"
                                            font.pixelSize: 14
                                            font.weight: Font.DemiBold
                                            font.family: "Segoe UI"
                                            color: "#64748B"
                                        }
                                    }

                                    Rectangle { width: 1; height: 70; color: "#E2E8F0" }

                                    ColumnLayout {
                                        spacing: 4
                                        Text {
                                            Layout.alignment: Qt.AlignHCenter
                                            text: Math.round(distItem.imgPct).toString() + "%"
                                            font.pixelSize: 42
                                            font.weight: Font.ExtraBold
                                            font.family: "Segoe UI"
                                            color: "#EC4899"
                                        }
                                        Text {
                                            Layout.alignment: Qt.AlignHCenter
                                            text: "صور ووسائط"
                                            font.pixelSize: 14
                                            font.weight: Font.DemiBold
                                            font.family: "Segoe UI"
                                            color: "#64748B"
                                        }
                                    }
                                }

                                // Progress bar
                                Rectangle {
                                    Layout.fillWidth: true
                                    height: 18
                                    radius: 9
                                    color: "#F1F5F9"
                                    clip: true

                                    Rectangle {
                                        width: parent.width * (distItem.textPct / 100)
                                        height: parent.height
                                        radius: 9
                                        gradient: Gradient {
                                            orientation: Gradient.Horizontal
                                            GradientStop { position: 0.0; color: "#3B82F6" }
                                            GradientStop { position: 1.0; color: "#8B5CF6" }
                                        }
                                        Behavior on width {
                                            NumberAnimation { duration: 1200; easing.type: Easing.OutQuint }
                                        }
                                    }
                                }

                                // Legend
                                RowLayout {
                                    Layout.alignment: Qt.AlignHCenter
                                    spacing: 30
                                    RowLayout {
                                        spacing: 8
                                        Rectangle { width: 14; height: 14; radius: 7; color: "#3B82F6" }
                                        Text { text: "مستندات"; font.pixelSize: 13; font.family: "Segoe UI"; color: "#64748B" }
                                    }
                                    RowLayout {
                                        spacing: 8
                                        Rectangle { width: 14; height: 14; radius: 7; color: "#EC4899" }
                                        Text { text: "صور"; font.pixelSize: 13; font.family: "Segoe UI"; color: "#64748B" }
                                    }
                                }
                            }
                        }
                    }
                }

                // Agent Progress Card
                Rectangle {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    Layout.preferredWidth: 1.4
                    radius: 20
                    color: "#D8EEF6"
                    border.color: "#90C8DE"
                    border.width: 1

                    Rectangle {
                        anchors.centerIn: parent
                        anchors.verticalCenterOffset: 5
                        width: parent.width; height: parent.height
                        radius: 20; color: "black"; opacity: 0.03; z: -1
                    }

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 28
                        spacing: 18

                        Text {
                            text: "🤖  تقدم الوكيل الذكي"
                            font.pixelSize: 18
                            font.weight: Font.Bold
                            font.family: "Segoe UI"
                            color: "#1E293B"
                        }

                        // Pipeline Steps
                        Repeater {
                            model: [
                                { step: "فحص المجلدات", icon: "🔍", pct: 100, clr: "#10B981", status: "مكتمل" },
                                { step: "تصنيف الملفات بالذكاء الاصطناعي", icon: "🧠", pct: 100, clr: "#6366F1", status: "مكتمل" },
                                { step: "نقل الملفات للمجلدات المناسبة", icon: "📦", pct: 100, clr: "#3B82F6", status: "مكتمل" },
                                { step: "التحقق من السلامة", icon: "✅", pct: 100, clr: "#10B981", status: "مكتمل" }
                            ]

                            delegate: ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 6

                                RowLayout {
                                    Layout.fillWidth: true
                                    spacing: 10

                                    // Status circle
                                    Rectangle {
                                        width: 28; height: 28; radius: 14
                                        color: modelData.clr

                                        Text {
                                            anchors.centerIn: parent
                                            text: "✓"
                                            font.pixelSize: 14
                                            font.weight: Font.Bold
                                            color: "white"
                                        }
                                    }

                                    Text {
                                        text: modelData.icon + "  " + modelData.step
                                        font.pixelSize: 14
                                        font.weight: Font.DemiBold
                                        font.family: "Segoe UI"
                                        color: "#334155"
                                        Layout.fillWidth: true
                                    }

                                    // Percentage badge
                                    Rectangle {
                                        width: 58; height: 26; radius: 13
                                        color: "#ECFDF5"
                                        border.color: "#A7F3D0"; border.width: 1
                                        Text {
                                            anchors.centerIn: parent
                                            text: Number(modelData.pct).toString() + "%"
                                            font.pixelSize: 12
                                            font.weight: Font.Bold
                                            font.family: "Segoe UI"
                                            color: "#059669"
                                        }
                                    }
                                }

                                // Progress bar for each step
                                Rectangle {
                                    Layout.fillWidth: true
                                    Layout.leftMargin: 38
                                    height: 8
                                    radius: 4
                                    color: "#F1F5F9"
                                    clip: true

                                    Rectangle {
                                        id: stepBar
                                        width: 0
                                        height: parent.height
                                        radius: 4
                                        color: modelData.clr

                                        Component.onCompleted: {
                                            stepGrow.start()
                                        }
                                        NumberAnimation {
                                            id: stepGrow
                                            target: stepBar
                                            property: "width"
                                            from: 0
                                            to: stepBar.parent.width * (modelData.pct / 100)
                                            duration: 1000 + index * 350
                                            easing.type: Easing.OutQuint
                                        }
                                    }
                                }
                            }
                        }

                        // Overall score
                        Item { Layout.fillHeight: true }

                        Rectangle {
                            Layout.fillWidth: true
                            height: 44
                            radius: 12
                            color: "#F0FDF4"
                            border.color: "#BBF7D0"; border.width: 1

                            RowLayout {
                                anchors.centerIn: parent
                                spacing: 10
                                Text { text: "🏆"; font.pixelSize: 18 }
                                Text {
                                    text: "العملية اكتملت بنسبة 100% — أداء ممتاز!"
                                    font.pixelSize: 14
                                    font.weight: Font.Bold
                                    font.family: "Segoe UI"
                                    color: "#166534"
                                }
                            }
                        }
                    }
                }
            }

            // ── Footer: Home Button Only ──────────────────────────────
            Rectangle {
                Layout.alignment: Qt.AlignHCenter
                Layout.topMargin: 10
                Layout.bottomMargin: 150
                width: 150 ////////////////////////////////////////
                height: 56
                radius: 28
                color: homeM.containsMouse ? "#C0DCE8" : "#D5EAF2"
                border.color: "#90C8DE"
                border.width: 1.5
                Behavior on color { ColorAnimation { duration: 150 } }
                scale: homeM.pressed ? 0.95 : 1.0
                Behavior on scale { NumberAnimation { duration: 100 } }

                RowLayout {
                    anchors.centerIn: parent
                    spacing: 10
                    Text { text: "🏠"; font.pixelSize: 18 }
                    Text {
                        text: "العودة للرئيسية" 
                        font.pixelSize: 18
                        font.weight: Font.Bold
                        font.family: "Segoe UI"
                        color: "#334155"
                    }
                }

                MouseArea {
                    id: homeM
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: {
                        if (typeof kiroBackend !== "undefined")
                            kiroBackend.currentScreen = "WelcomeScreen.qml"
                    }
                }
            }
        }
    }

    NumberAnimation {
        id: entAnim
        target: dashRoot
        property: "opacity"
        from: 0; to: 1
        duration: 500
        easing.type: Easing.OutCubic
    }
}
