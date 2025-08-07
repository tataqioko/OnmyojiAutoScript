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
            width: 250
            height: 50
            visible: true
            color: FluTheme.dark ? Window.active ?  Qt.rgba(38/255,44/255,54/255,1) : Qt.rgba(39/255,39/255,39/255,1) : Qt.rgba(251/255,251/255,253/255,1)

            property alias name: taskName.text
            property alias nextRun: taskTime.text
            property alias enable: taskEnable.selected


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
            FluText{
                id: taskTime
                anchors{
                    left: parent.left
                    leftMargin: 6
                    bottom: parent.bottom
                    bottomMargin: 6
                }
                text: model.next_run
                font: FluTextStyle.Caption
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
