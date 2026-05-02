# 测试报告

## 1. 测试范围

- 单元测试：协议编解码、文件名校验、异常链路。
- 集成测试：发送模块与接收模块在本机回环地址下协同传输。
- 系统测试：通过 CLI 子进程完成端到端文件传输。

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
| Unit | `test_invalid_filename_rejected` | 校验非法文件名拦截 |
| Unit | `test_recv_exact_raises_on_disconnect` | 校验连接提前断开处理 |
| Integration | `test_library_transfer` | 校验库接口端到端传输与字节一致性 |
| System | `test_cli_end_to_end` | 校验 CLI 进程级传输成功 |

## 4. 执行结果

- 执行时间：2026-05-02
- 命令输出摘要：
  - `Ran 7 tests in 0.713s`
  - `OK`
- 结果明细：

| 用例 | 结果 |
|---|---|
| `test_default_output_dir_prefers_executable_dir_when_writable` | 通过 |
| `test_default_output_dir_falls_back_to_cwd_when_not_writable` | 通过 |
| `test_encode_decode_round_trip` | 通过 |
| `test_invalid_filename_rejected` | 通过 |
| `test_recv_exact_raises_on_disconnect` | 通过 |
| `test_library_transfer` | 通过 |
| `test_cli_end_to_end` | 通过 |

## 5. 结论

当前实现满足需求文档中定义的 V1.0 核心目标与 FR-01~FR-06，未发现阻断性缺陷。系统在本地回环环境中可稳定完成单文件传输。

补充说明：

- 由于测试包含 socket 创建，沙箱默认权限下会失败；在提升权限后测试全部通过。
