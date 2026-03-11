import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Item {
    id: root
    width: parent ? parent.width : 1280
    height: parent ? parent.height : 820

    // Frosted Teal-Blue Glass Card
    Rectangle {
        id: card
        anchors.centerIn: parent
        width: Math.min(550, root.width * 0.7)
        height: contentCol.implicitHeight + 100
        radius: 28
        gradient: Gradient {
            GradientStop { position: 0.0; color: "#C8E8F5F7" }
            GradientStop { position: 1.0; color: "#C8D5EEF8" }
        }
        border.color: "#60B0D8E8"
        border.width: 1.5

        ColumnLayout {
            id: contentCol
            anchors { top: parent.top; left: parent.left; right: parent.right; margins: 50; topMargin: 50 }
            spacing: 0

            // ── AI Core Mascot (Bright & Friendly) ───────────────────────────────────────
            Item {
                Layout.alignment: Qt.AlignHCenter
                Layout.preferredWidth: 140; Layout.preferredHeight: 140
                Layout.bottomMargin: 30

                // Outer Pulse Ring
                Rectangle {
                    anchors.centerIn: parent; width: 120; height: 120; radius: 60
                    color: "transparent"; border.color: "#3B82F6"; border.width: 2; opacity: 0
                    SequentialAnimation on opacity {
                        loops: Animation.Infinite
                        NumberAnimation { to: 0.5; duration: 1500; easing.type: Easing.OutCubic }
                        NumberAnimation { to: 0; duration: 1500; easing.type: Easing.InCubic }
                    }
                    SequentialAnimation on scale {
                        loops: Animation.Infinite
                        NumberAnimation { to: 1.5; duration: 3000; easing.type: Easing.OutCubic }
                        NumberAnimation { to: 1.0; duration: 0 }
                    }
                }

                // AI Core Center
                Rectangle {
                    id: aiCore
                    width: 90; height: 90; radius: 45; anchors.centerIn: parent
                    gradient: Gradient {
                        GradientStop { position: 0.0; color: "#60A5FA" }
                        GradientStop { position: 1.0; color: "#3B82F6" }
                    }
                    // Inner shadow effect simulated
                    Rectangle { anchors.fill: parent; radius: 45; border.color: "#BFDBFE"; border.width: 1; color: "transparent" }

                    SequentialAnimation on anchors.verticalCenterOffset {
                        loops: Animation.Infinite
                        NumberAnimation { to: -8; duration: 2500; easing.type: Easing.InOutQuad }
                        NumberAnimation { to: 0; duration: 2500; easing.type: Easing.InOutQuad }
                    }
                    Text { anchors.centerIn: parent; text: "🤖"; font.pixelSize: 45 }
                    
                    // Shiny dot
                    Rectangle { x: 18; y: 15; width: 15; height: 10; radius: 5; color: "white"; opacity: 0.4; rotation: -30 }
                }
            }

            // ── Title ─────────────────────────────────────────────────────
            Text {
                Layout.alignment: Qt.AlignHCenter
                text: "Kiro AI"
                font.pixelSize: 48; font.weight: Font.ExtraBold; font.family: "Segoe UI"
                color: "#1E293B" // Slate 800
                Layout.bottomMargin: 8
            }

            // ── Subtitle ──────────────────────────────────────────────────
            Text {
                Layout.alignment: Qt.AlignHCenter
                text: "الوكيل الذكي المحلي لتنظيم ملفاتك باحترافية وأمان"
                font.pixelSize: 18; font.family: "Segoe UI"; color: "#64748B"
                Layout.fillWidth: true; Layout.bottomMargin: 35
                horizontalAlignment: Text.AlignHCenter
            }

            // ── Feature chips ─────────────────────────────────────────────
            RowLayout {
                Layout.alignment: Qt.AlignHCenter; spacing: 14; Layout.bottomMargin: 40

                Repeater {
                    model: [
                        { icon: "🛡️", label: "أمان 100%", bg: "#F1F5F9", fg: "#334155" },
                        { icon: "⚡", label: "سرعة فائقة", bg: "#EFF6FF", fg: "#1D4ED8" },
                        { icon: "🧠", label: "يعمل بالذكاء", bg: "#FDF2F8", fg: "#BE185D" }
                    ]
                    delegate: Rectangle {
                        height: 42; width: chipRow.implicitWidth + 30; radius: 21
                        color: modelData.bg; border.color: "#E2E8F0"; border.width: 1
                        RowLayout {
                            id: chipRow; anchors.centerIn: parent; spacing: 8
                            Text { text: modelData.icon; font.pixelSize: 15 }
                            Text { text: modelData.label; font.pixelSize: 14; font.weight: Font.Bold; font.family: "Segoe UI"; color: modelData.fg }
                        }
                    }
                }
            }

            // ── CTA Button ────────────────────────────────────────────────
            Rectangle {
                id: ctaBtn
                Layout.alignment: Qt.AlignHCenter
                Layout.preferredWidth: 260; Layout.preferredHeight: 60; Layout.bottomMargin: 10
                radius: 30
                gradient: Gradient {
                    orientation: Gradient.Horizontal
                    GradientStop { position: 0.0; color: ctaMouse.containsMouse ? "#2563EB" : "#3B82F6" }
                    GradientStop { position: 1.0; color: ctaMouse.containsMouse ? "#4F46E5" : "#6366F1" }
                }
                
                scale: ctaMouse.pressed ? 0.94 : 1.0
                Behavior on scale { NumberAnimation { duration: 150; easing.type: Easing.OutBack } }

                // Glowing background drop shadow
                Rectangle {
                    anchors.centerIn: parent; width: parent.width; height: parent.height; anchors.verticalCenterOffset: 6
                    radius: 30; color: "#3B82F6"; opacity: ctaMouse.containsMouse ? 0.4 : 0.25; z: -1
                    Behavior on opacity { NumberAnimation { duration: 200 } }
                }

                RowLayout {
                    anchors.centerIn: parent; spacing: 12
                    Text { text: "البدء الآن"; font.pixelSize: 19; font.weight: Font.Bold; font.family: "Segoe UI"; color: "white" }
                    Text { text: "←"; font.pixelSize: 22; font.weight: Font.Bold; font.family: "Segoe UI"; color: "white" }
                }

                MouseArea {
                    id: ctaMouse; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                    onClicked: if (typeof kiroBackend !== "undefined") kiroBackend.getStarted()
                }
            }
        }
    }

    Component.onCompleted: {
        card.opacity = 0; card.scale = 0.92
        entAnim.start()
    }
    ParallelAnimation {
        id: entAnim
        NumberAnimation { target: card; property: "opacity"; from: 0; to: 1.0; duration: 700; easing.type: Easing.OutCubic }
        NumberAnimation { target: card; property: "scale"; from: 0.92; to: 1.0; duration: 700; easing.type: Easing.OutBack }
    }
}
