# GitHub Actions 自动构建EXE指南

## 🚀 快速开始

### 方式一：自动触发构建
```bash
# 推送到master分支自动构建
git push origin master

# 创建版本标签触发发布
git tag v1.0.0
git push origin v1.0.0
```

### 方式二：手动触发构建
1. 访问 GitHub 仓库页面
2. 点击 **Actions** 标签
3. 选择 **Build Windows EXE** 工作流
4. 点击 **Run workflow** 按钮
5. 选择分支，点击 **Run workflow**

## 📦 构建产物

### 下载构建结果
1. 在 **Actions** 页面找到完成的构建
2. 点击构建任务进入详情页
3. 在 **Artifacts** 部分下载 EXE 文件

### 发布版本（推荐）
```bash
# 创建版本标签进行正式发布
git tag v1.0.0
git push origin v1.0.0
```
- 自动创建 GitHub Release
- EXE文件直接附加到发布页面
- 用户可直接下载使用

## 🔧 构建配置

### 工作流触发条件
- ✅ `push` 到 `master` 分支
- ✅ 创建以 `v` 开头的标签 (如 v1.0.0)
- ✅ `pull_request` 到 `master` 分支
- ✅ 手动触发 (`workflow_dispatch`)

### 构建环境
- **系统**: Windows Latest
- **Python**: 3.11
- **工具**: PyInstaller + auto-py-to-exe

### 构建步骤
1. **环境准备**: 安装 Python 和依赖
2. **缓存优化**: 缓存 pip 依赖提高速度
3. **清理构建**: 删除旧的构建文件
4. **EXE打包**: 使用 app.spec 配置打包
5. **结果验证**: 检查 EXE 文件是否成功生成
6. **上传产物**: 保存 EXE 文件供下载

## 📁 文件结构

```
.github/workflows/
├── build-exe.yml          # GitHub Actions 工作流配置
├── app.spec               # PyInstaller 打包配置
├── build_exe.bat          # 本地 Windows 打包脚本
├── requirements.txt       # Python 依赖清单
└── README_BUILD.md        # 构建说明文档
```

## 🎯 版本发布流程

### 1. 准备发布
```bash
# 确保代码已提交并测试通过
git status
git add .
git commit -m "feat: 准备 v1.0.0 发布"
git push origin master
```

### 2. 创建版本标签
```bash
# 创建版本标签
git tag -a v1.0.0 -m "v1.0.0: 首个正式版本"
git push origin v1.0.0
```

### 3. 自动构建发布
- GitHub Actions 自动检测到标签推送
- 启动 Windows 环境构建 EXE
- 创建 GitHub Release 页面
- 自动上传 EXE 文件

### 4. 发布验证
1. 检查 **Actions** 页面构建状态
2. 访问 **Releases** 页面确认发布
3. 下载测试 EXE 文件功能

## ⚙️ 本地构建 (备用)

如需在本地 Windows 环境构建：

```batch
# Windows 环境下运行
build_exe.bat
```

本地构建要求：
- Windows 10/11
- Python 3.9+
- 完整的项目依赖

## 🔍 故障排查

### 构建失败
1. 检查 **Actions** 页面的错误日志
2. 验证 `requirements.txt` 依赖完整性
3. 确认 `app.spec` 配置正确性

### EXE 运行问题
1. 检查构建的 EXE 文件大小
2. 在目标机器测试运行
3. 查看系统事件日志错误信息

### 发布问题
1. 确认标签格式为 `v*.*.*`
2. 检查仓库的 Actions 权限设置
3. 验证 `GITHUB_TOKEN` 权限

## 💡 最佳实践

- **版本管理**: 使用语义版本号 (v1.0.0, v1.1.0)
- **构建缓存**: 利用依赖缓存加速构建
- **测试验证**: 每次发布前充分测试
- **文档更新**: 同步更新 CHANGELOG 和文档

---

**📝 注意**: 初次设置后，每次代码更新推送都会自动构建，创建版本标签会自动发布。