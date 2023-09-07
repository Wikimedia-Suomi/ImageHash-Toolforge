-- MySQL dump 10.19  Distrib 10.3.39-MariaDB, for debian-linux-gnu (x86_64)
--
-- Host: tools.db.svc.wikimedia.cloud    Database: s55462__imagehash
-- ------------------------------------------------------
-- Server version	10.4.29-MariaDB-log

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `dhash`
--

DROP TABLE IF EXISTS `dhash`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `dhash` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `commons` int(11) DEFAULT NULL,
  `hash` bigint(20) unsigned DEFAULT NULL,
  `type` varchar(32) DEFAULT NULL,
  `source` varchar(32) DEFAULT NULL,
  `width` int(11) DEFAULT NULL,
  `height` int(11) DEFAULT NULL,
  `created` timestamp NOT NULL DEFAULT current_timestamp(),
  `url` varchar(1024) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `dhash_commons_idx` (`commons`),
  KEY `dhash_hashcommons_idx` (`hash`)
) ENGINE=InnoDB AUTO_INCREMENT=14386050 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `page`
--

DROP TABLE IF EXISTS `page`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `page` (
  `page_id` int(11) unsigned NOT NULL,
  `enabled` tinyint(1) NOT NULL DEFAULT 1,
  `phash_done` tinyint(1) NOT NULL DEFAULT 0,
  `dhash_done` tinyint(1) NOT NULL DEFAULT 0,
  `priority` smallint(6) NOT NULL DEFAULT 0,
  PRIMARY KEY (`page_id`),
  KEY `priority_idx` (`priority`),
  KEY `priority_2_idx` (`priority`,`enabled`,`phash_done`),
  KEY `page_enabled_phash_idx` (`enabled`,`phash_done`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `phash`
--

DROP TABLE IF EXISTS `phash`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `phash` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `commons` int(11) DEFAULT NULL,
  `hash` bigint(20) unsigned DEFAULT NULL,
  `type` varchar(32) DEFAULT NULL,
  `source` varchar(32) DEFAULT NULL,
  `width` int(11) DEFAULT NULL,
  `height` int(11) DEFAULT NULL,
  `created` timestamp NOT NULL DEFAULT current_timestamp(),
  `url` varchar(1024) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `phash_commons_idx` (`commons`),
  KEY `phash_hashcommons_idx` (`hash`)
) ENGINE=InnoDB AUTO_INCREMENT=14385993 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `status`
--

DROP TABLE IF EXISTS `status`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `status` (
  `keyword` varchar(255) NOT NULL,
  `last_processed_page_id` bigint(20) DEFAULT NULL,
  PRIMARY KEY (`keyword`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2023-09-07  1:02:31
