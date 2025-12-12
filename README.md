# DeepSeek Cookie 保存工具

这个脚本使用 Playwright 打开 deepseek.com，等待你登录后自动保存 cookie。

## 安装依赖

```bash
pip install -r requirements.txt
playwright install chromium
```

## 使用方法

1. 运行脚本：
```bash
python save_cookie.py
```

2. 脚本会自动打开浏览器并导航到 deepseek.com

3. 在浏览器中完成登录操作

4. 登录完成后，回到终端按 Enter 键

5. Cookie 将保存到 `deepseek_cookies.json` 文件中

## 注意事项

- 确保已安装 Python 3.7+
- 首次运行需要安装 Playwright 浏览器：`playwright install chromium`
- Cookie 文件包含敏感信息，请妥善保管

