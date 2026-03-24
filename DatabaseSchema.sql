-- MySQL dump 10.13  Distrib 8.0.43, for Win64 (x86_64)
--
-- Host: 54.37.40.206    Database: lacunar_stroke
-- ------------------------------------------------------
-- Server version	5.5.5-10.11.13-MariaDB-0ubuntu0.24.04.1

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Temporary view structure for view `detailed_reading`
--

DROP TABLE IF EXISTS `detailed_reading`;
/*!50001 DROP VIEW IF EXISTS `detailed_reading`*/;
SET @saved_cs_client     = @@character_set_client;
/*!50503 SET character_set_client = utf8mb4 */;
/*!50001 CREATE VIEW `detailed_reading` AS SELECT 
 1 AS `id`,
 1 AS `patient_id`,
 1 AS `timestamp`,
 1 AS `systolic_bp`,
 1 AS `diastolic_bp`,
 1 AS `blood_glucose`,
 1 AS `diabetes_type`,
 1 AS `bp_category`,
 1 AS `on_bp_medication`,
 1 AS `volatility_index`,
 1 AS `score_velocity`,
 1 AS `hba1c`,
 1 AS `left_sensory_score`,
 1 AS `right_sensory_score`,
 1 AS `asymmetry_difference`,
 1 AS `average_asymmetry`,
 1 AS `asymmetry_index`,
 1 AS `risk_label`*/;
SET character_set_client = @saved_cs_client;

--
-- Table structure for table `doctor_info`
--

