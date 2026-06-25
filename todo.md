下面是精简版 ToDo，适合直接丢给 Codex。重点是让它自己测试细节，不把需求写得太死。

```markdown
# AE Remote Script Bridge MVP ToDo

## 目标

开发一个最小可用的 AE remote script bridge，用于从外部命令行把 JSX 脚本发送到 Adobe After Effects 2024 执行。

当前已手动验证：

- `AfterFX.exe -r xxx.jsx`：不可靠，只会把 AE 拉到前台
- `AfterFX.com -r xxx.jsx`：可正常执行 JSX
- `AfterFX.com -s "alert('test')"`：可正常执行
- AE 菜单 `File > Scripts > Run Script File...`：可正常执行 JSX

因此本项目必须默认使用：

```bat
"C:\Program Files\Adobe\Adobe After Effects 2024\Support Files\AfterFX.com" -r "script.jsx"
```

不要使用 `AfterFX.exe`。

---

## 项目结构

建议结构：

```text
AE_remote_script_bridge/
├─ client/
│  └─ send_to_ae.py
├─ scripts/
│  ├─ ae_test_create_comp.jsx
│  ├─ ae_test_modify_active_comp.jsx
│  └─ ae_test_error.jsx
├─ logs/
│  └─ .gitkeep
├─ temp/
│  └─ .gitkeep
├─ config.json
└─ README.md
```

---

## 1. config.json

创建配置文件：

```json
{
  "afterfx_com_path": "C:\\Program Files\\Adobe\\Adobe After Effects 2024\\Support Files\\AfterFX.com"
}
```

要求：

- `send_to_ae.py` 从这里读取 AE 路径

- 如果路径不存在，给出清晰错误提示

- 后续用户可以手动修改路径

---

## 2. client/send_to_ae.py

实现一个命令行工具。

示例用法：

```bat
python client\send_to_ae.py scripts\ae_test_create_comp.jsx
```

基本功能：

- 接收一个 `.jsx` 文件路径

- 支持相对路径和绝对路径

- 检查 `AfterFX.com` 是否存在

- 检查 JSX 文件是否存在

- 调用 `AfterFX.com -r`

- 路径包含空格时也要正常运行

- 打印正在执行的 AE 路径和 JSX 路径

重点：

- 使用 `subprocess.run([afterfx_com_path, "-r", jsx_path])`

- 不要用字符串拼接命令

- 不要调用 `AfterFX.exe`

---

## 3. 增加简单返回机制

AE 不会直接把 JSX 的成功/失败返回到 CMD，所以需要做一个轻量 result file 机制。

思路：

- Python 执行前删除旧的 `logs/latest_result.json`

- Python 生成一个临时 wrapper JSX 到 `temp/`

- wrapper JSX 内部执行目标 JSX

- 成功后写入 `logs/latest_result.json`

- 报错后也写入 `logs/latest_result.json`

- Python 等待这个 result 文件出现，然后读取并打印结果

预期输出：

成功：

```text
[AE OK]
Script executed successfully.
```

失败：

```text
[AE ERROR]
Error: xxx
Line: xx
```

如果超时：

```text
[AE TIMEOUT]
No result file generated.
```

超时时间可以先设为 20 秒。

注意：

- ExtendScript 比较老，wrapper 里优先用 `var`

- 不要依赖现代 JS 语法

- JSON 写入可以手写字符串，不强制使用 `JSON.stringify`

- 具体实现细节可以自行测试调整

---

## 4. scripts/ae_test_create_comp.jsx

创建测试脚本。

功能：

- 创建一个 composition

- 名称：`AE_Bridge_Create_Comp_Test`

- 尺寸：1920x1080

- 帧率：30fps

- 时长：5秒

- 添加一个 solid layer

- 添加一个 text layer，文字：`AE Bridge OK`

- 打开 comp viewer

- 正常情况下不要弹 alert

- 使用 `app.beginUndoGroup()` / `app.endUndoGroup()`

---

## 5. scripts/ae_test_modify_active_comp.jsx

创建测试脚本。

功能：

- 检查当前 active item 是否为 composition

- 如果不是 comp，抛出错误或写入错误结果

- 如果是 comp：
  
  - 修改 duration 为 8 秒
  
  - 修改背景色
  
  - 添加 text layer：`Active Comp Modified`
  
  - 打开 viewer

正常情况下不要弹 alert。

---

## 6. scripts/ae_test_error.jsx

创建一个故意报错的测试脚本，用于验证错误返回机制。

例如：

```javascript
thisFunctionDoesNotExist();
```

运行后，CMD 应该能显示 `[AE ERROR]`。

---

## 7. README.md

README 写清楚：

### 项目用途

这是一个最小 AE remote script bridge，用于从外部命令行发送 JSX 到 AE 2024 执行。

### 环境要求

- Windows

- Adobe After Effects 2024

- Python 3

- AE 里建议开启：

```text
Edit > Preferences > Scripting & Expressions > Allow Scripts To Write Files and Access Network
```

### 重要说明

本机测试发现：

```bat
AfterFX.exe -r xxx.jsx
```

不可靠。

本项目使用：

```bat
AfterFX.com -r xxx.jsx
```

### 测试命令

```bat
python client\send_to_ae.py scripts\ae_test_create_comp.jsx
```

```bat
python client\send_to_ae.py scripts\ae_test_modify_active_comp.jsx
```

```bat
python client\send_to_ae.py scripts\ae_test_error.jsx
```

### 预期结果

- create comp 脚本可以创建新合成

- modify active comp 脚本可以修改当前合成

- error 脚本可以在 CMD 中显示错误

- result 文件写入到：

```text
logs/latest_result.json
```

---

## 8. 验收标准

项目完成后需要满足：

- 可以通过 Python 调用 AE 执行 JSX

- 可以创建 comp

- 可以修改 active comp

- 可以捕获 JSX 报错并在 CMD 输出

- 如果 AE 没有返回 result file，需要显示 timeout

- README 中有清晰测试步骤

---

## 暂不做

第一版不要做：

- socket server

- MCP

- CEP panel

- GUI

- 批量字体替换

- 批量整理素材

- 自动生成 JSX

- 复杂插件系统

先把 `AfterFX.com -r + result file` 这条链路跑通。

```
这个版本比较适合 MVP。关键不是做得很完整，而是先验证三件事：**能执行、能报错、能返回结果**。
```
