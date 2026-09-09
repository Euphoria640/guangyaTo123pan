# 123云盘文件上传工具计划

## 需求分析
- 用户有STRM文件，包含直链URL
- 将STRM文件上传到GitHub仓库
- 手动触发GitHub Action
- 下载文件并通过WebDAV上传到123云盘
- 保存到指定文件夹

## 技术方案

### 1. GitHub Action工作流
- 使用 `workflow_dispatch` 支持手动触发
- 输入参数：
  - `strm_folder`: STRM文件所在文件夹路径
  - `upload_path`: 123云盘保存路径

### 2. 核心脚本
- 读取STRM文件夹中的所有.strm文件
- 提取每个文件中的URL
- 使用curl下载文件
- 使用WebDAV上传到123云盘

### 3. WebDAV上传
- 使用Python的 `webdavlib` 或 `requests` 库
- 支持断点续传
- 错误处理和重试机制

### 4. 安全配置
- 使用GitHub Secrets存储：
  - `WEBDAV_ADDRESS`: WebDAV地址
  - `WEBDAV_USERNAME`: 用户名
  - `WEBDAV_PASSWORD`: 密码

## 文件结构
```
.github/
  workflows/
    upload-to-123pan.yml
scripts/
  upload.py
requirements.txt
README.md
```

## 实现步骤

### 第一步：创建GitHub Action工作流
```yaml
name: Upload to 123Pan
on:
  workflow_dispatch:
    inputs:
      strm_folder:
        description: 'STRM文件所在文件夹路径'
        required: true
        default: 'strm_files'
      upload_path:
        description: '123云盘保存路径'
        required: true
        default: '/'
```

### 第二步：编写上传脚本
- 读取STRM文件
- 提取URL
- 下载文件
- 上传到WebDAV

### 第三步：配置GitHub Secrets
- 在仓库设置中添加 Secrets

## 测试方案
1. 创建测试STRM文件
2. 手动触发Action
3. 检查123云盘中的文件
4. 验证文件完整性

## 注意事项
- STRM文件中的URL可能有过期时间
- 大文件下载可能需要较长时间
- WebDAV上传可能有文件大小限制
- 需要处理网络错误和重试