DROP TABLE IF EXISTS `doctor_info`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `doctor_info` (
  `id` bigint(20) NOT NULL,
  `first_name` varchar(64) DEFAULT NULL,
  `last_name` varchar(64) DEFAULT NULL,
  `title` varchar(64) DEFAULT NULL,
  `qualification` varchar(64) DEFAULT NULL,
  `profession` varchar(64) DEFAULT NULL,
  PRIMARY KEY (`id`),
  CONSTRAINT `USER_TO_DOCTOR` FOREIGN KEY (`id`) REFERENCES `user` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `doctor_info`
--

LOCK TABLES `doctor_info` WRITE;
/*!40000 ALTER TABLE `doctor_info` DISABLE KEYS */;
INSERT INTO `doctor_info` VALUES (1,'Cheerkoot','Loic Fred','Dr','Phil. Medical','Neurologist'),(2,'Ra\'eesah','Bibi Goolam\'Ossen','Dr','Phil. Medical','Neurologist'),(3,'Morane','Adisayam','Dr','Phil. Medical','Neurologist'),(4,'Brijraj','Diya Devi','Dr','Phil. Medical','Physician');
/*!40000 ALTER TABLE `doctor_info` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `notification`
--

DROP TABLE IF EXISTS `notification`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `notification` (
  `id` bigint(20) NOT NULL,
  `user_id` bigint(20) NOT NULL,
  `title` varchar(128) DEFAULT NULL,
  `message` varchar(512) DEFAULT NULL,
  `timestamp` datetime DEFAULT NULL,
  `type` varchar(45) NOT NULL DEFAULT 'Info',
  PRIMARY KEY (`id`),
  KEY `USER_TO_NOTIF_idx` (`user_id`),
  CONSTRAINT `USER_TO_NOTIF` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `notification`
--

LOCK TABLES `notification` WRITE;
/*!40000 ALTER TABLE `notification` DISABLE KEYS */;
/*!40000 ALTER TABLE `notification` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `patient_info`
--

DROP TABLE IF EXISTS `patient_info`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `patient_info` (
  `id` bigint(20) NOT NULL,
  `first_name` varchar(45) DEFAULT NULL,
  `last_name` varchar(45) DEFAULT NULL,
  `age_group` varchar(45) DEFAULT NULL,
  `sex` varchar(45) DEFAULT NULL,
  `smoking_history` tinyint(1) NOT NULL DEFAULT 0,
  `doctor_id` bigint(20) NOT NULL DEFAULT 2,
  `notes` varchar(600) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `PATIENT_OF_DOCTOR_idx` (`doctor_id`),
  CONSTRAINT `PATIENT_OF_DOCTOR` FOREIGN KEY (`doctor_id`) REFERENCES `doctor_info` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `PATIENT_USER` FOREIGN KEY (`id`) REFERENCES `user` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `patient_info`
--

LOCK TABLES `patient_info` WRITE;
/*!40000 ALTER TABLE `patient_info` DISABLE KEYS */;
INSERT INTO `patient_info` VALUES (6,'Emma','Johnson','60-69','Female',1,1,NULL),(7,'Noah','Williams','70-79','Male',1,1,NULL),(8,NULL,NULL,NULL,'Female',0,2,NULL);
/*!40000 ALTER TABLE `patient_info` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Temporary view structure for view `patient_report`
--

DROP TABLE IF EXISTS `patient_report`;
/*!50001 DROP VIEW IF EXISTS `patient_report`*/;
SET @saved_cs_client     = @@character_set_client;
/*!50503 SET character_set_client = utf8mb4 */;
/*!50001 CREATE VIEW `patient_report` AS SELECT 
 1 AS `id`,
 1 AS `first_name`,
 1 AS `email`,
 1 AS `last_name`,
 1 AS `age_group`,
 1 AS `sex`,
 1 AS `smoking_history`,
 1 AS `doctor_id`,
 1 AS `notes`,
 1 AS `doctor_first_name`,
 1 AS `doctor_last_name`,
 1 AS `doctor_title`,
 1 AS `doctor_qualification`,
 1 AS `doctor_profession`,
 1 AS `highest_reading_timestamp`,
 1 AS `highest_reading_systolic_bp`,
 1 AS `highest_reading_diastolic_bp`,
 1 AS `highest_reading_blood_glucose`,
 1 AS `highest_reading_diabetes_type`,
 1 AS `highest_reading_bp_category`,
 1 AS `highest_reading_on_bp_medication`,
 1 AS `highest_reading_volatility_index`,
 1 AS `highest_reading_score_velocity`,
 1 AS `highest_reading_hba1c`,
 1 AS `highest_reading_left_sensory_score`,
 1 AS `highest_reading_right_sensory_score`,
 1 AS `highest_reading_asymmetry_difference`,
 1 AS `highest_reading_average_asymmetry`,
 1 AS `highest_reading_asymmetry_index`,
 1 AS `highest_reading_risk_label`,
 1 AS `avg_systolic_bp`,
 1 AS `avg_hba1c`,
 1 AS `avg_left_sensory_score`,
 1 AS `avg_right_sensory_score`,
 1 AS `avg_asymmetry_difference`,
 1 AS `avg_score_velocity`,
 1 AS `avg_volatility_index`,
 1 AS `avg_average_asymmetry`,
 1 AS `avg_asymmetry_index`,
 1 AS `avg_risk_label`,
 1 AS `latest_reading_timestamp`,
 1 AS `latest_reading_systolic_bp`,
 1 AS `latest_reading_diastolic_bp`,
 1 AS `latest_reading_blood_glucose`,
 1 AS `latest_reading_diabetes_type`,
 1 AS `latest_reading_bp_category`,
 1 AS `latest_reading_on_bp_medication`,
 1 AS `latest_reading_volatility_index`,
 1 AS `latest_reading_score_velocity`,
 1 AS `latest_reading_hba1c`,
 1 AS `latest_reading_left_sensory_score`,
 1 AS `latest_reading_right_sensory_score`,
 1 AS `latest_reading_asymmetry_difference`,
 1 AS `latest_reading_average_asymmetry`,
 1 AS `latest_reading_asymmetry_index`,
 1 AS `latest_reading_risk_label`*/;
SET character_set_client = @saved_cs_client;

--
-- Table structure for table `reading`
--

DROP TABLE IF EXISTS `reading`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `reading` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `patient_id` bigint(20) DEFAULT NULL,
  `timestamp` datetime DEFAULT NULL,
  `systolic_bp` int(11) DEFAULT 0,
  `diastolic_bp` int(11) DEFAULT 0,
  `hba1c` double DEFAULT 0,
  `blood_glucose` int(11) DEFAULT 0,
  `diabetes_type` varchar(45) DEFAULT NULL,
  `bp_category` varchar(45) DEFAULT NULL,
  `on_bp_medication` varchar(45) DEFAULT '1',
  `left_sensory_score` double DEFAULT NULL,
  `right_sensory_score` double DEFAULT NULL,
  `volatility_index` double DEFAULT 0,
  `score_velocity` double DEFAULT 0,
  `asymmetry_index` float DEFAULT 0,
  `pattern_volatility` float DEFAULT 0,
  `pattern_velocity_trend` float DEFAULT 0,
  `pattern_stuttering_score` int(11) DEFAULT 0,
  `pattern_amplitude` float DEFAULT 0,
  `pattern_asymmetry_progression` float DEFAULT 0,
  `pattern_type` int(11) DEFAULT 0,
  `pattern_consistency` float DEFAULT 0,
  `pattern_reading_count` int(11) DEFAULT 5,
  PRIMARY KEY (`id`),
  KEY `READINGS_TO_PATIENT_idx` (`patient_id`),
  CONSTRAINT `READINGS_TO_PATIENT` FOREIGN KEY (`patient_id`) REFERENCES `patient_info` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=2161 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `reading`
--

LOCK TABLES `reading` WRITE;
/*!40000 ALTER TABLE `reading` DISABLE KEYS */;
INSERT INTO `reading` VALUES (111,6,'2026-01-18 23:41:47',155,88,7.2,165,'2','3','1',7.7837964630535454,8.977546808391965,0,0,0,0,0,0,0,0,0,0,5),(112,6,'2026-01-19 02:41:48',155,88,7.1,165,'2','3','1',7.4797398078617015,8.53465216577833,0,0,0,0,0,0,0,0,0,0,5),(113,6,'2026-01-19 05:41:49',155,88,7.2,165,'2','3','1',7.038057542740412,8.057366232800154,0,0,0,0,0,0,0,0,0,0,5),(114,6,'2026-01-19 08:41:50',155,88,7.1,165,'2','3','1',6.581491479212553,7.723347355533262,0,0,0,0,0,0,0,0,0,0,5),(115,6,'2026-01-19 11:41:52',155,88,7.2,165,'2','3','1',6.41534737873953,7.589113610437359,0,0,0,0,0,0,0,0,0,0,5),(116,6,'2026-01-19 14:41:53',155,88,7.1,164,'2','3','1',5.925123023435704,7.4319335700747935,0,0,0,0,0,0,0,0,0,0,5),(117,6,'2026-01-19 17:41:54',155,88,7.2,164,'2','3','1',5.454245414893033,7.28474725469476,0,0,0,0,0,0,0,0,0,0,5),(118,6,'2026-01-19 20:41:55',155,88,7.1,164,'2','3','1',5.445860912428135,6.941877992424778,0,0,0,0,0,0,0,0,0,0,5),(119,6,'2026-01-19 23:41:56',155,88,7.2,164,'2','3','1',5.1435529746767985,6.700707979905232,0,0,0,0,0,0,0,0,0,0,5),(120,6,'2026-01-20 02:41:57',155,88,7.1,164,'2','3','1',4.834088811210051,6.608289951915792,0,0,0,0,0,0,0,0,0,0,5),(121,7,'2026-01-18 23:42:00',155,88,5,165,'2','3','1',7.583638451572904,7.451702931012722,0,0,0,0,0,0,0,0,0,0,5),(122,7,'2026-01-19 02:42:01',155,88,5,165,'2','3','1',7.194036934714466,7.271965894453204,0,0,0,0,0,0,0,0,0,0,5),(123,7,'2026-01-19 05:42:03',155,88,5,165,'2','3','1',7.176796095987561,7.217118878274088,0,0,0,0,0,0,0,0,0,0,5),(124,7,'2026-01-19 08:42:04',155,88,5,165,'2','3','1',6.947850369887261,7.047857727683132,0,0,0,0,0,0,0,0,0,0,5),(125,7,'2026-01-19 11:42:05',155,88,5,165,'2','3','1',6.794727794401003,6.768778181785098,0,0,0,0,0,0,0,0,0,0,5),(126,7,'2026-01-19 14:42:06',155,88,5,165,'2','3','1',6.713736211386279,6.275493206803966,0,0,0,0,0,0,0,0,0,0,5),(127,7,'2026-01-19 17:42:07',155,88,5,165,'2','3','1',6.746838577454184,5.910184386804749,0,0,0,0,0,0,0,0,0,0,5),(128,7,'2026-01-19 20:42:08',155,88,5,165,'2','3','1',6.6585159798974,5.630659516656493,0,0,0,0,0,0,0,0,0,0,5),(129,7,'2026-01-19 23:42:09',155,88,5,165,'2','3','1',6.201577109417577,5.661796582123398,0,0,0,0,0,0,0,0,0,0,5),(130,7,'2026-01-20 02:42:10',155,88,5.1,165,'2','3','1',6.100398408691492,5.46664303368231,0,0,0,0,0,0,0,0,0,0,5),(2157,6,'2026-02-07 16:39:24',155,88,7.2,165,'2','3','1',8.9,3.8,0,0,0,0,0,0,0,0,0,0,5),(2158,6,'2026-02-16 09:58:59',135,80,5.8,100,'0','0','0',8.5,7.7,0,0,0,0,0,0,0,0,0,0,5),(2159,6,'2026-02-16 10:49:45',135,80,5.8,100,'0','0','0',8.4,7.5,0,0,0,0,0,0,0,0,0,0,5),(2160,6,'2026-02-22 17:37:18',118,78,5.3,95,'0','0','0',9.2,9,0,0,0,0,0,0,0,0,0,0,5);
/*!40000 ALTER TABLE `reading` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `user`
--

DROP TABLE IF EXISTS `user`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `user` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `email` varchar(64) NOT NULL,
  `password` varchar(256) NOT NULL,
  `role` varchar(16) NOT NULL DEFAULT 'USER',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=213 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `user`
--

LOCK TABLES `user` WRITE;
/*!40000 ALTER TABLE `user` DISABLE KEYS */;
INSERT INTO `user` VALUES (1,'loic.cheerkoot@gmail.com','scrypt:32768:8:1$SAi6AQicaNoKUOC7$54a477ed2fbac4a66d46540491ba23a6e63020dc7f33098ed298a5c0a248b5236df0d6ee135fe1903a9d0a5c46d1f0fad9f2b05096f3639b75f38c6e4635ec4a','DOCTOR'),(2,'raeesah@gmail.com','scrypt:32768:8:1$SAi6AQicaNoKUOC7$54a477ed2fbac4a66d46540491ba23a6e63020dc7f33098ed298a5c0a248b5236df0d6ee135fe1903a9d0a5c46d1f0fad9f2b05096f3639b75f38c6e4635ec4a','DOCTOR'),(3,'morane@gmail.com','scrypt:32768:8:1$SAi6AQicaNoKUOC7$54a477ed2fbac4a66d46540491ba23a6e63020dc7f33098ed298a5c0a248b5236df0d6ee135fe1903a9d0a5c46d1f0fad9f2b05096f3639b75f38c6e4635ec4a','DOCTOR'),(4,'diyabrijraj@gmail.com','scrypt:32768:8:1$SAi6AQicaNoKUOC7$54a477ed2fbac4a66d46540491ba23a6e63020dc7f33098ed298a5c0a248b5236df0d6ee135fe1903a9d0a5c46d1f0fad9f2b05096f3639b75f38c6e4635ec4a','DOCTOR'),(6,'user1@example.com','scrypt:32768:8:1$SAi6AQicaNoKUOC7$54a477ed2fbac4a66d46540491ba23a6e63020dc7f33098ed298a5c0a248b5236df0d6ee135fe1903a9d0a5c46d1f0fad9f2b05096f3639b75f38c6e4635ec4a','PATIENT'),(7,'user2@example.com','scrypt:32768:8:1$SAi6AQicaNoKUOC7$54a477ed2fbac4a66d46540491ba23a6e63020dc7f33098ed298a5c0a248b5236df0d6ee135fe1903a9d0a5c46d1f0fad9f2b05096f3639b75f38c6e4635ec4a','PATIENT'),(8,'test@gmail.com','scrypt:32768:8:1$SAi6AQicaNoKUOC7$54a477ed2fbac4a66d46540491ba23a6e63020dc7f33098ed298a5c0a248b5236df0d6ee135fe1903a9d0a5c46d1f0fad9f2b05096f3639b75f38c6e4635ec4a','PATIENT');
/*!40000 ALTER TABLE `user` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping events for database 'lacunar_stroke'
--

--
-- Dumping routines for database 'lacunar_stroke'
--
/*!50003 DROP FUNCTION IF EXISTS `GetAsymmetryDifference` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'STRICT_TRANS_TABLES,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`%` FUNCTION `GetAsymmetryDifference`(left_score DOUBLE, right_score DOUBLE) RETURNS double
BEGIN
    RETURN ABS(left_score - right_score);
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP FUNCTION IF EXISTS `GetAsymmetryIndex` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'STRICT_TRANS_TABLES,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`%` FUNCTION `GetAsymmetryIndex`(left_score DOUBLE, right_score DOUBLE) RETURNS double
BEGIN
    DECLARE avg_val DOUBLE;
    DECLARE asymm_diff DOUBLE;
    SET avg_val = GetAverageAsymmetry(left_score, right_score);
    SET asymm_diff = GetAsymmetryDifference(left_score, right_score);
    RETURN asymm_diff / (avg_val + 1);
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP FUNCTION IF EXISTS `GetAverageAsymmetry` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'STRICT_TRANS_TABLES,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`%` FUNCTION `GetAverageAsymmetry`(left_score DOUBLE, right_score DOUBLE) RETURNS double
BEGIN
    RETURN (left_score + right_score) / 2;
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP PROCEDURE IF EXISTS `GetCriticalAlert` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'IGNORE_SPACE,STRICT_TRANS_TABLES,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`%` PROCEDURE `GetCriticalAlert`(IN doctor_id bigint)
BEGIN
SELECT N.*, I.first_name, I.last_name FROM lacunar_stroke.notification N
JOIN patient_info I ON I.id = N.user_id
WHERE type = 'Critical' AND I.doctor_id = doctor_id;
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Final view structure for view `detailed_reading`
--

/*!50001 DROP VIEW IF EXISTS `detailed_reading`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`%` SQL SECURITY DEFINER */
/*!50001 VIEW `detailed_reading` AS select `reading`.`id` AS `id`,`reading`.`patient_id` AS `patient_id`,`reading`.`timestamp` AS `timestamp`,`reading`.`systolic_bp` AS `systolic_bp`,`reading`.`diastolic_bp` AS `diastolic_bp`,`reading`.`blood_glucose` AS `blood_glucose`,`reading`.`diabetes_type` AS `diabetes_type`,`reading`.`bp_category` AS `bp_category`,`reading`.`on_bp_medication` AS `on_bp_medication`,`reading`.`volatility_index` AS `volatility_index`,`reading`.`score_velocity` AS `score_velocity`,`reading`.`hba1c` AS `hba1c`,truncate(coalesce(`reading`.`left_sensory_score`,0),8) AS `left_sensory_score`,truncate(coalesce(`reading`.`right_sensory_score`,0),8) AS `right_sensory_score`,truncate(coalesce(`GETASYMMETRYDIFFERENCE`(`reading`.`left_sensory_score`,`reading`.`right_sensory_score`),0),8) AS `asymmetry_difference`,truncate(coalesce(`GETAVERAGEASYMMETRY`(`reading`.`left_sensory_score`,`reading`.`right_sensory_score`),0),8) AS `average_asymmetry`,truncate(coalesce(`GETASYMMETRYINDEX`(`reading`.`left_sensory_score`,`reading`.`right_sensory_score`),0),8) AS `asymmetry_index`,case when `GETASYMMETRYINDEX`(`reading`.`left_sensory_score`,`reading`.`right_sensory_score`) > 0.2 then 'Critical' when `GETASYMMETRYINDEX`(`reading`.`left_sensory_score`,`reading`.`right_sensory_score`) > 0.15 then 'Borderline' else 'Normal' end AS `risk_label` from `reading` order by `GETASYMMETRYINDEX`(`reading`.`left_sensory_score`,`reading`.`right_sensory_score`) desc */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `patient_report`
--

/*!50001 DROP VIEW IF EXISTS `patient_report`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`%` SQL SECURITY DEFINER */
/*!50001 VIEW `patient_report` AS with highest_reading as (select `R`.`id` AS `id`,`R`.`patient_id` AS `patient_id`,`R`.`timestamp` AS `timestamp`,`R`.`systolic_bp` AS `systolic_bp`,`R`.`diastolic_bp` AS `diastolic_bp`,`R`.`blood_glucose` AS `blood_glucose`,`R`.`diabetes_type` AS `diabetes_type`,`R`.`bp_category` AS `bp_category`,`R`.`on_bp_medication` AS `on_bp_medication`,`R`.`volatility_index` AS `volatility_index`,`R`.`score_velocity` AS `score_velocity`,`R`.`hba1c` AS `hba1c`,`R`.`left_sensory_score` AS `left_sensory_score`,`R`.`right_sensory_score` AS `right_sensory_score`,`R`.`asymmetry_difference` AS `asymmetry_difference`,`R`.`average_asymmetry` AS `average_asymmetry`,`R`.`asymmetry_index` AS `asymmetry_index`,`R`.`risk_label` AS `risk_label` from (`detailed_reading` `R` join (select `detailed_reading`.`patient_id` AS `patient_id`,max(`GETASYMMETRYINDEX`(`detailed_reading`.`left_sensory_score`,`detailed_reading`.`right_sensory_score`)) AS `max_asymmetry_index` from `detailed_reading` group by `detailed_reading`.`patient_id`) `M` on(`M`.`patient_id` = `R`.`patient_id` and `GETASYMMETRYINDEX`(`R`.`left_sensory_score`,`R`.`right_sensory_score`) = `M`.`max_asymmetry_index`))), average_reading as (select `detailed_reading`.`patient_id` AS `patient_id`,avg(`detailed_reading`.`systolic_bp`) AS `avg_systolic_bp`,avg(`detailed_reading`.`hba1c`) AS `avg_hba1c`,avg(`detailed_reading`.`left_sensory_score`) AS `avg_left_sensory_score`,avg(`detailed_reading`.`right_sensory_score`) AS `avg_right_sensory_score`,avg(`detailed_reading`.`asymmetry_difference`) AS `avg_asymmetry_difference`,avg(`detailed_reading`.`volatility_index`) AS `avg_volatility_index`,avg(`detailed_reading`.`score_velocity`) AS `avg_score_velocity`,avg(`detailed_reading`.`average_asymmetry`) AS `avg_average_asymmetry`,avg(`detailed_reading`.`asymmetry_index`) AS `avg_asymmetry_index`,case when avg(`detailed_reading`.`asymmetry_index`) > 0.2 then 'Critical' when avg(`detailed_reading`.`asymmetry_index`) > 0.15 then 'Borderline' else 'Normal' end AS `avg_risk_label` from `detailed_reading` group by `detailed_reading`.`patient_id`), latest_reading as (select `R`.`id` AS `id`,`R`.`patient_id` AS `patient_id`,`R`.`timestamp` AS `timestamp`,`R`.`systolic_bp` AS `systolic_bp`,`R`.`diastolic_bp` AS `diastolic_bp`,`R`.`blood_glucose` AS `blood_glucose`,`R`.`diabetes_type` AS `diabetes_type`,`R`.`bp_category` AS `bp_category`,`R`.`on_bp_medication` AS `on_bp_medication`,`R`.`volatility_index` AS `volatility_index`,`R`.`score_velocity` AS `score_velocity`,`R`.`hba1c` AS `hba1c`,`R`.`left_sensory_score` AS `left_sensory_score`,`R`.`right_sensory_score` AS `right_sensory_score`,`R`.`asymmetry_difference` AS `asymmetry_difference`,`R`.`average_asymmetry` AS `average_asymmetry`,`R`.`asymmetry_index` AS `asymmetry_index`,`R`.`risk_label` AS `risk_label` from (`detailed_reading` `R` join (select `detailed_reading`.`patient_id` AS `patient_id`,max(`detailed_reading`.`timestamp`) AS `latest_timestamp` from `detailed_reading` group by `detailed_reading`.`patient_id`) `L` on(`L`.`patient_id` = `R`.`patient_id` and `L`.`latest_timestamp` = `R`.`timestamp`)))select `P`.`id` AS `id`,`P`.`first_name` AS `first_name`,`U`.`email` AS `email`,`P`.`last_name` AS `last_name`,`P`.`age_group` AS `age_group`,`P`.`sex` AS `sex`,`P`.`smoking_history` AS `smoking_history`,`P`.`doctor_id` AS `doctor_id`,`P`.`notes` AS `notes`,`D`.`first_name` AS `doctor_first_name`,`D`.`last_name` AS `doctor_last_name`,`D`.`title` AS `doctor_title`,`D`.`qualification` AS `doctor_qualification`,`D`.`profession` AS `doctor_profession`,`HR`.`timestamp` AS `highest_reading_timestamp`,coalesce(`HR`.`systolic_bp`,0) AS `highest_reading_systolic_bp`,coalesce(`HR`.`diastolic_bp`,0) AS `highest_reading_diastolic_bp`,coalesce(`HR`.`blood_glucose`,0) AS `highest_reading_blood_glucose`,coalesce(`HR`.`diabetes_type`,0) AS `highest_reading_diabetes_type`,coalesce(`HR`.`bp_category`,0) AS `highest_reading_bp_category`,coalesce(`HR`.`on_bp_medication`,0) AS `highest_reading_on_bp_medication`,coalesce(`HR`.`volatility_index`,0) AS `highest_reading_volatility_index`,coalesce(`HR`.`score_velocity`,0) AS `highest_reading_score_velocity`,coalesce(`HR`.`hba1c`,0) AS `highest_reading_hba1c`,coalesce(`HR`.`left_sensory_score`,0) AS `highest_reading_left_sensory_score`,coalesce(`HR`.`right_sensory_score`,0) AS `highest_reading_right_sensory_score`,coalesce(`HR`.`asymmetry_difference`,0) AS `highest_reading_asymmetry_difference`,coalesce(`HR`.`average_asymmetry`,0) AS `highest_reading_average_asymmetry`,coalesce(`HR`.`asymmetry_index`,0) AS `highest_reading_asymmetry_index`,`HR`.`risk_label` AS `highest_reading_risk_label`,coalesce(`AR`.`avg_systolic_bp`,0) AS `avg_systolic_bp`,coalesce(`AR`.`avg_hba1c`,0) AS `avg_hba1c`,coalesce(`AR`.`avg_left_sensory_score`,0) AS `avg_left_sensory_score`,coalesce(`AR`.`avg_right_sensory_score`,0) AS `avg_right_sensory_score`,coalesce(`AR`.`avg_asymmetry_difference`,0) AS `avg_asymmetry_difference`,coalesce(`AR`.`avg_score_velocity`,0) AS `avg_score_velocity`,coalesce(`AR`.`avg_volatility_index`,0) AS `avg_volatility_index`,coalesce(`AR`.`avg_average_asymmetry`,0) AS `avg_average_asymmetry`,coalesce(`AR`.`avg_asymmetry_index`,0) AS `avg_asymmetry_index`,`AR`.`avg_risk_label` AS `avg_risk_label`,`LR`.`timestamp` AS `latest_reading_timestamp`,coalesce(`LR`.`systolic_bp`,0) AS `latest_reading_systolic_bp`,coalesce(`LR`.`diastolic_bp`,0) AS `latest_reading_diastolic_bp`,coalesce(`LR`.`blood_glucose`,0) AS `latest_reading_blood_glucose`,coalesce(`LR`.`diabetes_type`,0) AS `latest_reading_diabetes_type`,coalesce(`LR`.`bp_category`,0) AS `latest_reading_bp_category`,coalesce(`LR`.`on_bp_medication`,0) AS `latest_reading_on_bp_medication`,coalesce(`LR`.`volatility_index`,0) AS `latest_reading_volatility_index`,coalesce(`LR`.`score_velocity`,0) AS `latest_reading_score_velocity`,coalesce(`LR`.`hba1c`,0) AS `latest_reading_hba1c`,coalesce(`LR`.`left_sensory_score`,0) AS `latest_reading_left_sensory_score`,coalesce(`LR`.`right_sensory_score`,0) AS `latest_reading_right_sensory_score`,coalesce(`LR`.`asymmetry_difference`,0) AS `latest_reading_asymmetry_difference`,coalesce(`LR`.`average_asymmetry`,0) AS `latest_reading_average_asymmetry`,coalesce(`LR`.`asymmetry_index`,0) AS `latest_reading_asymmetry_index`,`LR`.`risk_label` AS `latest_reading_risk_label` from (((((`user` `U` join `patient_info` `P` on(`P`.`id` = `U`.`id`)) join `highest_reading` `HR` on(`HR`.`patient_id` = `U`.`id`)) join `average_reading` `AR` on(`AR`.`patient_id` = `U`.`id`)) join `latest_reading` `LR` on(`LR`.`patient_id` = `U`.`id`)) join `doctor_info` `D` on(`D`.`id` = `P`.`doctor_id`)) order by `AR`.`avg_asymmetry_index` desc */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-03-24 22:58:43
