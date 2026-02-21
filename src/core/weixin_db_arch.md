# 数据库结构
wx_idxxx/db_storage下结构

db_storage
├─bizchat
│      bizchat.db
│
├─contact
│      contact.db
│      contact_fts.db
│
├─emoticon
│      emoticon.db # 表情包
│
├─favorite
│      favorite.db
│      favorite_fts.db
│
├─general
│      general.db
│
├─hardlink
│      hardlink.db
│
├─head_image
│      head_image.db # 头像信息
│
├─message
│      biz_message_0.db
│      biz_message_0.kvdb
│      biz_message_1.db
│      biz_message_1.kvdb
│      biz_message_2.db
│      biz_message_2.kvdb
│      media_0.db
│      media_0.kvdb
│      message_0.db
│      message_0.kvdb
│      message_1.db
│      message_1.kvdb
│      message_2.db
│      message_2.kvdb
│      message_fts.db
│      message_resource.db
│
├─MMKV # 腾讯加速数据库访问使用的文件
│  
├─session
│      session.db # 会话信息
└─sns
        sns.db # TODO 未知

# 分析
## 上面未包含的文件
-wal,-shm是sqlite数据库的临时文件；
-first.material 等文件，用来监控数据库变化的信息

## 解密数据库
目前利用decipher.py 可以分析session.db了，目前利用的是WeFlow中提供的.dll文件

direct_decrypt.py 基于python库直接解密数据库，得到解密后的sqlite文件，已验证列表
- head_image.db
包含 username md5 image_buffer update_time 字段，image_buffer是实际的头像数据（DB browser显示为Blob数据）；username为wxid_xxx。
- session.db

- emoticon.db 主要包含的值如下
kNonStoreEmotionTable（自己收藏的表情包）
type	INTEGER	
md5	TEXT	表情包的md5，可以从message数据库里获取
cdn_url	TEXT	表情包url（可以直接引用，直接获得对应的数据）
微信表情包合集 / 其它，还有几个表没有解析出来

- bizchat.db 主要包含企业微信的基本信息
- biz_message.db 主要包含企业微信的消息信息

- contact.db
contact Table 包含微信好友（或者是群聊、公众号），头像，昵称，备注(remark)，描述， TODO Extra Buffer是什么意思？
username的命名：@chatroom 结尾是群聊；wxid是好友，gh是公众号
包含群聊的名称，群聊的成员列表（chatroom_member），群聊的公告（chatroom_info_detail）等信息

- favourite.db TODO 猜测是收藏的消息
- hardlink.db TODO 搞不明白
- general.db 一些杂七杂八的数据，比如最近转发列表 / 最近搜索
- media_0.db Voice Info表： chat_name_id local_id svr_id 根据name2id表转化为weixin_id. 然后还有 voice_data；前缀字节 02，核心签名 23 21 53 49 4c 4b 5f 56 33 0a 表示：#!SILK_V3
- message_0.db https://www.tianmiao.fun/archives/WPsezuW6#63-%E8%81%8A%E5%A4%A9%E8%AE%B0%E5%BD%95-message Msg_{md5(wxid)} 得到和一个人的聊天记录表
消息的实际内容，local_type是1时message_content是文本数据，其他类型都是 Zstandard 压缩后的xml二进制数据（一般是在有引用别的文件/图片的时候出现）