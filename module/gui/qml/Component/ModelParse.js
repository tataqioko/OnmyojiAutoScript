.pragma library

// 性能优化：添加缓存机制
var _parseCache = {}
var _maxCacheSize = 100

function clearCache() {
    _parseCache = {}
}

function getCacheKey(definitions, group) {
    return JSON.stringify({def: Object.keys(definitions).sort(), group: group})
}

//
//*****************************请注意下面的函数只适用与pydantic生成的task的参数
//

/**
 * 解析出group的数组，
 * @param {Object} data.properties
 * @returns {Array} 类似这样：[Device,Error,Optimization]
 */
function parseGroup(properties) {
    var result = []
    for(const key in properties){
        if(!('$ref' in properties[key])){
            continue
        }
        const value = properties[key]['$ref'];
        const lastPart = value.substring(value.lastIndexOf('/') + 1);
        result.push(lastPart)
    }
    return result
}

/**
 * 解析出group一一对应的的数组，
 * @param {Object} data.properties
 * @returns {Object} 类似这样：{"Device":"device", "Error":"error", "Optimization":"optimization"}
 */
function parseGroups(properties) {
    var result = {}
    for(const key in properties){
        if(!('$ref' in properties[key])){
            continue
        }
        const value = properties[key]['$ref'];
        const lastPart = value.substring(value.lastIndexOf('/') + 1);
        result[lastPart] = key
    }
    return result
}


/**
 * 解析ref的最后一个Name
 * @param {String} ref
 * @returns {String}
 */
function parseRef(ref){
    return ref.substring(ref.lastIndexOf('/') + 1)
}


/**
 * 解析出某个group的参数组，
 * @param {Object} definitions
 * @param {string} group
 * @returns {Array} -
 */
function parseArgument(definitions, group){
    if(!definitions){
        console.error("parseArgument: definitions is null or undefined");
        return null;
    }
    if(!(group in definitions)){
        console.error("parseArgument: group '" + group + "' not found in definitions");
        return null;
    }
    
    // 性能优化：检查缓存
    const cacheKey = getCacheKey(definitions, group);
    if(_parseCache[cacheKey]) {
        console.log("Using cached result for group:", group);
        return _parseCache[cacheKey];
    }
    
    const result = []
    if(!definitions[group] || !definitions[group]["properties"]){
        console.error("parseArgument: properties not found for group '" + group + "'");
        return null;
    }
    const pro = definitions[group]["properties"]
    for(const key in pro){
        const arg = {}
        const argName = pro[key]

        arg["name"] = key

        if("title" in argName){
            arg["title"] = argName.title
        }else{

        }

        //如果有allOf表示这个配置字段是一个枚举的, 一般枚举的就是string
        if("allOf" in argName){
            const ref = argName.allOf[0]["$ref"]
            arg["title"] = parseRef(ref)
            arg["type"] = "enum"
        }
        
        // 处理直接的 $ref 引用
        if("$ref" in argName){
            const refName = parseRef(argName["$ref"])
            if(refName && refName in definitions){
                const refDef = definitions[refName]
                if("enum" in refDef){
                    arg["type"] = "enum"
                    arg["options"] = refDef["enum"]
                    if(!arg["title"]){
                        arg["title"] = refName
                    }
                }
            }
        }
        
        // 处理 anyOf 结构
        if("anyOf" in argName){
            for(let i = 0; i < argName.anyOf.length; i++){
                const anyOfItem = argName.anyOf[i]
                if("$ref" in anyOfItem){
                    const refName = parseRef(anyOfItem["$ref"])
                    if(refName && refName in definitions){
                        const refDef = definitions[refName]
                        if("enum" in refDef){
                            arg["type"] = "enum"
                            arg["options"] = refDef["enum"]
                            if(!arg["title"]){
                                arg["title"] = refName
                            }
                            break; // 找到第一个有效的枚举就停止
                        }
                    }
                }
            }
        }

        if("description" in argName){
            arg["description"] = argName.description
        }else{
            // 没有帮助就没有帮助
        }

        if("default" in argName){
            arg["default"] = argName["default"]
        }else{
            console.error(arg["title"], 'have not default')
        }

        if("type" in argName){
            arg["type"] = argName.type
            // 将特殊类型转换为字符串类型
            if(arg["type"] === "date_time" || arg["type"] === "time_delta" || arg["type"] === "time"){
                arg["type"] = "string"
            }
        }

        if(arg["type"] === "enum"){
            // 如果已经在前面设置了 options，就不需要再设置了
            if(!arg["options"]){
                if(arg.title && definitions[arg.title] && definitions[arg.title]["enum"]){
                    arg["options"] = definitions[arg.title]["enum"]
                } else {
                    console.error("Cannot find enum options for", arg.title)
                    arg["type"] = "string" // 降级为字符串类型
                }
            }
        }

        result.push(arg)

    }
    
    // 性能优化：缓存结果
    if(Object.keys(_parseCache).length >= _maxCacheSize) {
        // 清理最旧的缓存项
        const oldestKey = Object.keys(_parseCache)[0];
        delete _parseCache[oldestKey];
    }
    _parseCache[cacheKey] = result;
    
    return result
}

/**
 * 合并某个group的参数组，
 * @param {Object} argument
 * @param {Object} values
 * @returns {Object} - 就是添加了value这个一个值
 */
function mergeArgument(argument, values){
    for(let key in argument){
        const name = argument[key].name
        if(name in values){
            argument[key]["value"] = values[name]
        }
    }
    return argument
}
