<?php
/************* DEBUT PARAMETRAGE *************/
/* PARAMETRAGE NECESSAIRE POUR BBB-POD-LIVE */
// Application en mode débogage (true - on logue toutes les lignes) ou en production (false - on logue seulement les erreurs et infos).
define ("DEBUG", true);
// Répertoire de base de l'application et avoir suffisamment d'espace disque pour l'enregistrement de quelques vidéos (stockage temporaire)
// !!! Ce répertoire doit être sur un disque dur de la machine serveur.
define ("PHYSICAL_BASE_ROOT","/home/pod/bbb-pod-live/");
// Constante permettant de définir le chemin physique du répertoire contenant les logs applicatifs.
// !!! L'arborescence doit être sur un disque dur local de la machine serveur.
define ("PHYSICAL_LOG_ROOT", "/home/pod/bbb-pod-live/logs/");
// Mail de l'administrateur de BBB-POD-LIVE, qui recevra les mails en cas de démarrage de live ou d'erreur
define ("ADMIN_EMAIL", "admin@univ.fr");
// Hostname de ce serveur BBB-POD-LIVE (utile pour Redis et le chat)
define ("SERVER_HOSTNAME", "server.univ.fr");
// Nombre de serveurs BBB-POD-LIVE
define ("NUMBER_SERVERS", 1);
// Numéro unique de ce serveur dans la liste des serveurs BBB-POD-LIVE
// Par exemple : s'il y a 2 serveurs BBB-POD-LIVE (NUMBER_SERVERS = 2), alors un serveur devra avoir SERVER_NUMBER=1 et l'autre SERVER_NUMBER=2
define ("SERVER_NUMBER", 1);
// Nombre de directs gérés par ce serveur (à adapter selon les ressources du serveur)
define ("NUMBER_LIVES", 3);

/* PARAMETRAGE NECESSAIRE POUR BigBlueButton-liveStreaming */
// URL du serveur BigBlueButton/Scalelite, avec la notion d'API
define ("BBB_URL", "https://bbb.univ.fr/bigbluebutton/api");
// Clé secrète du serveur BigBlueButton/Scalelite
define ("BBB_SECRET", "xxxxxxxxxxxxx");
// Résolution pour diffuser / télécharger au format WxH (Défaut: 1920x1080). cf. BBB_RESOLUTION
define ("BBB_RESOLUTION", "1280x720");
// Bitrate de la vidéo (Défaut: 4000). cf. FFMPEG_STREAM_VIDEO_BITRATE
define ("FFMPEG_STREAM_VIDEO_BITRATE", "3000");
// Threads utilisés pour le flux (Défaut: 0). 0 signifie auto. cf. FFMPEG_STREAM_THREADS
define ("FFMPEG_STREAM_THREADS", "0");
// Serveur RTMP qui va gérer les directs pour ce serveur BBB-POD-LIVE
// Format, sans authentification : rtmp://serveurRTMP.domaine.fr:port/application/
// Format, avec authentification : rtmp://user@password:serveur.domaine.fr:port/application/
// Exemple : rtmp://live.univ.fr:1935/live/ cf. BBB_STREAM_URL
define ("BBB_STREAM_URL", "rtmp://live.univ.fr/live/");
// Mot de passe des participants cf. BBB_ATTENDEE_PASSWORD
// Doit être défini comme le mot de passe du participant de Moodle / Greenlight ou de tout autre frontend pour permettre la participation via leurs liens
define ("BBB_ATTENDEE_PASSWORD", "xxxxxxx");
// Mot de passe des modérateurs cf. BBB_ATTENDEE_PASSWORD
// Doit être défini comme le mot de passe du modérateur de Moodle / Greenlight ou de tout autre frontend pour permettre la participation via leurs liens
define ("BBB_MODERATOR_PASSWORD", "xxxxxxx");


/* PARAMETRAGE NECESSAIRE POUR POD */
// Flux HLS, dépend de la configuration du serveur RTMP Nginx utilisé
define ("POD_HLS_STREAM", "https://live.univ.fr/hls/");
// URL du serveur Pod
define ("POD_URL", "https://pod.univ.fr");
// Token de sécurité de Pod, utile pour attaquer Pod via les API Rest (cf. administration de Pod / Jeton)
define ("POD_TOKEN", "xxxxxxxxxxxxxxx");
// Identifiant du bâtiment POD (au sens live/building de POD) de rattachement des diffuseurs créés par bbb-pod-live
define ("POD_ID_BUILDING", 1);
// Répertoire dans lequel copier les fichiers vidéo générés par BigBlueButton-liveStreaming
// Ce répertoire - typiquement un partage NFS - doit être accessible aussi par POD et correspondre à DEFAULT_BBB_PATH du fichier settings_local.py.
// Si ce n'est pas possible, laisser ce champ vide et positionner USE_BBB_LIVE_DOWNLOADING = False dans le settings_local de POD.
define ("POD_DEFAULT_BBB_PATH", "/data/www/pod/bbb-recorder/");
/************* FIN PARAMETRAGE *************/


/** Variables globales **/
// Variable permettant de savoir si le script a rencontré au moins une erreur
$txtErrorInScript = "";
// Variable permettant de connaitre les lives en cours sur ce serveur
$livesInProgressOnThisServer = array();
/*****************/

/********** Début de la phase principale**********/
try {
	// Gestion de la timezone
	date_default_timezone_set('Europe/Paris');

	// Décalage permettant d'éviter que chaque serveur n'exécute ce script en même temps.
	// Cela sert aussi de "load balancer" simpliste : chaque serveur va prendre en charge les demandes de directs sur la période de décalage.
	$delay = (SERVER_NUMBER - 1) * round(60 / NUMBER_SERVERS);
	sleep($delay);
	
	writeLog("----------" . date('Y-m-d H:i:s') . "----------", "DEBUG");
	
	// Création des répertoires, des fichiers compose et configuration initiale de ces derniers pour le plugin BigBlueButton-liveStreaming.
	// Un répertoire, par plugin BigBlueButton-liveStreaming, est créé, selon le nombre de directs que gère ce serveur (cf. NUMBER_LIVES).
	configureInitialBigBlueButtonLiveStreaming();
	
	// Démarrage des directs, si des usagers en ont fait la demande dans Pod
	startLives();

	// Arrêt des directs si les sessions BigBlueButton correspondante s ont été arrêtées
	stopLives();
}
catch(Exception $e) {
	$GLOBALS["txtErrorInScript"] .= $e->getMessage();
}

// Envoi d'un message à l'administrateur en cas d'erreur de script
if ($GLOBALS["txtErrorInScript"] != "") {
	sendEmail("[BBB-POD-LIVE] Erreur rencontrée", $GLOBALS["txtErrorInScript"]);
}
/********** Fin de la phase principale**********/

/**
 * Procédure de création et de configuration initile des différents plugin BigBlueButton-liveStreaming.
 * Un répertoire, par nombre de directs gérés par ce serveur (cf. NUMBER_LIVES), sera créé sous la forme bbb-live-streaming+incrémental.
 * Le fichier compose.yml sera copié depuis le répertoire courant (fichier docker-compose.default.yml).
 */
