-- 燕云十六声关系图 · 数据库结构
-- MySQL 5.7+ / 8.0，字符集 utf8mb4
CREATE DATABASE IF NOT EXISTS yanyun DEFAULT CHARACTER SET utf8mb4;
USE yanyun;

CREATE TABLE IF NOT EXISTS `people` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(50) NOT NULL,
  `role` varchar(100) DEFAULT NULL,
  `bio` text,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `pid` varchar(20) DEFAULT NULL,
  `surname` varchar(10) DEFAULT NULL,
  `color` varchar(10) DEFAULT NULL,
  `x` int(11) DEFAULT NULL,
  `y` int(11) DEFAULT NULL,
  `mx` int(11) DEFAULT NULL,
  `my` int(11) DEFAULT NULL,
  `tag` varchar(60) DEFAULT NULL,
  `center` tinyint(1) NOT NULL DEFAULT '0',
  `avatar` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`),
  UNIQUE KEY `pid` (`pid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `relationships` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `from_id` int(11) NOT NULL,
  `to_id` int(11) NOT NULL,
  `type` enum('xiayuan','shitu','jieyi') NOT NULL,
  `note` varchar(200) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `label` varchar(50) DEFAULT NULL,
  `bend` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `from_id` (`from_id`),
  KEY `to_id` (`to_id`),
  CONSTRAINT `relationships_ibfk_1` FOREIGN KEY (`from_id`) REFERENCES `people` (`id`),
  CONSTRAINT `relationships_ibfk_2` FOREIGN KEY (`to_id`) REFERENCES `people` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
