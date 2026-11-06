# Manifest与校验

在最终需求包根目录写`requirements-manifest.json`。所有路径相对根目录；禁止绝对路径、`..`和跳出根目录的符号链接。完整包的artifact role见deliverables.md。

示例是结构说明，生成时填实际文件和版本，不直接作为完成产物：

```json
{
  "version": "项目实际版本",
  "scope": "full",
  "status": "proposal",
  "artifacts": [
    {"role":"prd","path":"需求文档.md"},
    {"role":"api","path":"openapi.json"},
    {"role":"dictionary","path":"字段权限字典.md"},
    {"role":"prototype","path":"线框.html"},
    {"role":"trace","path":"需求验收追踪.md"},
    {"role":"fixtures","path":"验收数据.json"},
    {"role":"review","path":"审查修复记录.md"},
    {"role":"verification","path":"验证记录.json"},
    {"role":"readme","path":"阅读入口.md"}
  ],
  "requirements": [
    {"id":"BOOK-01","phase":"P0","status":"proposed","pageIds":["booking-form"],"operationIds":["booking_create"],"localOnly":false,"acceptanceIds":["CASE-01"]}
  ],
  "acceptanceCases": [
    {"id":"CASE-01","requirementIds":["BOOK-01"],"given":{"serverTime":"虚构固定测试时间"},"when":{"operationId":"booking_create","input":"实际固定输入"},"then":{"httpStatus":201,"status":"active"}}
  ]
}
```

可选`sha256`绑定文件；重新生成附件后须同步哈希。完整包每个role至少一个，可多个文件。partial必须给`omissions`字符串数组说明未含产物，不得标为完整包。

运行：`python scripts/validate_bundle.py <bundle-dir> [--report <report.json>]`。

requirements中的ID唯一；本期需求必须有页面、真实端点或明确localOnly及理由，并关联实际存在的验收ID。acceptanceCases须提供非空Given/When/Then对象，Then包含可判定结果，不能仅写“正确”。每个本期端点必须被需求引用；验收反向引用也要有效。完整可运行示例见assets/synthetic-room-booking/requirements-manifest.json。

校验器检查manifest、文件归属/存在/哈希、JSON可解析、OpenAPI引用/operationId/路径参数/schema基本约束、端点与需求与验收的双向引用、端点在追踪文档中的可检索标识。发现错误退出1，成功退出0；输出声明限制范围。

它不执行包内任意脚本，不连接网络，也不是完整OpenAPI规范验证器。金额、库存等语义仍需项目自己的独立样例与实际校验。必须在验证记录中写清真实命令、结果与未覆盖部分，不能仅把这个脚本的PASS称作全部问题已关闭。