function configureInitialBigBlueButtonLiveStreaming() {
	writeLog("----- Configuration des plugins nécessaires : configureBigBlueButtonLiveStreaming()-----", "DEBUG");
	// Création des répertoires et des fichiers compose pour le plugin BigBlueButton-liveStreaming
	for ($i = 1; $i <= NUMBER_LIVES; $i++) {
		// Définition du répertoire
		$directoryLiveStreaming = checkEndSlash(PHYSICAL_BASE_ROOT) . "bbb-live-streaming$i/";
		writeLog("Vérification pour le direct $i : $directoryLiveStreaming", "DEBUG");
		// Définition du fichier compose.yml dans ce répertoire
		$fichierCompose = $directoryLiveStreaming . "docker-compose.yml";
		// Création du répertoire et du fichier la 1° fois
		if (! file_exists($fichierCompose)) {
			// Création du répertoire
			writeLog("  + Création du répertoire $directoryLiveStreaming", "DEBUG");
			@mkdir("$directoryLiveStreaming", 0755);
			// Téléchargement du fichier compose depuis Github
			writeLog("  + Copie du fichier docker-compose.default.yml du répertoire courant", "DEBUG");
			$cmdCp = "cp ./docker-compose.default.yml $fichierCompose";
			exec("$cmdCp 2>&1", $aRetourVerificationCp, $sRetourVerificationCp);
			if ($sRetourVerificationCp == 0) {
				writeLog("  + Copie du fichier $fichierCompose réalisée", "DEBUG");
			}
			else {
				writeLog("      - Commande '$cmdCp' : $aRetourVerificationCp[0]", "ERROR", __FILE__, __LINE__);
			}
		}
	}
}

/**
 * Procédure permettant de démarrer des directs, si des usagers en ont fait la demande dans Pod.
 * Pour cela, on utilise l'API Rest de Pod.
 * Cette procédure permet d'identifier si un slot est disponible pour être utilisé pour lancer un direct.
 */
function startLives() {
	writeLog("-----Démarrage des directs : startLives()-----", "DEBUG");
	
	// Recherche si des lives sont en cours
	$cmdStatus1 = "curl --silent -H 'Content-Type: application/json' ";
	$cmdStatus1 .= "-H 'Authorization: Token " . POD_TOKEN . "' ";
	$cmdStatus1 .= "-X GET " . checkEndWithoutSlash(POD_URL). "/rest/bbb_livestream/?status=1";
	
	$verificationStatus1 = exec("$cmdStatus1 2>&1", $aRetourVerificationStatus1, $sRetourVerificationStatus1);

	writeLog("Recherche si des lives sont en cours", "DEBUG");
	
	// En cas d'erreur, le code de retour est différent de 0
	if ($sRetourVerificationStatus1 == 0) {
		writeLog("  + Commande '$cmdStatus1' : $aRetourVerificationStatus1[0]", "DEBUG");
		
		$oListeSessions = json_decode($aRetourVerificationStatus1[0]);
		// Recherche des lives existants en cours, sauvegardés dans Pod
		for ($i = 0; $i < $oListeSessions->count; $i++) {
			// Identifiant du live dans Pod
			$idLive = $oListeSessions->results[$i]->id;
			// Dans Pod, l'information est sauvegardé sous la forme NUMERO_SERVEUR/NUMERO_REPERTOIRE_bbb_live_streaming
			$server = $oListeSessions->results[$i]->server;
			// Le live est il déjà en cours sur un des serveurs BBB-POD-LIVE ?
			$status = $oListeSessions->results[$i]->status;
			// Utilisateur ayant lancé ce live
			$user = $oListeSessions->results[$i]->user;
			// Prise en compte seulement des lives en cours de ce serveur
			if (($status == 1) && (strpos("$server", SERVER_NUMBER . "/") !== false)) {
				// Sauvegarde du NUMERO_REPERTOIRE_bbb_live_streaming
				$processInProgress = str_replace(SERVER_NUMBER . "/", "", $server);
				// Utilisation d'une classe standard
				$liveInProgress = new stdClass();
				$liveInProgress->id = $idLive;
				$liveInProgress->idBbbLiveStreaming = $processInProgress;
				// Ajout de cet objet au tableau des lives en cours sur ce serveur
				$GLOBALS["livesInProgressOnThisServer"][] = $liveInProgress;
				writeLog("    => Le live $idLive de $user est toujours en cours sur le serveur/bbb_live_streaming : $server.", "DEBUG");
			}
		}
	}
	else {
		writeLog("  + Commande '$cmdStatus1' : $sRetourVerificationStatus1[0]", "ERROR", __FILE__, __LINE__);
	}

	// Recherche si des utilisateurs ont lancé des lives depuis Pod
	$cmdStatus0 = "curl --silent -H 'Content-Type: application/json' ";
	$cmdStatus0 .= "-H 'Authorization: Token " . POD_TOKEN . "' ";
	$cmdStatus0 .= "-X GET " . checkEndWithoutSlash(POD_URL) . "/rest/bbb_livestream/?status=0";
	
	$verificationStatus0 = exec("$cmdStatus0 2>&1", $aRetourVerificationStatus0, $sRetourVerificationStatus0);

	writeLog("Recherche si des utilisateurs ont lancé des lives depuis Pod", "DEBUG");
	
	// En cas d'erreur, le code de retour est différent de 0
	if ($sRetourVerificationStatus0 == 0) {
		writeLog("  + Commande '$cmdStatus0' : $aRetourVerificationStatus0[0]", "DEBUG");
		
		$oListeSessions = json_decode($aRetourVerificationStatus0[0]);
		// Recherche des nouvelles demandes de lives, sauvegardées dans Pod
		for ($i = 0; $i < $oListeSessions->count; $i++) {
			// Identifiant du live BBB dans Pod
			$idLive = $oListeSessions->results[$i]->id;
			// Adresse de la session dans Pod
			$urlMeeting = $oListeSessions->results[$i]->meeting;
			// Nom du serveur/processus déjà en charge de ce live
			$server = $oListeSessions->results[$i]->server;
			// Le live est il déjà en cours sur un des serveurs BBB-POD-LIVE ?
			$status = $oListeSessions->results[$i]->status;
			// Utilisateur ayant lancé ce live
			$user = $oListeSessions->results[$i]->user;
			// Identifiant du répertoire bbb-live-streaming qui s'occupera de réaliser le live, si disponible
			$idBbbLiveStreaming = 0;
			// Recherche si ce serveur peut encore lancer un direct
			for ($j = 1; $j <= NUMBER_LIVES; $j++) {
				// Variable de travail
				$idBbbLiveStreamingUsed = false;
				foreach ($GLOBALS["livesInProgressOnThisServer"] as $ligneLiveInProgressOnThisServer) {
					// Cet idBbbLiveStreaming est déjà utilisé
					if ($ligneLiveInProgressOnThisServer->idBbbLiveStreaming == $j) {
						$idBbbLiveStreamingUsed = true;
					}
				}
				// Le slot idBbbLiveStreaming est non utilisé
				if (! $idBbbLiveStreamingUsed) {
					// Un slot est disponible
					$idBbbLiveStreaming = $j;
					// Ajout de l'information aux lives en cours sur ce serveur
					$liveInProgress2 = new stdClass();
					$liveInProgress2->id = $idLive;
					$liveInProgress2->idBbbLiveStreaming = $idBbbLiveStreaming;
					$GLOBALS["livesInProgressOnThisServer"][] = $liveInProgress2;
					break;
				}
			}
			// Un slot est disponible sur ce serveur pour réaliser un live ?
			if ($idBbbLiveStreaming == 0) {
				writeLog("     => Impossible de lancer le live $idLive de $user sur ce serveur : il y a déjà " . NUMBER_LIVES . " directs qui sont gérés par ce serveur.", "INFO");
			}
			else {
				writeLog("     => Lancement du live $idLive de $user, via bbb-live-streaming$idBbbLiveStreaming", "INFO");
				configureAndStartLive($idLive, $urlMeeting, $idBbbLiveStreaming);
			}
		}
	}
	else {
		writeLog("  + Commande '$cmdStatus0' : $sRetourVerificationStatus0[0]", "ERROR", __FILE__, __LINE__);
	}
}

