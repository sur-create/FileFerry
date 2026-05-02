# 测试报告

## 1. 测试范围

- 单元测试：协议编解码、路径安全、CLI 默认目录策略。
- 集成测试：发送模块与接收模块在本机回环地址下协同传输。
- 系统测试：通过 CLI 子进程完成多源端到端传输。

## 2. 测试环境

- OS: Linux (workspace sandbox)
- Python: 3.12.3
- 命令：`python3 -m unittest discover -s tests -v`

## 3. 测试用例清单

| 类型 | 用例 | 目标 |
|---|---|---|
| Unit | `test_default_output_dir_prefers_executable_dir_when_writable` | 校验默认目录优先使用可写可执行入口目录 |
| Unit | `test_default_output_dir_falls_back_to_cwd_when_not_writable` | 校验安装目录不可写时自动回退当前目录 |
| Unit | `test_encode_decode_round_trip` | 校验头部编码/解码一致性 |
| Unit | `test_invalid_filename_rejected` | 校验非法文件名/相对路径拦截 |
| Unit | `test_recv_exact_raises_on_disconnect` | 校验连接提前断开处理 |
| Unit | `test_resolve_relative_output_path_rejects_escape` | 校验路径穿越防护 |
| Integration | `test_legacy_single_file_wrappers` | 校验单文件兼容接口 |
| Integration | `test_library_multi_source_recursive_and_mtime` | 校验多源递归传输与 mtime 保留 |
| Integration | `test_conflict_rename_policy` | 校验 `rename` 冲突策略 |
| Integration | `test_conflict_skip_policy` | 校验 `skip` 冲突策略 |
| Integration | `test_sender_policy_overrides_receiver_default` | 校验发送端会话策略可覆盖接收端默认策略 |
| System | `test_cli_end_to_end_multi_source` | 校验 CLI 多源传输成功 |

## 4. 执行结果

- 执行时间：2026-05-02
- 命令输出摘要：
  - `Ran 12 tests in 2.410s`
  - `OK`

## 5. 结论

当前实现满足 V1.3 迭代的核心目标：保留 V1.2 多源传输能力（多文件/目录递归、冲突策略、失败继续、mtime）并新增 GUI 代码路径。

补充说明：

- GUI（V1.3）功能未纳入自动化 Qt 界面测试；核心传输行为通过库/CLI 回归测试覆盖。
