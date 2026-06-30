# AE Remote Script Bridge Skill

本仓库包含一个可安装的 Codex skill：

```text
skills/ae-remote-script-bridge
```

安装时，将该目录复制到目标机器的 Codex skills 目录，例如：

```text
C:\Users\<user>\.codex\skills\ae-remote-script-bridge
```

该 skill 包含：

- Windows `AfterFX.com` JSX bridge
- AE ExtendScript 规则和常见坑
- 轻量级 API 与 matchName 速查表
- 常见 AE 脚本任务卡片
- 可复用的 JSX 模板

bridge 不需要硬编码 AE 路径。它会按顺序从 `--afterfx`、`AFTERFX_COM_PATH`、可选的本地 `config.json`，或 `C:\Program Files\Adobe` 下的自动发现结果解析 `AfterFX.com`。
