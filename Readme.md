# Bouygues Bbox Monitor

[![Domoticz](https://img.shields.io/badge/Domoticz-Plugin-blue)](https://www.domoticz.com/)
[![Python](https://img.shields.io/badge/Python-3.x-green)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-À%20définir-lightgrey)]()

Plugin **Domoticz** en Python pour surveiller et contrôler une **Bouygues Telecom Bbox** via son API REST.

Il crée automatiquement des dispositifs Domoticz pour suivre l’état Internet, la VoIP, l’uptime, le firmware, les adresses IP WAN, les statistiques de trafic et déclencher un reboot de la box.

## Sommaire

- [Fonctionnalités](#fonctionnalités)
- [Aperçu](#aperçu)
- [Appareils créés](#appareils-créés)
- [Prérequis](#prérequis)
- [Installation](#installation)
- [Configuration](#configuration)
- [Utilisation](#utilisation)
- [Dépannage](#dépannage)
- [Arborescence](#arborescence)
- [Licence](#licence)

## Fonctionnalités

- Surveillance de l’état du lien Internet WAN.
- Surveillance de l’état de la ligne VoIP.
- Affichage de l’uptime de la Bbox.
- Affichage de la version firmware.
- Affichage des adresses IPv4 et IPv6 WAN.
- Mesure des données reçues et envoyées en Go.
- Mesure des débits download et upload en Mbps.
- Redémarrage de la Bbox depuis Domoticz.
- Création automatique des appareils au démarrage du plugin.

## Aperçu

### Switchs Domoticz

![Switchs Domoticz](Docs/SwitchsDomoticz.png)

### Mesures Domoticz

![Mesures Domoticz](Docs/MesuresDomoticz.png)

## Appareils créés

Le plugin crée automatiquement les périphériques suivants dans Domoticz :

| Appareil | Type | Rôle |
|---|---|---|
| Internet | Switch | État du lien WAN |
| VoIP | Switch | État de la ligne VoIP |
| Uptime Bbox | Texte | Temps de fonctionnement |
| Firmware Bbox | Texte | Version du firmware |
| IP WAN | Texte | Adresse IPv4 WAN |
| IPv6 WAN | Texte | Adresse IPv6 WAN |
| Données Reçues | Capteur custom | Volume reçu en Go |
| Données Envoyées | Capteur custom | Volume envoyé en Go |
| Download | Capteur custom | Débit descendant en Mbps |
| Upload | Capteur custom | Débit montant en Mbps |
| Reboot Bbox | Switch | Déclenche un redémarrage |

## Prérequis

- Domoticz avec support des plugins Python.
- Python 3.
- Une Bouygues Telecom Bbox accessible sur le réseau local.
- Le fichier `bbox.zip` placé dans le même dossier que `plugin.py`.

## Installation

1. Copier `plugin.py` dans le dossier des plugins Domoticz.
2. Copier `bbox.zip` dans le même dossier.
3. Vérifier que le fichier `icons.txt` dans `bbox.zip` contient une clé commençant par `BboxPlugin`.
4. Redémarrer Domoticz ou recharger les plugins.
5. Ajouter le plugin depuis l’interface Domoticz.

## Configuration

Lors de l’ajout du plugin, renseigner les paramètres suivants :

| Paramètre | Description | Valeur par défaut |
|---|---|---|
| Adresse IP Bbox | Adresse locale de la box | `192.168.1.1` |
| Mot de passe | Mot de passe de la Bbox | `password` |
| Intervalle de scrutation | Fréquence de mise à jour en secondes | `60` |
| Ignorer les erreurs SSL | Recommandé pour une IP locale | `Oui` |
| Niveau de debug | Niveau de logs | `Aucun` |

## Utilisation

Une fois lancé, le plugin interroge régulièrement l’API de la Bbox pour mettre à jour les capteurs Domoticz.

Le switch **Reboot Bbox** permet de redémarrer la box directement depuis Domoticz après authentification sur l’API.

## Dépannage

- Vérifier que l’adresse IP de la Bbox est correcte.
- Vérifier que le mot de passe est valide.
- Vérifier la présence de `bbox.zip` dans le dossier du plugin.
- Vérifier que la clé d’icône `BboxPlugin` existe dans `icons.txt`.
- Activer l’option d’ignorance SSL si la box est en réseau local et que le certificat pose problème.
- Augmenter le niveau de debug en cas de problème de connexion ou de parsing JSON.

## Arborescence

```txt
.
├── plugin.py
├── bbox.zip
├── Docs
│   ├── SwitchsDomoticz.png
│   └── MesuresDomoticz.png
└── README.md
```

## Licence

À compléter selon la licence de ton projet.

---

Développé pour Domoticz et Bouygues Telecom Bbox.