/**
 * Procédure permettant de configurer, puis de lancer, le plugin nécessaire au démarrage d'un direct.
 * Cette procédure créé également le diffuseur nécessaire à l'affichage du live dans Pod.
 * @param string $idLive - Identifiant du live BBB de Pod à démarrer (cf. table bbb_meeting)
 * @param string $urlMeeting - URL de la session BBB de Pod à démarrer (cf. table bbb_livestream)
 * @param string $idBbbLiveStreaming - Identifiant du répertoire bbb-live-streaming qui va être utilisé pour lancer ce direct
 */
function configureAndStartLive($idLive, $urlMeeting, $idBbbLiveStreaming) {
	writeLog("-----Configuration et démarrage du direct : configureAndStartLive($idLive, '$urlMeeting', $idBbbLiveStreaming)-----", "DEBUG");
	
	$cmd = "curl --silent -H 'Content-Type: application/json' ";
	$cmd .= "-H 'Authorization: Token " . POD_TOKEN . "' ";
	$cmd .= "-X GET $urlMeeting";
	$verification = exec("$cmd 2>&1", $aRetourVerification, $sRetourVerification);
	
	writeLog("Récupération de l'objet meeting ($urlMeeting) depuis Pod", "DEBUG");
	
	if ($sRetourVerification == 0) {
		writeLog("  + Commande '$cmd' : $aRetourVerification[0]", "DEBUG");
		
		// Récupération de l'objet meeting
		$oMeeting = json_decode($aRetourVerification[0]);
		// Nom de la session, sans caractères problématiques ni espaces, et la chaîne bbb- en premier pour éviter toute confusion avec un diffuseur existant
		$nameMeeting = "bbb-" . formatString($oMeeting->meeting_name);
		// Nom de la session, sans caractères problématiques avec espaces, et la chaîne (BBB) en premier pour éviter toute confusion avec un diffuseur existant
		$nameMeetingToDisplay = "[BBB] " . formatStringToDisplay($oMeeting->meeting_name);
		// Id de la session
		$idMeeting = $oMeeting->meeting_id;
		
		
		// Récupération des informations concernant les options saisies par l'utilisateur
		$cmdOptions = "curl --silent -H 'Content-Type: application/json' ";
		$cmdOptions .= "-H 'Authorization: Token " . POD_TOKEN . "' ";
		$cmdOptions .= "-X GET " . checkEndWithoutSlash(POD_URL) . "/rest/bbb_livestream/$idLive/";
		$verificationOptions = exec("$cmdOptions 2>&1", $aRetourVerificationOptions, $sRetourVerificationOptions);
		
		writeLog("Récupération des options de l'objet bbb_livestream (/rest/bbb_livestream/$idLive/) depuis Pod", "DEBUG");
		
		$isRestricted = "false";
		$enableChat = "false";
		$showChat = "true";
		$downloadMeeting = "false";
		if ($sRetourVerificationOptions == 0) {
			// Récupération de l'objet live
			$oLive = json_decode($aRetourVerificationOptions[0]);
			// Accès restreint
			if ($oLive->is_restricted == 1) {
				$isRestricted = "true";
			} else {
				$isRestricted = "false";
			}
			// Utilisation du chat
			if ($oLive->enable_chat == 1) {
				$enableChat = "true";
			} else {
				$enableChat = "false";
			}
			// Affichage du chat dans la vidéo
			if ($oLive->show_chat == 1) {
				$showChat = "true";
			} else {
				$showChat = "false";
			}
			// Téléchargement de la vidéo en fin de live
			if ($oLive->download_meeting == 1) {
				$downloadMeeting = "true";
			} else {
				$downloadMeeting = "false";
			}
		}
		else {
			writeLog("  + Commande '$cmdOptions' : $sRetourVerificationOptions[0]", "ERROR", __FILE__, __LINE__);
		}
		
		/* Modification de la configuration du docker-compose.yml */
		writeLog("  + Modification de la configuration du docker-compose.yml", "DEBUG");
		$dockerFile = checkEndSlash(PHYSICAL_BASE_ROOT) . "bbb-live-streaming" . $idBbbLiveStreaming . "/docker-compose.yml";
		// Configuration du nom du container (container_name)
		$nameContainer = "liveStreaming" . $idBbbLiveStreaming;
		$cmdSed0 = "sed -i \"s/^.*container_name:.*/    container_name: $nameContainer/\" $dockerFile";
		exec("$cmdSed0 2>&1", $aRetourVerificationSed0, $sRetourVerificationSed0);
		if ($sRetourVerificationSed0 != 0) { writeLog("      - Commande '$cmdSed0' : $aRetourVerificationSed0[0]", "ERROR", __FILE__, __LINE__); }
		// Configuration du port utilisé par le host (ligne sous ports:), de la forme - "6379:6379" pour 1°, - "6380:6379" pour le 2°....
		$port = 6378 + $idBbbLiveStreaming;
		$cmdSed01 = "sed -i \"s/^.*:6379:.*/     - \"$port:6379\"/\" $dockerFile";
		exec("$cmdSed01 2>&1", $aRetourVerificationSed01, $sRetourVerificationSed01);
		if ($sRetourVerificationSed01 != 0) { writeLog("      - Commande '$cmdSed01' : $aRetourVerificationSed01[0]", "ERROR", __FILE__, __LINE__); }
		// Configuration du serveur BBB/Scalelite (BBB_URL)		
		// Gestion des caractères / de BBB_URL pour être utilisé via sed
		$bbbURL = str_replace("/", "\/", checkEndWithoutSlash(BBB_URL));
		$cmdSed1 = "sed -i \"s/^.*BBB_URL=.*/      - BBB_URL=$bbbURL/\" $dockerFile";
		exec("$cmdSed1 2>&1", $aRetourVerificationSed1, $sRetourVerificationSed1);
		if ($sRetourVerificationSed1 != 0) { writeLog("      - Commande '$cmdSed1' : $aRetourVerificationSed1[0]", "ERROR", __FILE__, __LINE__); }
		// Configuration de la clé secrète (BBB_SECRET)
		$cmdSed2 = "sed -i \"s/^.*BBB_SECRET=.*/      - BBB_SECRET=".BBB_SECRET."/\" $dockerFile";
		exec("$cmdSed2 2>&1", $aRetourVerificationSed2, $sRetourVerificationSed2);
		if ($sRetourVerificationSed2 != 0) { writeLog("      - Commande '$cmdSed2' : $aRetourVerificationSed2[0]", "ERROR", __FILE__, __LINE__); }
		// Configuration de la timezone (TZ)
		$cmdSed3 = "sed -i \"s/^.*TZ=.*/      - TZ=Europe\/Paris/\" $dockerFile";
		exec("$cmdSed3 2>&1", $aRetourVerificationSed3, $sRetourVerificationSed3);
		if ($sRetourVerificationSed3 != 0) { writeLog("      - Commande '$cmdSed3' : $aRetourVerificationSed3[0]", "ERROR", __FILE__, __LINE__); }
		// Configuration de la résolution (BBB_RESOLUTION)
		$cmdSed4 = "sed -i \"s/^.*BBB_RESOLUTION=.*/      - BBB_RESOLUTION=".BBB_RESOLUTION."/\" $dockerFile";
		exec("$cmdSed4 2>&1", $aRetourVerificationSed4, $sRetourVerificationSed4);
		if ($sRetourVerificationSed4 != 0) { writeLog("      - Commande '$cmdSed4' : $aRetourVerificationSed4[0]", "ERROR", __FILE__, __LINE__); }
		// Configuration du bitrate de la vidéo (FFMPEG_STREAM_VIDEO_BITRATE)
		$cmdSed5 = "sed -i \"s/^.*FFMPEG_STREAM_VIDEO_BITRATE=.*/      - FFMPEG_STREAM_VIDEO_BITRATE=".FFMPEG_STREAM_VIDEO_BITRATE."/\" $dockerFile";
		exec("$cmdSed5 2>&1", $aRetourVerificationSed5, $sRetourVerificationSed5);
		if ($sRetourVerificationSed5 != 0) { writeLog("      - Commande '$cmdSed5' : $aRetourVerificationSed5[0]", "ERROR", __FILE__, __LINE__); }
		// Configuration du nombre de threads (FFMPEG_STREAM_THREADS)
		$cmdSed6 = "sed -i \"s/^.*FFMPEG_STREAM_THREADS=.*/      - FFMPEG_STREAM_THREADS=".FFMPEG_STREAM_THREADS."/\" $dockerFile";
		exec("$cmdSed6 2>&1", $aRetourVerificationSed6, $sRetourVerificationSed6);
		if ($sRetourVerificationSed6 != 0) { writeLog("      - Commande '$cmdSed6' : $aRetourVerificationSed6[0]", "ERROR", __FILE__, __LINE__); }
		// Modification de la ligne concernant l'id de la session à streamer (BBB_MEETING_ID)
		$cmdSed7 = "sed -i \"s/^.*BBB_MEETING_ID=.*/      - BBB_MEETING_ID=$idMeeting/\" " . $dockerFile;
		exec("$cmdSed7 2>&1", $aRetourVerificationSed7, $sRetourVerificationSed7);
		if ($sRetourVerificationSed7 != 0) { writeLog("      - Commande '$cmdSed7' : $aRetourVerificationSed7[0]", "ERROR", __FILE__, __LINE__); }
		// Modification de la ligne concernant le flux RTMP (BBB_STREAM_URL)
		// Gestion des caractères / du serveur RTMP pour être utilisé via sed
		$rtmpServer = str_replace("/", "\/", checkEndSlash(BBB_STREAM_URL));
		$cmdSed8 = "sed -i \"s/^.*BBB_STREAM_URL=.*/      - BBB_STREAM_URL=" . $rtmpServer . "$nameMeeting/\" " . $dockerFile;
		exec("$cmdSed8 2>&1", $aRetourVerificationSed8, $sRetourVerificationSed8);
		if ($sRetourVerificationSed8 != 0) { writeLog("      - Commande '$cmdSed8' : $aRetourVerificationSed8[0]", "ERROR", __FILE__, __LINE__); }
		// Modification de la ligne concernant l'utilisation de chat (BBB_ENABLE_CHAT)
		$cmdSed9 = "sed -i \"s/^.*BBB_ENABLE_CHAT=.*/      - BBB_ENABLE_CHAT=$enableChat/\" " . $dockerFile;
		exec("$cmdSed9 2>&1", $aRetourVerificationSed9, $sRetourVerificationSed9);
		if ($sRetourVerificationSed9 != 0) { writeLog("      - Commande '$cmdSed9' : $aRetourVerificationSed9[0]", "ERROR", __FILE__, __LINE__); }
		// Modification de la ligne concernant l'affichage du chat dans la vidéo (BBB_SHOW_CHAT)
		$cmdSed10 = "sed -i \"s/^.*BBB_SHOW_CHAT=.*/      - BBB_SHOW_CHAT=$showChat/\" " . $dockerFile;
		exec("$cmdSed10 2>&1", $aRetourVerificationSed10, $sRetourVerificationSed10);
		if ($sRetourVerificationSed10 != 0) { writeLog("      - Commande '$cmdSed10' : $aRetourVerificationSed10[0]", "ERROR", __FILE__, __LINE__); }
		// Modification de la ligne concernant l'enregistrement de la vidéo du live (BBB_DOWNLOAD_MEETING)
		$cmdSed11 = "sed -i \"s/^.*BBB_DOWNLOAD_MEETING=.*/      - BBB_DOWNLOAD_MEETING=$downloadMeeting/\" " . $dockerFile;
		exec("$cmdSed11 2>&1", $aRetourVerificationSed11, $sRetourVerificationSed11);
		if ($sRetourVerificationSed11 != 0) { writeLog("      - Commande '$cmdSed11' : $aRetourVerificationSed11[0]", "ERROR", __FILE__, __LINE__); }
		// Modification de la ligne concernant le titre de la session (BBB_MEETING_TITLE)
		$cmdSed12 = "sed -i \"s/^.*BBB_MEETING_TITLE=.*/      - BBB_MEETING_TITLE=$nameMeetingToDisplay/\" " . $dockerFile;
		exec("$cmdSed12 2>&1", $aRetourVerificationSed12, $sRetourVerificationSed12);
		if ($sRetourVerificationSed12 != 0) { writeLog("      - Commande '$cmdSed12' : $aRetourVerificationSed12[0]", "ERROR", __FILE__, __LINE__); }
		// Modification de la ligne concernant le mot de passe d'un participant de la session (BBB_ATTENDEE_PASSWORD)
		$cmdSed13 = "sed -i \"s/^.*BBB_ATTENDEE_PASSWORD=.*/      - BBB_ATTENDEE_PASSWORD=".BBB_ATTENDEE_PASSWORD."/\" " . $dockerFile;
		exec("$cmdSed13 2>&1", $aRetourVerificationSed13, $sRetourVerificationSed13);
		if ($sRetourVerificationSed13 != 0) { writeLog("      - Commande '$cmdSed13' : $aRetourVerificationSed13[0]", "ERROR", __FILE__, __LINE__); }
		// Modification de la ligne concernant le mot de passe d'un modérateur de la session (BBB_MODERATOR_PASSWORD)
		$cmdSed14 = "sed -i \"s/^.*BBB_MODERATOR_PASSWORD=.*/      - BBB_MODERATOR_PASSWORD=".BBB_MODERATOR_PASSWORD."/\" " . $dockerFile;
		exec("$cmdSed14 2>&1", $aRetourVerificationSed14, $sRetourVerificationSed14);
		if ($sRetourVerificationSed14 != 0) { writeLog("      - Commande '$cmdSed14' : $aRetourVerificationSed14[0]", "ERROR", __FILE__, __LINE__); }
		// Modification de la ligne concernant le channel pour REDIS, encas d'utilisation du chat (BBB_REDIS_CHANNEL)
		// Typiquement pour le répertoire 1 => chat1, 2 => chat2, 3 => chat3...
		$channelRedis = "chat" . $idBbbLiveStreaming;
		$cmdSed15 = "sed -i \"s/^.*BBB_REDIS_CHANNEL=.*/      - BBB_REDIS_CHANNEL=$channelRedis/\" " . $dockerFile;
		exec("$cmdSed15 2>&1", $aRetourVerificationSed15, $sRetourVerificationSed15);
		if ($sRetourVerificationSed15 != 0) { writeLog("      - Commande '$cmdSed15' : $aRetourVerificationSed15[0]", "ERROR", __FILE__, __LINE__); }
		// Modification de la ligne concernant le mode DEBUG (DEBUG)
		if (DEBUG) { $debug = "true"; } else { $debug = "false"; }
		$cmdSed16 = "sed -i \"s/^.*DEBUG=.*/      - DEBUG=$debug/\" " . $dockerFile;
		exec("$cmdSed16 2>&1", $aRetourVerificationSed16, $sRetourVerificationSed16);
		if ($sRetourVerificationSed16 != 0) { writeLog("      - Commande '$cmdSed16' : $aRetourVerificationSed16[0]", "ERROR", __FILE__, __LINE__); }

		
		/* Création du diffuseur correspondant dans Pod */
		$cmdBroadcaster = "curl --silent  -H 'Content-Type: multipart/form-data' ";
		$cmdBroadcaster .= "-H 'Authorization: Token " . POD_TOKEN . "' ";
		$cmdBroadcaster .= "-F 'url=" . checkEndSlash(POD_HLS_STREAM) . "$nameMeeting.m3u8' ";
		$cmdBroadcaster .= "-F 'building=" . checkEndWithoutSlash(POD_URL) . "/rest/buildings/" . POD_ID_BUILDING . "/' ";
		$cmdBroadcaster .= "-F 'name=$nameMeetingToDisplay' -F 'status=true' -F 'is_restricted=$isRestricted' '" . checkEndWithoutSlash(POD_URL) . "/rest/broadcasters/'";
		$verificationBroadcaster = exec("$cmdBroadcaster 2>&1", $aRetourVerificationBroadcaster, $sRetourVerificationBroadcaster);
		
		writeLog("  + Création du diffuseur correspondant dans Pod", "DEBUG");
		
		if ($sRetourVerificationBroadcaster == 0) {
			writeLog("    - Commande '$cmdBroadcaster' : $aRetourVerificationBroadcaster[0]", "DEBUG");
			// Id du diffuseur
			$idBroadcaster = 0;
			
			// Récupération du diffuseur créé
			$oBroadcaster = json_decode($aRetourVerificationBroadcaster[0]);
			
			// Si le diffuseur existe déjà, $aRetourVerificationBroadcaster[0] contiendra un message d'avertissement du type :
			// {"url":["Un objet Diffuseur avec ce champ URL existe déjà."],"name":["Un objet Diffuseur avec ce champ nom existe déjà."]}
			if (strpos($aRetourVerificationBroadcaster[0], "Un objet Diffuseur avec ce champ nom existe déjà.") !== false) {
				$cmdBroadcaster2 = "curl --silent -H 'Content-Type: application/json' ";
				$cmdBroadcaster2 .= "-H 'Authorization: Token " . POD_TOKEN . "' ";
				$cmdBroadcaster2 .= "-X GET " . checkEndWithoutSlash(POD_URL) . "/rest/broadcasters/$nameMeeting/";
				$verificationBroadcaster2 = exec("$cmdBroadcaster2 2>&1", $aRetourVerificationBroadcaster2, $sRetourVerificationBroadcaster2);
				
				writeLog("  + Récupération du diffuseur déjà existant dans Pod", "DEBUG");
				if ($sRetourVerificationBroadcaster2 == 0) {
					writeLog("    - Commande '$cmdBroadcaster2' : $aRetourVerificationBroadcaster2[0]", "DEBUG");
					$oBroadcaster2 = json_decode($aRetourVerificationBroadcaster2[0]);
					$idBroadcaster = $oBroadcaster2->id;
				}
				else {
					writeLog("  + Commande '$cmdBroadcaster2' : $aRetourVerificationBroadcaster2[0]", "ERROR", __FILE__, __LINE__);
				}
			}
			else {
				$idBroadcaster = $oBroadcaster->id;
			}

			if ($idBroadcaster != 0) {
				writeLog("      + Utilisation du diffuseur $idBroadcaster", "DEBUG");
			
				// Démarrage du live, si nécessaire
				startLive($idLive, checkEndSlash(BBB_STREAM_URL) . "$nameMeeting", $idBbbLiveStreaming, $idBroadcaster);
			}
			else {
				writeLog("  + Démarrage impossible du live : aucun identifiant du diffuseur défini.", "ERROR", __FILE__, __LINE__);
			}
		}
		else {
			writeLog("  + Commande '$cmdBroadcaster' : $aRetourVerificationBroadcaster[0]", "ERROR", __FILE__, __LINE__);
		}
	}
	else {
		writeLog("  + Commande '$cmd' : $sRetourVerification[0]", "ERROR", __FILE__, __LINE__);
	}
}

