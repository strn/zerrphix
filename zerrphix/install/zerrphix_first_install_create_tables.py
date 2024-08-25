# -*- coding: utf-8 -*-
# rember to remove AUTOINC after copy the below from mysqldump output
# AUTO_INCREMENT=\d+\s
zerrphix_first_install_create_tables = \
"""-- MySQL dump 10.13  Distrib 5.5.55, for debian-linux-gnu (x86_64)
--
-- Host: localhost    Database: zerrphix
-- ------------------------------------------------------
-- Server version	5.5.55-0+deb8u1

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `ZP_ACODEC`
--

DROP TABLE IF EXISTS `ZP_ACODEC`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_ACODEC` (
  `ID` tinyint(3) unsigned NOT NULL AUTO_INCREMENT,
  `CODEC` text COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_ACODEC_XREF`
--

DROP TABLE IF EXISTS `ZP_ACODEC_XREF`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_ACODEC_XREF` (
  `ID` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
  `ZP_ACODEC_ID` tinyint(3) unsigned NOT NULL,
  `CODEC_ID` text COLLATE utf8mb4_unicode_ci,
  `CODEC` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_DB_LOG`
--

DROP TABLE IF EXISTS `ZP_DB_LOG`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_DB_LOG` (
  `ID` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `LEVEL` tinyint(4) unsigned NOT NULL,
  `TEXT` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `TRACEBACK` text COLLATE utf8mb4_unicode_ci,
  `COUNT_24` int(11) unsigned NOT NULL,
  `SOURCE_ID` smallint(5) unsigned NOT NULL,
  `FIRST_OCCURRENCE_DATE_TIME` datetime NOT NULL,
  `LAST_OCCURRENCE_DATE_TIME` datetime NOT NULL,
  PRIMARY KEY (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_DUNE`
--

DROP TABLE IF EXISTS `ZP_DUNE`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_DUNE` (
  `ID` tinyint(3) unsigned NOT NULL AUTO_INCREMENT,
  `NAME` text CHARACTER SET utf8mb4 NOT NULL,
  PRIMARY KEY (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_DUNE_FILM_COLLECTION_IMAGE_RENDER_HASH_XREF`
--

DROP TABLE IF EXISTS `ZP_DUNE_FILM_COLLECTION_IMAGE_RENDER_HASH_XREF`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_DUNE_FILM_COLLECTION_IMAGE_RENDER_HASH_XREF` (
  `ZP_DUNE_ID` tinyint(3) unsigned NOT NULL,
  `ZP_FILM_COLLECTION_IMAGE_RENDER_HASH_ID` int(10) unsigned NOT NULL,
  `EXT` varchar(5) COLLATE utf8mb4_unicode_ci NOT NULL,
  `RENDER_DATETIME` datetime NOT NULL,
  PRIMARY KEY (`ZP_DUNE_ID`,`ZP_FILM_COLLECTION_IMAGE_RENDER_HASH_ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_DUNE_FILM_IMAGE_RENDER_HASH_XREF`
--

DROP TABLE IF EXISTS `ZP_DUNE_FILM_IMAGE_RENDER_HASH_XREF`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_DUNE_FILM_IMAGE_RENDER_HASH_XREF` (
  `ZP_DUNE_ID` tinyint(3) unsigned NOT NULL,
  `ZP_FILM_IMAGE_RENDER_HASH_ID` int(10) unsigned NOT NULL,
  `EXT` varchar(5) COLLATE utf8mb4_unicode_ci NOT NULL,
  `RENDER_DATETIME` datetime NOT NULL,
  PRIMARY KEY (`ZP_DUNE_ID`,`ZP_FILM_IMAGE_RENDER_HASH_ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_DUNE_PLAY_PATH`
--

DROP TABLE IF EXISTS `ZP_DUNE_PLAY_PATH`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_DUNE_PLAY_PATH` (
  `ID` tinyint(3) unsigned NOT NULL AUTO_INCREMENT,
  `ZP_DUNE_ID` tinyint(3) unsigned NOT NULL,
  `ZP_SCAN_PATH_ID` tinyint(3) unsigned NOT NULL,
  `PLAY_ROOT_PATH` text COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`ID`),
  UNIQUE KEY `ZP_DUNE_ID` (`ZP_DUNE_ID`,`ZP_SCAN_PATH_ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_DUNE_SHARE_XREF`
--

DROP TABLE IF EXISTS `ZP_DUNE_SHARE_XREF`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_DUNE_SHARE_XREF` (
  `ID` tinyint(4) unsigned NOT NULL AUTO_INCREMENT,
  `REF_NAME` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `ZP_SHARE_ID` tinyint(3) unsigned NOT NULL,
  `ZP_SHARE_SERVER_ID` tinyint(3) unsigned NOT NULL,
  `ZP_SHARE_CREDENTIAL_ID` tinyint(3) unsigned NOT NULL,
  PRIMARY KEY (`ZP_SHARE_ID`,`ZP_SHARE_SERVER_ID`,`ZP_SHARE_CREDENTIAL_ID`),
  UNIQUE KEY `ID` (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_DUNE_TV_EPISODE_IMAGE_RENDER_HASH_XREF`
--

DROP TABLE IF EXISTS `ZP_DUNE_TV_EPISODE_IMAGE_RENDER_HASH_XREF`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_DUNE_TV_EPISODE_IMAGE_RENDER_HASH_XREF` (
  `ZP_DUNE_ID` tinyint(3) unsigned NOT NULL,
  `ZP_TV_EPISODE_IMAGE_RENDER_HASH_ID` int(10) unsigned NOT NULL,
  `EXT` varchar(5) COLLATE utf8mb4_unicode_ci NOT NULL,
  `RENDER_DATETIME` datetime NOT NULL,
  PRIMARY KEY (`ZP_DUNE_ID`,`ZP_TV_EPISODE_IMAGE_RENDER_HASH_ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_DUNE_TV_IMAGE_RENDER_HASH_XREF`
--

DROP TABLE IF EXISTS `ZP_DUNE_TV_IMAGE_RENDER_HASH_XREF`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_DUNE_TV_IMAGE_RENDER_HASH_XREF` (
  `ZP_DUNE_ID` tinyint(3) unsigned NOT NULL,
  `ZP_TV_IMAGE_RENDER_HASH_ID` int(10) unsigned NOT NULL,
  `EXT` varchar(5) COLLATE utf8mb4_unicode_ci NOT NULL,
  `RENDER_DATETIME` datetime NOT NULL,
  PRIMARY KEY (`ZP_DUNE_ID`,`ZP_TV_IMAGE_RENDER_HASH_ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_DUNE_UI_IMAGE_STORE_TYPE`
--

DROP TABLE IF EXISTS `ZP_DUNE_UI_IMAGE_STORE_TYPE`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_DUNE_UI_IMAGE_STORE_TYPE` (
  `ID` tinyint(3) unsigned NOT NULL AUTO_INCREMENT,
  `DESCR` text COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_DUNE_UI_IMAGE_STORE_TYPE_XREF`
--

DROP TABLE IF EXISTS `ZP_DUNE_UI_IMAGE_STORE_TYPE_XREF`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_DUNE_UI_IMAGE_STORE_TYPE_XREF` (
  `ZP_DUNE_ID` tinyint(3) unsigned NOT NULL,
  `ZP_DUNE_UI_IMAGE_STORE_TYPE_ID` tinyint(3) unsigned NOT NULL,
  `ZP_DUNE_SHARE_XREF_ID` tinyint(4) DEFAULT NULL,
  `ZP_DUNE_UI_IMAGE_STORE_ROOT` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `DUNE_LOCAL_REF` text COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`ZP_DUNE_ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_DUNE_USER_IMAGE_RENDER_HASH_XREF`
--

DROP TABLE IF EXISTS `ZP_DUNE_USER_IMAGE_RENDER_HASH_XREF`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_DUNE_USER_IMAGE_RENDER_HASH_XREF` (
  `ZP_DUNE_ID` tinyint(3) unsigned NOT NULL,
  `ZP_USER_IMAGE_RENDER_HASH_ID` int(10) unsigned NOT NULL,
  `EXT` varchar(5) COLLATE utf8mb4_unicode_ci NOT NULL,
  `RENDER_DATETIME` datetime NOT NULL,
  PRIMARY KEY (`ZP_DUNE_ID`,`ZP_USER_IMAGE_RENDER_HASH_ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_EAPI`
--

DROP TABLE IF EXISTS `ZP_EAPI`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_EAPI` (
  `ID` tinyint(3) unsigned NOT NULL AUTO_INCREMENT,
  `NAME` tinytext COLLATE utf8mb4_unicode_ci NOT NULL,
  `DESC` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `SOURCE` tinyint(1) NOT NULL,
  `LOOKUP` tinyint(1) NOT NULL,
  PRIMARY KEY (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_EAPI_LIBRARY_XREF`
--

DROP TABLE IF EXISTS `ZP_EAPI_LIBRARY_XREF`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_EAPI_LIBRARY_XREF` (
  `ZP_EAPI_ID` tinyint(3) unsigned NOT NULL,
  `ZP_LIBRARY_ID` tinyint(3) unsigned NOT NULL,
  PRIMARY KEY (`ZP_EAPI_ID`,`ZP_LIBRARY_ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_EAPI_LINK`
--

DROP TABLE IF EXISTS `ZP_EAPI_LINK`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_EAPI_LINK` (
  `ID` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
  `ZP_EAPI_ID` tinyint(3) unsigned NOT NULL,
  `HAVE_ZP_EAPI_ID` tinyint(3) unsigned NOT NULL,
  `WANT_ZP_EAPI_ID` tinyint(3) unsigned NOT NULL,
  PRIMARY KEY (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_FILE_EXTENSION`
--

DROP TABLE IF EXISTS `ZP_FILE_EXTENSION`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_FILE_EXTENSION` (
  `ID` tinyint(3) unsigned NOT NULL AUTO_INCREMENT,
  `EXTENSION` tinytext COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_FILM`
--

DROP TABLE IF EXISTS `ZP_FILM`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_FILM` (
  `ID` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `ADDED_DATE_TIME` datetime NOT NULL,
  `LAST_EDIT_DATETIME` datetime NOT NULL,
  `ZP_FILM_FILEFOLDER_ID` int(10) unsigned NOT NULL,
  `ZP_FILM_COLLECTION_ID` int(10) unsigned DEFAULT NULL,
  PRIMARY KEY (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_FILM_COLLECTION`
--

DROP TABLE IF EXISTS `ZP_FILM_COLLECTION`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_FILM_COLLECTION` (
  `ID` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `LAST_EDIT_DATETIME` datetime NOT NULL,
  PRIMARY KEY (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_FILM_COLLECTION_EAPI_EID`
--

DROP TABLE IF EXISTS `ZP_FILM_COLLECTION_EAPI_EID`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_FILM_COLLECTION_EAPI_EID` (
  `ZP_FILM_COLLECTION_ID` mediumint(8) unsigned NOT NULL,
  `ZP_EAPI_ID` tinyint(3) unsigned NOT NULL,
  `ZP_EAPI_COLLECTION_EID` varchar(25) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`ZP_FILM_COLLECTION_ID`,`ZP_EAPI_ID`) USING BTREE,
  UNIQUE KEY `ZP_EAPI_ID` (`ZP_EAPI_ID`,`ZP_EAPI_COLLECTION_EID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_FILM_COLLECTION_IMAGE_RENDER_HASH`
--

DROP TABLE IF EXISTS `ZP_FILM_COLLECTION_IMAGE_RENDER_HASH`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_FILM_COLLECTION_IMAGE_RENDER_HASH` (
  `ID` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `ZP_FILM_COLLECTION_IMAGE_TYPE_ID` tinyint(3) unsigned NOT NULL,
  `ZP_FILM_COLLECTION_ID` int(10) unsigned NOT NULL,
  `ZP_IMAGE_SUB_TYPE` tinyint(3) unsigned NOT NULL,
  `HASH` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `ZP_TEMPLATE_ID` smallint(5) unsigned NOT NULL,
  PRIMARY KEY (`ID`),
  UNIQUE KEY `ZP_FILM_COLLECTION_IMAGE_TYPE_ID` (`ZP_FILM_COLLECTION_IMAGE_TYPE_ID`,`ZP_FILM_COLLECTION_ID`,`ZP_IMAGE_SUB_TYPE`,`HASH`,`ZP_TEMPLATE_ID`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_FILM_COLLECTION_OVERVIEW`
--

DROP TABLE IF EXISTS `ZP_FILM_COLLECTION_OVERVIEW`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_FILM_COLLECTION_OVERVIEW` (
  `ID` int(11) NOT NULL AUTO_INCREMENT,
  `ZP_FILM_COLLECTION_ID` mediumint(9) NOT NULL,
  `ZP_LANG_ID` smallint(5) unsigned NOT NULL,
  `ZP_EAPI_ID` tinyint(3) unsigned NOT NULL DEFAULT '0',
  `ZP_USER_ID` smallint(5) unsigned NOT NULL DEFAULT '0',
  `LANG_DEFAULT` tinyint(1) NOT NULL DEFAULT '0',
  `MAIN_DEFAULT` tinyint(1) NOT NULL DEFAULT '0',
  `OVERVIEW` text COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`ID`),
  UNIQUE KEY `ZP_FILM_COLLECTION_ID` (`ZP_FILM_COLLECTION_ID`,`ZP_LANG_ID`,`ZP_EAPI_ID`,`ZP_USER_ID`,`LANG_DEFAULT`,`MAIN_DEFAULT`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_FILM_COLLECTION_RAW_IMAGE`
--

DROP TABLE IF EXISTS `ZP_FILM_COLLECTION_RAW_IMAGE`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_FILM_COLLECTION_RAW_IMAGE` (
  `ID` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `ZP_EAPI_ID` tinyint(3) unsigned NOT NULL,
  `ZP_EAPI_IMAGE_REF` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `ADDED_DATETIME` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `ZP_ENTITY_TYPE_ID` tinyint(3) unsigned NOT NULL,
  `ZP_ENTITY_ID` int(10) unsigned NOT NULL,
  `ZP_USER_ID` int(11) DEFAULT NULL,
  `ZP_LANG_ID` int(11) DEFAULT NULL,
  `LANG_DEFAULT` tinyint(1) DEFAULT NULL,
  `MAIN_DEFAULT` tinyint(1) DEFAULT NULL,
  `FILENAME` text COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_FILM_COLLECTION_SPECIAL_TYPE`
--

DROP TABLE IF EXISTS `ZP_FILM_COLLECTION_SPECIAL_TYPE`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_FILM_COLLECTION_SPECIAL_TYPE` (
  `ID` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
  `DESCR` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `USES_LANG` tinyint(1) NOT NULL DEFAULT '0',
  PRIMARY KEY (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_FILM_COLLECTION_SPEICAL_TYPE_XREF`
--

DROP TABLE IF EXISTS `ZP_FILM_COLLECTION_SPEICAL_TYPE_XREF`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_FILM_COLLECTION_SPEICAL_TYPE_XREF` (
  `ZP_FILM_COLLECTION_ID` int(10) unsigned NOT NULL,
  `ZP_FILM_COLLECTION_SPECIAL_TYPE_ID` tinyint(3) unsigned NOT NULL,
  `ZP_EAPI_ID_REQ` tinyint(3) unsigned NOT NULL DEFAULT '0',
  `ZP_EAPI_ID_ACT` tinyint(3) unsigned NOT NULL,
  `ZP_LANG_ID_REQ` smallint(5) unsigned NOT NULL DEFAULT '0',
  `ZP_LANG_ID_ACT` smallint(5) unsigned NOT NULL DEFAULT '0',
  `ZP_FILM_COLLECTION_IMAGE_TYPE_ID` tinyint(3) unsigned NOT NULL,
  PRIMARY KEY (`ZP_FILM_COLLECTION_ID`,`ZP_FILM_COLLECTION_SPECIAL_TYPE_ID`,`ZP_EAPI_ID_REQ`,`ZP_LANG_ID_REQ`,`ZP_FILM_COLLECTION_IMAGE_TYPE_ID`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_FILM_COLLECTION_TITLE`
--

DROP TABLE IF EXISTS `ZP_FILM_COLLECTION_TITLE`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_FILM_COLLECTION_TITLE` (
  `ID` int(11) NOT NULL AUTO_INCREMENT,
  `ZP_FILM_COLLECTION_ID` mediumint(9) NOT NULL,
  `ZP_FILM_COLLECTION_TITLE_TYPE_ID` tinyint(3) unsigned NOT NULL,
  `ZP_LANG_ID` smallint(5) unsigned NOT NULL,
  `ZP_EAPI_ID` tinyint(3) unsigned NOT NULL,
  `ZP_USER_ID` smallint(6) NOT NULL DEFAULT '0',
  `LANG_DEFAULT` tinyint(1) NOT NULL DEFAULT '0',
  `MAIN_DEFAULT` tinyint(1) NOT NULL DEFAULT '0',
  `TITLE` text COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`ID`),
  UNIQUE KEY `ZP_FILM_COLLECTION_ID` (`ZP_FILM_COLLECTION_ID`,`ZP_FILM_COLLECTION_TITLE_TYPE_ID`,`ZP_LANG_ID`,`ZP_EAPI_ID`,`ZP_USER_ID`,`LANG_DEFAULT`,`MAIN_DEFAULT`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_FILM_COLLECTION_XREF`
--

DROP TABLE IF EXISTS `ZP_FILM_COLLECTION_XREF`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_FILM_COLLECTION_XREF` (
  `ZP_FILM_COLLECTION_ID` mediumint(8) unsigned NOT NULL,
  `ZP_FILM_ID` int(10) unsigned NOT NULL,
  PRIMARY KEY (`ZP_FILM_COLLECTION_ID`,`ZP_FILM_ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_FILM_EAPI_EID`
--

DROP TABLE IF EXISTS `ZP_FILM_EAPI_EID`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_FILM_EAPI_EID` (
  `ID` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `ZP_FILM_ID` int(11) NOT NULL,
  `ZP_EAPI_EID` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `ZP_EAPI_ID` tinyint(4) NOT NULL,
  PRIMARY KEY (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_FILM_FILEFOLDER`
--

DROP TABLE IF EXISTS `ZP_FILM_FILEFOLDER`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_FILM_FILEFOLDER` (
  `ID` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `ZP_FILM_ID` mediumint(8) unsigned DEFAULT NULL,
  `ENABLED` tinyint(1) NOT NULL DEFAULT '1',
  `ENABLED_UPDATE_DATETIME` datetime NOT NULL,
  `ZP_SCAN_PATH_ID` smallint(5) unsigned NOT NULL,
  `LAST_PATH` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `SCAN_PATH_SUB_DIR` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `ZP_FILM_FOLDER_TYPE_ID` smallint(5) unsigned DEFAULT NULL,
  `TITLE_LIST` text COLLATE utf8mb4_unicode_ci,
  `HD` tinyint(1) NOT NULL DEFAULT '0',
  `FHD` tinyint(1) NOT NULL DEFAULT '0',
  `UHD` tinyint(1) NOT NULL DEFAULT '0',
  PRIMARY KEY (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_FILM_FILEFOLDER_AUIDO_METADATA`
--

DROP TABLE IF EXISTS `ZP_FILM_FILEFOLDER_AUIDO_METADATA`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_FILM_FILEFOLDER_AUIDO_METADATA` (
  `ZP_FILM_FILEFOLDER_ID` int(10) unsigned NOT NULL,
  `TRACK_ID` smallint(3) unsigned NOT NULL DEFAULT '0',
  `ZP_CODEC_ID` tinyint(3) unsigned DEFAULT NULL,
  `ZP_LANG_ID` int(11) DEFAULT NULL,
  `CHANNELS` int(11) DEFAULT NULL,
  PRIMARY KEY (`ZP_FILM_FILEFOLDER_ID`,`TRACK_ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_FILM_FILEFOLDER_SCORE`
--

DROP TABLE IF EXISTS `ZP_FILM_FILEFOLDER_SCORE`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_FILM_FILEFOLDER_SCORE` (
  `ID` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `ZP_FILM_FILEFOLDER_ID` int(10) unsigned NOT NULL,
  `SCORE` tinyint(3) unsigned NOT NULL,
  `ZP_SOURCE_ID` tinyint(3) unsigned NOT NULL,
  `ZP_RES_ID` tinyint(3) unsigned NOT NULL,
  `DISC` tinyint(1) NOT NULL,
  PRIMARY KEY (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_FILM_FILEFOLDER_TEXT_METADATA`
--

DROP TABLE IF EXISTS `ZP_FILM_FILEFOLDER_TEXT_METADATA`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_FILM_FILEFOLDER_TEXT_METADATA` (
  `ZP_FILM_FILEFOLDER_ID` int(10) unsigned NOT NULL,
  `TRACK_ID` smallint(3) unsigned NOT NULL DEFAULT '0',
  `ZP_CODEC_ID` tinyint(3) unsigned DEFAULT NULL,
  `FORMAT` text COLLATE utf8mb4_unicode_ci,
  `ZP_LANG_ID` smallint(5) unsigned DEFAULT NULL,
  PRIMARY KEY (`ZP_FILM_FILEFOLDER_ID`,`TRACK_ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_FILM_FILEFOLDER_VIDEO_METADATA`
--

DROP TABLE IF EXISTS `ZP_FILM_FILEFOLDER_VIDEO_METADATA`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_FILM_FILEFOLDER_VIDEO_METADATA` (
  `ZP_FILM_FILEFOLDER_ID` int(10) unsigned NOT NULL,
  `TRACK_ID` smallint(3) unsigned NOT NULL DEFAULT '0',
  `ZP_CODEC_ID` tinyint(3) unsigned DEFAULT NULL,
  `ASPECT_RATIO` text COLLATE utf8mb4_unicode_ci,
  `FRAME_RATE` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`ZP_FILM_FILEFOLDER_ID`,`TRACK_ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_FILM_GENRE_XREF`
--

DROP TABLE IF EXISTS `ZP_FILM_GENRE_XREF`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_FILM_GENRE_XREF` (
  `ZP_FILM_ID` int(10) unsigned NOT NULL,
  `ZP_GENRE_ID` tinyint(3) unsigned NOT NULL,
  PRIMARY KEY (`ZP_FILM_ID`,`ZP_GENRE_ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_FILM_IMAGE_RENDER_HASH`
--

DROP TABLE IF EXISTS `ZP_FILM_IMAGE_RENDER_HASH`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_FILM_IMAGE_RENDER_HASH` (
  `ID` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `ZP_FILM_IMAGE_TYPE_ID` tinyint(3) unsigned NOT NULL,
  `ZP_FILM_ID` int(10) unsigned NOT NULL,
  `ZP_IMAGE_SUB_TYPE` tinyint(3) unsigned NOT NULL,
  `HASH` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `ZP_TEMPLATE_ID` smallint(5) unsigned NOT NULL,
  PRIMARY KEY (`ID`),
  UNIQUE KEY `ZP_FILM_IMAGE_TYPE_ID` (`ZP_FILM_IMAGE_TYPE_ID`,`ZP_FILM_ID`,`ZP_IMAGE_SUB_TYPE`,`HASH`,`ZP_TEMPLATE_ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_FILM_OVERVIEW`
--

DROP TABLE IF EXISTS `ZP_FILM_OVERVIEW`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_FILM_OVERVIEW` (
  `ID` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `ZP_FILM_ID` int(10) unsigned NOT NULL,
  `ZP_LANG_ID` smallint(5) unsigned NOT NULL,
  `ZP_EAPI_ID` tinyint(3) unsigned NOT NULL,
  `ZP_USER_ID` smallint(5) unsigned NOT NULL DEFAULT '0',
  `LANG_DEFAULT` tinyint(1) NOT NULL DEFAULT '0',
  `MAIN_DEFAULT` tinyint(1) NOT NULL DEFAULT '0',
  `OVERVIEW` text COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`ID`),
  UNIQUE KEY `ZP_FILM_ID` (`ZP_FILM_ID`,`ZP_LANG_ID`,`ZP_EAPI_ID`,`ZP_USER_ID`,`LANG_DEFAULT`,`MAIN_DEFAULT`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_FILM_RATING`
--

DROP TABLE IF EXISTS `ZP_FILM_RATING`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_FILM_RATING` (
  `ZP_FILM_ID` int(3) unsigned NOT NULL,
  `RATING` tinyint(3) unsigned NOT NULL,
  PRIMARY KEY (`ZP_FILM_ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_FILM_RAW_IMAGE`
--

DROP TABLE IF EXISTS `ZP_FILM_RAW_IMAGE`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_FILM_RAW_IMAGE` (
  `ID` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `ZP_EAPI_ID` tinyint(3) unsigned NOT NULL,
  `ZP_EAPI_IMAGE_REF` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `ADDED_DATETIME` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `ZP_ENTITY_TYPE_ID` tinyint(3) unsigned NOT NULL,
  `ZP_ENTITY_ID` int(10) unsigned NOT NULL,
  `ZP_USER_ID` int(11) DEFAULT NULL,
  `ZP_LANG_ID` int(11) DEFAULT NULL,
  `LANG_DEFAULT` tinyint(1) DEFAULT NULL,
  `MAIN_DEFAULT` tinyint(1) DEFAULT NULL,
  `FILENAME` text COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_FILM_RELEASE`
--

DROP TABLE IF EXISTS `ZP_FILM_RELEASE`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_FILM_RELEASE` (
  `ZP_FILM_ID` int(10) unsigned NOT NULL,
  `RELEASE_DATE` date NOT NULL,
  PRIMARY KEY (`ZP_FILM_ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_FILM_ROLE_XREF`
--

DROP TABLE IF EXISTS `ZP_FILM_ROLE_XREF`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_FILM_ROLE_XREF` (
  `ZP_FILM_ID` int(10) unsigned NOT NULL,
  `ZP_PEOPLE_ID` int(10) unsigned NOT NULL,
  `ZP_ROLE_ID` tinyint(3) unsigned NOT NULL,
  `ROLE_ORDER` smallint(5) unsigned DEFAULT NULL,
  PRIMARY KEY (`ZP_FILM_ID`,`ZP_PEOPLE_ID`,`ZP_ROLE_ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_FILM_RUNTIME`
--

DROP TABLE IF EXISTS `ZP_FILM_RUNTIME`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_FILM_RUNTIME` (
  `ZP_FILM_ID` int(10) unsigned NOT NULL,
  `RUNTIME` smallint(5) unsigned NOT NULL,
  PRIMARY KEY (`ZP_FILM_ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_FILM_SPECIAL_TYPE`
--

DROP TABLE IF EXISTS `ZP_FILM_SPECIAL_TYPE`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_FILM_SPECIAL_TYPE` (
  `ID` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
  `DESCR` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `USES_LANG` tinyint(1) NOT NULL DEFAULT '0',
  PRIMARY KEY (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_FILM_SPEICAL_TYPE_XREF`
--

DROP TABLE IF EXISTS `ZP_FILM_SPEICAL_TYPE_XREF`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_FILM_SPEICAL_TYPE_XREF` (
  `ZP_FILM_ID` int(10) unsigned NOT NULL,
  `ZP_FILM_SPECIAL_TYPE_ID` tinyint(3) unsigned NOT NULL,
  `ZP_EAPI_ID_REQ` tinyint(3) unsigned NOT NULL DEFAULT '0',
  `ZP_EAPI_ID_ACT` tinyint(3) unsigned NOT NULL,
  `ZP_LANG_ID_REQ` smallint(5) unsigned NOT NULL DEFAULT '0',
  `ZP_LANG_ID_ACT` smallint(5) unsigned NOT NULL DEFAULT '0',
  `ZP_FILM_IMAGE_TYPE_ID` tinyint(3) unsigned NOT NULL,
  PRIMARY KEY (`ZP_FILM_ID`,`ZP_FILM_SPECIAL_TYPE_ID`,`ZP_EAPI_ID_REQ`,`ZP_LANG_ID_REQ`,`ZP_FILM_IMAGE_TYPE_ID`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_FILM_TITLE`
--

DROP TABLE IF EXISTS `ZP_FILM_TITLE`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_FILM_TITLE` (
  `ID` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `ZP_FILM_ID` int(10) unsigned NOT NULL,
  `ZP_FILM_TITLE_TYPE_ID` tinyint(3) unsigned NOT NULL,
  `ZP_LANG_ID` smallint(5) unsigned NOT NULL,
  `ZP_EAPI_ID` tinyint(3) unsigned DEFAULT '0',
  `ZP_USER_ID` smallint(6) unsigned NOT NULL DEFAULT '0',
  `LANG_DEFAULT` tinyint(1) NOT NULL DEFAULT '0',
  `MAIN_DEFAULT` tinyint(1) NOT NULL DEFAULT '0',
  `TITLE` text COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`ID`),
  UNIQUE KEY `ZP_FILM_ID` (`ZP_FILM_ID`,`ZP_FILM_TITLE_TYPE_ID`,`ZP_LANG_ID`,`ZP_EAPI_ID`,`ZP_USER_ID`,`LANG_DEFAULT`,`MAIN_DEFAULT`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_FOLDER_TYPE`
--

DROP TABLE IF EXISTS `ZP_FOLDER_TYPE`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_FOLDER_TYPE` (
  `ID` int(11) NOT NULL,
  `NAME` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `ZP_RES_RES` int(11) NOT NULL,
  `ZP_SOURCE_SOURCE` text COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_GENRE`
--

DROP TABLE IF EXISTS `ZP_GENRE`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_GENRE` (
  `ID` tinyint(3) unsigned NOT NULL AUTO_INCREMENT,
  `GENRE` text COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_ICON_SUB_TYPE`
--

DROP TABLE IF EXISTS `ZP_ICON_SUB_TYPE`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_ICON_SUB_TYPE` (
  `ID` tinyint(3) unsigned NOT NULL AUTO_INCREMENT,
  `DESCR` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_IMAGE_SUB_TYPE`
--

DROP TABLE IF EXISTS `ZP_IMAGE_SUB_TYPE`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_IMAGE_SUB_TYPE` (
  `ID` tinyint(3) unsigned NOT NULL AUTO_INCREMENT,
  `DESCR` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL,
  `POST_IMAGE_TYPE_TEXT` text COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_IMAGE_TYPE`
--

DROP TABLE IF EXISTS `ZP_IMAGE_TYPE`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_IMAGE_TYPE` (
  `ID` tinyint(4) NOT NULL AUTO_INCREMENT,
  `NAME` varchar(190) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`ID`),
  UNIQUE KEY `NAME` (`NAME`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_INVALID_FILEFOLDER`
--

DROP TABLE IF EXISTS `ZP_INVALID_FILEFOLDER`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_INVALID_FILEFOLDER` (
  `ID` int(11) NOT NULL AUTO_INCREMENT,
  `ZP_LIBRARY_ID` tinyint(3) unsigned NOT NULL,
  `ZP_SCAN_PATH_ID` tinyint(3) unsigned NOT NULL,
  `SOURCE_ID` tinyint(3) unsigned NOT NULL,
  `SCAN_PATH_JSON` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `ADDED_DATETIME` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `LAST_OCCURANCE_DATETIME` datetime NOT NULL,
  `PATH` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `PATH_EXTRA` text COLLATE utf8mb4_unicode_ci,
  `REASON` text COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_INVALID_FILEFOLDER_SOURCE`
--

DROP TABLE IF EXISTS `ZP_INVALID_FILEFOLDER_SOURCE`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_INVALID_FILEFOLDER_SOURCE` (
  `ID` tinyint(4) NOT NULL AUTO_INCREMENT,
  `SOURCE` text COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_LANG`
--

DROP TABLE IF EXISTS `ZP_LANG`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_LANG` (
  `ID` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
  `ISO_639_Part3` varchar(3) COLLATE utf8mb4_unicode_ci NOT NULL,
  `ISO_639_Part3_obs1` varchar(3) COLLATE utf8mb4_unicode_ci NOT NULL,
  `ISO_639_Part2B` varchar(3) COLLATE utf8mb4_unicode_ci NOT NULL,
  `ISO_639_Part2T` varchar(3) COLLATE utf8mb4_unicode_ci NOT NULL,
  `ISO_639_Part1` varchar(2) COLLATE utf8mb4_unicode_ci NOT NULL,
  `Ref_Name` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `Native_Ref_Name` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `Comment` text COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_LIBRARY`
--

DROP TABLE IF EXISTS `ZP_LIBRARY`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_LIBRARY` (
  `ID` tinyint(3) unsigned NOT NULL AUTO_INCREMENT,
  `DESC` text COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_LIBRARY_FILE_EXTENSION`
--

DROP TABLE IF EXISTS `ZP_LIBRARY_FILE_EXTENSION`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_LIBRARY_FILE_EXTENSION` (
  `ZP_LIBRARY_ID` tinyint(3) unsigned NOT NULL,
  `ZP_FILE_EXTENSION_ID` tinyint(3) unsigned NOT NULL,
  `IGNORE_EXTENSION` tinyint(1) NOT NULL,
  PRIMARY KEY (`ZP_LIBRARY_ID`,`ZP_FILE_EXTENSION_ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_LIBRARY_RUN`
--

DROP TABLE IF EXISTS `ZP_LIBRARY_RUN`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_LIBRARY_RUN` (
  `ZP_LIBRARY_ID` int(11) NOT NULL,
  `LAST_RUN` datetime NOT NULL,
  `RUN_INTERVAL` int(11) NOT NULL,
  PRIMARY KEY (`ZP_LIBRARY_ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_PEOPLE`
--

DROP TABLE IF EXISTS `ZP_PEOPLE`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_PEOPLE` (
  `ID` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `DOB` date DEFAULT NULL,
  `NAME` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `ADDED_DATETIME` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_PEOPLE_EAPI_XREF`
--

DROP TABLE IF EXISTS `ZP_PEOPLE_EAPI_XREF`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_PEOPLE_EAPI_XREF` (
  `ZP_PEOPLE_ID` int(11) unsigned NOT NULL,
  `ZP_EAPI_ID` tinyint(3) unsigned NOT NULL,
  `ZP_EAPI_EID` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `ADDED_DATETIME` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`ZP_EAPI_ID`,`ZP_PEOPLE_ID`),
  KEY `ZP_PEOPLE_ID` (`ZP_PEOPLE_ID`),
  CONSTRAINT `ZP_PEOPLE_EAPI_XREF_ibfk_1` FOREIGN KEY (`ZP_PEOPLE_ID`) REFERENCES `ZP_PEOPLE` (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_PROCESS_RUN`
--

DROP TABLE IF EXISTS `ZP_PROCESS_RUN`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_PROCESS_RUN` (
  `ZP_PROCESS_ID` int(11) NOT NULL AUTO_INCREMENT,
  `PROCESS_NAME` varchar(25) COLLATE utf8mb4_unicode_ci NOT NULL,
  `ZP_LIBRARY_ID` tinyint(3) unsigned NOT NULL,
  `ENABLED` tinyint(1) NOT NULL DEFAULT '0',
  `LAST_RUN_START` datetime NOT NULL,
  `LAST_RUN_END` datetime NOT NULL,
  `FORCE_RUN` tinyint(1) NOT NULL DEFAULT '0',
  `FORCE_RUN_REQUEST_DATE_TIME` datetime NOT NULL,
  `RUN_INTERVAL` smallint(6) NOT NULL DEFAULT '60',
  `RUN_BETWEEN` tinyint(1) NOT NULL DEFAULT '0',
  `RUN_BETWEEN_START` varchar(4) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `RUN_BETWEEN_END` varchar(4) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`ZP_PROCESS_ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_PROCESS_RUNNING`
--

DROP TABLE IF EXISTS `ZP_PROCESS_RUNNING`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_PROCESS_RUNNING` (
  `ZP_LIBRARY_ID` tinyint(4) NOT NULL,
  `ZP_PROCESS_ID` tinyint(3) unsigned NOT NULL,
  `PROCESS` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `PROCESS_STATE` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `PROCESS_DATE_TIME` datetime NOT NULL,
  `PROCESS_STATE_DATE_TIME` datetime NOT NULL,
  PRIMARY KEY (`ZP_LIBRARY_ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_PROCESS_RUNNING_HISTORY`
--

DROP TABLE IF EXISTS `ZP_PROCESS_RUNNING_HISTORY`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_PROCESS_RUNNING_HISTORY` (
  `ID` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `ZP_LIBRARY_ID` tinyint(3) unsigned NOT NULL,
  `ZP_PROCESS_ID` tinyint(3) unsigned NOT NULL,
  `PROCESS` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `PROCESS_STATE` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `PROCESS_STATE_DATETIME` datetime NOT NULL,
  `PROCESS_STATE_INITIAL_DATETIME` datetime NOT NULL,
  `COUNT` int(10) unsigned NOT NULL,
  PRIMARY KEY (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_RES`
--

DROP TABLE IF EXISTS `ZP_RES`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_RES` (
  `ID` tinyint(1) NOT NULL AUTO_INCREMENT,
  `RES` smallint(6) NOT NULL,
  `SCORE` tinyint(3) unsigned NOT NULL,
  `FILE_REQUIRE_RES` tinyint(1) NOT NULL DEFAULT '0',
  `HD` tinyint(1) NOT NULL,
  `MIN_WIDTH` smallint(5) unsigned NOT NULL,
  `MAX_WIDTH` smallint(5) unsigned NOT NULL,
  `MIN_HEIGHT` smallint(5) unsigned NOT NULL,
  `MAX_HEIGHT` smallint(5) unsigned NOT NULL,
  PRIMARY KEY (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_RETRY`
--

DROP TABLE IF EXISTS `ZP_RETRY`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_RETRY` (
  `ZP_RETRY_TYPE_ID` tinyint(3) unsigned NOT NULL,
  `ZP_RETRY_ENTITY_TYPE_ID` tinyint(3) unsigned NOT NULL,
  `ZP_RETRY_ENTITY_ID` int(10) unsigned NOT NULL,
  `ZP_EAPI_ID` tinyint(3) unsigned NOT NULL DEFAULT '0',
  `ZP_LANG_ID` smallint(5) unsigned NOT NULL DEFAULT '0',
  `DATETIME` datetime NOT NULL,
  `COUNT` tinyint(3) unsigned NOT NULL,
  PRIMARY KEY (`ZP_RETRY_TYPE_ID`,`ZP_RETRY_ENTITY_TYPE_ID`,`ZP_RETRY_ENTITY_ID`,`ZP_EAPI_ID`,`ZP_LANG_ID`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_RETRY_COUNT`
--

DROP TABLE IF EXISTS `ZP_RETRY_COUNT`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_RETRY_COUNT` (
  `ZP_RETRY_TYPE_ID` tinyint(3) unsigned NOT NULL,
  `COUNT` tinyint(3) unsigned NOT NULL,
  `DELAY` tinyint(3) unsigned NOT NULL,
  PRIMARY KEY (`ZP_RETRY_TYPE_ID`,`COUNT`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_RETRY_ENTITY_TYPE`
--

DROP TABLE IF EXISTS `ZP_RETRY_ENTITY_TYPE`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_RETRY_ENTITY_TYPE` (
  `ID` tinyint(4) NOT NULL AUTO_INCREMENT,
  `NAME` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL,
  `ZP_LIBRARY_ID` tinyint(3) unsigned NOT NULL,
  PRIMARY KEY (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_RETRY_TYPE`
--

DROP TABLE IF EXISTS `ZP_RETRY_TYPE`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_RETRY_TYPE` (
  `ID` tinyint(3) unsigned NOT NULL AUTO_INCREMENT,
  `DESCR` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL,
  `MAX_COUNT` tinyint(3) unsigned NOT NULL,
  `RUN_BETWEEN` tinyint(1) NOT NULL DEFAULT '0',
  `RUN_BETWEEN_START` varchar(4) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `RUN_BETWEEN_END` varchar(4) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_ROLE`
--

DROP TABLE IF EXISTS `ZP_ROLE`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_ROLE` (
  `ID` int(11) NOT NULL AUTO_INCREMENT,
  `DESC` text COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_SCAN_PATH`
--

DROP TABLE IF EXISTS `ZP_SCAN_PATH`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_SCAN_PATH` (
  `ID` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
  `PATH` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `ZP_LIBRARY_ID` tinyint(3) unsigned NOT NULL,
  `ZP_SCAN_PATH_FS_TYPE_ID` tinyint(3) unsigned DEFAULT NULL,
  `LAST_MOD_DATETIME` datetime NOT NULL,
  `LAST_SCAN_DATETIME` datetime NOT NULL,
  `FORCE_FULL_SCAN` tinyint(1) NOT NULL,
  `ALWAYS_FULL_SCAN` tinyint(1) NOT NULL,
  `ENABLED` tinyint(1) NOT NULL DEFAULT '1',
  `VERIFY` tinyint(1) NOT NULL DEFAULT '1',
  PRIMARY KEY (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_SCAN_PATH_FS_TYPE`
--

DROP TABLE IF EXISTS `ZP_SCAN_PATH_FS_TYPE`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_SCAN_PATH_FS_TYPE` (
  `ID` tinyint(3) unsigned NOT NULL AUTO_INCREMENT,
  `DESCRIPTION` text COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_SCAN_PATH_SHARE_XREF`
--

DROP TABLE IF EXISTS `ZP_SCAN_PATH_SHARE_XREF`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_SCAN_PATH_SHARE_XREF` (
  `ZP_SCAN_PATH_ID` tinyint(3) unsigned NOT NULL,
  `ZP_SHARE_ID` tinyint(3) unsigned NOT NULL,
  `ZP_SHARE_SERVER_ID` tinyint(3) unsigned NOT NULL,
  `ZP_SHARE_CREDENTIAL_ID` tinyint(3) unsigned NOT NULL,
  PRIMARY KEY (`ZP_SCAN_PATH_ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_SCHEMA_VERSION`
--

DROP TABLE IF EXISTS `ZP_SCHEMA_VERSION`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_SCHEMA_VERSION` (
  `RELEASE` smallint(6) NOT NULL,
  `MAJOR_VERSION` smallint(6) NOT NULL,
  `MINOR_VERSION` smallint(6) NOT NULL,
  `NOTES` text COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`RELEASE`,`MAJOR_VERSION`,`MINOR_VERSION`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_SHARE`
--

DROP TABLE IF EXISTS `ZP_SHARE`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_SHARE` (
  `ID` tinyint(3) unsigned NOT NULL AUTO_INCREMENT,
  `REF_NAME` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `SHARE_NAME` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `DOMAIN` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_SHARE_CREDENTIAL`
--

DROP TABLE IF EXISTS `ZP_SHARE_CREDENTIAL`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_SHARE_CREDENTIAL` (
  `ID` tinyint(4) NOT NULL AUTO_INCREMENT,
  `REF_NAME` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `USERNAME` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `PASSWORD` text COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_SHARE_SERVER`
--

DROP TABLE IF EXISTS `ZP_SHARE_SERVER`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_SHARE_SERVER` (
  `ID` int(11) NOT NULL AUTO_INCREMENT,
  `REF_NAME` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `REMOTE_NAME` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `HOSTNAME` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL,
  `PORT` smallint(5) unsigned NOT NULL,
  PRIMARY KEY (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_SOURCE`
--

DROP TABLE IF EXISTS `ZP_SOURCE`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_SOURCE` (
  `ID` tinyint(1) NOT NULL AUTO_INCREMENT,
  `SOURCE` text NOT NULL,
  `SCORE` tinyint(3) unsigned NOT NULL,
  `DISC_SCORE` tinyint(3) unsigned NOT NULL,
  PRIMARY KEY (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_TCODEC_XREF`
--

DROP TABLE IF EXISTS `ZP_TCODEC_XREF`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_TCODEC_XREF` (
  `ID` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
  `ZP_TCODEC_ID` tinyint(3) unsigned NOT NULL,
  `CODEC_ID` text COLLATE utf8mb4_unicode_ci,
  `CODEC` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_TEMPLATE`
--

DROP TABLE IF EXISTS `ZP_TEMPLATE`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_TEMPLATE` (
  `ID` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `REF_NAME` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `PATH` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `PATH_TYPE` tinyint(3) unsigned NOT NULL,
  `LAST_MOD_DATETIME` datetime NOT NULL,
  PRIMARY KEY (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_TV`
--

DROP TABLE IF EXISTS `ZP_TV`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_TV` (
  `ID` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `ADDED_DATE_TIME` datetime NOT NULL,
  `LAST_EDIT_DATETIME` datetime NOT NULL,
  `ZP_TV_FILEFOLDER_ID` int(10) unsigned NOT NULL,
  PRIMARY KEY (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_TV_EAPI_EID`
--

DROP TABLE IF EXISTS `ZP_TV_EAPI_EID`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_TV_EAPI_EID` (
  `ZP_TV_ID` int(11) NOT NULL,
  `ZP_EAPI_EID` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `ZP_EAPI_ID` tinyint(4) NOT NULL,
  PRIMARY KEY (`ZP_TV_ID`,`ZP_EAPI_ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_TV_EPISODE`
--

DROP TABLE IF EXISTS `ZP_TV_EPISODE`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_TV_EPISODE` (
  `ID` int(11) NOT NULL AUTO_INCREMENT,
  `ZP_TV_ID` int(10) unsigned NOT NULL,
  `SEASON` smallint(5) unsigned NOT NULL,
  `EPISODE` smallint(8) unsigned NOT NULL,
  `LAST_EDIT_DATETIME` datetime NOT NULL,
  `ZP_TV_EPISODE_FILEFOLDER_ID` int(10) unsigned DEFAULT NULL,
  PRIMARY KEY (`ID`),
  UNIQUE KEY `ZP_TV_ID` (`ZP_TV_ID`,`SEASON`,`EPISODE`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_TV_EPISODE_FILEFOLDER`
--

DROP TABLE IF EXISTS `ZP_TV_EPISODE_FILEFOLDER`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_TV_EPISODE_FILEFOLDER` (
  `ID` int(11) NOT NULL AUTO_INCREMENT,
  `ZP_TV_FILEFOLDER_ID` smallint(5) unsigned NOT NULL,
  `SEASON` smallint(5) unsigned NOT NULL,
  `FIRST_EPISODE` smallint(8) unsigned NOT NULL,
  `LAST_EPISODE` smallint(8) unsigned NOT NULL,
  `LAST_PATH` text COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_TV_EPISODE_IMAGE_RENDER_HASH`
--

DROP TABLE IF EXISTS `ZP_TV_EPISODE_IMAGE_RENDER_HASH`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_TV_EPISODE_IMAGE_RENDER_HASH` (
  `ID` int(11) NOT NULL AUTO_INCREMENT,
  `ZP_TV_ID` smallint(5) unsigned NOT NULL,
  `SEASON` smallint(5) unsigned NOT NULL,
  `FIRST_EPISODE` smallint(5) unsigned NOT NULL,
  `ZP_IMAGE_SUB_TYPE` tinyint(3) unsigned NOT NULL,
  `ZP_TV_IMAGE_TYPE_ID` tinyint(3) unsigned NOT NULL,
  `HASH` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `ZP_TEMPLATE_ID` smallint(6) unsigned NOT NULL,
  PRIMARY KEY (`ID`),
  UNIQUE KEY `ZP_TV_ID` (`ZP_TV_ID`,`SEASON`,`FIRST_EPISODE`,`ZP_IMAGE_SUB_TYPE`,`ZP_TV_IMAGE_TYPE_ID`,`HASH`,`ZP_TEMPLATE_ID`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_TV_EPISODE_IMAGE_SUB_TYPE_XREF`
--

DROP TABLE IF EXISTS `ZP_TV_EPISODE_IMAGE_SUB_TYPE_XREF`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_TV_EPISODE_IMAGE_SUB_TYPE_XREF` (
  `ZP_IMAGE_SUB_TYPE` tinyint(3) unsigned NOT NULL,
  `pre_ident` text COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`ZP_IMAGE_SUB_TYPE`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_TV_EPISODE_OVERVIEW`
--

DROP TABLE IF EXISTS `ZP_TV_EPISODE_OVERVIEW`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_TV_EPISODE_OVERVIEW` (
  `ID` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `ZP_TV_ID` smallint(5) unsigned NOT NULL,
  `ZP_LANG_ID` smallint(5) unsigned NOT NULL,
  `ZP_EAPI_ID` tinyint(3) unsigned NOT NULL,
  `ZP_USER_ID` smallint(5) unsigned NOT NULL DEFAULT '0',
  `LANG_DEFAULT` tinyint(1) NOT NULL DEFAULT '0',
  `MAIN_DEFAULT` tinyint(1) NOT NULL DEFAULT '0',
  `OVERVIEW` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `SEASON` smallint(5) unsigned NOT NULL,
  `EPISODE` smallint(5) unsigned NOT NULL,
  PRIMARY KEY (`ID`),
  UNIQUE KEY `ZP_TV_ID` (`ZP_TV_ID`,`ZP_LANG_ID`,`ZP_EAPI_ID`,`ZP_USER_ID`,`LANG_DEFAULT`,`MAIN_DEFAULT`,`SEASON`,`EPISODE`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_TV_EPISODE_RAW_IMAGE`
--

DROP TABLE IF EXISTS `ZP_TV_EPISODE_RAW_IMAGE`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_TV_EPISODE_RAW_IMAGE` (
  `ID` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `ZP_EAPI_ID` tinyint(3) unsigned NOT NULL,
  `ZP_EAPI_IMAGE_REF` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `ADDED_DATETIME` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `ZP_ENTITY_TYPE_ID` tinyint(3) unsigned NOT NULL,
  `ZP_ENTITY_ID` int(10) unsigned NOT NULL,
  `SEASON` smallint(5) unsigned NOT NULL,
  `EPISODE` smallint(5) unsigned NOT NULL,
  `ZP_USER_ID` int(11) DEFAULT NULL,
  `ZP_LANG_ID` int(11) DEFAULT NULL,
  `LANG_DEFAULT` tinyint(1) DEFAULT NULL,
  `MAIN_DEFAULT` tinyint(1) DEFAULT NULL,
  `FILENAME` text COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_TV_EPISODE_SPEICAL_TYPE_XREF`
--

DROP TABLE IF EXISTS `ZP_TV_EPISODE_SPEICAL_TYPE_XREF`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_TV_EPISODE_SPEICAL_TYPE_XREF` (
  `ZP_TV_ID` int(10) unsigned NOT NULL,
  `SEASON` smallint(5) unsigned NOT NULL,
  `FIRST_EPISODE` smallint(5) unsigned NOT NULL,
  `ZP_TV_SPECIAL_TYPE_ID` tinyint(3) unsigned NOT NULL,
  `ZP_EAPI_ID_REQ` tinyint(3) unsigned NOT NULL DEFAULT '0',
  `ZP_EAPI_ID_ACT` tinyint(3) unsigned NOT NULL,
  `ZP_LANG_ID_REQ` smallint(5) unsigned NOT NULL DEFAULT '0',
  `ZP_LANG_ID_ACT` smallint(5) unsigned NOT NULL DEFAULT '0',
  `ZP_TV_IMAGE_TYPE_ID` tinyint(3) unsigned NOT NULL,
  PRIMARY KEY (`ZP_TV_ID`,`SEASON`,`FIRST_EPISODE`,`ZP_TV_SPECIAL_TYPE_ID`,`ZP_EAPI_ID_REQ`,`ZP_LANG_ID_REQ`,`ZP_TV_IMAGE_TYPE_ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_TV_EPISODE_TITLE`
--

DROP TABLE IF EXISTS `ZP_TV_EPISODE_TITLE`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_TV_EPISODE_TITLE` (
  `ID` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `ZP_TV_ID` smallint(5) unsigned NOT NULL,
  `ZP_LANG_ID` smallint(5) unsigned NOT NULL,
  `ZP_EAPI_ID` tinyint(3) unsigned NOT NULL,
  `ZP_USER_ID` smallint(5) unsigned NOT NULL DEFAULT '0',
  `LANG_DEFAULT` tinyint(1) NOT NULL DEFAULT '0',
  `MAIN_DEFAULT` tinyint(1) NOT NULL DEFAULT '0',
  `TITLE` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `SEASON` smallint(5) unsigned NOT NULL,
  `EPISODE` smallint(5) unsigned NOT NULL,
  PRIMARY KEY (`ID`),
  UNIQUE KEY `ZP_TV_ID` (`ZP_TV_ID`,`ZP_LANG_ID`,`ZP_EAPI_ID`,`ZP_USER_ID`,`LANG_DEFAULT`,`MAIN_DEFAULT`,`SEASON`,`EPISODE`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_TV_FILEFOLDER`
--

DROP TABLE IF EXISTS `ZP_TV_FILEFOLDER`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_TV_FILEFOLDER` (
  `ID` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `ZP_TV_ID` mediumint(8) unsigned DEFAULT NULL,
  `ZP_SCAN_PATH_ID` smallint(5) unsigned NOT NULL,
  `LAST_PATH` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `ENABLED` tinyint(1) NOT NULL DEFAULT '1',
  `ENABLED_UPDATE_DATETIME` datetime NOT NULL,
  PRIMARY KEY (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_TV_GENRE_XREF`
--

DROP TABLE IF EXISTS `ZP_TV_GENRE_XREF`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_TV_GENRE_XREF` (
  `ZP_TV_ID` int(10) unsigned NOT NULL,
  `ZP_GENRE_ID` tinyint(3) unsigned NOT NULL,
  PRIMARY KEY (`ZP_TV_ID`,`ZP_GENRE_ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_TV_IMAGE_RENDER_HASH`
--

DROP TABLE IF EXISTS `ZP_TV_IMAGE_RENDER_HASH`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_TV_IMAGE_RENDER_HASH` (
  `ID` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `ZP_TV_ID` int(10) unsigned NOT NULL,
  `ZP_IMAGE_SUB_TYPE` tinyint(3) unsigned NOT NULL,
  `ZP_TV_IMAGE_TYPE_ID` tinyint(3) unsigned NOT NULL,
  `HASH` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `ZP_TEMPLATE_ID` smallint(5) unsigned NOT NULL,
  PRIMARY KEY (`ID`),
  UNIQUE KEY `ZP_TV_ID` (`ZP_TV_ID`,`ZP_IMAGE_SUB_TYPE`,`ZP_TV_IMAGE_TYPE_ID`,`HASH`,`ZP_TEMPLATE_ID`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_TV_OVERVIEW`
--

DROP TABLE IF EXISTS `ZP_TV_OVERVIEW`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_TV_OVERVIEW` (
  `ID` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `ZP_TV_ID` int(10) unsigned NOT NULL,
  `ZP_LANG_ID` smallint(5) unsigned NOT NULL,
  `ZP_EAPI_ID` tinyint(3) unsigned NOT NULL,
  `ZP_USER_ID` smallint(5) unsigned NOT NULL DEFAULT '0',
  `LANG_DEFAULT` tinyint(1) NOT NULL DEFAULT '0',
  `MAIN_DEFAULT` tinyint(1) NOT NULL DEFAULT '0',
  `OVERVIEW` text COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`ID`),
  UNIQUE KEY `ZP_TV_ID` (`ZP_TV_ID`,`ZP_LANG_ID`,`ZP_EAPI_ID`,`ZP_USER_ID`,`LANG_DEFAULT`,`MAIN_DEFAULT`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_TV_RATING`
--

DROP TABLE IF EXISTS `ZP_TV_RATING`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_TV_RATING` (
  `ZP_TV_ID` int(3) unsigned NOT NULL,
  `RATING` tinyint(3) unsigned NOT NULL,
  PRIMARY KEY (`ZP_TV_ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_TV_RAW_IMAGE`
--

DROP TABLE IF EXISTS `ZP_TV_RAW_IMAGE`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_TV_RAW_IMAGE` (
  `ID` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `ZP_EAPI_ID` tinyint(3) unsigned NOT NULL,
  `ZP_EAPI_IMAGE_REF` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `ADDED_DATETIME` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `ZP_ENTITY_TYPE_ID` tinyint(3) unsigned NOT NULL,
  `ZP_ENTITY_ID` int(10) unsigned NOT NULL,
  `ZP_USER_ID` int(11) DEFAULT NULL,
  `ZP_LANG_ID` int(11) DEFAULT NULL,
  `LANG_DEFAULT` tinyint(1) DEFAULT NULL,
  `MAIN_DEFAULT` tinyint(1) DEFAULT NULL,
  `FILENAME` text COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_TV_RELEASE`
--

DROP TABLE IF EXISTS `ZP_TV_RELEASE`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_TV_RELEASE` (
  `ZP_TV_ID` int(10) unsigned NOT NULL,
  `RELEASE_DATE` date NOT NULL,
  PRIMARY KEY (`ZP_TV_ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_TV_ROLE_XREF`
--

DROP TABLE IF EXISTS `ZP_TV_ROLE_XREF`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_TV_ROLE_XREF` (
  `ZP_TV_ID` int(10) unsigned NOT NULL,
  `ZP_PEOPLE_ID` int(10) unsigned NOT NULL,
  `ZP_ROLE_ID` tinyint(3) unsigned NOT NULL,
  `ROLE_ORDER` smallint(6) DEFAULT NULL,
  PRIMARY KEY (`ZP_TV_ID`,`ZP_PEOPLE_ID`,`ZP_ROLE_ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_TV_RUNNING`
--

DROP TABLE IF EXISTS `ZP_TV_RUNNING`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_TV_RUNNING` (
  `ZP_TV_ID` mediumint(8) unsigned NOT NULL,
  PRIMARY KEY (`ZP_TV_ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_TV_RUNTIME`
--

DROP TABLE IF EXISTS `ZP_TV_RUNTIME`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_TV_RUNTIME` (
  `ZP_TV_ID` int(10) unsigned NOT NULL,
  `RUNTIME` smallint(5) unsigned NOT NULL,
  PRIMARY KEY (`ZP_TV_ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_TV_SEASON_RAW_IMAGE`
--

DROP TABLE IF EXISTS `ZP_TV_SEASON_RAW_IMAGE`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_TV_SEASON_RAW_IMAGE` (
  `ID` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `ZP_EAPI_ID` tinyint(3) unsigned NOT NULL,
  `ZP_EAPI_IMAGE_REF` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `ADDED_DATETIME` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `ZP_ENTITY_TYPE_ID` tinyint(3) unsigned NOT NULL,
  `ZP_ENTITY_ID` int(10) unsigned NOT NULL,
  `SEASON` smallint(5) unsigned NOT NULL,
  `ZP_USER_ID` int(11) DEFAULT NULL,
  `ZP_LANG_ID` int(11) DEFAULT NULL,
  `LANG_DEFAULT` tinyint(1) DEFAULT NULL,
  `MAIN_DEFAULT` tinyint(1) DEFAULT NULL,
  `FILENAME` text COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_TV_SPECIAL_TYPE`
--

DROP TABLE IF EXISTS `ZP_TV_SPECIAL_TYPE`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_TV_SPECIAL_TYPE` (
  `ID` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
  `DESCR` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `USES_LANG` tinyint(1) NOT NULL DEFAULT '0',
  PRIMARY KEY (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_TV_SPEICAL_TYPE_XREF`
--

DROP TABLE IF EXISTS `ZP_TV_SPEICAL_TYPE_XREF`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_TV_SPEICAL_TYPE_XREF` (
  `ZP_TV_ID` int(10) unsigned NOT NULL,
  `ZP_TV_SPECIAL_TYPE_ID` tinyint(3) unsigned NOT NULL,
  `ZP_EAPI_ID_REQ` tinyint(3) unsigned NOT NULL DEFAULT '0',
  `ZP_EAPI_ID_ACT` tinyint(3) unsigned NOT NULL,
  `ZP_LANG_ID_REQ` smallint(5) unsigned NOT NULL DEFAULT '0',
  `ZP_LANG_ID_ACT` smallint(5) unsigned NOT NULL DEFAULT '0',
  `ZP_TV_IMAGE_TYPE_ID` tinyint(3) unsigned NOT NULL,
  PRIMARY KEY (`ZP_TV_ID`,`ZP_TV_SPECIAL_TYPE_ID`,`ZP_EAPI_ID_REQ`,`ZP_LANG_ID_REQ`,`ZP_TV_IMAGE_TYPE_ID`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_TV_TITLE`
--

DROP TABLE IF EXISTS `ZP_TV_TITLE`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_TV_TITLE` (
  `ID` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `ZP_TV_ID` int(10) unsigned NOT NULL,
  `ZP_TV_TITLE_TYPE_ID` tinyint(3) unsigned NOT NULL,
  `ZP_LANG_ID` smallint(5) unsigned NOT NULL,
  `ZP_EAPI_ID` smallint(5) unsigned NOT NULL,
  `ZP_USER_ID` smallint(5) unsigned NOT NULL DEFAULT '0',
  `LANG_DEFAULT` tinyint(1) NOT NULL DEFAULT '0',
  `MAIN_DEFAULT` tinyint(1) NOT NULL DEFAULT '0',
  `TITLE` text COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`ID`),
  UNIQUE KEY `ZP_TV_ID` (`ZP_TV_ID`,`ZP_TV_TITLE_TYPE_ID`,`ZP_LANG_ID`,`ZP_EAPI_ID`,`ZP_USER_ID`,`LANG_DEFAULT`,`MAIN_DEFAULT`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_USER`
--

DROP TABLE IF EXISTS `ZP_USER`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_USER` (
  `ID` tinyint(3) unsigned NOT NULL AUTO_INCREMENT,
  `USERNAME` text NOT NULL,
  `PASSWORD` text NOT NULL,
  `ENABLED` tinyint(1) NOT NULL,
  `LAST_EDIT_DATETIME` datetime NOT NULL,
  PRIMARY KEY (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_USER_EAPI_PREF`
--

DROP TABLE IF EXISTS `ZP_USER_EAPI_PREF`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_USER_EAPI_PREF` (
  `ZP_USER_ID` tinyint(3) unsigned NOT NULL,
  `ZP_EAPI_ID` tinyint(3) unsigned NOT NULL,
  `ZP_LIBRARY_ID` int(11) NOT NULL,
  `ORDER` tinyint(3) unsigned NOT NULL,
  PRIMARY KEY (`ZP_USER_ID`,`ZP_EAPI_ID`,`ZP_LIBRARY_ID`,`ORDER`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_USER_FILM_COLLECTION_ENTITY_XREF`
--

DROP TABLE IF EXISTS `ZP_USER_FILM_COLLECTION_ENTITY_XREF`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_USER_FILM_COLLECTION_ENTITY_XREF` (
  `ID` int(11) NOT NULL AUTO_INCREMENT,
  `ZP_USER_ID` smallint(5) unsigned NOT NULL,
  `ZP_FILM_COLLECTION_ID` int(10) unsigned NOT NULL,
  `ZP_FILM_COLLECTION_ENTITY_TYPE_ID` smallint(5) unsigned NOT NULL,
  `ZP_FILM_COLLECTION_ENTITY_ID` int(10) unsigned DEFAULT NULL,
  `FORCED` tinyint(1) NOT NULL DEFAULT '0',
  `LAST_UPDATE_DATETIME` datetime NOT NULL,
  PRIMARY KEY (`ID`),
  UNIQUE KEY `ZP_USER_ID` (`ZP_USER_ID`,`ZP_FILM_COLLECTION_ID`,`ZP_FILM_COLLECTION_ENTITY_TYPE_ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_USER_FILM_COLLECTION_IMAGE_RENDER_HASH_XREF`
--

DROP TABLE IF EXISTS `ZP_USER_FILM_COLLECTION_IMAGE_RENDER_HASH_XREF`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_USER_FILM_COLLECTION_IMAGE_RENDER_HASH_XREF` (
  `ZP_USER_ID` tinyint(3) unsigned NOT NULL,
  `ZP_FILM_COLLECTION_ID` int(10) unsigned NOT NULL,
  `ZP_FILM_COLLECTION_IMAGE_TYPE_ID` tinyint(3) unsigned NOT NULL,
  `ZP_IMAGE_SUB_TYPE` tinyint(3) unsigned NOT NULL,
  `ZP_FILM_COLLECTION_IMAGE_RENDER_HASH_ID` int(10) unsigned NOT NULL,
  PRIMARY KEY (`ZP_USER_ID`,`ZP_FILM_COLLECTION_ID`,`ZP_FILM_COLLECTION_IMAGE_TYPE_ID`,`ZP_IMAGE_SUB_TYPE`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_USER_FILM_ENTITY_XREF`
--

DROP TABLE IF EXISTS `ZP_USER_FILM_ENTITY_XREF`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_USER_FILM_ENTITY_XREF` (
  `ID` int(11) NOT NULL AUTO_INCREMENT,
  `ZP_USER_ID` smallint(5) unsigned NOT NULL,
  `ZP_FILM_ID` int(10) unsigned NOT NULL,
  `ZP_FILM_ENTITY_TYPE_ID` smallint(5) unsigned NOT NULL,
  `ZP_FILM_ENTITY_ID` int(10) unsigned DEFAULT NULL,
  `FORCED` tinyint(1) NOT NULL DEFAULT '0',
  `LAST_UPDATE_DATETIME` datetime NOT NULL,
  PRIMARY KEY (`ID`),
  UNIQUE KEY `ZP_USER_ID` (`ZP_USER_ID`,`ZP_FILM_ID`,`ZP_FILM_ENTITY_TYPE_ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_USER_FILM_FAVOURITE`
--

DROP TABLE IF EXISTS `ZP_USER_FILM_FAVOURITE`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_USER_FILM_FAVOURITE` (
  `ZP_FILM_ID` int(10) unsigned NOT NULL,
  `ZP_USER_ID` smallint(5) unsigned NOT NULL,
  PRIMARY KEY (`ZP_FILM_ID`,`ZP_USER_ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_USER_FILM_IMAGE_RENDER_HASH_XREF`
--

DROP TABLE IF EXISTS `ZP_USER_FILM_IMAGE_RENDER_HASH_XREF`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_USER_FILM_IMAGE_RENDER_HASH_XREF` (
  `ZP_USER_ID` tinyint(3) unsigned NOT NULL,
  `ZP_FILM_ID` int(10) unsigned NOT NULL,
  `ZP_FILM_IMAGE_TYPE_ID` tinyint(3) unsigned NOT NULL,
  `ZP_IMAGE_SUB_TYPE` tinyint(3) unsigned NOT NULL,
  `ZP_FILM_IMAGE_RENDER_HASH_ID` int(10) unsigned NOT NULL,
  PRIMARY KEY (`ZP_USER_ID`,`ZP_FILM_ID`,`ZP_FILM_IMAGE_TYPE_ID`,`ZP_IMAGE_SUB_TYPE`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_USER_FILM_TITLE_TYPE_PREF`
--

DROP TABLE IF EXISTS `ZP_USER_FILM_TITLE_TYPE_PREF`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_USER_FILM_TITLE_TYPE_PREF` (
  `ZP_USER_ID` tinyint(3) unsigned NOT NULL,
  `ZP_FILM_TITLE_TYPE_ID` tinyint(3) unsigned NOT NULL,
  PRIMARY KEY (`ZP_USER_ID`,`ZP_FILM_TITLE_TYPE_ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_USER_FILM_TOWATCH`
--

DROP TABLE IF EXISTS `ZP_USER_FILM_TOWATCH`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_USER_FILM_TOWATCH` (
  `ZP_FILM_ID` int(10) unsigned NOT NULL,
  `ZP_USER_ID` smallint(5) unsigned NOT NULL,
  PRIMARY KEY (`ZP_FILM_ID`,`ZP_USER_ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_USER_FILM_WATCHED`
--

DROP TABLE IF EXISTS `ZP_USER_FILM_WATCHED`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_USER_FILM_WATCHED` (
  `ZP_FILM_ID` int(10) unsigned NOT NULL,
  `ZP_USER_ID` tinyint(3) unsigned NOT NULL,
  `DATETIME` datetime NOT NULL,
  PRIMARY KEY (`ZP_FILM_ID`,`ZP_USER_ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_USER_GROUP`
--

DROP TABLE IF EXISTS `ZP_USER_GROUP`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_USER_GROUP` (
  `ZP_USER_ID` tinyint(3) unsigned NOT NULL,
  `ZP_DUNE_ID` tinyint(3) unsigned NOT NULL,
  PRIMARY KEY (`ZP_USER_ID`,`ZP_DUNE_ID`),
  KEY `FK_ZP_DUNE_ID` (`ZP_DUNE_ID`),
  CONSTRAINT `FK_ZP_DUNE_ID` FOREIGN KEY (`ZP_DUNE_ID`) REFERENCES `ZP_DUNE` (`ID`),
  CONSTRAINT `FK_ZP_USER_ID` FOREIGN KEY (`ZP_USER_ID`) REFERENCES `ZP_USER` (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_USER_IMAGE_RENDER_HASH`
--

DROP TABLE IF EXISTS `ZP_USER_IMAGE_RENDER_HASH`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_USER_IMAGE_RENDER_HASH` (
  `ID` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `ZP_USER_IMAGE_TYPE_ID` tinyint(3) unsigned NOT NULL,
  `ZP_USER_ID` smallint(5) unsigned NOT NULL,
  `ZP_IMAGE_SUB_TYPE` tinyint(3) unsigned NOT NULL,
  `HASH` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `TEMPLATE_NAME` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_USER_LIBRARY_LANG`
--

DROP TABLE IF EXISTS `ZP_USER_LIBRARY_LANG`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_USER_LIBRARY_LANG` (
  `ZP_USER_ID` tinyint(3) unsigned NOT NULL,
  `ZP_LANG_ID` smallint(5) unsigned NOT NULL,
  `ZP_LIBRARY_ID` tinyint(3) unsigned NOT NULL,
  PRIMARY KEY (`ZP_USER_ID`,`ZP_LANG_ID`,`ZP_LIBRARY_ID`),
  UNIQUE KEY `ZP_USER_ID` (`ZP_USER_ID`,`ZP_LIBRARY_ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_USER_PRIV`
--

DROP TABLE IF EXISTS `ZP_USER_PRIV`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_USER_PRIV` (
  `ZP_USER_ID` int(11) NOT NULL,
  `ZP_USER_PRIV_ID` tinyint(4) NOT NULL,
  PRIMARY KEY (`ZP_USER_ID`,`ZP_USER_PRIV_ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_USER_SPECIAL_TYPE`
--

DROP TABLE IF EXISTS `ZP_USER_SPECIAL_TYPE`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_USER_SPECIAL_TYPE` (
  `ID` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
  `DESCR` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `USES_LANG` tinyint(1) NOT NULL DEFAULT '0',
  PRIMARY KEY (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_USER_TEMPLATE_XREF`
--

DROP TABLE IF EXISTS `ZP_USER_TEMPLATE_XREF`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_USER_TEMPLATE_XREF` (
  `ZP_USER_ID` int(10) unsigned NOT NULL,
  `ZP_TEMPLATE_ID` smallint(5) unsigned NOT NULL,
  PRIMARY KEY (`ZP_USER_ID`,`ZP_TEMPLATE_ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_USER_TV_ENTITY_XREF`
--

DROP TABLE IF EXISTS `ZP_USER_TV_ENTITY_XREF`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_USER_TV_ENTITY_XREF` (
  `ID` int(11) NOT NULL AUTO_INCREMENT,
  `ZP_USER_ID` smallint(5) unsigned NOT NULL,
  `ZP_TV_ID` int(10) unsigned NOT NULL,
  `ZP_TV_ENTITY_TYPE_ID` smallint(5) unsigned NOT NULL,
  `ZP_TV_ENTITY_ID` int(10) unsigned DEFAULT NULL,
  `FORCED` tinyint(1) NOT NULL DEFAULT '0',
  `LAST_UPDATE_DATETIME` datetime NOT NULL,
  PRIMARY KEY (`ID`),
  UNIQUE KEY `ZP_USER_ID` (`ZP_USER_ID`,`ZP_TV_ID`,`ZP_TV_ENTITY_TYPE_ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_USER_TV_EPISODE_ENTITY_XREF`
--

DROP TABLE IF EXISTS `ZP_USER_TV_EPISODE_ENTITY_XREF`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_USER_TV_EPISODE_ENTITY_XREF` (
  `ID` int(11) NOT NULL AUTO_INCREMENT,
  `ZP_USER_ID` smallint(5) unsigned NOT NULL,
  `ZP_TV_ID` int(10) unsigned NOT NULL,
  `SEASON` smallint(5) unsigned NOT NULL,
  `EPISODE` int(11) NOT NULL,
  `ZP_TV_ENTITY_TYPE_ID` smallint(5) unsigned NOT NULL,
  `ZP_TV_ENTITY_ID` int(10) unsigned DEFAULT NULL,
  `FORCED` tinyint(1) NOT NULL DEFAULT '0',
  `LAST_UPDATE_DATETIME` datetime NOT NULL,
  PRIMARY KEY (`ID`),
  UNIQUE KEY `ZP_USER_ID` (`ZP_USER_ID`,`ZP_TV_ID`,`SEASON`,`EPISODE`,`ZP_TV_ENTITY_TYPE_ID`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_USER_TV_EPISODE_IMAGE_RENDER_HASH_XREF`
--

DROP TABLE IF EXISTS `ZP_USER_TV_EPISODE_IMAGE_RENDER_HASH_XREF`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_USER_TV_EPISODE_IMAGE_RENDER_HASH_XREF` (
  `ZP_USER_ID` tinyint(3) unsigned NOT NULL,
  `ZP_TV_ID` smallint(5) unsigned NOT NULL,
  `SEASON` smallint(5) unsigned NOT NULL,
  `FIRST_EPISODE` smallint(5) unsigned NOT NULL,
  `ZP_TV_IMAGE_TYPE_ID` tinyint(3) unsigned NOT NULL,
  `ZP_IMAGE_SUB_TYPE` tinyint(3) unsigned NOT NULL,
  `ZP_TV_EPISODE_IMAGE_RENDER_HASH_ID` int(10) unsigned NOT NULL,
  PRIMARY KEY (`ZP_USER_ID`,`ZP_TV_ID`,`SEASON`,`FIRST_EPISODE`,`ZP_TV_IMAGE_TYPE_ID`,`ZP_IMAGE_SUB_TYPE`,`ZP_TV_EPISODE_IMAGE_RENDER_HASH_ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_USER_TV_EPISODE_WATCHED`
--

DROP TABLE IF EXISTS `ZP_USER_TV_EPISODE_WATCHED`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_USER_TV_EPISODE_WATCHED` (
  `ZP_USER_ID` tinyint(3) unsigned NOT NULL,
  `ZP_TV_ID` int(10) unsigned NOT NULL,
  `SEASON` smallint(5) unsigned NOT NULL,
  `EPISODE` smallint(5) unsigned NOT NULL,
  `DATETIME` datetime NOT NULL,
  PRIMARY KEY (`ZP_USER_ID`,`ZP_TV_ID`,`SEASON`,`EPISODE`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_USER_TV_FAVOURITE`
--

DROP TABLE IF EXISTS `ZP_USER_TV_FAVOURITE`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_USER_TV_FAVOURITE` (
  `ZP_TV_ID` int(10) unsigned NOT NULL,
  `ZP_USER_ID` smallint(5) unsigned NOT NULL,
  PRIMARY KEY (`ZP_TV_ID`,`ZP_USER_ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_USER_TV_IMAGE_RENDER_HASH_XREF`
--

DROP TABLE IF EXISTS `ZP_USER_TV_IMAGE_RENDER_HASH_XREF`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_USER_TV_IMAGE_RENDER_HASH_XREF` (
  `ZP_USER_ID` tinyint(3) unsigned NOT NULL,
  `ZP_TV_ID` int(10) unsigned NOT NULL,
  `ZP_TV_IMAGE_TYPE_ID` tinyint(3) unsigned NOT NULL,
  `ZP_IMAGE_SUB_TYPE` tinyint(3) unsigned NOT NULL,
  `ZP_TV_IMAGE_RENDER_HASH_ID` int(10) unsigned NOT NULL,
  PRIMARY KEY (`ZP_USER_ID`,`ZP_TV_ID`,`ZP_TV_IMAGE_TYPE_ID`,`ZP_IMAGE_SUB_TYPE`,`ZP_TV_IMAGE_RENDER_HASH_ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_USER_TV_SEASON_ENTITY_XREF`
--

DROP TABLE IF EXISTS `ZP_USER_TV_SEASON_ENTITY_XREF`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_USER_TV_SEASON_ENTITY_XREF` (
  `ID` int(11) NOT NULL AUTO_INCREMENT,
  `ZP_USER_ID` smallint(5) unsigned NOT NULL,
  `ZP_TV_ID` int(10) unsigned NOT NULL,
  `SEASON` smallint(5) unsigned NOT NULL,
  `ZP_TV_ENTITY_TYPE_ID` smallint(5) unsigned NOT NULL,
  `ZP_TV_ENTITY_ID` int(10) unsigned DEFAULT NULL,
  `FORCED` tinyint(1) NOT NULL DEFAULT '0',
  `LAST_UPDATE_DATETIME` datetime NOT NULL,
  PRIMARY KEY (`ID`),
  UNIQUE KEY `ZP_USER_ID` (`ZP_USER_ID`,`ZP_TV_ID`,`SEASON`,`ZP_TV_ENTITY_TYPE_ID`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_USER_TV_TITLE_TYPE_PREF`
--

DROP TABLE IF EXISTS `ZP_USER_TV_TITLE_TYPE_PREF`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_USER_TV_TITLE_TYPE_PREF` (
  `ZP_USER_ID` tinyint(3) unsigned NOT NULL,
  `ZP_TV_TITLE_TYPE_ID` tinyint(3) unsigned NOT NULL,
  PRIMARY KEY (`ZP_USER_ID`,`ZP_TV_TITLE_TYPE_ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_USER_TV_TITLE_XREF`
--

DROP TABLE IF EXISTS `ZP_USER_TV_TITLE_XREF`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_USER_TV_TITLE_XREF` (
  `ZP_USER_ID` tinyint(3) unsigned NOT NULL,
  `ZP_TV_ID` int(10) unsigned NOT NULL,
  `ZP_TV_TITLE_ID` int(10) unsigned NOT NULL,
  PRIMARY KEY (`ZP_USER_ID`,`ZP_TV_ID`,`ZP_TV_TITLE_ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_USER_TV_TOWATCH`
--

DROP TABLE IF EXISTS `ZP_USER_TV_TOWATCH`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_USER_TV_TOWATCH` (
  `ZP_TV_ID` int(10) unsigned NOT NULL,
  `ZP_USER_ID` smallint(5) unsigned NOT NULL,
  PRIMARY KEY (`ZP_TV_ID`,`ZP_USER_ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ZP_VCODEC_XREF`
--

DROP TABLE IF EXISTS `ZP_VCODEC_XREF`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ZP_VCODEC_XREF` (
  `ID` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
  `ZP_VCODEC_ID` tinyint(3) unsigned NOT NULL,
  `CODEC_ID` text COLLATE utf8mb4_unicode_ci,
  `CODEC` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping events for database 'zerrphix'
--

--
-- Dumping routines for database 'zerrphix'
--
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2017-12-17 13:25:49
"""
