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
- AE ExtendScript 核心规则
- 常用且经过验证的 matchName 速查表
- 素材替换和 Render Queue 等高风险任务卡片
- 可复用的 JSX 模板

bridge 不需要硬编码 AE 路径。它会按顺序从 `--afterfx`、`AFTERFX_COM_PATH`、可选的本地 `config.json`，或 `C:\Program Files\Adobe` 下的自动发现结果解析 `AfterFX.com`。

## 安全保护

`client\send_to_ae.py` 默认会在执行目标 JSX 前做保护检查：

- AE 必须打开工程。
- 当前工程必须已经保存为 `.aep`。
- 当前工程不能有未保存改动。
- 检查通过后，bridge 会在当前 `.aep` 同目录下创建 `agent backups\`，把工程复制进去，文件名前缀为 `agent backup`，并滚动保留最新 10 个备份。

如果工程未保存或存在未保存改动，bridge 会先把失败结果返回给 agent，再在 AE 中弹窗提示用户；目标 JSX 不会执行。只读检查或一次性测试可以显式加 `--no-protect`。

同一轮 agent 操作中如果需要连续执行多条 JSX 命令，应复用同一个 `--operation-id`。第一次命令会触发保护检查和备份；后续同 id 命令会复用这次备份，不会因为前面命令把工程变 dirty 而再次拦截。下一轮用户任务应使用新的 `--operation-id`。

保护状态在 24 小时后自动过期。每次命令使用独立的 `logs\runs\<Run ID>\` 目录保存结果、报告、包装 JSX 和预览文件，滚动保留最近 10 次运行。

`--timeout-seconds` 限制客户端等待时间，但不能保证 AE 已停止内部正在执行的 JSX。超时后应先等待 AE 恢复响应并执行只读检查，再继续修改工程。

## 画面检查

关键视觉操作或一批操作完成后，可以让 bridge 返回当前合成的一帧图片：

```bat
python client\send_to_ae.py scripts\your_script.jsx --capture-frame --capture-time-mode two-thirds
```

默认截图使用临时 `8 bpc` 的 `saveFrameToPng` 预览路径：bridge 会记录原始项目位深，切到 `8 bpc` 导出当前帧，再恢复原始位深。这个方法不碰用户已有 Render Queue，适合 agent 做常规画面检查。输出图片会规范成 PNG 预览图，默认长边不超过 `1500px`。注意，AE 仍可能因为临时位深切换把工程标记为有未保存改动；bridge 会在截图报告中标记 `dirtyChangedByCapture` 并输出 warning。

如果怀疑颜色、HDR、线性工作流或 32-bit 高亮结果不准，再显式使用 Render Queue 核对：

```bat
python client\send_to_ae.py scripts\your_script.jsx --capture-frame --capture-method render-queue --capture-time-mode two-thirds
```

Render Queue 截图会临时禁用已有待渲染项，只渲染截图项，随后删除截图项并恢复原队列状态。

对于有动画的合成，agent 应根据任务选择检查时间帧：可以使用 `current`、`middle`、`two-thirds`、`end`，或通过 `--capture-time <seconds>` 指定具体时间。通常中部或中后部帧比第一帧更能暴露动画结果。

如果本轮操作涉及动画、转场、时间错位或多次连续改动，可以额外生成低帧率预览视频供 agent 做最终检查：

```bat
python client\send_to_ae.py scripts\your_script.jsx --capture-video
```

视频预览同样走临时 `8 bpc` 的 `saveFrameToPng` 路径，不使用 Render Queue。bridge 会按当前合成时长均匀抽样 PNG 序列，再生成 MP4 和 contact sheet。默认最多抽 `48` 帧、以 `4fps` 播放、长边不超过 `960px`，适合检查动画节奏和关键画面变化，不作为最终画质渲染。文件保存在当前运行目录的 `temp\video_preview\` 下，并随最近 10 次运行一起滚动清理。

如果只是静态合成或只改了单帧视觉，不需要生成视频；继续使用 `--capture-frame` 更快。
