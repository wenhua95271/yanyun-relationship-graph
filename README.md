# 燕云十六声关系图

一个用 Muse 做的燕云十六声人物关系一览图：搜名字或者点开角色，他所有的侠缘、师徒、结义关系一目了然。自带一个名单管理页，人物随手就能增删改，头像支持自己上传图片。

## 功能

- **收录名单**：按拼音首字母排序，带字母筛选（只显示有的字母），可搜索
- **关系图**：点开一个人，本人居中、相关的人围成一圈（放射布局），边是直线；支持滚轮缩放、拖背景平移、点人聚焦
- **三种关系**：侠缘（红线）、师徒（带箭头，跟师傅头像色走）、结义（金色虚线，只画与选中人相连的）
- **管理页**：新增人物（名字 + 头像 + 关系）、编辑人物与关系、删除人物、上传/更换头像（圆形裁剪器）
- **关系规则**（服务端校验）：结义成组有传递性、每组上限 10 人；侠缘每人最多 5 个；每人最多 5 个徒弟

## 使用方法

部署好打开 `https://你的域名/yanyun/` 就能用：

- **找人**：顶部搜索框输名字，或直接在名单里点一个人
- **看关系**：点开一个人，他本人居中，侠缘、师徒、结义都围在他周围；点任意一个人切换到他的关系图
- **缩放平移**：滚轮缩放，拖背景平移，点缩放条里的「全图」回到完整视图
- **管人**：打开 `https://你的域名/yanyun/admin/`，输管理页密码（见部署第 5 步），新增人物、编辑关系、上传头像都在这里

## 部署

### 需要准备

- 一台 Linux 服务器（1 核 1G 就够），装好 MySQL、Python 3、Nginx
- 一个域名（或直接用 IP 也行）
- **注意**：前端固定请求 `/yanyun/api/data`，所以必须部署在域名根目录下的 `/yanyun/` 子路径，换别的路径会取不到数据

### 步骤

1. **建库建表**
   ```bash
   mysql -u root -p < schema.sql
   ```
   `schema.sql` 里自带建库（`yanyun`），不用先手动建库。

2. **导入示例数据（可选）**
   ```bash
   mysql -u root -p < example-data.sql
   ```
   示例数据是 30 个人物，其中 10 人带头像（`yanyun/avatars/avatar1.jpg` ~ `avatar10.jpg`，古风武侠画风）。

3. **建数据库专用账号**
   不要用 root 跑接口，建一个只有 `yanyun.*` 权限的账号：
   ```sql
   CREATE USER 'yanyun'@'127.0.0.1' IDENTIFIED BY '你的密码';
   GRANT ALL PRIVILEGES ON yanyun.* TO 'yanyun'@'127.0.0.1';
   FLUSH PRIVILEGES;
   ```

4. **放接口文件、配数据库连接**
   ```bash
   mkdir -p /opt/yanyun
   cp api.py /opt/yanyun/api.py
   cp db.conf.example /opt/yanyun/db.conf
   chmod 600 /opt/yanyun/db.conf
   ```
   再编辑 `/opt/yanyun/db.conf`，把账号密码填成第 3 步建好的：
   ```ini
   [client]
   host=127.0.0.1
   user=yanyun
   password=你的密码
   database=yanyun
   ```

5. **装依赖、配管理页密码**
   ```bash
   pip install pymysql
   openssl rand -hex 16 > /opt/yanyun/admin-token
   chmod 600 /opt/yanyun/admin-token
   ```
   Debian/Ubuntu 上 pip 若提示 externally-managed，改用 `apt install python3-pymysql`。
   管理页的登录密码就是这个 token 文件里的内容，查看：
   ```bash
   cat /opt/yanyun/admin-token
   ```

6. **起接口服务**
   `api.py` 是 Python 服务（只依赖 pymysql），用 systemd 常驻：
   ```bash
   cp yanyun-api.service.example /etc/systemd/system/yanyun-api.service
   systemctl daemon-reload
   systemctl enable --now yanyun-api.service
   ```
   接口默认只绑 `127.0.0.1:39002`，不要对外暴露。

7. **配 Nginx**
   - 静态文件：把 `yanyun/` 目录放到网站根目录下（即访问 `https://你的域名/yanyun/` 能打开主页）
   - 反代接口：`location /yanyun/api/` 转到 `127.0.0.1:39002`
   - 具体配置见 `nginx.example.conf`

8. **头像目录给写权限**
   上传头像要往 `yanyun/avatars/` 里写文件，api.py 运行的用户须对这个目录有写权限。示例服务以 root 运行，直接可用；换别的用户跑时记得 `chown` 或 `chmod`。

9. **打开管理页**，输密码（第 5 步查到的 token），开始加人。

> 排错：接口没起来时页面会回退显示内置示例数据，不是数据库坏了，先查接口服务状态（`systemctl status yanyun-api`）。

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
