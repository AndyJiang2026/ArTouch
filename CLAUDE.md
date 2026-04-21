# 项目编码规范

## 🤖 AI辅助编程政策

本项目采用AI辅助编程，所有AI生成的代码必须遵循以下规范。

---

## 1. 代码风格

### 1.1 Python
- **格式化**: 使用 `black`
- **行长度**: 最大 120 字符
- **缩进**: 4 空格
- **类型注解**: 必须使用类型注解（公共API）

```python
# ✅ 正确
def calculate_total(amount: float, tax_rate: float) -> float:
    return amount * (1 + tax_rate)

# ❌ 错误
def calculate_total(amount, tax_rate):
    return amount * (1 + tax_rate)
```

### 1.2 JavaScript/TypeScript
- **格式化**: 使用 `prettier`
- **缩进**: 2 空格
- **类型**: 必须使用 TypeScript 类型

---

## 2. AI生成代码标记

所有AI辅助生成的代码必须包含以下标记：

```python
# AI-ASSISTED: Yes
# AI-TOOL: Claude Code / GitHub Copilot / Codex
# PROMPT: <简要提示词>
# DATE: YYYY-MM-DD
# ENGINEER: <工程师姓名>
# RISK-LEVEL: [P0/P1/P2/P3]
```

### 示例

```python
# AI-ASSISTED: Yes
# AI-TOOL: Claude Code
# PROMPT: 生成用户登录验证函数，包含密码哈希验证
# DATE: 2026-04-18
# ENGINEER: 张三
# RISK-LEVEL: P1

def verify_user_login(username: str, password: str) -> bool:
    """验证用户登录"""
    # 实现代码
    pass
```

---

## 3. 风险等级定义

| 等级 | 说明 | AI限制 | 审查要求 |
|------|------|--------|----------|
| **P0** | 安全/金融/认证 | ❌ 禁止 | 100% 高级工程师 |
| **P1** | 核心业务逻辑 | ⚠️ 仅参考 | 100% 工程师 |
| **P2** | 普通业务逻辑 | ✅ AI辅助 | 50% 抽样 |
| **P3** | 样板/文档/测试 | ✅ AI生成 | 10% 抽查 |

---

## 4. 代码审查清单

### AI生成代码必须检查：

- [ ] 代码逻辑正确性
- [ ] 类型注解完整性
- [ ] 错误处理完善
- [ ] 安全漏洞检测
- [ ] 性能考虑
- [ ] 测试覆盖充分

### 安全检查（P0/P1必须）：

- [ ] 无SQL注入风险
- [ ] 无XSS风险
- [ ] 无敏感信息泄露
- [ ] 权限控制正确
- [ ] 加密算法正确使用

---

## 5. 测试要求

| 风险等级 | 覆盖率要求 | 测试类型 |
|----------|------------|----------|
| P0 | ≥95% | 单元+集成+E2E |
| P1 | ≥85% | 单元+集成 |
| P2 | ≥80% | 单元 |
| P3 | ≥70% | 基本测试 |

---

## 6. 提交规范

### Commit Message 格式

```
<type>(<scope>): <subject>

Types:
  feat:     新功能
  fix:      缺陷修复
  docs:     文档更新
  style:    代码格式
  refactor: 重构
  perf:     性能优化
  test:     测试
  security: 安全相关

Examples:
  feat(auth): 实现用户注册功能
  fix(api): 修复订单查询边界问题
  security(auth): 添加密码强度验证
```

### PR描述必须包含

1. 变更描述
2. 风险等级标记
3. AI辅助说明（如有）
4. 测试结果
5. 审查记录

---

## 7. 禁止事项

### ❌ P0禁止

- 使用 `eval()` 或 `exec()`
- 硬编码密码/密钥
- 直接拼接SQL
- 使用不安全的序列化（pickle）
- AI生成认证/加密逻辑

### ❌ 一般禁止

- 代码复杂度超过 15
- 函数超过 50 行
- 类超过 500 行
- 未经测试的AI代码合并

---

## 8. 工具配置

```bash
# 代码格式化
black .

# 代码检查
ruff check .
mypy .

# 运行测试
pytest --cov=. --cov-report=term-missing

# 安全扫描
bandit -r .
safety check
```

---

## 9. AI使用建议

### ✅ 推荐场景

- 样板代码生成
- 测试用例生成
- 文档生成
- 代码重构建议
- 正则表达式
- 简单算法实现

### ⚠️ 谨慎场景

- 复杂业务逻辑
- 数据库查询
- 性能优化
- API设计

### ❌ 禁止场景

- 安全认证逻辑
- 金融交易
- 加密实现
- 权限控制

---

## 10. 持续改进

- 每月审查AI使用效率指标
- 每季度更新编码规范
- 安全事件后立即复盘

---

**版本**: v1.0  
**更新**: 2026-04-18  
**维护人**: 工程团队
