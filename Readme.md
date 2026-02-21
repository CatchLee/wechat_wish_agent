# 祝福生成器客户端代码简介
`src/` 目录核心模块：

- `main.py`：应用入口，初始化窗口并挂载各页面。
- `core/`
	- `call_llm.py`：封装 LLM 调用，按好友信息 + 聊天记录生成祝福。（由于没有许多模型的api key 目前并没有实现多种模型的代码，目前测试完成的只有 Gemini, Qwen, GLM. 可以根据自己需求选择需要的模型添加所需代码。）
	- `direct_decrypt.py`：使用密钥解密微信数据库到可读的 sqlite。
	- `search_users.py`：在联系人库中按关键词检索好友。
	- `get_friend_info.py`：读取单个好友的基础信息。
	- `get_chat_data.py`：按 wxid 拉取该好友的聊天记录。
	- `get_key.py`：辅助抓取/获取解密或模型所需的 key。
	- `config_manager.py`：集中管理 config.json 读取/写入。
	- `utils/`：数据模型与工具（消息、好友结构、常量、MD5 等）。
- `ui/`
	- `main_window.py`：主窗口与页面切换。
	- `friends.py`：好友列表页，支持搜索、展示详情与生成祝福。
	- `friends_detailed.py`：好友详情展示组件。
	- `decrypt.py`：一键解密页面，触发数据库解密流程。
	- `setting.py`：设置页，配置路径、密钥、模型名称与 API Key。

# 致谢
感谢项目https://github.com/hicccc77/WeFlow，https://github.com/ycccccccy/wx_key在关于wechat api key提取上的支持。https://www.tianmiao.fun/archives/WPsezuW6#63-%E8%81%8A%E5%A4%A9%E8%AE%B0%E5%BD%95-message 对微信数据库理解提供了帮助