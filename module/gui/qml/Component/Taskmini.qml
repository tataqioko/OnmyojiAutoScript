import QtQuick
import QtQuick.Layouts
import FluentUI
import "../Global"
// 这个组件是在总览那儿小小的显示
// 任务的名称 + 时间 以及一个设置的入口

Item {
    id: root
    width: 225
    height: 40
    visible: true

    property alias name: taskName.text
    property alias nextRun: taskTime.text
    property string taskKey: ""  // 保存原始任务名称，用于后端调用
    signal click(string title)
    
    // 防止重复点击的定时器
    Timer {
        id: enableButtonTimer
        interval: 2000  // 2秒后重新启用按钮
        repeat: false
        onTriggered: {
            runNowButton.enabled = true
        }
    }

    FluText{
        id: taskName
        anchors{
            left: parent.left
            leftMargin: 0
            top: parent.top
            topMargin: 0
        }
        text: qsTr("taskName")
        font: FluTextStyle.BodyStrong
    }
    // 时间显示和立即运行按钮的容器
    Row {
        id: timeContainer
        anchors{
            left: parent.left
            leftMargin: 0
            bottom: parent.bottom
            bottomMargin: 0
        }
        spacing: 6
        
        FluText{
            id: taskTime
            text: "2023-05-26 18:33:55"
            font: FluTextStyle.Caption
            anchors.verticalCenter: parent.verticalCenter
        }
        
        // 立即运行按钮
        FluButton{
            id: runNowButton
            width: 50
            height: 18
            text: "立即运行"
            font.pixelSize: 9
            normalColor: FluTheme.dark ? Qt.rgba(80/255, 160/255, 240/255, 0.8) : Qt.rgba(70/255, 130/255, 180/255, 0.8)
            hoverColor: FluTheme.dark ? Qt.rgba(90/255, 170/255, 250/255, 1) : Qt.rgba(80/255, 140/255, 190/255, 1)
            onClicked: {
                console.log("Run task immediately:", taskKey)  // 使用英文避免控制台乱码
                runNowButton.enabled = false  // 防止重复点击
                
                // 检查是否有正在运行的任务
                var isRunning = process_manager.is_running(MainEvent.scriptName)
                
                if(isRunning) {
                    // 如果脚本正在运行，检查是否有任务在执行
                    var currentStatus = process_manager.get_current_task_status(MainEvent.scriptName)
                    try {
                        var status = JSON.parse(currentStatus)
                        if(status.running && status.running.name) {
                            // 有任务正在运行，询问用户是否要强制停止
                            showInfo("检测到正在运行: " + status.running.name + 
                                   "\\n立即运行将会停止当前任务")
                            
                            // 直接使用强制停止选项
                            if(process_manager.gui_run_task_immediately_with_options(MainEvent.scriptName, taskKey, true)) {
                                showSuccess("已停止当前任务，" + name + " 将立即执行")
                                enableButtonTimer.start()
                            } else {
                                showError("强制运行失败")
                                runNowButton.enabled = true
                            }
                            return
                        }
                    } catch(e) {
                        console.warn("Failed to parse task status:", e)
                    }
                }
                
                // 正常立即运行
                if(process_manager.gui_run_task_immediately(MainEvent.scriptName, taskKey)) {
                    showSuccess("任务 " + name + " 已设置为立即运行")
                    enableButtonTimer.start()
                } else {
                    showError("立即运行设置失败")
                    runNowButton.enabled = true  // 失败时立即重新启用
                }
            }
        }
    }
    
    FluButton{
        id: settingButton
        anchors{
            right: parent.right
            rightMargin: 0
            verticalCenter: parent.verticalCenter
        }
        text:"设置"
        onClicked: {
            showSuccess(name)
            root.click(configName)
        }
    }
    // 使用这个的前提是 data 是字符串
    function  setData(data){
        if(data === "{}"){  // 这个表示没有数据，是空的
            root.visible = false
            return
        }
        root.visible = true
        const d = JSON.parse(data)
        root.taskKey = d["name"]  // 保存原始任务名称（大驼峰格式）
        root.name = qsTranslate("FluTreeView", d["name"])  // 使用正确的翻译上下文
        root.nextRun = d["next_run"]
    }
}
