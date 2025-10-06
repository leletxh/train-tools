# 训练工具认证系统说明

## 概述

训练工具现已集成完整的用户认证系统，实现了"约定大于配置"的设计理念。系统在启动时自动生成管理员密码，提供完整的用户管理功能。

## 主要特性

### 🔐 自动化认证配置
- **自动生成admin密码**：首次启动时自动生成安全的随机密码
- **环境变量支持**：可通过 `ADMIN_PASSWORD` 环境变量自定义管理员密码
- **会话管理**：基于Cookie的会话系统，24小时自动过期

### 👥 用户管理
- **管理员账户**：用户名固定为 `admin`，具有完整管理权限
- **普通用户**：由管理员创建，用户名和密码自动生成
- **权限控制**：只有登录用户才能访问系统功能

### 🛡️ 安全保护
- **全面路由保护**：所有页面和API都需要登录认证
- **密码哈希**：使用SHA256对密码进行哈希存储
- **会话安全**：HttpOnly Cookie，防止XSS攻击

## 使用指南

### 1. 启动应用

```bash
python main.py
```

启动时会显示生成的admin密码：
```
生成的admin密码: -zYTcsSGkDjX-C_84dTUQw
请保存此密码，或通过环境变量ADMIN_PASSWORD设置自定义密码
```

### 2. 自定义admin密码

通过环境变量设置：

**Windows:**
```cmd
set ADMIN_PASSWORD=your_custom_password
python main.py
```

**Linux/Mac:**
```bash
export ADMIN_PASSWORD=your_custom_password
python main.py
```

### 3. 登录系统

1. 访问 `http://localhost:5000`
2. 自动跳转到登录页面
3. 使用以下凭据登录：
   - **用户名**: `admin`
   - **密码**: 启动时显示的密码或自定义密码

### 4. 管理用户

管理员登录后可以：

1. **访问管理面板**：点击页面右上角的"管理面板"
2. **创建新用户**：点击"创建新用户"按钮
3. **查看用户列表**：查看所有用户的创建时间和登录状态
4. **删除用户**：删除不需要的普通用户（不能删除admin）

### 5. 普通用户使用

1. 管理员创建用户后会显示用户名和密码
2. 普通用户使用生成的凭据登录
3. 登录后可以使用所有训练工具功能

## 技术实现

### 文件结构

```
app/
├── models/
│   ├── __init__.py
│   └── user.py              # 用户模型和管理器
├── routes/
│   ├── auth_routes.py       # 认证相关路由
│   └── ...
├── auth.py                  # 认证中间件和装饰器
└── ...

templates/
├── login.html               # 登录页面
├── admin.html               # 管理员面板
└── ...
```

### 核心组件

1. **UserManager**: 用户数据管理，支持JSON文件存储
2. **认证装饰器**: `@login_required` 和 `@admin_required`
3. **会话管理**: 基于内存的会话存储，支持过期清理
4. **密码安全**: SHA256哈希 + 随机盐值

### 数据存储

- **用户数据**: 存储在 `users.json` 文件中
- **会话数据**: 存储在内存中，重启后清空
- **密码**: 经过SHA256哈希处理，不存储明文

## 安全注意事项

### ⚠️ 重要提醒

1. **保存admin密码**: 首次启动时务必保存显示的admin密码
2. **生产环境**: 建议使用环境变量设置强密码
3. **HTTPS**: 生产环境建议使用HTTPS协议
4. **备份**: 定期备份 `users.json` 文件

### 🔒 安全特性

- 密码哈希存储，不保存明文
- 会话自动过期（24小时）
- HttpOnly Cookie防止XSS
- 所有API都需要认证
- 管理员权限分离

## 故障排除

### 常见问题

**Q: 忘记了admin密码怎么办？**
A: 删除 `users.json` 文件并重启应用，系统会重新生成admin密码。

**Q: 如何重置所有用户？**
A: 删除 `users.json` 文件，重启应用即可。

**Q: 普通用户可以修改密码吗？**
A: 当前版本不支持用户自行修改密码，这是"约定大于配置"的设计理念。

**Q: 如何批量创建用户？**
A: 可以通过API接口 `POST /auth/api/users` 批量创建。

### 日志调试

查看应用日志文件 `app.log` 获取详细的认证信息：

```bash
tail -f app.log | grep -E "(登录|认证|用户)"
```

## API接口

### 认证相关API

- `POST /auth/login` - 用户登录
- `POST /auth/logout` - 用户登出
- `GET /auth/api/user/info` - 获取当前用户信息
- `GET /auth/api/users` - 获取用户列表（仅管理员）
- `POST /auth/api/users` - 创建新用户（仅管理员）
- `DELETE /auth/api/users/<username>` - 删除用户（仅管理员）

### 示例请求

```javascript
// 获取当前用户信息
fetch('/auth/api/user/info')
  .then(response => response.json())
  .then(data => console.log(data));

// 创建新用户（管理员）
fetch('/auth/api/users', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  }
})
.then(response => response.json())
.then(data => console.log(data));
```

## 更新日志

### v1.0.0 (当前版本)
- ✅ 实现基础认证系统
- ✅ 自动生成admin密码
- ✅ 用户管理界面
- ✅ 全面路由保护
- ✅ 会话管理
- ✅ 管理员面板

### 未来计划
- 🔄 用户密码修改功能
- 🔄 用户角色权限细分
- 🔄 登录日志记录
- 🔄 密码强度策略
- 🔄 双因素认证支持

---

如有问题或建议，请查看应用日志或联系系统管理员。
