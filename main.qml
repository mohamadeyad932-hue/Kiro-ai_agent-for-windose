import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Window 2.15

ApplicationWindow {
    id: window
    width: 1280
    height: 820
    minimumWidth: 900
    minimumHeight: 640
    visible: true
    title: qsTr("Kiro AI — Intelligent File Organizer")
    color: "#FAFBFF"

    // Background image for the entire application
    Image {
        id: bgImage
        anchors.fill: parent
        source: "background.jpg"
        fillMode: Image.PreserveAspectCrop
        z: -10
    }

    // Light frosted overlay for readability
    Rectangle {
        anchors.fill: parent
        color: "#FFFFFF"
        opacity: 0.15
        z: -9
    }

    StackView {
        id: screenStack
        anchors.fill: parent

        pushEnter: Transition {
            NumberAnimation { property: "opacity"; from: 0; to: 1; duration: 450; easing.type: Easing.OutQuart }
            NumberAnimation { property: "scale"; from: 0.96; to: 1.0; duration: 450; easing.type: Easing.OutBack }
        }
        pushExit: Transition {
            NumberAnimation { property: "opacity"; from: 1; to: 0; duration: 350; easing.type: Easing.InQuart }
            NumberAnimation { property: "scale"; from: 1.0; to: 1.04; duration: 350; easing.type: Easing.InQuart }
        }
        popEnter: Transition {
            NumberAnimation { property: "opacity"; from: 0; to: 1; duration: 450; easing.type: Easing.OutQuart }
            NumberAnimation { property: "scale"; from: 1.04; to: 1.0; duration: 450; easing.type: Easing.OutBack }
        }
        popExit: Transition {
            NumberAnimation { property: "opacity"; from: 1; to: 0; duration: 350; easing.type: Easing.InQuart }
            NumberAnimation { property: "scale"; from: 1.0; to: 0.96; duration: 350; easing.type: Easing.InQuart }
        }

        initialItem: "WelcomeScreen.qml"

        Connections {
            target: typeof kiroBackend !== "undefined" ? kiroBackend : null
            function onCurrentScreenChanged(screenName) {
                if (screenName === "WelcomeScreen.qml") {
                    while (screenStack.depth > 1) {
                        screenStack.pop(StackView.Immediate)
                    }
                } else {
                    screenStack.push(screenName)
                }
            }
        }
    }
}
