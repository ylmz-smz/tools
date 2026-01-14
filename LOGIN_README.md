# 12306 登录功能使用说明

## 功能概述

本项目已添加12306账号登录功能，支持在查询车票时保持登录状态。

## 配置方法

### 1. 在 config.yaml 中配置账号信息

打开 `config.yaml` 文件，找到 `login_config` 部分：

```yaml
# 12306 账号登录配置（可选，如果查询需要登录则填写）
login_config:
  enabled: true           # 改为 true 启用登录
  username: '你的手机号'   # 填写你的12306账号（手机号或邮箱）
  password: '你的密码'     # 填写你的12306密码
```

### 2. 配置示例

```yaml
login_config:
  enabled: true
  username: '13800138000'
  password: 'your_password_here'
```

## 使用方法

### 方式一：使用配置文件（推荐）

1. 按上述方法配置好 `config.yaml`
2. 运行程序：
   ```bash
   python train_ticket_monitor.py
   ```
3. 程序会自动尝试登录，然后进行查询

### 方式二：不使用登录

如果不需要登录（部分查询可能无需登录），可以将 `enabled` 设置为 `false`：

```yaml
login_config:
  enabled: false
  username: ''
  password: ''
```

## 重要说明

### ⚠️ 关于验证码

12306的登录流程较为复杂，通常需要：
- 滑动验证码
- 图形验证码
- 短信验证码

当前实现会尝试基本登录，但可能因验证码而失败。

### 🔒 安全建议

1. **不要将包含密码的配置文件上传到公共代码仓库**
2. 建议在 `.gitignore` 中添加：
   ```
   config.yaml
   ```
3. 可以创建一个 `config.example.yaml` 作为模板

### 🔄 替代方案

如果自动登录失败，可以尝试以下方案：

#### 方案一：浏览器登录 + Cookie导出
1. 在浏览器中登录12306并保持登录状态
2. 使用浏览器扩展导出Cookie
3. 将Cookie导入到程序中（需要额外开发）

#### 方案二：暂时禁用登录
部分查询可能无需登录即可进行：
```yaml
login_config:
  enabled: false
```

## 示例配置文件

完整的 `config.yaml` 示例：

```yaml
# 12306 账号登录配置
login_config:
  enabled: true
  username: '13800138000'
  password: 'your_password'

# 查询参数配置
query_params:
  from_station: 北京
  to_station: 上海
  train_date: '2026-01-20'
  train_codes:
    - G1
    - G3
  seat_types:
    - 二等座
    - 一等座
  interval: 60
```

## 故障排除

### 登录失败
- 检查账号密码是否正确
- 检查网络连接是否正常
- 查看是否需要验证码验证

### 提示需要验证码
当前版本暂不支持自动处理验证码，建议：
1. 暂时禁用登录功能
2. 或等待后续版本更新

### 查询仍然失败
即使登录失败，程序也会尝试继续查询，因为：
- 部分查询接口可能无需登录
- 可以先尝试是否能正常查询

## 隐私保护

配置文件中的密码是明文存储的，请注意：
1. 不要分享你的配置文件
2. 不要将配置文件提交到 Git 仓库
3. 建议定期更改密码

## 更新日志

### 2026-01-14
- ✅ 添加登录配置支持
- ✅ 实现基本登录功能
- ✅ 添加登录状态检查
- ⚠️ 暂不支持验证码自动处理
