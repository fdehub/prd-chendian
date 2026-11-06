# 需求文档Skill

作者：[陈淀](https://github.com/fdehub) · 调用标识：`$prd-chendian`

把模糊想法、功能清单或现有资料，整理成开发能实现、测试能验收的产品需求文档（PRD）。支持从零梳理、补全文档、审查并修复三种入口。

## 能产出什么

完整需求包包含：统一PRD、字段与权限字典、OpenAPI接口契约、页面线框、固定验收数据、需求追踪矩阵、审查修复记录。明确只需局部产物时，按实际范围交付。

重点写清页面和字段、操作条件、状态变化、并发/失败处理、版本与历史影响，以及可以判定的验收结果；不以功能列表和接口名称代替详细设计。

## 安装与调用

以Codex为例，在终端执行（已存在同名目录时先检查，不覆盖自己的修改）：

```bash
git clone https://github.com/fdehub/prd-chendian.git ~/.codex/skills/prd-chendian
```

其他支持SKILL.md的工具，将仓库置入该工具实际扫描的skills目录；目录名称保留`prd-chendian`。不同宿主对脚本、子目录和调用方式的支持可能不同，按其能力使用。

调用示例：

```text
使用 $prd-chendian，把这个项目的想法或现有资料整理成可实施、可验收的需求包，并审查修复跨模块缺口。
```

## 示例与约束

`SKILL.md`为入口，`references/`包含执行要求和完成门槛，`assets/synthetic-room-booking/`提供从零编写的虚构教学案例及正反示例。案例不包含真实客户需求、账号、截图、聊天或私有业务资料。

Python 3校验工具：

```bash
python scripts/validate_bundle.py assets/synthetic-room-booking
python assets/synthetic-room-booking/check_examples.py
```

校验只覆盖其声明的结构、引用和参考算例，不等于实际软件、数据库并发或生产接入已验收。该skill负责需求设计和文档交付，不自动开发或发布产品，不授权对外发送资料。

## 原版核验

需要Node.js，使用从作者可信发布渠道取得并独立核对的公钥指纹：

```bash
node scripts/verify_origin.mjs --trusted-fingerprint 913ffa698c0a3cee8fccced7614636b26baf11cf610364dc4aba164b5442df6c
```

`PROVENANCE.json`签名绑定发布文件；Git自身的根目录`.git`元数据不属于签名范围。其他新增、删除或修改的文件会导致原版核验失败。安装脚本产生的缓存请放在skill目录外，以保留原版文件集合。

指纹仅从待验包本身读取不能独立确认来源；请通过作者发布记录核对。签名可核验同一发布密钥和文件完整性，不阻止复制改名，也不证明现实身份。私钥不在仓库和分享包中。署名针对skill，不自动写入用户的需求文档。