/**
 * Procédure permettant de démarrer un direct.
 * @param string $idLive - Identifiant du live BBB de Pod à démarrer (cf. table bbb_meeting)
 * @param string $streamName - Nom du stream utilisé, en correspondance avec le diffuseur créé précédemment
 * @param string $idBbbLiveStreaming - Identifiant du répertoire bbb-live-streaming qui va être utilisé pour lancer ce direct
 * @param string $idBroadcaster - Identifiant du diffuseur qui va être utilisé pour lancer ce direct
 */
function startLive($idLive, $streamName, $idBbbLiveStreaming, $idBroadcaster) {
	writeLog("-----Démarrage du direct : startLive($idLive, '$streamName', $idBbbLiveStreaming, $idBroadcaster)-----", "DEBUG");
	
	if (DEBUG) {
		// Avec gestions des logs, dans le répertoire des logs. Le nom du fichier correspond à l'id du live BBB de Pod ((cf. table bbb_meeting)
		$cmd = "cd " . checkEndSlash(PHYSICAL_BASE_ROOT) . "bbb-live-streaming" . $idBbbLiveStreaming . " ; docker-compose up 1>" . checkEndSlash(PHYSICAL_LOG_ROOT) . "$idLive.log";
		exec("$cmd 2>&1 &", $aRetourVerification, $sRetourVerification);
	}
	else {
		// En mode daemon
		$cmd = "cd " . checkEndSlash(PHYSICAL_BASE_ROOT) . "bbb-live-streaming" . $idBbbLiveStreaming . " ; docker-compose up -d";
		exec("$cmd 2>&1", $aRetourVerification, $sRetourVerification);
	}
	
	writeLog("Démarrage du live", "DEBUG");
	
	if ($sRetourVerification == 0) {
		writeLog("  + Commande '$cmd'", "DEBUG");

		// Définition du port pour REDIS (en cas d'utilisation du chat)
		// Typiquement pour le répertoire 1 => 6379, 2 => 6380, 3 => 6381...
		$portRedis = 6378 + $idBbbLiveStreaming;
		
		// Définition du channel pour REDIS (en cas d'utilisation du chat)
		// Typiquement pour le répertoire 1 => chat1, 2 => chat2, 3 => chat3...
		$channelRedis = "chat" . $idBbbLiveStreaming;
		
		// Mise à jour de l'information dans Pod, via l'API Rest
		$cmdMajPod = "curl --silent -H 'Content-Type: application/json' ";
		$cmdMajPod .= "-H 'Authorization: Token " . POD_TOKEN . "' ";
		$cmdMajPod .= "-X PATCH -d '{\"server\":\"" . SERVER_NUMBER . "/" . $idBbbLiveStreaming . "\", \"status\":1, \"broadcaster_id\": $idBroadcaster, \"redis_hostname\":\"" . SERVER_HOSTNAME . "\", \"redis_port\": $portRedis, \"redis_channel\":\"$channelRedis\"}' ";
		$cmdMajPod .= "" . checkEndWithoutSlash(POD_URL) . "/rest/bbb_livestream/$idLive/";
		exec("$cmdMajPod", $aRetourVerificationMajPod, $sRetourVerificationMajPod);
		
		writeLog("  + Mise à jour de l'information du bbb_livestream dans Pod", "DEBUG");
		
		if ($sRetourVerificationMajPod == 0) {
			writeLog("    - Commande '$cmdMajPod' : $aRetourVerificationMajPod[0]", "DEBUG");
		}
		else {
			writeLog("    - Commande '$cmdMajPod' : $sRetourVerificationMajPod[0]", "ERROR", __FILE__, __LINE__);
		}
	}
	else {
		writeLog("  + Commande '$cmd' : $sRetourVerification[0]", "ERROR", __FILE__, __LINE__);
	}
	sendEmail("[BBB-POD-LIVE] Démarrage d'un live", "Démarrage d'un direct (id : $idLive, stream : $streamName) sur le serveur " . SERVER_NUMBER);
}

