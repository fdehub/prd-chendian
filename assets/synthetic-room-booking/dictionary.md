# 字段与权限字典（完全虚构）

| 键/视图 | 类型/边界 | 空值/默认/权限 |
|---|---|---|
| Create.roomId | string 1–80 | 必填，无默认，来源enabled列表 |
| Create.startAt/endAt | UTC RFC3339 | 必填；秒0、分钟15倍数；时长30–120；服务器now+15分钟，不支持null/清空 |
| Create.purpose | trim后string 1–80纯文本 | 必填，无默认；本人/operator读 |
| Booking.ownerId | 服务端会话推导 | 只读，客户端提交即400，不从ID猜授权 |
| Booking.status | active/cancelled | 服务器动作控制，不接受任意PATCH |
| Booking.revision | int≥1 | 创建1；有效取消+1；重复取消不变 |
| Cancel.reason | string 1–200 | 必填；不是可选备注，不发邮件 |
| Room.capacity | int 1–100 | 本例仅展示，不按人数拆分同一时段资源 |
| Room.enabled | bool | operator改，必须版本头；member 403；不影响历史预约 |

成员读列表/详情只限本人；operator可读全部。其他成员访问ID统一404；不存在与无归属不可区分。角色在服务端执行，UI隐藏按钮不替代校验。

JSON所有未知字段400；字段值非法422；POST幂等键必须非空；创建幂等键按会话+键绑定24小时，载荷不同时409。PATCH If-Match为当前revision的带引号十进制字符串，缺失428、不符409。CSRF由会话中间件验证，缺令牌403；真实认证接入为DEP-AUTH，示例不包含凭据。
