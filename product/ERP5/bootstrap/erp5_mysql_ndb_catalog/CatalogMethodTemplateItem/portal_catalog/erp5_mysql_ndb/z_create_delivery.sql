CREATE TABLE `delivery` (
  `uid` BIGINT UNSIGNED NOT NULL,
  `source_uid` BIGINT UNSIGNED default '0',
  `destination_uid` BIGINT UNSIGNED default '0',
  `source_section_uid` BIGINT UNSIGNED default '0',
  `destination_section_uid` BIGINT UNSIGNED default '0',
  `resource_uid` BIGINT UNSIGNED default '0',
  `start_date` datetime default NULL,
  `start_date_range_min` datetime default NULL,
  `start_date_range_max` datetime default NULL,
  `stop_date` datetime default NULL,
  `stop_date_range_min` datetime default NULL,
  `stop_date_range_max` datetime default NULL,
  PRIMARY KEY (`uid`),
  KEY `source_uid` (`source_uid`),
  KEY `destination_uid` (`destination_uid`),
  KEY `source_section_uid` (`source_section_uid`),
  KEY `destination_section_uid` (`destination_section_uid`),
  KEY `resource_uid` (`resource_uid`)
) TYPE=ndb
