CREATE DATABASE IF NOT EXISTS grom_config DEFAULT CHARSET utf8 COLLATE utf8_general_ci;

CREATE TABLE IF NOT EXISTS `grom_config`.`general`(
    `id`                               INT AUTO_INCREMENT,
    `name`                             VARCHAR(100) NOT NULL,
    `env_id`                           INT NOT NULL,
    `belongto`                         VARCHAR(256),
    `is_delete`                        BOOL DEFAULT FALSE,
    `meta`                             JSON,
    `create_time`                      TIMESTAMP(6),
    `creator`                          VARCHAR(64),
    PRIMARY KEY (`id`),
    CONSTRAINT col_unique UNIQUE (`name`, `env_id`, `belongto`)
)ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE IF NOT EXISTS `grom_config`.`general_version`(
    `id`                               INT AUTO_INCREMENT,
    `general_id`                       INT NOT NULL,
    `name`                             VARCHAR(100) NOT NULL,
    `content`                          Text,
    `status`                           VARCHAR(255) NOT NULL,
    `publish_time`                     TIMESTAMP(6) DEFAULT NULL,
    `publisher`                        VARCHAR(50) DEFAULT NULL,
    `update_time`                      TIMESTAMP(6) NOT NULL,
    `modifier`                         VARCHAR(50) NOT NULL,
    INDEX (`general_id`),
    INDEX (`update_time`),
    PRIMARY KEY (`id`)
)ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE IF NOT EXISTS `grom_config`.`general_version_log`(
    `id`                               INT AUTO_INCREMENT,
    `general_id`                       INT NOT NULL,
    `general_version_id`               INT NOT NULL,
    `name`                             VARCHAR(100) NOT NULL,
    `info`                             Text,
    `status`                           VARCHAR(255) NOT NULL,
    `update_time`                      TIMESTAMP(6) NOT NULL,
    `modifier`                         VARCHAR(50) NOT NULL,
    INDEX (`general_id`),
    INDEX (`general_version_id`),
    PRIMARY KEY (`id`)
)ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE IF NOT EXISTS `grom_config`.`env`(
    `id`                               INT AUTO_INCREMENT,
    `name`                             VARCHAR(100) NOT NULL,
    `prefix`                           VARCHAR(256),
    `notification`                     VARCHAR(256),
    `notification_token`               VARCHAR(256),
    `is_callback`                      BOOL DEFAULT FALSE,
    `callback_token`                   VARCHAR(256),
    `update_time`                      TIMESTAMP(6),
    `modifier`                         VARCHAR(64),
    PRIMARY KEY (`id`),
    CONSTRAINT col_unique UNIQUE (`name`, `prefix`)
)ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE IF NOT EXISTS `grom_config`.`public_item`(
    `id`                               INT AUTO_INCREMENT,
    `env_id`                           INT NOT NULL,
    `k`                                VARCHAR(255) NOT NULL,
    `meta`                             JSON,
    `create_time`                      TIMESTAMP(6) NOT NULL,
    `creator`                          VARCHAR(50) NOT NULL,
    PRIMARY KEY (`id`),
    CONSTRAINT col_unique UNIQUE (`env_id`, `k`)
)ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE IF NOT EXISTS `grom_config`.`public_item_version`(
    `id`                               INT AUTO_INCREMENT,
    `public_item_id`                   INT NOT NULL,
    `name`                             VARCHAR(100) NOT NULL,
    `v`                                VARCHAR(255) NOT NULL,
    `status`                           VARCHAR(255) NOT NULL,
    `publish_time`                     TIMESTAMP(6) DEFAULT NULL,
    `publisher`                        VARCHAR(50) DEFAULT NULL,
    `update_time`                      TIMESTAMP(6) NOT NULL,
    `modifier`                         VARCHAR(50) NOT NULL,
    INDEX (`name`),
    INDEX (`public_item_id`),
    INDEX (`update_time`),
    PRIMARY KEY (`id`)
)ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE IF NOT EXISTS `grom_config`.`public_item_version_record`(
    `id`                               INT AUTO_INCREMENT,
    `public_item_version_id`           INT NOT NULL,
    `general_version_id`               INT NOT NULL,
    `msg`                              VARCHAR(255),
    `update_time`                      TIMESTAMP(6) NOT NULL,
    `modifier`                         VARCHAR(50) NOT NULL,
    INDEX (`public_item_version_id`, `general_version_id`),
    PRIMARY KEY (`id`)
)ENGINE=InnoDB DEFAULT CHARSET=utf8;