/**
 * Procédure permettant d'identifier et d'arrêter des directs dont la session BigBlueButton a été arrêtée.
 */
function stopLives() {
	writeLog("-----Arrêt des directs : stopLives()-----", "DEBUG");
	
	// Checksum utile pour récupérer les informations des sessions en cours sur BigBlueButton/Scalelite
	$checksum = sha1("getMeetings" . BBB_SECRET);
	// Adresse utile pour récupérer les informations des sessions en cours sur BigBlueButton/Scalelite
	$bbbUrlGetMeetings = checkEndWithoutSlash(BBB_URL) . "/getMeetings?checksum=" . $checksum;
	// Variable permettant de connaitre les sessions en cours sur le serveur BigBlueButton/Scalelite
	$meetingsInProgressOnBBB = array();
	
	// On ne récupère les sessions du serveur BigBlueButton/Scalelite que s'il existe des lives en cours sur ce serveur
	if (count($GLOBALS["livesInProgressOnThisServer"]) > 0) {
		$xml = simplexml_load_file($bbbUrlGetMeetings);
		writeLog("Récupération des sessions depuis le serveur BigBlueButton/Scalelite", "DEBUG");
		if($xml ===  FALSE) {
			writeLog("  + Impossible de se connecter au serveur BBB/Scalelite : $bbbUrlGetMeetings", "ERROR", __FILE__, __LINE__);
		} else {
			writeLog("  + Requête sur le serveur BBB/Scalelite : $bbbUrlGetMeetings", "DEBUG");
			foreach ($xml->meetings->meeting as $meeting) {
				// Ajout du meetingID au tableau des sessions BBB en cours
				$meetingsInProgressOnBBB[] = $meeting->meetingID;
			}
		}

		// Recherche de tous les directs marqués comme étant en cours
		foreach ($GLOBALS["livesInProgressOnThisServer"] as $ligneLiveInProgressOnThisServer) {
			// Récupération du BBB_MEETING_ID correspondant dans le docker-compose.yml
			$dockerFile = checkEndSlash(PHYSICAL_BASE_ROOT) . "bbb-live-streaming" . $ligneLiveInProgressOnThisServer->idBbbLiveStreaming . "/docker-compose.yml";
			$dockerDirectory = checkEndSlash(PHYSICAL_BASE_ROOT) . "bbb-live-streaming" . $ligneLiveInProgressOnThisServer->idBbbLiveStreaming;
			$cmdGrep1="grep BBB_MEETING_ID $dockerFile| cut -d\"=\" -f2";
			$verificationGrep1 = exec("$cmdGrep1 2>&1", $aRetourVerificationGrep1, $sRetourVerificationGrep1);
			if ($sRetourVerificationGrep1 == 0) {
				writeLog("  + Commande '$cmdGrep1' : $aRetourVerificationGrep1[0]", "DEBUG");
				// Meeting ID correspondant
				$bbbMeetingId = $aRetourVerificationGrep1[0];

				// Recherche du nom du diffuseur correspondant (sauvegardé aussi dans BBB_MEETING_TITLE du fichier compose)
				$broadcasterName = "";
				$cmdGrep2="grep BBB_MEETING_TITLE $dockerFile| cut -d\"=\" -f2";
				$verificationGrep2 = exec("$cmdGrep2 2>&1", $aRetourVerificationGrep2, $sRetourVerificationGrep2);
				if ($sRetourVerificationGrep2 == 0) {
					writeLog("  + Commande '$cmdGrep2' : $aRetourVerificationGrep2[0]", "DEBUG");
					// Nom du diffuseur correspondant
					$broadcasterName = formatString($aRetourVerificationGrep2[0]);
				}
				else {
					writeLog("  + Commande '$cmdGrep2' : $sRetourVerificationGrep2[0]", "ERROR", __FILE__, __LINE__);
				}
				
				// Cet ID n'est plus dans la liste des sessions en cours sur BBB : 
				//  - on arrête le container docker correspondant
				//  - on supprime le diffuseur correspondant
				//  - on copie, pour permettre l'encodage, le fichier vidéo si l'utilisateur a enregistré la session
				if (! in_array($bbbMeetingId, $meetingsInProgressOnBBB)) {
					writeLog("   + La session BigBlueButton $bbbMeetingId est arrêtée. Arrêt du container docker $dockerFile, suppression du diffuseur correspondant, copie du fichier vidéo généré selon le souhait de l'utilisateur", "INFO");
					$cmdStop = "cd $dockerDirectory; docker-compose down";
					exec("$cmdStop 2>&1", $aRetourVerificationStop, $sRetourVerificationStop);				
					if ($sRetourVerificationStop == 0) {
						writeLog("   - Le container docker $dockerDirectory est bien arrêté", "DEBUG");
						// Formatage de la date d'arrêt dans le bon format
						$endDate = date('Y-m-d H:i:s');
						// On sauvegarde cette information dans la base de Pod via l'appel à l'API Rest
						$cmdMajPod1 = "curl --silent -H 'Content-Type: application/json' ";
						$cmdMajPod1 .= "-H 'Authorization: Token " . POD_TOKEN . "' ";
						$cmdMajPod1 .= "-X PATCH -d '{\"end_date\":\"$endDate\", \"status\":2}' ";
						$cmdMajPod1 .= "" . checkEndWithoutSlash(POD_URL) . "/rest/bbb_livestream/" . $ligneLiveInProgressOnThisServer->id . "/";
						exec("$cmdMajPod1", $aRetourVerificationMajPod1, $sRetourVerificationMajPod1);
						
						writeLog("  + Mise à jour de l'information du bbb_livestream dans Pod", "DEBUG");
						
						// URL de l'API Rest du meeting en cours d'arrêt
						$urlApiRestMeeting = "";
						// URL de l'API Rest du user qui a réalisé le live qui en cours d'arrêt
						$urlApiRestUser = "";
						if ($sRetourVerificationMajPod1 == 0) {
							writeLog("    - Commande '$cmdMajPod1' : $aRetourVerificationMajPod1[0]", "DEBUG");
							$oLive = json_decode($aRetourVerificationMajPod1[0]);
							if (isset($oLive->meeting)) {
								$urlApiRestMeeting = $oLive->meeting;
								$urlApiRestUser = $oLive->user;
							}
						}
						else {
							writeLog("    - Commande '$cmdMajPod1' : $sRetourVerificationMajPod1[0]", "ERROR", __FILE__, __LINE__);
						}
						// Suppression du diffuseur
						if ($broadcasterName != "") {
							deleteBroadcaster($broadcasterName);
						}
						
						// Recherche si l'utilisateur a souhaité cet enregistrement (sauvegardé aussi dans BBB_DOWNLOAD_MEETING du fichier compose)
						$downloadMeeting = false;
						$cmdGrep3="grep BBB_DOWNLOAD_MEETING $dockerFile| cut -d\"=\" -f2";
						$verificationGrep3 = exec("$cmdGrep3 2>&1", $aRetourVerificationGrep3, $sRetourVerificationGrep3);
						if ($sRetourVerificationGrep3 == 0) {
							writeLog("  + Commande '$cmdGrep3' : $aRetourVerificationGrep3[0]", "DEBUG");
							// Nom du diffuseur correspondant
							if ($aRetourVerificationGrep3[0] == "true") {
								$downloadMeeting = true;
							}
						}
						else {
							writeLog("  + Commande '$cmdGrep3' : $sRetourVerificationGrep3[0]", "ERROR", __FILE__, __LINE__);
						}
												
						// Copie du fichier vidéo créé : si c'est configuré pour et que l'utilisateur a souhaité cet enregistrement
						if (POD_DEFAULT_BBB_PATH != "" && $downloadMeeting) {
							// Recherche de internal_meeting_id correspondant à cette session
							$cmdMajPod2 = "curl --silent -H 'Content-Type: application/json' ";
							$cmdMajPod2 .= "-H 'Authorization: Token " . POD_TOKEN . "' ";
							$cmdMajPod2 .= "-X PATCH -d '{\"encoded_by\":\"$urlApiRestUser\", \"encoding_step\":3}' ";
							$cmdMajPod2 .= "$urlApiRestMeeting";
							$verificationMajPod2 = exec("$cmdMajPod2 2>&1", $aRetourVerificationMajPod2, $sRetourVerificationMajPod2);
							
							writeLog("  + Récupération de l'internal_meeting_id correspondant à l'objet bbb_meeting $bbbMeetingId depuis Pod", "DEBUG");
							$internalMeetingId = "";
							if ($sRetourVerificationMajPod2 == 0) {
								writeLog("    - Commande '$cmdMajPod2' : $aRetourVerificationMajPod2[0]", "DEBUG");
								
								// Recherche de l'internal_meeting_id correspondant au meeting
								$oMeeting = json_decode($aRetourVerificationMajPod2[0]);
								if (isset($oMeeting->internal_meeting_id)) {
									$internalMeetingId = $oMeeting->internal_meeting_id;
								}
							}
							else {
								writeLog("    - Commande '$cmdMajPod2' : $sRetourVerificationMajPod2[0]", "ERROR", __FILE__, __LINE__);
							}
							
							if ($internalMeetingId != "") {
								processDirectory($ligneLiveInProgressOnThisServer->idBbbLiveStreaming, $internalMeetingId);
							}
							else {
								writeLog("    - Impossible de récupérer l'internal meeting id pour le direct " . $ligneLiveInProgressOnThisServer->idBbbLiveStreaming, "ERROR", __FILE__, __LINE__);
							}
						}
					}
					else {
						writeLog("  + Commande '$cmdStop' : $sRetourVerificationStop[0]", "ERROR", __FILE__, __LINE__);
					}
				}
			}
			else {
				writeLog("  + Commande '$cmdGrep1' : $sRetourVerificationGrep1[0]", "ERROR", __FILE__, __LINE__);
			}
		}
	}
}

