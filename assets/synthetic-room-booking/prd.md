# 虚构教学案例：活动室预约需求包

来源：完全虚构、独立编写。状态：提案。数据仅教学，无客户品牌、真实预约、账号、聊天或本机路径。不表示已经开发上线。

## 范围与角色

P0：查询活动室、空闲查询、创建预约、本人列表/详情、取消、运营启停。排除付款、积分、多组织、审批、循环预约。成员member使用已验证会话；运营operator管理活动室，可读/取消全部预约。成员只能读取/取消自己的预约，ID不是授权。

## BOOK-01 查询（page-room-list、page-availability）

列表包含活动室名称、人数上限、启停状态；成员只见enabled，operator可见停用。输入roomId及startAt/endAt查询空闲，不预留。空态与查询失败分开；相邻区间允许，重叠返回available=false；查询结果可能过期，不能代替提交时校验。

## BOOK-02 创建（page-booking-form）

从列表点预约，页面上方房间摘要，中间开始/结束选择器及用途，右侧时长/冲突预览，底部取消/提交。字段如下：

| 字段ID/契约键 | 控件/类型/必填 | 校验/默认/权限 |
|---|---|---|
| F-01 roomId | 选择器/string/必填 | 来自enabled列表，无默认；成员/运营可提交 |
| F-02 startAt | 日期时间/UTC RFC3339/必填 | 无默认；15分钟整数倍、秒为0；至少晚于服务器now 15分钟 |
| F-03 endAt | 日期时间/UTC RFC3339/必填 | 无默认；15分钟整数倍、秒为0；时长30至120分钟，均含边界 |
| F-04 purpose | 单行/string/必填 | trim后1–80字符，纯文本；只对预约人及operator展示 |

前台按虚构场地时区UTC显示，明确UTC标签。时间校验基于服务端时间，不能依赖客户电脑时钟。时间区间[start,end)，两个active预约冲突当且仅当同room且newStart<oldEnd且oldStart<newEnd。

提交按钮校验→loading禁双击→服务端验证角色/字段/房间启用/时间→原子冲突检查与写入。冲突返回409 SLOT_CONFLICT，保留表单、定位时间，零新增记录；未知字段400 UNKNOWN_FIELD，字段非法422 VALIDATION_FAILED。成功201 active及revision=1，跳本人详情。

相同会话/Idempotency-Key/相同载荷24小时返回原预约且不新增；同键不同载荷409 IDEMPOTENCY_CONFLICT。不同请求键也受room/区间原子约束，不以幂等键代替并发互斥。网络超时显示“结果待确认”，同键重试，不擅自新建请求。

## BOOK-03 本人列表与详情（page-my-bookings、page-booking-detail）

列表列roomId/start/end/status，按start升序、同值id升序；cursor分页默认20上限50。详情只有本人或operator可见，非法归属统一404，不显示是否存在。字段ownerId在接口创建时从会话推导，客户端提交ownerId为400；成员不能借此冒领。

## BOOK-04 取消（page-booking-detail）

仅active且服务器now<startAt可取消，取消原因1–200必填。点按钮显示房间/区间/资源释放说明后确认，服务端再次校验。成功200 cancelled、revision+1，原子状态变更才释放该区间；不是发出请求就先释放。重复取消同一记录200原cancelled且revision不再增加。开始后409 CANCELLATION_WINDOW_CLOSED；notOwner为404。

取消与并发创建共同按房间区间串行化：取消事务提交之前原时段仍冲突，提交之后可重新预约。不能回滚历史取消来删除后来预约；错误取消需新建记录。

## BOOK-05 运营启停（page-room-admin）

operator可修改enabled，需If-Match当前revision。member调用403 FORBIDDEN；版本不符409 REVISION_CONFLICT，保留输入刷新比对。停用只阻止新预约，不删除已有记录；已有预约仍可按取消规则处理。无草稿/发布多层流程，保存即生效，审计actor/old/new/time/requestId。

## 状态与副作用

| 当前/事件 | 守卫/原子结果 | 后续 |
|---|---|---|
| 无记录→create | enabled、时间合法、无active冲突→插入active | 201，资源被占；重复原请求返回原记录 |
| active→cancel | 本人/operator、开始前→改cancelled、revision+1 | 200，资源释放；事务失败保持active，不提前释放 |
| cancelled→cancel | 权限合法 | 200原记录，无新副作用 |
| active已开始→cancel | 时间不允许 | 409，active不变 |

审计是内部记录，本例不发送任何邮件。需求中不存在默认通知/付款/库存功能；实现不得无依据新增。并发压力和实际数据库隔离需要软件阶段验证，参考模型不是实测。

## 依赖、非功能与验收

本例假定由既有身份系统提供member/operator会话，具体生产接入为DEP-AUTH，责任集成人员，缺少时不可上线但可用隔离fixture评审。真实活动室名、容量和营业安排为DEP-DATA，责任运营；本例固定demo-room全天仅教学，不能冒充真实场地。

提案测试协议：2vCPU/4GiB应用、独立2vCPU/4GiB数据库、1000房间/10000预约；20个虚拟用户每2秒一次查询，另10用户同时争同区间，持续5分钟；P95本地接口≤500ms、5xx<0.1%、同区间最多1个active。未实测；变更目标需记录影响和批准，不在验收时临时改口径。

本期每条需求、端点和用例在trace.md及manifest双向关联。版本为synthetic-1；批准状态proposal。改变时间边界、角色或取消规则必须关联需求ID和用例修改，用户尚未签字。软件交付还需真实身份接入和并发/性能证据。
