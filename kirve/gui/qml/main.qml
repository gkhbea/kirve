import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Window {
    id: root
    visible: true
    width: 1160
    height: 760
    minimumWidth: 980
    minimumHeight: 680
    title: "KİRVE AI OS // Masaüstü HUD & Sesli Kokpit"
    color: "#0A1433"

    property real wavePhase: 0.0

    // Sound wave animation timer
    Timer {
        interval: 33 // ~30 FPS
        running: true
        repeat: true
        onTriggered: {
            root.wavePhase += (bridge.isListening ? 0.15 : 0.05);
            waveCanvas.requestPaint();
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 28
        spacing: 20

        // 1. TOP HEADER (HUD Header)
        RowLayout {
            Layout.fillWidth: true
            spacing: 16

            ColumnLayout {
                spacing: 2
                Text {
                    text: "KİRVE"
                    font.family: "Rajdhani"
                    font.pixelSize: 34
                    font.bold: true
                    font.letterSpacing: 8
                    color: "#FFC93C"
                }
                Text {
                    text: "SESİNİ DİNLER · HER ZAMAN YANINDA"
                    font.family: "DM Sans"
                    font.pixelSize: 12
                    font.letterSpacing: 2.5
                    color: "#93A1CC"
                }
            }

            Item { Layout.fillWidth: true }

            // Live Network Badge (psutil)
            Rectangle {
                width: 210
                height: 42
                radius: 21
                color: "#111F4D"
                border.color: "#2A3F7E"
                border.width: 1

                RowLayout {
                    anchors.centerIn: parent
                    spacing: 12
                    Text {
                        text: "▼ " + bridge.netDown
                        font.family: "JetBrains Mono"
                        font.pixelSize: 11
                        font.bold: true
                        color: "#10B981"
                    }
                    Text {
                        text: "▲ " + bridge.netUp
                        font.family: "JetBrains Mono"
                        font.pixelSize: 11
                        font.bold: true
                        color: "#FFC93C"
                    }
                }
            }

            // Silent Mode / DND Badge
            Rectangle {
                width: 120
                height: 42
                radius: 21
                color: bridge.silentMode ? "#2E1A1A" : "#111F4D"
                border.color: bridge.silentMode ? "#EF4444" : "#2A3F7E"
                border.width: 1

                Text {
                    anchors.centerIn: parent
                    text: bridge.silentMode ? "DND: AKTİF" : "DND: NORMAL"
                    font.family: "Rajdhani"
                    font.pixelSize: 12
                    font.bold: true
                    font.letterSpacing: 1
                    color: bridge.silentMode ? "#EF4444" : "#93A1CC"
                }
            }
        }

        // 2. MAIN CENTER HUD
        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 24

            // LEFT PANEL: Gerçek psutil Donanım Telemetrisi
            Rectangle {
                Layout.preferredWidth: 260
                Layout.fillHeight: true
                radius: 16
                color: "#111F4D"
                border.color: "#2A3F7E"
                border.width: 1

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 18
                    spacing: 14

                    Text {
                        text: "DONANIM TELEMETRİSİ"
                        font.family: "Rajdhani"
                        font.pixelSize: 15
                        font.bold: true
                        font.letterSpacing: 3
                        color: "#FFC93C"
                    }

                    // CPU Usage (Real psutil)
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 4
                        RowLayout {
                            Layout.fillWidth: true
                            Text { text: "İŞLEMCİ (CPU)"; font.family: "DM Sans"; font.pixelSize: 12; color: "#93A1CC" }
                            Item { Layout.fillWidth: true }
                            Text {
                                text: bridge.cpuPercent.toFixed(1) + " %"
                                font.family: "JetBrains Mono"
                                font.pixelSize: 13
                                font.bold: true
                                color: bridge.cpuPercent > 80 ? "#EF4444" : "#F6F1DC"
                            }
                        }
                        // Custom Gauge Bar
                        Rectangle {
                            Layout.fillWidth: true
                            height: 8
                            radius: 4
                            color: "#0A1433"
                            Rectangle {
                                width: parent.width * Math.min(bridge.cpuPercent / 100.0, 1.0)
                                height: parent.height
                                radius: 4
                                color: "#FFC93C"
                            }
                        }
                    }

                    // RAM Usage (Real psutil)
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 4
                        RowLayout {
                            Layout.fillWidth: true
                            Text { text: "BELLEK (RAM)"; font.family: "DM Sans"; font.pixelSize: 12; color: "#93A1CC" }
                            Item { Layout.fillWidth: true }
                            Text {
                                text: bridge.ramPercent.toFixed(1) + " %"
                                font.family: "JetBrains Mono"
                                font.pixelSize: 13
                                font.bold: true
                                color: "#F6F1DC"
                            }
                        }
                        Rectangle {
                            Layout.fillWidth: true
                            height: 8
                            radius: 4
                            color: "#0A1433"
                            Rectangle {
                                width: parent.width * Math.min(bridge.ramPercent / 100.0, 1.0)
                                height: parent.height
                                radius: 4
                                color: "#10B981"
                            }
                        }
                        Text {
                            text: bridge.ramUsed.toFixed(1) + " GB / " + bridge.ramTotal.toFixed(1) + " GB"
                            font.family: "JetBrains Mono"
                            font.pixelSize: 11
                            color: "#93A1CC"
                        }
                    }

                    Rectangle { Layout.fillWidth: true; height: 1; color: "#1B2C66" }

                    // Togg T10X Mini Widget
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 6
                        Text {
                            text: "TOGG T10X"
                            font.family: "Rajdhani"
                            font.pixelSize: 14
                            font.bold: true
                            font.letterSpacing: 2
                            color: "#FFC93C"
                        }
                        Text {
                            text: "Batarya: %" + bridge.toggSoc + " · Menzil: " + bridge.toggRange + " km"
                            font.family: "DM Sans"
                            font.pixelSize: 12
                            color: "#F6F1DC"
                        }
                        Button {
                            Layout.fillWidth: true
                            text: "⚡ Şarjı Değiştir"
                            onClicked: bridge.toggleToggCharging()
                        }
                    }

                    Item { Layout.fillHeight: true }
                }
            }

            // CENTER HERO: Fütüristik Ses Dalgası & KİRVE Amblemi
            Rectangle {
                Layout.fillWidth: true
                Layout.fillHeight: true
                radius: 16
                color: "#080F28"
                border.color: "#1B2C66"
                border.width: 1

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 20
                    spacing: 12

                    // Central Equalizer Canvas
                    Canvas {
                        id: waveCanvas
                        Layout.fillWidth: true
                        Layout.fillHeight: true

                        onPaint: {
                            var ctx = getContext("2d");
                            ctx.clearRect(0, 0, width, height);

                            var cx = width / 2;
                            var cy = height / 2;
                            var maxR = Math.min(cx, cy) - 20;

                            // 1. Outer Orbit Rings
                            ctx.strokeStyle = "#1B2C66";
                            ctx.lineWidth = 2;
                            ctx.beginPath();
                            ctx.arc(cx, cy, maxR * 0.9, 0, Math.PI * 2);
                            ctx.stroke();

                            // 2. Golden Dashed Ring (Rotating)
                            ctx.save();
                            ctx.translate(cx, cy);
                            ctx.rotate(root.wavePhase * 0.3);
                            ctx.strokeStyle = "#FFC93C";
                            ctx.lineWidth = 3;
                            ctx.setLineDash([12, 18]);
                            ctx.beginPath();
                            ctx.arc(0, 0, maxR * 0.75, 0, Math.PI * 2);
                            ctx.stroke();
                            ctx.restore();

                            // 3. Central Dynamic Waveform Lines (Equalizer)
                            var barCount = 19;
                            var barSpacing = 14;
                            var startX = cx - (barCount * barSpacing) / 2;

                            ctx.lineWidth = 6;
                            ctx.lineCap = "round";

                            for (var i = 0; i < barCount; i++) {
                                var distFromCenter = Math.abs(i - barCount / 2);
                                var baseH = 20 + (10 - distFromCenter) * 8;
                                var dynamicFactor = Math.sin(root.wavePhase * 3 + i * 0.45) * (bridge.isListening ? 45 : 15);
                                var h = Math.max(16, baseH + dynamicFactor);

                                ctx.strokeStyle = (i === Math.floor(barCount / 2)) ? "#F6F1DC" : "#FFC93C";
                                ctx.beginPath();
                                ctx.moveTo(startX + i * barSpacing, cy - h / 2);
                                ctx.lineTo(startX + i * barSpacing, cy + h / 2);
                                ctx.stroke();
                            }
                        }
                    }

                    // Sleek Minimalist JARVIS Status Badge (No intrusive subtitles)
                    Rectangle {
                        Layout.fillWidth: true
                        height: 44
                        radius: 22
                        color: "#08102A"
                        border.color: bridge.isListening ? "#10B981" : "#1B2C66"
                        border.width: 1

                        RowLayout {
                            anchors.centerIn: parent
                            spacing: 10

                            Rectangle {
                                width: 8
                                height: 8
                                radius: 4
                                color: bridge.isListening ? "#10B981" : (bridge.statusIndicator.indexOf("AÇILIYOR") !== -1 ? "#FFC93C" : "#3B82F6")
                            }

                            Text {
                                text: bridge.isListening ? "SESİNİ DİNLİYORUM..." : bridge.statusIndicator
                                font.family: "Rajdhani"
                                font.pixelSize: 13
                                font.bold: true
                                font.letterSpacing: 2.5
                                color: bridge.isListening ? "#10B981" : (bridge.statusIndicator.indexOf("AÇILIYOR") !== -1 ? "#FFC93C" : "#93A1CC")
                            }
                        }
                    }
                }
            }

            // RIGHT PANEL: Roborock & Hızlı Akıllı Ev
            Rectangle {
                Layout.preferredWidth: 260
                Layout.fillHeight: true
                radius: 16
                color: "#111F4D"
                border.color: "#2A3F7E"
                border.width: 1

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 18
                    spacing: 14

                    Text {
                        text: "AKILLI EV & ROBOT"
                        font.family: "Rajdhani"
                        font.pixelSize: 15
                        font.bold: true
                        font.letterSpacing: 3
                        color: "#FFC93C"
                    }

                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 6
                        Text { text: "ROBOROCK Q8"; font.family: "Rajdhani"; font.pixelSize: 14; font.bold: true; color: "#FFC93C" }
                        Text { text: "LiDAR Sensörü: " + bridge.roborockLidar; font.family: "DM Sans"; font.pixelSize: 12; color: "#F6F1DC" }
                        Button {
                            Layout.fillWidth: true
                            text: "🧹 Salon Temizliğini Başlat"
                            onClicked: bridge.startRoborockZone("Salon")
                        }
                    }

                    Rectangle { Layout.fillWidth: true; height: 1; color: "#1B2C66" }

                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 8
                        Text { text: "GÜVENLİK PROTOKOLÜ"; font.family: "Rajdhani"; font.pixelSize: 14; font.bold: true; color: "#FFC93C" }
                        Text {
                            text: "Kritik işlemlerde [E/H] onayı zorunludur."
                            font.family: "DM Sans"
                            font.pixelSize: 11
                            color: "#93A1CC"
                        }
                        Button {
                            Layout.fillWidth: true
                            text: "💳 Ödeme Testi (/ode)"
                            onClicked: bridge.sendCommand("/ode")
                        }
                    }

                    Item { Layout.fillHeight: true }
                }
            }
        }

        // 3. BOTTOM COMMAND BAR ("Emret, patron…")
        Rectangle {
            Layout.fillWidth: true
            height: 64
            radius: 32
            color: "#111F4D"
            border.color: "#FFC93C"
            border.width: 1

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 24
                anchors.rightMargin: 6
                spacing: 14

                TextInput {
                    id: cmdInput
                    Layout.fillWidth: true
                    font.family: "DM Sans"
                    font.pixelSize: 16
                    color: "#F6F1DC"
                    clip: true
                    Text {
                        text: "Seni dinliyorum... (örneğin: '1 kg luk nutella en ucuz nerede araştır', '/togg', '/roborock')"
                        font.family: "DM Sans"
                        font.pixelSize: 15
                        color: "#93A1CC"
                        visible: !cmdInput.text && !cmdInput.activeFocus
                    }
                    onAccepted: {
                        if (text.trim().length > 0) {
                            bridge.sendCommand(text.trim());
                            text = "";
                        }
                    }
                }

                // Voice Listening Trigger Button
                Rectangle {
                    width: 52
                    height: 52
                    radius: 26
                    color: bridge.isListening ? "#10B981" : "#FFC93C"

                    Text {
                        anchors.centerIn: parent
                        text: bridge.isListening ? "●" : "🎤"
                        font.pixelSize: 18
                        color: "#0A1433"
                    }

                    MouseArea {
                        anchors.fill: parent
                        cursorShape: Qt.PointingHandCursor
                        onClicked: bridge.triggerVoiceInput()
                    }
                }
            }
        }
    }
}