/**
 * Procédure permettant de supprimer un diffuseur dans Pod.
 * @param string $broadcasterName - Nom du diffuseur à supprimer
 */
function deleteBroadcaster($broadcasterName) {
	// Via l'API, il faut utiliser le slug et non le nom
	$slug = str_replace("[BBB]", "bbb", $broadcasterName);
	/* Suppression du diffuseur correspondant dans Pod */
	$cmdBroadcaster = "curl --silent ";
	$cmdBroadcaster .= "-H 'Authorization: Token " . POD_TOKEN . "' ";
	$cmdBroadcaster .= "-X DELETE '" . checkEndWithoutSlash(POD_URL) . "/rest/broadcasters/$slug/'";
	$verificationBroadcaster = exec("$cmdBroadcaster 2>&1", $aRetourVerificationBroadcaster, $sRetourVerificationBroadcaster);
	
	writeLog("  + Suppression du diffuseur $slug dans Pod", "DEBUG");
	
	if ($sRetourVerificationBroadcaster == 0) {
		writeLog("    - Commande '$cmdBroadcaster' exécutée", "DEBUG");
	}
	else {
		writeLog("  + Commande '$cmdBroadcaster' : $aRetourVerificationBroadcaster[0]", "ERROR", __FILE__, __LINE__);
	}
}

