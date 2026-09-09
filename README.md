# 123云盘文件上传工具

通过GitHub Action将STRM文件中的文件上传到123云盘。

## 功能特点

- 读取STRM文件中的直链URL
- 自动下载文件
- 通过WebDAV上传到123云盘
- 支持手动触发
- 支持自定义保存路径

## 使用方法

### 1. 配置GitHub Secrets

在GitHub仓库的 Settings > Secrets and variables > Actions 中添加以下 Secrets：

- `WEBDAV_ADDRESS`: WebDAV地址（如：https://webdav.123pan.com）
- `WEBDAV_USERNAME`: WebDAV用户名
- `WEBDAV_PASSWORD`: WebDAV密码

### 2. 上传STRM文件

将STRM文件放到仓库的 `strm_files` 文件夹中（或其他指定文件夹）。

### 3. 触发Action

1. 进入仓库的 Actions 页面
2. 选择 "Upload to 123Pan"
3. 点击 "Run workflow"
4. 输入参数：
   - `strm_folder`: STRM文件所在文件夹路径（默认：strm_files）
   - `upload_path`: 123云盘保存路径（默认：/）
5. 点击 "Run workflow"

## STRM文件格式

STRM文件是纯文本文件，内容为直链URL：

```
https://example.com/path/to/file.mp4
```

## 获取123云盘WebDAV信息

1. 登录123云盘网页版
2. 进入 设置 > WebDAV
3. 创建应用密码
4. 获取WebDAV地址、用户名和密码

## 注意事项

- STRM文件中的URL可能有过期时间，请及时处理
- 大文件下载可能需要较长时间
- 请确保WebDAV凭证的安全性
- 建议定期检查上传日志

## 错误处理

如果上传失败，请检查：
1. WebDAV凭证是否正确
2. STRM文件中的URL是否有效
3. 网络连接是否正常
4. 123云盘空间是否充足

## 许可证

MIT License