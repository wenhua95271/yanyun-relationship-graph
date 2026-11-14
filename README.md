# 燕云十六声关系图

一个用 Muse 做的燕云十六声人物关系一览图：搜名字或者点开角色，他所有的侠缘、师徒、结义关系一目了然。自带一个名单管理页，人物随手就能增删改，头像支持自己上传图片。

## 功能

- **收录名单**：按拼音首字母排序，带字母筛选（只显示有的字母），可搜索
- **关系图**：点开一个人，本人居中、相关的人围成一圈（放射布局），边是弧线；支持滚轮缩放、拖背景平移、点人聚焦
- **三种关系**：侠缘（红线）、师徒（带箭头，跟师傅头像色走）、结义（金色虚线，只画与选中人相连的）
- **管理页**：新增人物（名字 + 头像 + 关系）、编辑人物与关系、删除人物、上传/更换头像（圆形裁剪器）
- **关系规则**（服务端校验）：结义成组有传递性、每组上限 10 人；侠缘每人最多 5 个；每人最多 5 个徒弟

## 部署

### 需要准备

- 一台 Linux 服务器（1 核 1G 就够），装好 MySQL、Python 3、Nginx
- 一个域名（或直接用 IP 也行）

### 步骤

1. **建库建表**
   ```bash
   mysql -u root -p < schema.sql
   ```

2. **导入示例数据（可选）**
   ```bash
   mysql -u root -p < example-data.sql
   ```
   示例数据是 30 个人物，其中 10 人带头像（`yanyun/avatars/avatar1.jpg` ~ `avatar10.jpg`，古风武侠画风）。

3. **配数据库账号**
   复制 `db.conf.example` 为 `db.conf`，填上你的 MySQL 账号密码：
   ```ini
   [client]
   host=127.0.0.1
   user=yanyun
   password=你的密码
   database=yanyun
   ```
   建议建一个只有 `yanyun.*` 权限的专用账号，不要用 root。

4. **配管理页密码**
   生成一个 token 写进 `admin-token` 文件（600 权限）：
   ```bash
   openssl rand -hex 16 > /opt/yanyun/admin-token
   chmod 600 /opt/yanyun/admin-token
   ```

5. **起接口服务**
   `api.py` 是 Python 服务（只依赖 pymysql），用 systemd 常驻：
   ```bash
   # 见 yanyun-api.service.example，按你的路径改好后
   systemctl enable --now yanyun-api.service
   ```
   接口默认只绑 `127.0.0.1:39002`，不要对外暴露。

6. **配 Nginx**
   - 静态文件：`yanyun/` 目录放到网站根目录下
   - 反代接口：`location /yanyun/api/` 转到 `127.0.0.1:39002`
   - 具体配置见 `nginx.example.conf`

7. **打开管理页**，输密码，开始加人。

## 目录结构

```
yanyun/                  # 静态页面（放网站根目录）
  index.html             # 主页面：名单 + 关系图
  admin/
    index.html           # 管理页：增删改人物与关系、传头像
  avatars/               # 头像文件（avatar1.jpg ~ avatar10.jpg 为示例）
api.py                   # 后端接口（Python + pymysql）
schema.sql               # 建库建表
example-data.sql         # 30 人示例数据
db.conf.example          # 数据库配置模板
yanyun-api.service.example  # systemd 服务模板
nginx.example.conf       # Nginx 配置模板
```

## 附录：交给 AI 部署可以事半功倍

这个项目从第一版到上线，基本是交给 AI（Muse）去做的：页面、管理页、接口、数据库、关系规则、头像裁剪，都是按需求一版一版改出来的。人工只负责提需求、看效果、拍板。

如果你也想搭一个，不用从零写代码，把需求说清楚，让 AI 帮你写、帮你改、帮你部署，遇到问题让它自己查、自己修，你只管验收。事半功倍。