/**
 * Procédure permettant de copier le fichier vidéo créé, si un enregistrement existe de ce dernier.
 * Le fichier vidéo est créé dans le répertoire videodata du répertoire BigBlueButton-liveStreaming concerné.
 * Ce fichier vidéo sera copié dans le POD_DEFAULT_BBB_PATH et renommé sous la forme internalMeetingId.mkv.
 * Ce nommage est très important et permet au CRON Job bbb de Pod d'assigner le bon propriétaire à cette vidéo.
 * @param string $idBbbLiveStreaming - Identifiant du répertoire BigBlueButton-liveStreaming concerné.
 * @param string $internalMeetingId - Identifiant interne de la session BBB enregistrée.
 */
function processDirectory($idBbbLiveStreaming, $internalMeetingId) {
	writeLog("-----Copie des fichiers vidéos enregistrées sur le partage NFS, pour traitement automatique par POD : processDirectory($idBbbLiveStreaming, $internalMeetingId)-----", "DEBUG");
	// Parcours du répertoire videodata du répertoire BigBlueButton-liveStreaming concerné
	// Définition du répertoire
	$directoryLiveStreaming = checkEndSlash(PHYSICAL_BASE_ROOT) . "bbb-live-streaming$idBbbLiveStreaming/videodata";
	writeLog("Recherche de fichiers vidéos pour le direct $idBbbLiveStreaming : $directoryLiveStreaming", "DEBUG");
	if (file_exists($directoryLiveStreaming)) {
		$listFiles = scandir("$directoryLiveStreaming");
		// Mise en place d'une boucle, mais il ne doit y avoir qu'un seul fichier au maximum
		foreach ($listFiles as $key => $value) {
			if (strrpos($value, ".mkv")) {
				// Déplacer et renommer le fichier avec l'internalMeetingId
				$oldFilename = "$directoryLiveStreaming/$value";
				$newFilename = checkEndSlash(POD_DEFAULT_BBB_PATH) . "$internalMeetingId" . ".mkv";
				writeLog("  + Déplacement du fichier $oldFilename vers $newFilename", "DEBUG");
				@rename("$oldFilename", "$newFilename");
				// Positionnement de droits adéquats pour pouvoir être encodé par Pod
				// Normalement, il n'y en a pas besoin : le fichier généré a les droits 644, ce qui est suffisant.
				@chmod("$newFilename", 0755);
			}
		}
	}
}

