# 测试报告

## 1. 测试范围

- 单元测试：协议编解码、路径安全、CLI 默认目录策略、GUI 状态逻辑。
- 集成测试：发送模块与接收模块在回环地址下协同传输。
- 系统测试：CLI 子进程端到端多源传输。
- 增量测试（V1.4）：发送进度回调事件链路。

## 2. 测试环境

- OS: Linux (workspace sandbox)
- Python: 3.12.3
- 执行日期：2026-05-04

执行命令：

```bash
python3 -m compileall fileferry fileferry_gui tests scripts
python3 -m unittest discover -s tests -v
python3 -m fileferry send --help
python3 -m fileferry recv --help
bash -n packaging/linux/build_deb.sh packaging/linux/build_rpm.sh packaging/macos/build_pkg.sh
```

## 3. 测试用例清单

| 类型 | 用例 | 目标 |
|---|---|---|
| Unit | `test_default_output_dir_prefers_executable_dir_when_writable` | 校验默认目录策略 |
| Unit | `test_default_output_dir_falls_back_to_cwd_when_not_writable` | 校验目录回退策略 |
| Unit | `test_encode_decode_round_trip` | 校验头部编码/解码一致性 |
| Unit | `test_invalid_filename_rejected` | 校验非法文件名/路径拦截 |
| Unit | `test_recv_exact_raises_on_disconnect` | 校验连接提前断开处理 |
| Unit | `test_resolve_relative_output_path_rejects_escape` | 校验路径穿越防护 |
| Unit | `test_send_button_state_auto_switch` | 校验发送按钮状态自动切换 |
| Unit | `test_progress_helpers` | 校验进度格式化逻辑 |
| Integration | `test_legacy_single_file_wrappers` | 校验单文件兼容接口 |
| Integration | `test_library_multi_source_recursive_and_mtime` | 校验多源递归与 mtime 保留 |
| Integration | `test_conflict_rename_policy` | 校验 `rename` 策略 |
| Integration | `test_conflict_skip_policy` | 校验 `skip` 策略 |
| Integration | `test_sender_policy_overrides_receiver_default` | 校验会话策略覆盖 |
| Integration | `test_send_progress_callback_emits_events` | 校验发送进度回调链路 |
| System | `test_cli_end_to_end_multi_source` | 校验 CLI 端到端多源传输 |

## 4. 执行结果

- `python3 -m compileall ...`：通过。
- `python3 -m unittest discover -s tests -v`：
  - `Ran 15 tests in 2.685s`
  - `OK`
- `python3 -m fileferry send --help`：通过。
- `python3 -m fileferry recv --help`：通过。
- `bash -n packaging/...`：通过。

## 5. 结论

V1.4 本次迭代已满足核心目标：

- 传输进度具备可视化基础能力（发送端与接收端均可消费进度事件）。
- 发送按钮状态自动切换逻辑具备测试覆盖。
- 既有 V1.2/V1.3 回归能力保持通过。
- 文件夹断点续传完成调研文档化，后续可按阶段 A/B 推进。

补充说明：

- GUI 运行时验证依赖 `PySide6`；当前自动化覆盖以核心逻辑与传输链路为主。
