pragma Singleton

import QtQuick
import FluentUI

FluObject{
    id: itemsOriginal

    property var navigationView
    FluPaneItem{
        title: qsTr("home")
        icon:FluentIcons.Home
        onTap:{
//            navigationView.push(Qt.resolvedUrl("../../qml/Page/O_Home.qml"))
            navigationView.pushScript(Qt.resolvedUrl("../../qml/Page/O_Home.qml"), "home")
        }
    }
    function getRecentlyAddedData(){
        var arr = []
        for(var i=0;i<children.length;i++){
            var item = children[i]
            if(item instanceof FluPaneItem && item.recentlyAdded){
                arr.push(item)
            }
            if(item instanceof FluPaneItemExpander){
                for(var j=0;j<item.children.length;j++){
                    var itemChild = item.children[j]
                    if(itemChild instanceof FluPaneItem && itemChild.recentlyAdded){
                        arr.push(itemChild)
                    }
                }
            }
        }
        arr.sort(function(o1,o2){ return o2.order-o1.order })
        return arr
    }

    function getRecentlyUpdatedData(){
        var arr = []
        var items = navigationView.getItems();
        for(var i=0;i<items.length;i++){
            var item = items[i]
            if(item instanceof FluPaneItem && item.recentlyUpdated){
                arr.push(item)
            }
        }
        return arr
    }

    function getSearchData(){
        var arr = []
        var items = navigationView.getItems();
        for(var i=0;i<items.length;i++){
            var item = items[i]
            if(item instanceof FluPaneItem){
                arr.push({title:item.title,key:item.key})
            }
        }
        return arr
    }

    function startPageByItem(data){
        navigationView.startPageByItem(data)
    }
    //获取现在存在的所有的Item
    function allPaneItems(){
        var arr = []
        var items = navigationView.getItems();
        for(var i=0;i<items.length;i++){
            var item = items[i]
            if(item instanceof FluPaneItem && item.configName){
                arr.push(item.configName)
            }
        }
        return arr
    }

    //动态添加Paneitem
    function createPaneItem(configName){
        var component = Qt.createComponent("../../qml/Component/ScriptItem.qml")
        if (component.status === Component.Ready) {
            var object = component.createObject(itemsOriginal, {
                configName: configName
            });

            if (object !== null) {
                object.configName = configName  // 设置原始英文名称
                children.push(object)
            } else {
                console.error("Failed to create config item:", configName)
            }
        } else {
            console.error("Failed to load component for:", configName, "Error:", component.errorString())
        }
    }
    //给添加
    function addFluPaneItems(){
        try {
            // 检查add_config是否可用
            if (typeof add_config === 'undefined') {
                console.error("add_config object is not available")
                return
            }
            
            var configs = add_config.all_script_files()
            if (!configs || configs.length === 0) {
                console.warn("No config files found")
                return
            }
            
            var exists = allPaneItems()
            for(var i=0; i<configs.length; i++){
                if(!exists.includes(configs[i])){
                    createPaneItem(configs[i])
                }
            }
        } catch(e) {
            console.error("Error adding config items:", e.toString())
        }
    }
    
    // 刷新配置列表 - 删除不存在的配置项
    function refreshConfigList(){
        var configs = add_config.all_script_files()
        var items = navigationView.getItems()
        
        // 找到需要删除的项目
        var itemsToRemove = []
        for(var i = 0; i < items.length; i++){
            var item = items[i]
            if(item instanceof FluPaneItem && item.configName && item.configName !== "home"){
                // 如果配置文件不存在，标记为删除
                if(!configs.includes(item.configName)){
                    itemsToRemove.push(item)
                }
            }
        }
        
        // 删除标记的项目
        for(var j = 0; j < itemsToRemove.length; j++){
            var itemToRemove = itemsToRemove[j]
            // 从children中移除
            for(var k = 0; k < children.length; k++){
                if(children[k] === itemToRemove){
                    children.splice(k, 1)
                    break
                }
            }
            // 销毁对象
            itemToRemove.destroy()
        }
        
        // 添加新的配置项（如果有的话）
        addFluPaneItems()
    }

}
