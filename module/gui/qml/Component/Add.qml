import QtQuick
import QtQuick.Layouts
import QtQuick.Window
import QtQuick.Controls
import FluentUI
import "../Global"

FluContentDialog{
    id:dialog
    title: qsTranslate("Args", "Manage Configs")

    signal updateScriptItems

    contentItem: Rectangle {
        id:layout_content
        implicitWidth:minWidth
        implicitHeight: text_title.height + contextC.height + layout_actions.height
        color:FluTheme.dark ? Qt.rgba(45/255,45/255,45/255,1) : Qt.rgba(249/255,249/255,249/255,1)
        radius:5
        FluShadow{
            radius: 5
        }
        FluText{
            id:text_title
            font: FluTextStyle.Subtitle
            text:title
            topPadding: 20
            leftPadding: 20
            rightPadding: 20
            wrapMode: Text.WrapAnywhere
            horizontalAlignment: Text.AlignHCenter
            anchors{
                top:parent.top
                left: parent.left
                right: parent.right
            }
        }
        Column{
            id: contextC
            anchors{
                horizontalCenter: parent.horizontalCenter
                top: text_title.bottom
            }
            spacing: 10
            FluText{
                text: qsTranslate("Args", 'New name')
                leftPadding: 6
                font: FluTextStyle.Caption
            }
            FluTextBox{
                id: newNameBox
                placeholderText:"推荐:oas+number"
//                maxLength: 20
                validator: RegularExpressionValidator { regularExpression: /^[a-zA-Z0-9]*$/ }
            }
            FluText{
                text: qsTranslate("Args", 'Copy from existing config')
                leftPadding: 6
                font: FluTextStyle.Caption
            }
            FComboBox{
                id: copyConfig
                width: newNameBox.width
                model: ["Option 1", "Option 2", "Option 3"]
            }
            
            // 分隔线
            Rectangle {
                width: newNameBox.width
                height: 1
                color: FluTheme.dark ? Qt.rgba(1,1,1,0.1) : Qt.rgba(0,0,0,0.1)
                anchors.horizontalCenter: parent.horizontalCenter
            }
            
            FluText{
                text: qsTranslate("Args", 'Delete existing config')
                leftPadding: 6
                font: FluTextStyle.Caption
            }
            
            Row {
                spacing: 10
                FComboBox{
                    id: deleteConfig
                    width: newNameBox.width - 80
                    model: []
                }
                FluButton {
                    text: qsTranslate("Args", 'Delete')
                    width: 70
                    enabled: deleteConfig.currentIndex >= 0 && deleteConfig.model.length > 1
                    onClicked: {
                        if (deleteConfig.currentText) {
                            deleteConfirmDialog.configName = deleteConfig.currentText
                            deleteConfirmDialog.open()
                        }
                    }
                }
            }
        }
        Rectangle{
            id:layout_actions
            height: 68
            radius: 5
            color: FluTheme.dark ? Qt.rgba(32/255,32/255,32/255,1) : Qt.rgba(243/255,243/255,243/255,1)
            anchors{
                top:contextC.bottom
                topMargin: 12
                left: parent.left
                right: parent.right
            }
            RowLayout{
                anchors
                {
                    centerIn: parent
                    margins: spacing
                    fill: parent
                }
                spacing: 15
                FluButton{
                    id:neutral_btn
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    visible: dialog.buttonFlags&FluContentDialog.NeutralButton
                    text: neutralText
                    onClicked: {
                        dialog.close()
                        neutralClicked()
                    }
                }
                FluButton{
                    id:negative_btn
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    visible: dialog.buttonFlags&FluContentDialog.NegativeButton
                    text: negativeText
                    onClicked: {
                        dialog.close()
                        negativeClicked()
                    }
                }
                FluFilledButton{
                    id:positive_btn
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    visible: dialog.buttonFlags&FluContentDialog.PositiveButton
                    text: positiveText
                    onClicked: {
                        dialog.close()
                        positiveClicked()
                    }
                }
            }
        }
    }

    negativeText:"取消"
    buttonFlags: FluContentDialog.NegativeButton | FluContentDialog.PositiveButton
    onNegativeClicked:{
        showSuccess("取消创建")
    }
    positiveText:"确定"
    onPositiveClicked:{
        // 验证输入
        if (!newNameBox.text || newNameBox.text.trim() === "") {
                                    showError(qsTranslate("Args", "Please enter a valid config name"))
            return
        }
        
        if (!copyConfig.currentText) {
            showError(qsTranslate("Args", "Please select a template to copy from"))
            return
        }
        
        // 检查配置名是否已存在
        var existingConfigs = add_config.all_script_files()
        if (existingConfigs.includes(newNameBox.text.trim())) {
            showError(qsTranslate("Args", "Config '%1' already exists").arg(newNameBox.text.trim()))
            return
        }
        
        var success = add_config.copy(newNameBox.text.trim(), copyConfig.currentText)
        if (success) {
            showSuccess(qsTranslate("Args", "Config '%1' created successfully").arg(newNameBox.text.trim()))
            
            // 刷新配置列表
            refreshConfigLists()
            dialog.updateScriptItems()
            
            // 重置输入
            newNameBox.text = add_config.generate_script_name()
        } else {
            showError(qsTranslate("Args", "Failed to create config '%1'").arg(newNameBox.text.trim()))
        }
    }

    // 提取刷新配置列表的函数
    function refreshConfigLists() {
        var allConfigs = add_config.all_json_file()
        copyConfig.model = allConfigs
        
        // 为删除下拉框设置模型，排除template
        var deleteableConfigs = allConfigs.filter(function(config) {
            return config !== "template"
        })
        deleteConfig.model = deleteableConfigs
        
        // 如果只有一个可删除的配置，自动选择它
        if (deleteableConfigs.length === 1) {
            deleteConfig.currentIndex = 0
        }
    }
    
    onOpened: {
        newNameBox.text = add_config.generate_script_name()
        refreshConfigLists()
    }
    
    // 删除确认对话框
    FluContentDialog {
        id: deleteConfirmDialog
        property string configName: ""
        
        title: qsTranslate("Args", "Confirm Delete")
        message: qsTranslate("Args", "Are you sure you want to delete the config '%1'? This action cannot be undone.").arg(configName)
        buttonFlags: FluContentDialog.NegativeButton | FluContentDialog.PositiveButton
        negativeText: qsTranslate("Args", "Cancel")
        positiveText: qsTranslate("Args", "Delete")
        
        onPositiveClicked: {
            var success = add_config.delete_config(configName)
            if (success) {
                showSuccess(qsTranslate("Args", "Config '%1' deleted successfully").arg(configName))
                
                // 使用提取的函数刷新配置列表
                refreshConfigLists()
                
                // 刷新导航菜单
                dialog.updateScriptItems()
                
                // 自动关闭删除确认对话框
                deleteConfirmDialog.close()
            } else {
                showError(qsTranslate("Args", "Failed to delete config '%1'").arg(configName))
            }
        }
    }
}
