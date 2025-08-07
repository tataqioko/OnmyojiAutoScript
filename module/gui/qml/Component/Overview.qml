import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import FluentUI
import "../Global"

Item {
    id: root
    property string configName: ""
    property var splitPanel: null  // 传入一个主控制的引用

    Timer{
        id: startInit
        interval: 2500 // 定时器间隔为一秒
        repeat: false // 设置为一次性定时器
        onTriggered: {
            // 停止定时器
            setStatus(MainEvent.RunStatus.Free)
        }
    }
    
    // 定期刷新调度器数据
    Timer{
        id: refreshTimer
        interval: 5000  // 每5秒刷新一次
        repeat: true
        running: true
        onTriggered: {
            // 如果脚本没有运行，定期刷新静态数据
            if(!process_manager.is_running(configName)) {
                loadInitialSchedulerData()
            }
        }
    }


    Item{
        id: leftScheduler
        width: 260
        anchors{
            left: parent.left
            top: parent.top
            bottom: parent.bottom
        }
        FluArea{
            id: schedulerOpen
            anchors.top: parent.top
            width: parent.width
            height: 50
            RowLayout{
                anchors.fill: parent
                property int scriptState: 0  // 0是
                FluText{
                    text: "调度器"
                    Layout.leftMargin: 16
                    font: FluTextStyle.Subtitle
                    Layout.alignment: Qt.AlignVCenter | Qt.AlignLeft
                }
                FluIconButton{
                     Layout.alignment: Qt.AlignVCenter | Qt.AlignRight
                    text: "Restart"
                    iconSource: FluentIcons.RepeatAll
                    onClicked: {
                        showSuccess("Restart"+" "+configName)
                        process_manager.restart(configName)
                        setStatus(MainEvent.RunStatus.Free)
                        textLog.text = ''
                        textLog.currentLine = 0
                    }
                }

            }
        }
        FluArea{
            id: schedulerRunning
            anchors.top: schedulerOpen.bottom
            anchors.topMargin: 10
            width: parent.width
            height: 100
            ColumnLayout{
                width: parent.width
                spacing: 8
                FluText{
                    text: "运行中"
                    Layout.leftMargin: 16
                    Layout.topMargin: 6
                    font: FluTextStyle.Subtitle
                }
                Rectangle{
                    width: schedulerRunning.width - 20
                    height: 2
                    Layout.alignment: Qt.AlignHCenter
                    color: FluTheme.dark ? Qt.rgba(64/255, 68/255, 75/255, 1) : Qt.rgba(234/255, 236/255, 239/255, 1)
                    radius: 2
                }
                Taskmini{
                    id: task_running
                    visible: false
                    Layout.leftMargin: 16
                    onClick: {
                        root.splitPanel.title = task_running.name
                    }
                }
            }
        }
        FluArea{
            id: schedulerPending
            anchors.top: schedulerRunning.bottom
            anchors.topMargin: 10
            width: parent.width
            height: 240
            FluText{
                id: pendingText
                anchors{
                    top: parent.top
                    topMargin: 6

                }
                width: parent.width
                text: "等待执行"
                leftPadding: 16
                font: FluTextStyle.Subtitle
            }
            Rectangle{
                // 这个是一条横线
                id: linePending
                anchors{
                    top: pendingText.bottom
                    topMargin: 8
                    horizontalCenter: parent.horizontalCenter
                }
                width: schedulerRunning.width - 20
                height: 2
                color: FluTheme.dark ? Qt.rgba(64/255, 68/255, 75/255, 1) : Qt.rgba(234/255, 236/255, 239/255, 1)
                radius: 2
            }
            ListView{
                id: pendingListView
                anchors{
                    top: linePending.bottom
                    topMargin: 8
                    bottom: parent.bottom
                    bottomMargin: 8
                    horizontalCenter: parent.horizontalCenter
                }

                width: 225
                height: 200
                clip: true
                spacing: 8
                model: ListModel{
                    id: pendingListModel
                }
                                    delegate: Component{
                        Taskmini{
                            name: model.name
                            nextRun: model.next_run
                            taskKey: model.originalName || model.name  // 使用原始任务名称
                            onClick: {
                                root.splitPanel.title = model.name
                            }
                        }
                    }
            }
        }
        FluArea{
            id: schedulerWaiting
            anchors.top: schedulerPending.bottom
            anchors.topMargin: 10
            anchors.bottom: parent.bottom
            anchors.bottomMargin: 0
            width: parent.width                  

//            ColumnLayout{
//                width: parent.width
//                spacing: 8
            FluText{
                id: waitingText
                anchors{
                    top: parent.top
                    topMargin: 6

                }
                width: parent.width
                text: "等待中"
                leftPadding: 16
                font: FluTextStyle.Subtitle
            }
                Rectangle{
                    id: lineWaiting
                    anchors{
                        top: waitingText.bottom
                        topMargin: 8
                        horizontalCenter: parent.horizontalCenter
                    }
                    width: schedulerPending.width - 20
                    height: 2
                    color: FluTheme.dark ? Qt.rgba(64/255, 68/255, 75/255, 1) : Qt.rgba(234/255, 236/255, 239/255, 1)
                    radius: 2
                }
                ListView{
                    id: waitingListView
                    anchors{
                        top: lineWaiting.bottom
                        topMargin: 8
                        bottom: parent.bottom
                        bottomMargin: 8
                        horizontalCenter: parent.horizontalCenter
                    }
                    width: 225
                    clip: true
                    spacing: 8
                    model: ListModel{
                        id: waitingListModel
                    }
                    delegate: Component{
                        Taskmini{
                            name: model.name
                            nextRun: model.next_run
                            taskKey: model.originalName || model.name  // 使用原始任务名称
                            onClick: {
                                root.splitPanel.title = model.name
                            }
                        }
                    }
                }
//            }
        }
    }

    FluArea{
        id: logHeader
        anchors.top: parent.top
        anchors.left: leftScheduler.right
        anchors.leftMargin: 10
        anchors.right: parent.right
        height: 50
        RowLayout{
            anchors.fill: parent
            RowLayout.alignment: Qt.AlignRight | Qt.AlignVCenter
            FluText{
                text: "日志"
                Layout.leftMargin: 16
                font: FluTextStyle.Subtitle
                Layout.alignment: Qt.AlignVCenter | Qt.AlignLeft
            }
            OverStatus{
                id: overStatus
                Layout.alignment: Qt.AlignVCenter | Qt.AlignRight
            }
            FluToggleButton{
                id: startButton
                Layout.alignment: Qt.AlignVCenter | Qt.AlignRight
                Layout.rightMargin: 16
                text: {if(overStatus.runStatus === MainEvent.RunStatus.Run){return "Stop"}
                       else{return "Start"}}
                selected: {if(overStatus.runStatus === MainEvent.RunStatus.Free){return true}
                            else{return false}}
                disabled: {if(overStatus.runStatus === MainEvent.RunStatus.Error ||
                              overStatus.runStatus === MainEvent.RunStatus.Empty){return true}
                           else{return false}
                }
                onClicked: {
                    console.debug(overStatus.runStatus)
                    if(overStatus.runStatus === MainEvent.RunStatus.Free){
                        //如果这个时候初始化好了但是还没有运行脚本
                        setStatus(MainEvent.RunStatus.Run)
                        process_manager.start_script(root.configName)
                        return
                    }
                    if(overStatus.runStatus === MainEvent.RunStatus.Run){
                        // 如果这个时候运行中
                        setStatus(MainEvent.RunStatus.Empty)
                        process_manager.stop_script(root.configName)
                        return
                    }
                }
            }
        }
    }

    FluArea{
        anchors.top: logHeader.bottom
        anchors.topMargin: 10
        anchors.bottom: parent.bottom
        anchors.left: leftScheduler.right
        anchors.leftMargin: 10
        anchors.right: parent.right
        FluScrollablePage{
            id: logScrollPage
            anchors.fill: parent
        FluText{
            id: textLog
            width: parent.width-10
            padding: 10
            clip: true
            wrapMode: Text.WordWrap // 设置自动换行模式
            maximumLineCount: 100
            property int currentLine: 0
            textFormat: Text.RichText
            text: ''

            function add_log(config, log){
                if(config !== root.configName){
                    return
                }
                if(log.includes('ERROR') || log.includes('CRITICAL')){
                    setStatus(MainEvent.RunStatus.Error)
                }


                if (currentLine > maximumLineCount) {
                    var index = textLog.text.indexOf("<br>"); //找到第一个<br>的位置
                    if (index !== -1) {
                        textLog.text = textLog.text.substring(index + 4); //从<br>之后开始截取字符串
                        currentLine -= 1
                    }
                }
                currentLine += 1
                textLog.text += log

                // 自动滚动到底部（始终启用）
                Qt.callLater(function() {
                    var flickable = logScrollPage.children[1] // 获取FluScrollablePage内部的Flickable
                    if(flickable && flickable.contentHeight > flickable.height) {
                        flickable.contentY = flickable.contentHeight - flickable.height
                    }
                })
            }

            Component.onCompleted:{
                process_manager.log_signal.connect(textLog.add_log)
            }


        }}
    }

    Component.onCompleted:{
        process_manager.sig_update_task.connect(update_task)
        process_manager.sig_update_pending.connect(update_pending)
        process_manager.sig_update_waiting.connect(update_waiting)
        
        // 立即尝试加载初始数据，即使脚本未运行
        loadInitialSchedulerData()
        
        startInit.start()
    }
    
    function loadInitialSchedulerData() {
        try {
            // 获取静态任务列表
            const taskListResult = process_manager.gui_task_list(configName)
            if(taskListResult) {
                const data = JSON.parse(taskListResult)
                const waitingTasks = []
                
                // 将所有任务作为等待任务显示
                for(const taskName in data) {
                    const taskInfo = data[taskName]
                    if(taskInfo.enable) {  // 只显示启用的任务
                        waitingTasks.push({
                            name: taskName,
                            originalName: taskName,
                            next_run: taskInfo.next_run
                        })
                    }
                }
                
                // 更新等待列表
                update_waiting(configName, JSON.stringify(waitingTasks))
                
                console.log("Loaded initial scheduler data:", waitingTasks.length, "tasks")
            }
        } catch (error) {
            console.warn("Failed to load initial scheduler data:", error)
        }
    }
    function update_task(config, data){
        if(typeof data !== "string"){
            console.error("Pass an incorrect type")
            return
        }

        if(config !== configName){
            return
        }
        task_running.setData(data)
    }
    function update_pending(config, data){
        if(typeof data !== "string"){
            console.error("Pass an incorrect type")
            return
        }
        if(config !== configName){
            return
        }
        if(data === "[]"){
            pendingListModel.clear()
            return
        }
        pendingListModel.clear()
        const d = JSON.parse(data)
        for(var item of d){
            // 保存原始任务名用于后端调用
            item.originalName = item.name
            // 翻译任务名用于显示
            item.name = qsTranslate("FluTreeView", item.name)
            pendingListModel.append(item)
        }
    }
    function update_waiting(config, data){
        if(typeof data !== "string"){
            console.error("Pass an incorrect type")
            return
        }
        if(config !== configName){
            return
        }
        if(data === "[]"){
            waitingListModel.clear()
            return
        }
        waitingListModel.clear()
        const d = JSON.parse(data)
        for(var item of d){
            // 保存原始任务名用于后端调用
            item.originalName = item.name
            // 翻译任务名用于显示
            item.name = qsTranslate("FluTreeView", item.name)
            waitingListModel.append(item)
        }
    }
    function setStatus(s){
        overStatus.runStatus = s
    }
}
