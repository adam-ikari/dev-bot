# 使用 AI 创建 Spec

SDD CLI 提供了 `ai-spec` 命令，使用 AI 自动生成规格说明文档。

## 基本用法

```bash
# 创建功能 spec
sdd ai-spec user-authentication --type feature --desc "用户认证功能，包含登录、注册和密码重置"

# 创建 API spec
sdd ai-spec user-api --type api --desc "用户管理 REST API"

# 创建组件 spec
sdd ai-spec button --type component --desc "通用按钮组件"

# 创建服务 spec
sdd ai-spec email --type service --desc "邮件发送服务"

# 指定 AI 工具
sdd ai-spec feature --ai-tool iflow

# 指定输出目录
sdd ai-spec feature --output ./specs
```

## 命令参数

- `spec_name` - spec 文件名（必需）
- `--type` / `-t` - spec 类型：feature/api/component/service（默认：feature）
- `--desc` / `--description` - spec 描述，帮助 AI 更好地生成内容
- `--ai-tool` - AI 工具命令（默认：iflow）
- `--output` / `-o` - 输出目录（默认：specs/）

## AI 工具配置

### 使用 iflow（默认）

```bash
sdd ai-spec feature --desc "功能描述"
```

### 使用其他 AI 工具

```bash
# 使用 claude
sdd ai-spec feature --ai-tool claude

# 使用 openai
sdd ai-spec feature --ai-tool openai
```

确保 AI 工具已安装并在 PATH 中可用。

## 工作流程

1. **描述需求**: 使用 `--desc` 参数提供清晰的功能描述
2. **AI 生成**: CLI 调用 AI 工具生成 spec 内容
3. **自动保存**: 生成的 spec 自动保存为 JSON 文件
4. **验证验证**: 使用 `sdd validate` 验证生成的 spec

## 提示技巧

### Feature Spec

```bash
# 提供详细的用户场景
sdd ai-spec shopping-cart \
  --type feature \
  --desc "电商购物车功能，支持添加/删除商品、修改数量、计算总价、应用优惠券"

# 包含用户角色
sdd ai-spec admin-dashboard \
  --type feature \
  --desc "管理员仪表板，用于查看用户统计、订单管理、系统监控"
```

### API Spec

```bash
# 描述资源关系
sdd ai-spec product-api \
  --type api \
  --desc "产品管理 API，包含产品 CRUD 操作、分类管理、库存查询"

# 包含认证信息
sdd ai-spec payment-api \
  --type api \
  --desc "支付处理 API，支持多种支付方式、退款、交易查询，需要 JWT 认证"
```

### Component Spec

```bash
# 描述交互行为
sdd ai-spec data-table \
  --type component \
  --desc "数据表格组件，支持排序、筛选、分页、行选择、导出"

# 描述样式变体
sdd ai-spec alert \
  --type component \
  --desc "警告提示组件，包含 success/error/warning/info 四种类型，支持关闭按钮"
```

### Service Spec

```bash
# 描述接口和依赖
sdd ai-spec cache-service \
  --type service \
  --desc "缓存服务，支持 Redis/Memcached，提供 get/set/delete 操作和过期时间管理"

# 包含配置项
sdd ai-spec notification-service \
  --type service \
  --desc "通知服务，支持邮件/短信/推送，包含模板管理、队列、重试机制"
```

## 示例

### 创建用户认证功能 spec

```bash
sdd ai-spec user-authentication \
  --type feature \
  --desc "用户认证功能，支持邮箱密码登录、Google OAuth、邮箱验证、密码重置"
```

生成的 spec 包含：
- 需求列表（登录、注册、验证、重置）
- 用户故事
- 验收标准

### 创建 REST API spec

```bash
sdd ai-spec blog-api \
  --type api \
  --desc "博客 API，管理文章、分类、标签、评论，支持分页、搜索、富文本编辑"
```

生成的 spec 包含：
- API 端点定义
- 请求/响应模型
- 认证方式

### 创建 UI 组件 spec

```bash
sdd ai-spec form-input \
  --type component \
  --desc "表单输入组件，支持文本、数字、日期、邮箱等类型，包含验证和错误提示"
```

生成的 spec 包含：
- 组件属性
- 事件定义
- 使用示例

## 后续步骤

AI 生成 spec 后：

1. **验证格式**
   ```bash
   sdd validate specs/user-authentication.json
   ```

2. **完善内容** - 手动编辑 spec 补充细节

3. **生成代码** - 使用 AI 工具基于 spec 生成代码

4. **迭代优化** - 根据实际需求调整 spec

## 故障排除

### AI 工具未找到

```
✗ AI 工具调用失败: [Errno 2] No such file or directory: 'iflow'
```

解决方案：
```bash
# 安装 AI 工具
pip install iflow

# 或指定其他工具
sdd ai-spec feature --ai-tool claude
```

### JSON 解析失败

如果 AI 返回的内容无法解析为 JSON，CLI 会创建一个空的 spec 模板，然后可以手动编辑。

### 超时

AI 调用默认超时 120 秒，可以修改代码中的 `timeout` 参数。

## 最佳实践

1. **描述要具体** - 详细的描述能生成更准确的 spec
2. **分步创建** - 复杂功能可以拆分为多个小的 spec
3. **迭代完善** - 先生成基础结构，再逐步补充细节
4. **验证格式** - 生成后立即验证格式正确性
5. **版本控制** - 将 spec 文件纳入 Git 版本控制