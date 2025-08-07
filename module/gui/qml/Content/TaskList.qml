import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import FluentUI
import '../Global'


Item{
    id: taskList
    signal click(string title)
    onClick: {

    }

    FluScrollablePage{
        id: contentScrollable
        width: 800
        height: parent.height
        spacing: 12
        anchors.horizontalCenter: parent.horizontalCenter
    }

    // 任务组
    Component{
        id: group_item
        FluExpander{
            id: expander
            property string groupName: ""
            property string groupTitle: ""
            property var argumentValue: {""}
            property alias model: groupModel
            expand: true
            headerText: qsTranslate("FluTreeView", groupName)
            width: contentScrollable.width
            contentHeight: groupGridView.height + 20
            ListModel{
                id: groupModel
            }

            GridLayout{
                id: groupGridView
                clip: true
                columns: 3
                anchors{
                    top: parent.top
                    topMargin: 12
                    left: parent.left
                    leftMargin: 12
                    right: parent.right
                    rightMargin: 15
                    bottomMargin: 12
                }
                Repeater {
                    delegate: task_item
                    model: groupModel
                }
            }
        }
    }

    // 任务小项
    Component{
        id: task_item
        FluArea{
            id: task_root
            width: 280  // 增加宽度以容纳新按钮
            height: 50
            visible: true
            color: FluTheme.dark ? Window.active ?  Qt.rgba(38/255,44/255,54/255,1) : Qt.rgba(39/255,39/255,39/255,1) : Qt.rgba(251/255,251/255,253/255,1)

            property alias name: taskName.text
            property alias nextRun: taskTime.text
            property alias enable: taskEnable.selected
            
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
                    leftMargin: 6
                    top: parent.top
                    topMargin: 6
                }
                text: qsTranslate("FluTreeView", model.task)
                font: FluTextStyle.BodyStrong
            }
            
            // 时间显示和立即运行按钮的容器
            Row {
                id: timeContainer
                anchors{
                    left: parent.left
                    leftMargin: 6
                    bottom: parent.bottom
                    bottomMargin: 6
                }
                spacing: 8
                
                FluText{
                    id: taskTime
                    text: model.next_run
                    font: FluTextStyle.Caption
                    anchors.verticalCenter: parent.verticalCenter
                }
                
                // 立即运行按钮
                FluButton{
                    id: runNowButton
                    width: 60
                    height: 20
                    text: "立即运行"
                    font.pixelSize: 10
                    normalColor: FluTheme.dark ? Qt.rgba(80/255, 160/255, 240/255, 0.8) : Qt.rgba(70/255, 130/255, 180/255, 0.8)
                    hoverColor: FluTheme.dark ? Qt.rgba(90/255, 170/255, 250/255, 1) : Qt.rgba(80/255, 140/255, 190/255, 1)
                    onClicked: {
                        console.log("Run task immediately:", model.task)  // 使用英文避免控制台乱码
                        runNowButton.enabled = false  // 防止重复点击
                        
                        // 检查是否有正在运行的任务
                        var isRunning = process_manager.is_running(MainEvent.scriptName)
                        
                        if(isRunning) {
                            // 如果脚本正在运行，使用强制停止模式
                            var currentStatus = process_manager.get_current_task_status(MainEvent.scriptName)
                            try {
                                var status = JSON.parse(currentStatus)
                                if(status.running && status.running.name) {
                                    showInfo("检测到正在运行: " + status.running.name + 
                                           "\\n立即运行将会停止当前任务")
                                    
                                    // 使用强制停止选项
                                    if(process_manager.gui_run_task_immediately_with_options(MainEvent.scriptName, model.task, true)) {
                                        showSuccess("已停止当前任务，" + qsTranslate("FluTreeView", model.task) + " 将立即执行")
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
                        if(process_manager.gui_run_task_immediately(MainEvent.scriptName, model.task)) {
                            showSuccess("任务 " + qsTranslate("FluTreeView", model.task) + " 已设置为立即运行")
                            enableButtonTimer.start()
                        } else {
                            showError("立即运行设置失败")
                            runNowButton.enabled = true  // 失败时立即重新启用
                        }
                    }
                }
            }
            FluCheckBox{
                id: taskEnable
                anchors{
                    right: settingButton.left
                    rightMargin: 6
                    verticalCenter: parent.verticalCenter
                }
                selected: model.enable
//                onSelectedChanged: {
//                    if(process_manager.gui_set_task_bool(MainEvent.scriptName, task_root.name, 'scheduler', 'enable', selected)){
//                        showSuccess("Enable")
//                        return true
//                    }
//                    showSuccess('Disenable')
//                }
                clickFunc: function click_func(){
                    try {
                        selected = !selected
                        if(process_manager.gui_set_task_bool(MainEvent.scriptName, model.task, 'scheduler', 'enable', selected)){
                            showSuccess(selected ? "已启用" : "已禁用")
                            return true
                        }
                        showError("设置失败")
                        selected = !selected // 回滚状态
                        return false
                    } catch (error) {
                        console.error("Error toggling task enable:", error)
                        selected = !selected // 回滚状态
                        showError("操作失败: " + error)
                        return false
                    }
                }

                text: ''
            }

            FluButton{
                id: settingButton
                anchors{
                    right: parent.right
                    rightMargin: 10
                    verticalCenter: parent.verticalCenter
                }
                                 text:"设置"
                onClicked: {
                    try {
                        if(!model.task) {
                            console.error("Task name is empty")
                            showError("任务名称为空")
                            return
                        }
                        showSuccess("打开设置: " + model.task)
                        taskList.click(name)
                        if(taskList.parent && taskList.parent.parent) {
                            taskList.parent.parent.title = model.task
                        }
                    } catch (error) {
                        console.error("Error opening task settings:", error)
                        showError("打开设置失败: " + error)
                    }
                }
            }
        }
    }



    Component.onCompleted:{
        try {
            const taskListResult = process_manager.gui_task_list(MainEvent.scriptName)
            if(!taskListResult) {
                console.error("Failed to get task list: gui_task_list returned null")
                return
            }
            
            const menuResult = process_manager.gui_menu()
            if(!menuResult) {
                console.error("Failed to get menu: gui_menu returned null")
                return
            }
            
            const data = JSON.parse(taskListResult)
            const menu = JSON.parse(menuResult)
            
            for(const key in menu){
                if(key === "Overview" || key === 'TaskList' || key === 'Script' || key === 'Tools'){
                    continue
                }
                const groupData = classify(menu[key], data)
                create_group(key, groupData)
            }
        } catch (error) {
            console.error("Error initializing TaskList:", error)
        }
    }

    // 分类对每一个任务组，
    // 第一个参数是这个菜单组的所有， 如["Script", "Restart", "GlobalGame"]
    // 第二个参数是整个的数据
    // 会提取data的数据 返回一个dict
    function classify(group, data){
        const result = {}
        for(const item in data){
            if(group.includes(item)){
                result[item] = data[item]
            }
        }
        return result
    }
    // 创建一个的任务组
    function create_group(groupName, groupData){
        try {
            const object = group_item.createObject(contentScrollable)
            if(object === null){
                console.error('Create group item failed for group:', groupName)
                return
            }
            
            object.groupName = groupName
            object.groupTitle = qsTranslate("FluTreeView", groupName)
            object.argumentValue = groupData
            
            for(const key in groupData){
                if(!groupData[key] || typeof groupData[key] !== 'object') {
                    console.warn('Invalid task data for:', key)
                    continue
                }
                
                const item = {
                    "task": key,
                    "enable": groupData[key]["enable"] || false,
                    "next_run": groupData[key]["next_run"] || "未设置"
                }
                object.model.append(item)
            }

            contentScrollable.content.push(object)
        } catch (error) {
            console.error('Error creating group', groupName, ':', error)
        }
    }
}
