DROP SCHEMA IF EXISTS Travel_Journal_CMV;
CREATE SCHEMA Travel_Journal_CMV;
USE Travel_Journal_CMV;

DROP TABLE IF EXISTS `USERS`;
CREATE TABLE `USERS` (
	`user_id` BIGINT NOT NULL AUTO_INCREMENT,
	`user_name` VARCHAR(50) NOT NULL,
	`user_email` VARCHAR(50) NOT NULL,
	`password_hash` VARCHAR(255) NOT NULL,
	`user_fname` VARCHAR(50) NOT NULL,
	`user_lname` VARCHAR(50) NOT NULL,
	`user_location` VARCHAR(255) NOT NULL,
	`user_description` TEXT NOT NULL,
	`user_photo` VARCHAR(255),
	`user_status` ENUM('active', 'blocked', 'banned') NOT NULL DEFAULT 'active',
	`user_role` ENUM('traveller', 'editor', 'admin', 'moderator','itadmin') NOT NULL DEFAULT 'traveller',
    `is_public` BOOLEAN NOT NULL DEFAULT TRUE,
	PRIMARY KEY (`user_id`) USING BTREE,
    UNIQUE (user_email),
    UNIQUE (user_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


DROP VIEW IF EXISTS `USER_VIEW`;
CREATE VIEW `USER_VIEW` AS
SELECT 
    user_id,
    user_name,
    user_email,
    password_hash,
    user_fname,
    user_lname,
    user_location,
    user_description,
    user_photo,
    user_status,
    user_role,
    is_public,
    CONCAT(user_fname, ' ', user_lname) AS user_full_name
FROM USERS;


DROP TABLE IF EXISTS `JOURNEYS`;
CREATE TABLE `JOURNEYS` (
	`journey_id` BIGINT NOT NULL AUTO_INCREMENT,
	`user_id` BIGINT NOT NULL,
	`created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
	`updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
	`journey_title` VARCHAR(255) NOT NULL,
	`journey_description` TEXT,
	`journey_start_date` DATE NOT NULL,
	`journey_status` ENUM('public', 'private', 'hidden','share') DEFAULT 'public',
    `journey_photo_url` VARCHAR(255) NULL,
	PRIMARY KEY (`journey_id`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


DROP TABLE IF EXISTS `EVENTS`;
CREATE TABLE `EVENTS` (
	`event_id` BIGINT NOT NULL AUTO_INCREMENT,
	`journey_id` BIGINT NOT NULL,
	`event_title` VARCHAR(255) NOT NULL,
	`event_description` TEXT,
	`event_start_date` DATETIME NOT NULL,
	`event_end_date` DATETIME,
	`event_location` VARCHAR(255) NOT NULL,
	PRIMARY KEY (`event_id`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


DROP TABLE IF EXISTS `EVENT_PHOTOS`;
CREATE TABLE `EVENT_PHOTOS` (
	`event_photo_id` BIGINT NOT NULL AUTO_INCREMENT,
	`event_id` BIGINT NOT NULL,
	`event_photo_address` VARCHAR(255),
	PRIMARY KEY (`event_photo_id`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


DROP TABLE IF EXISTS `ANNOUNCEMENTS`;
CREATE TABLE ANNOUNCEMENTS (
    `announcement_id` BIGINT AUTO_INCREMENT,
    `user_id` BIGINT NOT NULL,
    `announcement_title` VARCHAR(255) NOT NULL,
    `announcement_content` TEXT NOT NULL,
    `announcement_type` VARCHAR(100) DEFAULT 'General',
    `announcement_redirect_url` TEXT,
    `start_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `end_time` DATETIME NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`announcement_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DROP TABLE IF EXISTS `PLANS`;
CREATE TABLE `PLANS` (
    `plan_id` BIGINT NOT NULL AUTO_INCREMENT,
    `plan_name` VARCHAR(50) NOT NULL,
    `plan_duration` INT NOT NULL,
    `plan_price` DECIMAL(10, 2) NOT NULL,
    `plan_discount` DECIMAL(5, 2) NOT NULL DEFAULT 0.00,
    PRIMARY KEY (`plan_id`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


DROP TABLE IF EXISTS `SUBSCRIPTIONS`;
CREATE TABLE `SUBSCRIPTIONS` (
    `subscription_id` BIGINT NOT NULL AUTO_INCREMENT,
    `user_id` BIGINT NOT NULL,
    `plan_id` BIGINT NOT NULL,
    `start_date` DATE NOT NULL,
    `end_date` DATE,
    `is_gifted` BOOLEAN NOT NULL DEFAULT FALSE,
    PRIMARY KEY (`subscription_id`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DROP TABLE IF EXISTS `PAYMENTS`;
CREATE TABLE `PAYMENTS` (
    `payment_id` BIGINT NOT NULL AUTO_INCREMENT,
    `subscription_id` BIGINT NOT NULL,
    `payment_date` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `billing_country` VARCHAR(100) NOT NULL,
    `card_number_last4` CHAR(4),
    `gst_amount` DECIMAL(10,2),
    `payment_total` DECIMAL(10,2),
    PRIMARY KEY (`payment_id`),
    UNIQUE (`subscription_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DROP TABLE IF EXISTS `PREMIER_USERS`;
CREATE TABLE `PREMIER_USERS` (
    `premier_id` BIGINT NOT NULL AUTO_INCREMENT,
    `user_id` BIGINT NOT NULL,
    `premier_start_at` DATETIME NOT NULL,
    `premier_end_at` DATETIME NOT NULL,
    PRIMARY KEY (`premier_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DROP TABLE IF EXISTS `LIKES`;
CREATE TABLE `LIKES` (
    `like_id` BIGINT AUTO_INCREMENT,
    `user_id` BIGINT NOT NULL,
    `target_type` ENUM('event', 'comment') NOT NULL,
    `target_id` BIGINT NOT NULL,
    `is_like` BOOLEAN NOT NULL,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`like_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DROP TABLE IF EXISTS `COMMENTS`;
CREATE TABLE `COMMENTS` (
    `comment_id` BIGINT AUTO_INCREMENT,
    `event_id` BIGINT NOT NULL,
    `user_id` BIGINT NOT NULL,
    `comment_text` TEXT NOT NULL,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `is_hidden` BOOLEAN DEFAULT FALSE,
    PRIMARY KEY (`comment_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DROP TABLE IF EXISTS `COMMENT_REPORTS`;
CREATE TABLE `COMMENT_REPORTS` (
    `report_id` BIGINT AUTO_INCREMENT,
    `comment_id` BIGINT NOT NULL,
    `reported_by` BIGINT NOT NULL,
    `report_reason` ENUM('abusive', 'offensive', 'spam', 'other') NOT NULL,
    `reported_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `escalated_to_admin` BOOLEAN DEFAULT FALSE,
    `escalated_by` BIGINT NULL,
    `escalated_at` DATETIME NULL,
    `moderated_by`  BIGINT NULL,
    `moderated_at` DATETIME NULL,
    PRIMARY KEY (`report_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

ALTER TABLE COMMENT_REPORTS
ADD CONSTRAINT unique_comment_user_report
UNIQUE (comment_id, reported_by);

DROP TABLE IF EXISTS `PRIVATE_MESSAGES`;
CREATE TABLE `PRIVATE_MESSAGES` (
    `message_id` BIGINT AUTO_INCREMENT,
    `sender_id` BIGINT NOT NULL,
    `recipient_id` BIGINT NOT NULL,
    `message_text` TEXT NOT NULL,
    `sent_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `is_read` BOOLEAN DEFAULT FALSE,
    PRIMARY KEY (`message_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


DROP TABLE IF EXISTS `HELPDESK`;

CREATE TABLE `HELPDESK` (
  `request_id` bigint NOT NULL AUTO_INCREMENT,
  `request_user_id` bigint NOT NULL,
  `request_user_name` varchar(100) DEFAULT NULL,
  `request_email` varchar(100) DEFAULT NULL,
  `request_type` enum('request','bug') NOT NULL,
  `request_category` enum('journey','event','profile','subscription','other') NOT NULL,
  `request_title` varchar(255) NOT NULL,
  `request_description` text NOT NULL,
  `request_status` enum('new','open','stalled','resolved') DEFAULT 'new',
  `request_priority` enum('low','medium','high') DEFAULT 'medium',
  `request_assigned_to` bigint DEFAULT NULL,
  `request_assigned_name` varchar(100) DEFAULT NULL,
  `request_take_pending` tinyint DEFAULT '1',
  `request_take_candidate_id` bigint DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`request_id`),
  KEY `fk_request_user` (`request_user_id`),
  KEY `fk_assigned_to` (`request_assigned_to`),
  KEY `fk_take_candidate` (`request_take_candidate_id`),
  CONSTRAINT `fk_assigned_to` FOREIGN KEY (`request_assigned_to`) REFERENCES `USERS` (`user_id`) ON DELETE SET NULL,
  CONSTRAINT `fk_request_user` FOREIGN KEY (`request_user_id`) REFERENCES `USERS` (`user_id`) ON DELETE CASCADE,
  CONSTRAINT `fk_take_candidate` FOREIGN KEY (`request_take_candidate_id`) REFERENCES `USERS` (`user_id`) ON DELETE SET NULL
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DROP TABLE IF EXISTS `HELPDESK_COMMENTS`;
CREATE TABLE `HELPDESK_COMMENTS` (
  `comment_id` bigint NOT NULL AUTO_INCREMENT,
  `request_id` bigint NOT NULL,
  `user_id` bigint DEFAULT NULL,
  `comment_user` varchar(100) DEFAULT NULL,
  `comment_text` text NOT NULL,
  `request_status` enum('new','open','stalled','resolved') DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`comment_id`),
  KEY `request_id` (`request_id`),
  CONSTRAINT `helpdesk_comments_ibfk_1` FOREIGN KEY (`request_id`) REFERENCES `HELPDESK` (`request_id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=20 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DROP TABLE IF EXISTS `HELPDESK_HISTORY`;
CREATE TABLE `HELPDESK_HISTORY` (
  `history_id` bigint NOT NULL AUTO_INCREMENT,
  `request_id` bigint NOT NULL,
  `request_user_id` bigint NOT NULL,
  `request_user_name` varchar(100) DEFAULT NULL,
  `request_email` varchar(100) DEFAULT NULL,
  `request_type` varchar(20) NOT NULL,
  `request_category` varchar(20) NOT NULL,
  `request_title` varchar(255) NOT NULL,
  `request_description` text NOT NULL,
  `request_status` varchar(20) NOT NULL,
  `request_priority` varchar(20) NOT NULL,
  `request_assigned_to` bigint DEFAULT NULL,
  `request_assigned_name` varchar(100) DEFAULT NULL,
  `request_take_pending` tinyint DEFAULT '1',
  `request_take_candidate_id` bigint DEFAULT NULL,
  `request_created_at` datetime DEFAULT NULL,
  `request_updated_at` datetime DEFAULT NULL,
  `history_created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`history_id`),
  KEY `fk_history_request` (`request_id`),
  CONSTRAINT `fk_history_request` FOREIGN KEY (`request_id`) REFERENCES `HELPDESK` (`request_id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=18 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


DROP VIEW IF EXISTS HELPDESK_STATUS_SUMMARY;
CREATE OR REPLACE VIEW `HELPDESK_STATUS_SUMMARY` AS
SELECT 
    request_status,
    COUNT(*) AS total_count
FROM `HELPDESK`
GROUP BY request_status;

DROP TABLE IF EXISTS `PROFILE_BLOCKS`;
CREATE TABLE PROFILE_BLOCKS (
    `block_id` INT AUTO_INCREMENT PRIMARY KEY,
    `block_name` VARCHAR(50) NOT NULL UNIQUE,
    `block_description` VARCHAR(255)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DROP TABLE IF EXISTS `PROFILE_VISIBILITY_SETTINGS`;
CREATE TABLE PROFILE_VISIBILITY_SETTINGS (
    `user_id` BIGINT NOT NULL,
    `block_id` INT NOT NULL,
    `is_visible` BOOLEAN NOT NULL DEFAULT TRUE,
    PRIMARY KEY (`user_id`, `block_id`),
    FOREIGN KEY (`user_id`) REFERENCES USERS(`user_id`),
    FOREIGN KEY (`block_id`) REFERENCES PROFILE_BLOCKS(`block_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


DELIMITER $$

CREATE TRIGGER after_user_insert
AFTER INSERT ON USERS
FOR EACH ROW
BEGIN
    INSERT INTO PROFILE_VISIBILITY_SETTINGS (user_id, block_id, is_visible)
    SELECT NEW.user_id, block_id, TRUE
    FROM PROFILE_BLOCKS;
END$$

DELIMITER ;