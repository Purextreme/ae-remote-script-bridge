# AE Remote Script Bridge

这是一个最小 AE remote script bridge，用于从外部命令行发送 JSX 到 Adobe After Effects 2024 执行。

## 环境要求

- Windows
- Adobe After Effects 2024
- Python 3
- AE 里建议开启：

```text
Edit > Preferences > Scripting & Expressions > Allow Scripts To Write Files and Access Network
```

## 重要说明

本机测试发现：

```bat
AfterFX.exe -r xxx.jsx
```

不可靠。本项目默认使用：

```bat
"C:\Program Files\Adobe\Adobe After Effects 2024\Support Files\AfterFX.com" -r "script.jsx"
```

AE 路径配置在 `config.json`：

```json
{
  "afterfx_com_path": "C:\\Program Files\\Adobe\\Adobe After Effects 2024\\Support Files\\AfterFX.com"
}
```

如果 AE 安装路径不同，手动修改这个值。

## 测试命令

```bat
python client\send_to_ae.py scripts\ae_test_create_comp.jsx
```

```bat
python client\send_to_ae.py scripts\ae_test_modify_active_comp.jsx
```

```bat
python client\send_to_ae.py scripts\ae_test_error.jsx
```

## 预期结果

- `ae_test_create_comp.jsx` 创建名为 `AE_Bridge_Create_Comp_Test` 的新合成
- `ae_test_modify_active_comp.jsx` 修改当前 active composition
- `ae_test_error.jsx` 在 CMD 中显示 `[AE ERROR]`
- 最新执行结果写入 `logs/latest_result.json`
- `ae_inspect_project.jsx` 将当前 AE 工程结构写入 `logs/project_structure.json`
- `ae_test_integration_ops.jsx` 验证效果、关键帧、项目整理、输出、渲染和保存链路

成功输出：

```text
[AE OK]
Script executed successfully.
```

失败输出：

```text
[AE ERROR]
Error: xxx
Line: xx
```

超时输出：

```text
[AE TIMEOUT]
No result file generated.
```

## Codex Skill

项目内包含可复制的 Codex skill：

```text
skills/ae-remote-script-bridge
```

在另一台电脑上使用时，将该目录复制到：

```text
C:\Users\<你的用户名>\.codex\skills\ae-remote-script-bridge
```

之后在新对话中请求 Codex 操作 AE 时，触发 `$ae-remote-script-bridge` 即可复用本 bridge。
