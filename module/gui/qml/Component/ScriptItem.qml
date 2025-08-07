import QtQuick
import FluentUI
import "../Global/"

FluPaneItem{
    title: qsTranslate("FluTreeView", "home")
    icon:FluentIcons.Play36
    
    // 添加自定义属性标识这是一个可删除的配置项
    property bool isConfigItem: true
    property string configName: "home"  // 保存原始的英文名称用于后端通信
    
    // 当设置configName时，更新显示的title
    onConfigNameChanged: {
        title = qsTranslate("FluTreeView", configName)
    }
    
    onTap:{
//        var component = Qt.createComponent("../../qml/Page/ScriptView.qml")
//        if (component.status === Component.Ready) {
//            var object = component.createObject(navigationView);

//            if (object !== null) {
//                object.configName = title
//                // 创建成功，可以进行操作
//                console.debug('创建成功')
//                navigationView.push(object)

//            }else{
//                // 创建失败
//            }
//        }else{
//            // 组件加载失败
//        }
    navigationView.pushScript(Qt.resolvedUrl("../../qml/Page/ScriptView.qml"), configName)
        MainEvent.scriptName = configName
    }
}
