-- 燕云十六声关系图 · 示例数据（30 人，10 人带头像）
-- 先建库建表（schema.sql），再导入本文件
USE yanyun;

-- 人物：前 10 人有头像（avatar1.jpg ~ avatar10.jpg，放在 yanyun/avatars/ 下）
INSERT INTO `people` (`id`, `name`, `role`, `surname`, `color`, `avatar`) VALUES
(1, '沈听澜', '白衣剑客', '沈', '#5b7fa6', 'avatar1.jpg'),
(2, '唐小棠', '红衣女侠', '唐', '#c65d5d', 'avatar2.jpg'),
(3, '陆九章', '青衫书生', '陆', '#5d8a6a', 'avatar3.jpg'),
(4, '苏清欢', '白衣医仙', '苏', '#7a9e7e', 'avatar4.jpg'),
(5, '萧策', '黑衣刀客', '萧', '#4a4a4a', 'avatar5.jpg'),
(6, '柳如烟', '绿衣琴师', '柳', '#6a9e7a', 'avatar6.jpg'),
(7, '玄真子', '灰袍道士', '玄', '#8a8a8a', 'avatar7.jpg'),
(8, '蓝凤凰', '蓝衣侠女', '蓝', '#5b7fb6', 'avatar8.jpg'),
(9, '叶小天', '少年英雄', '叶', '#b67a3a', 'avatar9.jpg'),
(10, '紫阳真人', '紫袍掌门', '紫', '#7a5ba6', 'avatar10.jpg'),
(11, '白展堂', NULL, '白', '#9e8a5a', NULL),
(12, '楚天舒', NULL, '楚', '#5b8aa6', NULL),
(13, '花弄影', NULL, '花', '#c67a9e', NULL),
(14, '李慕白', NULL, '李', '#6a7a9e', NULL),
(15, '阿星', NULL, '阿', '#b68a3a', NULL),
(16, '郭啸天', NULL, '郭', '#7a6a5a', NULL),
(17, '黄莺', NULL, '黄', '#c6a53a', NULL),
(18, '杨子轩', NULL, '杨', '#5a8a7a', NULL),
(19, '龙雪儿', NULL, '龙', '#9e6a8a', NULL),
(20, '令狐云', NULL, '令', '#8a7a6a', NULL),
(21, '任青青', NULL, '任', '#7a9e6a', NULL),
(22, '岳飞鸿', NULL, '岳', '#6a8a9e', NULL),
(23, '风无痕', NULL, '风', '#9e9e5a', NULL),
(24, '段天涯', NULL, '段', '#5a7a9e', NULL),
(25, '乔天放', NULL, '乔', '#8a5a7a', NULL),
(26, '虚云', NULL, '虚', '#7a7a7a', NULL),
(27, '慕容轩', NULL, '慕', '#6a5a9e', NULL),
(28, '王小蝶', NULL, '王', '#c68a6a', NULL),
(29, '鸠无言', NULL, '鸠', '#5a6a8a', NULL),
(30, '丁一凡', NULL, '丁', '#9a6a4a', NULL);

-- 关系：侠缘 8 对、师徒 12 条、结义 3 组
-- 侠缘
INSERT INTO `relationships` (`from_id`, `to_id`, `type`) VALUES
(1, 2, 'xiayuan'), (3, 4, 'xiayuan'), (5, 6, 'xiayuan'), (9, 8, 'xiayuan'),
(11, 17, 'xiayuan'), (12, 13, 'xiayuan'), (14, 19, 'xiayuan'), (16, 21, 'xiayuan');
-- 师徒
INSERT INTO `relationships` (`from_id`, `to_id`, `type`) VALUES
(10, 1, 'shitu'), (10, 5, 'shitu'), (7, 3, 'shitu'), (7, 9, 'shitu'),
(1, 15, 'shitu'), (2, 8, 'shitu'), (5, 30, 'shitu'), (6, 28, 'shitu'),
(22, 18, 'shitu'), (23, 24, 'shitu'), (25, 26, 'shitu'), (27, 29, 'shitu');
-- 结义（组内两两互连）
INSERT INTO `relationships` (`from_id`, `to_id`, `type`) VALUES
(1, 5, 'jieyi'), (1, 3, 'jieyi'), (5, 3, 'jieyi'),
(2, 4, 'jieyi'), (2, 6, 'jieyi'), (2, 8, 'jieyi'),
(4, 6, 'jieyi'), (4, 8, 'jieyi'), (6, 8, 'jieyi'),
(11, 12, 'jieyi'), (11, 14, 'jieyi'), (12, 14, 'jieyi');