/**
 * Fonction d'écriture dans le fichier de logs.
 * Les messages au niveau debug ne seront écris que si l'application est configuré en mode DEBUG (DEBUG = true).
 * @param string $message - Message à écrire
 * @param string $level - Niveau de log de ce message (debug, info, warning, error)
 * @param string $file - Nom du fichier PHP concerné (en cas d'erreur) 
 * @param int $line - Ligne dans le fichier PHP concerné (en cas d'erreur)
 * @return nombre d'octets écris, false sinon
 */
function writeLog($message, $level, $file=null, $line=null) {
	// Ecriture des lignes de debug seulement en cas de mode DEBUG
	if (($level == "DEBUG") && (! DEBUG)) {
		return false;
	}
	
	// Création du répertoire des logs si besoin
	if (! file_exists(checkEndSlash(PHYSICAL_LOG_ROOT))) {
		// Création du répertoire
		@mkdir(checkEndSlash(PHYSICAL_LOG_ROOT), 0755);
	}

	// Configuration du fichier de log, 1 par jour
	$logFile = checkEndSlash(PHYSICAL_LOG_ROOT) . gmdate("Y-m-d") . "_bbb-pod-live.log";
		
	// En cas de non existence, on créé ce fichier
	if (!file_exists($logFile)) {
		$file = fopen($logFile, "x+");
		// Une exception est levée en cas de non existence du fichier (problème manifeste de droits utilisateurs)
		if (!file_exists($logFile)) {
			echo "Erreur de configuration : impossible de créer le fichier $logFile.";
			throw new Exception("Impossible de créer le fichier $logFile.");
		}            		
	}
	
	// Une exception est levée en cas de problème d'écriture (problème manifeste de droits utilisateurs)
	if(!is_writeable($logFile)) {
		throw new Exception("$logFile n'a pas les droits en écriture.");
	}
	
	$message = gmdate("Y-m-d H:i:s") . " - [$level] - " . $message;
	$message .= is_null($file) ? '' : " - Fichier [$file]";
	$message .= is_null($line) ? '' : " - Ligne [$line].";
	$message .= "\n";
	
	// Surcharge de la variable globale signifiant une erreur dans le script
	if ($level == "ERROR") {
		$GLOBALS["txtErrorInScript"] .= "$message";
	}
	
	return file_put_contents( $logFile, $message, FILE_APPEND );
}

/**
 * Fonction permettant de vérifier que la chaîne de caractères finit par un /. En ajoute un si nécessaire.
 * @param string - Chaîne de caractères. 
 * @return Chaîne de caractères identique à celle en entrée, mais avec un / comme dernier caractère.
 */
function checkEndSlash($string) {
	if (substr($string, -1) !== "/" ) {
		$string .= "/";
	}
	return $string;
}

/**
 * Fonction permettant de vérifier que la chaîne de caractères ne finit pas par un /. Supprime ce / un si nécessaire.
 * @param string - Chaîne de caractères. 
 * @return Chaîne de caractères identique à celle en entrée, mais sans / à la fin.
 */
function checkEndWithoutSlash($string) {
	if (substr($string, -1) == "/" ) {
		$string = substr($string, 0, -1);
	}
	return $string;
}

/**
* Fonction permettant de supprimer les caractères accentués et autres caractéres problématiques d'une chaîne de caractères.
* Remplace aussi les espaces par des tirets
* @param $string - chaîne avec accents
* @return chaîne sans accents
*/
function formatString($string) {
	$string = htmlentities($string, ENT_NOQUOTES, 'utf-8');
	$string = preg_replace('#&([A-za-z])(?:uml|circ|tilde|acute|grave|cedil|ring);#', '\1', $string);
	$string = preg_replace('#&([A-za-z]{2})(?:lig);#', '\1', $string);
	$string = preg_replace('#&[^;]+;".()\'#', '', $string);
	$string = preg_replace('/\s+/', '-', $string);
	$string = str_replace("'", "-", $string);
	return $string;
}

/**
* Fonction permettant de supprimer les caractères accentués et autres caractéres problématiques d'une chaîne de caractères.
* Ne replace pas les espaces.
* @param $string - chaîne avec accents
* @return chaîne sans accents
*/
function formatStringToDisplay($string) {
	$string = htmlentities($string, ENT_NOQUOTES, 'utf-8');
	$string = preg_replace('#&([A-za-z])(?:uml|circ|tilde|acute|grave|cedil|ring);#', '\1', $string);
	$string = preg_replace('#&([A-za-z]{2})(?:lig);#', '\1', $string);
	$string = preg_replace('#&[^;]+;".()\'#', '', $string);
	$string = str_replace("'", "-", $string);
	return $string;
}

/**
* Procédure permettant d'envoyer un email à l'administrateur.
* @param $subject - sujet du mail
* @param $message - message du mail
*/
function sendEmail($subject, $message) {
	$to = ADMIN_EMAIL;
	$message = nl2br($message);

	$headers  = "MIME-Version: 1.0\r\n";
	$headers .= "Content-type: text/html; charset=utf-8\r\n";

	mail ($to, $subject, $message, $headers);
}			   
?>