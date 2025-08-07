import QtQuick
import QtQuick.Controls
import FluentUI
import QtQuick.Layouts
import "./ModelParse.js" as MP

Item {
    property string argsData: ""
    property string valueData: ""
    // 存入 配置名和 任务名两个 上下文
    property string configName: ""
    property string taskName: ""
    signal updataData
    FluScrollablePage{
        id: contentScrollable
        width: 700
        height: parent.height
        spacing: 12
        anchors.horizontalCenter: parent.horizontalCenter
    }

    Component{
        id: group_item
        FluExpander{
            id: expander
            property string groupName: ""
            property string groupTitle: ""
            property var argumentValue: {""}
            expand: true
            headerText: qsTranslate("Args", groupTitle) +" "+ qsTranslate("Args", "Setting")
            width: contentScrollable.width
            contentHeight: group_column.height + 20
            Column{
                id: group_column
                spacing: 4
                clip: true
                anchors{
                    top: parent.top
                    topMargin: 12
                    left: parent.left
                    leftMargin: 15
                    right: parent.right
                    rightMargin: 15
                    bottomMargin: 12
                }
            }
            onArgumentValueChanged: {
                for(let index in argumentValue){
                    const arg = argumentValue[index]
                    createItem(arg)
//                    expander.contentHeight = group_column.height
                }
            }
            /**
             * 创建某个具体的字段
             * @param {Object} arg 打包的变量大概长这样的：
                {
                    "name": "handle_error",
                    "title": "Handle Error",
                    "description": "none",
                    "default": false,
                    "type": "boolean",
                    "value": false
                }
             * @returns {Object}
             */
            function createItem(arg){
                if(arg === null){
                    console.error("it is emtry when create arg")
                    return
                }

                var object = null
                if(arg.type === "string"){
                    object = string_item.createObject(group_column)
                    if(object === null){
                        console.error("can not create component string_item", arg.title)
                        return
                    }
                }
                else if(arg.type === "integer"){
                    object = int_item.createObject(group_column)
                    if(object === null){
                        console.error("can not create component integer_item", arg.title)
                        return
                    }
                }
                else if(arg.type === "number"){
                    object = float_item.createObject(group_column)
                    if(object === null){
                        console.error("can not create component float_item", arg.title)
                        return
                    }
                }
                else if(arg.type === "boolean"){
                    object = bool_item.createObject(group_column)
                    if(object === null){
                        console.error("can not create component boolean_item", arg.title)
                        return
                    }
                }
                else if(arg.type === "enum"){
                    object = enum_item.createObject(group_column)
                    if(object === null){
                        console.error("can not create component enum_item", arg.title)
                        return
                    }
                }
                else if(arg.type === "multi_line"){
                    object = multi_line_item.createObject(group_column)
                    if(object === null){
                        console.error("can not create component multi_line_item", arg.title)
                        return
                    }
                }


                if(object === null){
                    console.error("can not create component ", arg.title)
                    return
                }
                object.modelData = arg
                group_column.data.push(object)
            }
        }

    }

    Component{
        id: string_item
        Item{
            id: stringItem
            property var modelData: null
            property bool isDateTime: false
            width: parent.width
            implicitHeight: string_title.implicitHeight + string_description.implicitHeight
            Layout.fillHeight: true
            FluTextBox{
                id: string_text
                anchors{
                    top: parent.top
                    topMargin: 2
                    right: parent.right
                }
                placeholderText: ""
                onEditingFinished: {
                    if(stringItem.isDateTime){
                        if(string_text.text === ""){
                            string_text.text = utils.current_datetime()
                        }
                    }

                    if(set_task(stringItem.parent.parent.parent.groupName, modelData.name, text)){
                        showSuccess( qsTr("Successful setting"))
                    }
                }
            }

            FluText{
                id: string_title
                anchors{
                    top: parent.top
                    left: parent.left
                    right: string_text.left
                }
                text: ""
                font: FluTextStyle.BodyStrong
                wrapMode: Text.WrapAnywhere
                topPadding: 6
            }
            FluText{
                id: string_description
                anchors{
                    top: string_title.bottom
                    left: parent.left
                }
                width: string_title.width
                text: ""
                font: FluTextStyle.Caption
                wrapMode: Text.WordWrap
//                textFormat: Text.PlainText
                topPadding: 6
                rightPadding: 6
            }
            onModelDataChanged: {
                if(modelData === null){
                    console.error("string model is null")
                    return
                }
                string_text.text = modelData.value
                string_text.placeholderText = modelData["default"]
                if(string_text.placeholderText.startsWith("2023-01-01")){
                    //判断是不是时间类型的变量2023-01-01
                    stringItem.isDateTime = true
                }
                string_title.text = qsTranslate("Args", modelData.title)
                if( typeof modelData.description === 'undefined'){
                    return
                }
                string_description.text = qsTranslate("Args", modelData.description.replace("\\n","\n"))
            }
        }
    }
    Component{
        id: int_item
        Item{
            id: itemArg
            property var modelData: null
            width: parent.width
            implicitHeight: itemArg_title.implicitHeight + itemArg_description.implicitHeight
            Layout.fillHeight: true
            FluTextBox{
                id: itemArg_text
                anchors{
                    top: parent.top
                    topMargin: 2
                    right: parent.right
                }
                validator: IntValidator {}
                placeholderText: ""
                onEditingFinished: {
                    if(set_task(itemArg.parent.parent.parent.groupName, modelData.name, parseInt(text))){
                        showSuccess( qsTr("Successful setting"))
                    }
                }
            }

            FluText{
                id: itemArg_title
                anchors{
                    top: parent.top
                    left: parent.left
                    right: itemArg_text.left
                }
                text: ""
                font: FluTextStyle.BodyStrong
                wrapMode: Text.WrapAnywhere
                topPadding: 6
            }
            FluText{
                id: itemArg_description
                anchors{
                    top: itemArg_title.bottom
                    left: parent.left
                }
                width: itemArg_title.width
                text: ""
                font: FluTextStyle.Caption
                wrapMode: Text.WrapAnywhere
//                textFormat: Text.PlainText
                topPadding: 6
                rightPadding: 6
            }
            onModelDataChanged: {
                if(modelData === null){
                    console.error("int model is null")
                    return
                }
                itemArg_text.text = modelData.value
                itemArg_text.placeholderText = modelData["default"]
                itemArg_title.text = qsTranslate("Args", modelData.title)
                if( typeof modelData.description === 'undefined'){
                    return
                }
                itemArg_description.text = qsTranslate("Args", modelData.description)
            }
        }
    }
    Component{
        id: float_item
        Item{
            id: itemArg
            property var modelData: null
            width: parent.width
            implicitHeight: itemArg_title.implicitHeight + itemArg_description.implicitHeight
            Layout.fillHeight: true
            FluTextBox{
                id: itemArg_text
                anchors{
                    top: parent.top
                    topMargin: 2
                    right: parent.right
                }
                validator: DoubleValidator {}
                placeholderText: ""
                onEditingFinished: {
                    if(set_task(itemArg.parent.parent.parent.groupName, modelData.name, parseFloat(text))){
                        showSuccess( qsTr("Successful setting"))
                    }
                }
            }

            FluText{
                id: itemArg_title
                anchors{
                    top: parent.top
                    left: parent.left
                    right: itemArg_text.left
                }
                text: ""
                font: FluTextStyle.BodyStrong
                wrapMode: Text.WrapAnywhere
                topPadding: 6
            }
            FluText{
                id: itemArg_description
                anchors{
                    top: itemArg_title.bottom
                    left: parent.left
                }
                width: itemArg_title.width
                text: ""
                font: FluTextStyle.Caption
                wrapMode: Text.WrapAnywhere
//                textFormat: Text.PlainText
                topPadding: 6
                rightPadding: 6
            }
            onModelDataChanged: {
                if(modelData === null){
                    console.error("float model is null")
                    return
                }
                itemArg_text.text = modelData.value
                itemArg_text.placeholderText = modelData["default"]
                itemArg_title.text = qsTranslate("Args", modelData.title)
                if( typeof modelData.description === 'undefined'){
                    return
                }
                itemArg_description.text = qsTranslate("Args", modelData.description)
            }
        }
    }
    Component{
        id: bool_item
        Item{
            id: itemArg
            property var modelData: null
            width: parent.width
            implicitHeight: itemArg_title.implicitHeight + itemArg_description.implicitHeight
            Layout.fillHeight: true
            FluCheckBox{
                id: itemArg_text
                anchors{
                    top: parent.top
                    topMargin: 2
                    right: parent.right
                    rightMargin: 300 - 24
                }
                selected: true
                clickFunc: function click_func(){
                    selected = !selected
                    if(set_task(itemArg.parent.parent.parent.groupName, modelData.name, selected)){
                        showSuccess( qsTr("Successful setting"))
                    }
                }
            }

            FluText{
                id: itemArg_title
                anchors{
                    top: parent.top
                    left: parent.left
                    right: itemArg_text.left
                }
                text: ""
                font: FluTextStyle.BodyStrong
                wrapMode: Text.WrapAnywhere
                topPadding: 6
            }
            FluText{
                id: itemArg_description
                anchors{
                    top: itemArg_title.bottom
                    left: parent.left
                }
                width: itemArg_title.width
                text: ""
                font: FluTextStyle.Caption
                wrapMode: Text.WrapAnywhere
                topPadding: 6
                rightPadding: 6
            }
            onModelDataChanged: {
                if(modelData === null){
                    console.error("bool model is null")
                    return
                }
                itemArg_text.selected = modelData.value
                itemArg_title.text = qsTranslate("Args", modelData.title)
                if( typeof modelData.description === 'undefined'){
                    return
                }
                itemArg_description.text = qsTranslate("Args", modelData.description)
            }
        }
    }
    Component{
        id: enum_item
        Item{
            id: itemArg
            property var modelData: null
            width: parent.width
            implicitHeight: itemArg_title.implicitHeight + itemArg_description.implicitHeight
            Layout.fillHeight: true
            FComboBox{
                id: itemArg_text
                width: 300
                anchors{
                    top: parent.top
                    topMargin: 2
                    right: parent.right
                }
                model: ["0", "1", "2"]
                onActivated: {
                    // 获取原始英文值
                    var originalValue = modelData.options[currentIndex]
                    if(set_task(itemArg.parent.parent.parent.groupName, modelData.name, originalValue)){
                        showSuccess( qsTranslate("Args", "Successful setting"))
                    }
                }
            }

            FluText{
                id: itemArg_title
                anchors{
                    top: parent.top
                    left: parent.left
                    right: itemArg_text.left
                }
                text: ""
                font: FluTextStyle.BodyStrong
                wrapMode: Text.WrapAnywhere
                topPadding: 6
            }
            FluText{
                id: itemArg_description
                anchors{
                    top: itemArg_title.bottom
                    left: parent.left
                }
                width: itemArg_title.width
                text: ""
                font: FluTextStyle.Caption
                wrapMode: Text.WrapAnywhere
//                textFormat: Text.PlainText
                topPadding: 6
                rightPadding: 6
            }
            onModelDataChanged: {
                if(modelData === null){
                    console.error("enum model is null")
                    return
                }
                // 翻译下拉选项值
                var translatedOptions = []
                for(var i = 0; i < modelData.options.length; i++){
                    translatedOptions.push(qsTranslate("Args", modelData.options[i]))
                }
                itemArg_text.model = translatedOptions
                itemArg_text.show(qsTranslate("Args", modelData.value))
                itemArg_title.text = qsTranslate("Args", modelData.title)
                if( typeof modelData.description === 'undefined'){
                    return
                }
                itemArg_description.text = qsTranslate("Args", modelData.description)
            }
        }
    }
    Component{
        id: multi_line_item
        Item{
            id: multiLineItem
            property var modelData: null
            width: parent.width
            implicitHeight: string_title.implicitHeight + string_description.implicitHeight
            height: if(string_text.height > (string_title.implicitHeight + string_description.implicitHeight)){
                        return string_text.height
                    }else{
                        return string_title.implicitHeight + string_description.implicitHeight
                    }

            Layout.fillHeight: true
            FluMultilineTextBox{
                id: string_text
                anchors{
                    top: parent.top
                    topMargin: 2
                    right: parent.right
                }
                placeholderText: ""
                onEditingFinished: {
                    if(set_task(multiLineItem.parent.parent.parent.groupName, modelData.name, text)){
                        showSuccess( qsTr("Successful setting"))
                    }
                }
//                onTextChanged: {
//                    if(set_task(multiLineItem.parent.parent.parent.groupName, modelData.name, text)){
//                        showSuccess( qsTr("Successful setting"))
//                    }
//                }
            }

            FluText{
                // 设置的名称
                id: string_title
                anchors{
                    top: parent.top
                    left: parent.left
                    right: string_text.left
                }
                text: ""
                font: FluTextStyle.BodyStrong
                wrapMode: Text.WrapAnywhere
                topPadding: 6
            }
            FluText{
                //描述
                id: string_description
                anchors{
                    top: string_title.bottom
                    left: parent.left
                }
                width: string_title.width
                text: ""
                font: FluTextStyle.Caption
                wrapMode: Text.WordWrap
                topPadding: 6
                rightPadding: 6
            }
            onModelDataChanged: {
                if(modelData === null){
                    console.error("string model is null")
                    return
                }
                string_text.text = modelData.value
                string_text.placeholderText = modelData["default"]

                string_title.text = qsTranslate("Args", modelData.title)
                if( typeof modelData.description === 'undefined'){
                    return
                }
                string_description.text = qsTranslate("Args", modelData.description.replace("\\n","\n"))
            }
        }
    }
    onArgsDataChanged: {

    }
    onValueDataChanged: {

    }
    onUpdataData: {
        if(argsData === ""){
            console.error("解析 顺序出问题了")
            return
        }
        if(valueData === ""){
            console.debug("没有数据")
        }

        // 性能优化：延迟JSON解析和数据预处理
        let args, values;
        try {
            args = JSON.parse(argsData)
            values = JSON.parse(valueData)
        } catch (e) {
            console.error("JSON parsing error:", e)
            return
        }
        
        // 调试输出 (已注释)
        // console.log("Processing task:", taskName)
        // console.log("Args data:", JSON.stringify(args, null, 2))
        
        // 适配 Pydantic v2 格式：$defs 替代 definitions
        let definitions = args.definitions || args.$defs || args["$defs"];
        if(!definitions) {
            console.error("Args data missing definitions/$defs field!")
            return
        }
        
        // 将 $defs 赋值给 args.definitions 以保持兼容性
        args.definitions = definitions;
        
        // 性能优化：批量解析组信息
        const group = MP.parseGroup(args["properties"])
        const groups = MP.parseGroups(args["properties"])

        for(let task in group){
            const argument = MP.parseArgument(args.definitions, group[task])
            const groupLetter = groups[group[task]]
            const argumentVuale = MP.mergeArgument(argument, values[groupLetter])
//            console.debug(JSON.stringify( argumentVuale ))
//            console.debug("---------------------------------------------------------------")
            createGroup(groupLetter, group[task], argumentVuale)
        }
    }

    /**
     * 创建某个组 的显示组件并显示
     * @param {Object} groupName 变量的名字 是小写的
     * @param {Object} groupTitle 用于向用户显示的名字 大写的
     * @param {Object} argumentVaule 总的显示的参数
     * @returns {Object}
     */
    function createGroup(groupName, groupTitle, argumentValue){
        if(!groupName){
            console.error("no group name")
            return
        }
        if(!groupTitle){
            console.error("no group title")
            return
        }

        const object = group_item.createObject(contentScrollable)
        if(object !== null){
            object.groupName = groupName
            object.groupTitle = qsTr(groupTitle)
            object.argumentValue = argumentValue

            contentScrollable.content.push(object)
        }
        else{
            console.error('create group item failed!')
        }
    }

    function set_task(group, arg, value){
        //如果是字符串
        if( typeof value == "string" ){
        if(process_manager.gui_set_task(configName, taskName, group, arg, value)){
            return true
        }
        else{
            return false
        }}

        //如果是整形的
        else if(typeof value == "number"){
        if(process_manager.gui_set_task_number(configName, taskName, group, arg, value)){
            return true
        }
        else{
            return false
        }}


        //如果是bool的
        else if(typeof value == "boolean"){
        if(process_manager.gui_set_task_bool(configName, taskName, group, arg, value)){
            return true
        }
        else{
            return false
        }}


    }
}
