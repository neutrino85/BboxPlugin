"""
<plugin key="BboxPlugin" name="Bouygues Bbox Monitor" author="Neutrino" version="1.2.0"
        externallink="https://github.com/neutrino85/BboxPlugin">
    <description>
        <h2>Bouygues Bbox Monitor</h2>
        Surveille et contrôle votre box Bouygues Telecom (Bbox).<br/>
        Crée automatiquement les appareils suivants :
        <ul>
            <li>Internet (Interrupteur - état WAN)</li>
            <li>VoIP (Interrupteur - état ligne VoIP)</li>
            <li>Uptime Bbox (Texte - jours:heures:min:sec)</li>
            <li>Firmware Bbox (Texte - version firmware)</li>
            <li>IP WAN / IPv6 WAN (Texte)</li>
            <li>Données Reçues / Envoyées (Capteur custom - Go)</li>
            <li>Download / Upload (Capteur personnalisé - Mbps)</li>
            <li>Reboot Bbox (Interrupteur - déclenche un redémarrage)</li>
        </ul>
        Placez le fichier <b>bbox.zip</b> dans le même dossier que plugin.py.<br/>
        Le fichier icons.txt dans bbox.zip doit avoir une clé commençant par <b>BboxPlugin</b>.
    </description>
    <params>
        <param field="Address" label="Adresse IP Bbox" width="200px" required="true" default="192.168.1.1"/>
        <param field="Password" label="Mot de passe Bbox" width="200px" required="true" default="" password="true"/>
        <param field="Mode1" label="Intervalle de scrutation (secondes)" width="100px" required="true" default="60"/>
        <param field="Mode2" label="Ignorer les erreurs SSL" width="100px">
            <options>
                <option label="Oui (recommandé pour IP locale)" value="true" default="true"/>
                <option label="Non" value="false"/>
            </options>
        </param>
        <param field="Mode6" label="Niveau de debug" width="150px">
            <options>
                <option label="Aucun" value="0" default="true"/>
                <option label="Python seulement" value="2"/>
                <option label="Debug basique" value="62"/>
                <option label="Tout" value="-1"/>
            </options>
        </param>
    </params>
</plugin>
"""

import Domoticz
import requests
import urllib3

# ─── Numéros d'unités ────────────────────────────────────────────────────────
UNIT_INTERNET   = 1   # Interrupteur – état lien WAN
UNIT_VOIP       = 2   # Interrupteur – état VoIP
UNIT_UPTIME     = 3   # Texte        – uptime formaté
UNIT_FIRMWARE   = 4   # Texte        – version firmware
UNIT_IPV4       = 5   # Texte        – adresse IPv4 WAN
UNIT_IPV6       = 6   # Texte        – adresse IPv6 WAN
UNIT_DATA_RX    = 7   # Capteur custom – données reçues (Go)
UNIT_DATA_TX    = 8   # Capteur custom – données envoyées (Go)
UNIT_DL_SPEED   = 9   # Capteur custom – débit download (Mbps)
UNIT_UL_SPEED   = 10  # Capteur custom – débit upload (Mbps)
UNIT_REBOOT     = 11  # Interrupteur – déclenche reboot

# Clé de base des icônes dans icons.txt du zip
ICON_KEY = "bbox"
ICON_ZIP = "bbox.zip"

BYTES_TO_GO = 1_000_000_000  # 1 Go = 10^9 octets (unité opérateur)


class BasePlugin:
    def __init__(self):
        self._heartbeat_tick = 0
        self._poll_ticks = 6
        self._base_url = ""
        self._password = ""
        self._verify_ssl = False
        return

    # ─── Cycle de vie ─────────────────────────────────────────────────────────

    def onStart(self):
        if Parameters["Mode6"] != "0":
            Domoticz.Debugging(int(Parameters["Mode6"]))

        self._base_url  = "https://{}/api/".format(Parameters["Address"])
        self._password  = Parameters["Password"]
        self._verify_ssl = (Parameters["Mode2"].lower() == "false")

        if not self._verify_ssl:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        # Heartbeat toutes les 10 s ; compteur interne pour l'intervalle voulu
        Domoticz.Heartbeat(10)
        interval = max(10, int(Parameters["Mode1"]))
        self._poll_ticks = max(1, interval // 10)

        # ── Chargement icône personnalisée ──────────────────────────────────
        # bbox.zip doit être dans le dossier du plugin.
        # icons.txt dans le zip doit avoir une clé commençant par "BboxPlugin".
        # Exemple de icons.txt :
        #   BboxPlugin
        #   Bbox Router
        #   Icône pour la Bouygues Bbox
        if ICON_KEY not in Images:
            try:
                Domoticz.Image(Filename=ICON_ZIP).Create()
                Domoticz.Log("Icône '{}' chargée depuis {}".format(ICON_KEY, ICON_ZIP))
            except Exception as exc:
                Domoticz.Error("Impossible de charger {} : {}".format(ICON_ZIP, exc))

        self._create_devices()
        Domoticz.Log("Bbox Plugin démarré – scrutation toutes les {} s".format(interval))
        self._poll_all()

    def onStop(self):
        Domoticz.Log("Bbox Plugin arrêté")

    def onHeartbeat(self):
        self._heartbeat_tick += 1
        if self._heartbeat_tick >= self._poll_ticks:
            self._heartbeat_tick = 0
            self._poll_all()

    def onCommand(self, Unit, Command, Level, Hue):
        Domoticz.Debug("onCommand – unité : {}, commande : {}".format(Unit, Command))
        if Unit == UNIT_REBOOT and Command.lower() == "on":
            Domoticz.Log("Reboot Bbox demandé…")
            self._do_reboot()

    # ─── Résolution de l'ID icône ─────────────────────────────────────────────

    def _icon_id(self):
        """Retourne l'ID de l'icône Bbox si disponible, sinon None."""
        if ICON_KEY in Images:
            return Images[ICON_KEY].ID
        return None

    # ─── Création des appareils ───────────────────────────────────────────────

    def _create_devices(self):
        icon = self._icon_id()

        def make(unit, name, typename=None, type_=None, subtype=None,
                 switchtype=None, options=None, use_icon=True):
            if unit in Devices:
                return
            kwargs = dict(Name=name, Unit=unit, Used=1)
            if typename:
                kwargs["TypeName"] = typename
            if type_ is not None:
                kwargs["Type"] = type_
            if subtype is not None:
                kwargs["Subtype"] = subtype
            if switchtype is not None:
                kwargs["Switchtype"] = switchtype
            if options:
                kwargs["Options"] = options
            if use_icon and icon is not None:
                kwargs["Image"] = icon
            Domoticz.Device(**kwargs).Create()
            Domoticz.Log("Appareil créé : {}".format(name))

        make(UNIT_INTERNET,  "Internet",          typename="Switch")
        make(UNIT_VOIP,      "VoIP",              typename="Switch")
        make(UNIT_UPTIME,    "Uptime Bbox",        typename="Text")
        make(UNIT_FIRMWARE,  "Firmware Bbox",      typename="Text")
        make(UNIT_IPV4,      "IP WAN",             typename="Text")
        make(UNIT_IPV6,      "IPv6 WAN",           typename="Text")
        # Données en Go (Custom sensor)
        make(UNIT_DATA_RX,   "Données Reçues",
             typename="Custom", options={"Custom": "1;Go"})
        make(UNIT_DATA_TX,   "Données Envoyées",
             typename="Custom", options={"Custom": "1;Go"})
        # Débits en kbps
        make(UNIT_DL_SPEED,  "Download",
             typename="Custom", options={"Custom": "1;Mbps"})
        make(UNIT_UL_SPEED,  "Upload",
             typename="Custom", options={"Custom": "1;Mbps"})
        make(UNIT_REBOOT,    "Reboot Bbox",        typename="Switch", switchtype=9)

        # Mise à jour de l'icône sur les appareils déjà existants
        if icon is not None:
            self._apply_icon_to_existing(icon)

    def _apply_icon_to_existing(self, icon):
        """Met à jour l'icône sur les appareils déjà présents en base."""
        for unit in (UNIT_INTERNET, UNIT_VOIP, UNIT_UPTIME, UNIT_FIRMWARE,
                     UNIT_IPV4, UNIT_IPV6, UNIT_DATA_RX, UNIT_DATA_TX,
                     UNIT_DL_SPEED, UNIT_UL_SPEED, UNIT_REBOOT):
            if unit in Devices and Devices[unit].Image != icon:
                Devices[unit].Update(
                    nValue=Devices[unit].nValue,
                    sValue=Devices[unit].sValue,
                    Image=icon
                )

    # ─── Scrutation API ───────────────────────────────────────────────────────

    def _poll_all(self):
        Domoticz.Debug("Scrutation Bbox en cours…")
        self._fetch_stats()
        self._fetch_device()
        self._fetch_ip()
        self._fetch_summary()

    def _get(self, endpoint):
        """Effectue un GET sur l'API Bbox et retourne le JSON décodé ou None."""
        url = self._base_url + endpoint
        try:
            r = requests.get(url, verify=self._verify_ssl, timeout=10)
            if r.status_code == 200:
                return r.json()
            Domoticz.Error("HTTP {} sur {}".format(r.status_code, url))
        except Exception as exc:
            Domoticz.Error("Erreur GET {} : {}".format(url, exc))
        return None

    def _fetch_stats(self):
        """v1/wan/ip/stats → données (Go) + débits (kbps)."""
        data = self._get("v1/wan/ip/stats")
        if not data:
            return
        try:
            stats    = data[0]["wan"]["ip"]["stats"]
            rx_bytes = int(stats["rx"]["bytes"])
            tx_bytes = int(stats["tx"]["bytes"])
            rx_bw    = int(stats["rx"]["bandwidth"])
            tx_bw    = int(stats["tx"]["bandwidth"])

            rx_go = rx_bytes / BYTES_TO_GO
            tx_go = tx_bytes / BYTES_TO_GO

            Domoticz.Debug("DL : {:.3f} Go  {:.1f} kbps".format(rx_go, rx_bw / 1024))
            Domoticz.Debug("UL : {:.3f} Go  {:.1f} kbps".format(tx_go, tx_bw / 1024))

            Devices[UNIT_DATA_RX].Update(nValue=0, sValue="{:.3f}".format(rx_go))
            Devices[UNIT_DATA_TX].Update(nValue=0, sValue="{:.3f}".format(tx_go))
            Devices[UNIT_DL_SPEED].Update(nValue=0, sValue="{:.2f}".format(rx_bw / 1024))
            Devices[UNIT_UL_SPEED].Update(nValue=0, sValue="{:.2f}".format(tx_bw / 1024))
        except (KeyError, IndexError, TypeError) as exc:
            Domoticz.Error("_fetch_stats – données inattendues : {}".format(exc))

    def _fetch_device(self):
        """v1/device → firmware + uptime."""
        data = self._get("v1/device")
        if not data:
            return
        try:
            device  = data[0]["device"]
            fw_ver  = device["running"]["version"]
            uptime  = int(device["uptime"])

            Domoticz.Debug("Firmware : {}  Uptime : {} s".format(fw_ver, uptime))

            if Devices[UNIT_FIRMWARE].sValue != fw_ver:
                Devices[UNIT_FIRMWARE].Update(nValue=0, sValue=fw_ver)

            days    =  uptime  // 86400
            remain  =  uptime  %  86400
            hours   =  remain  // 3600
            remain  =  remain  %  3600
            minutes =  remain  // 60
            seconds =  remain  %  60
            uptime_str = "{}:{:02d}:{:02d}:{:02d}".format(days, hours, minutes, seconds)
            Devices[UNIT_UPTIME].Update(nValue=0, sValue=uptime_str)
        except (KeyError, IndexError, TypeError) as exc:
            Domoticz.Error("_fetch_device – données inattendues : {}".format(exc))

    def _fetch_ip(self):
        """v1/wan/ip → adresses IPv4/IPv6 + état du lien."""
        data = self._get("v1/wan/ip")
        if not data:
            return
        try:
            wan        = data[0]["wan"]
            ipv4_addr  = wan["ip"]["address"]
            ipv6_addr  = wan["ip"]["ip6address"][0]["ipaddress"]
            link_state = wan["link"]["state"]

            Domoticz.Debug("IPv4 : {}  IPv6 : {}  Lien : {}".format(
                ipv4_addr, ipv6_addr, link_state))

            Devices[UNIT_IPV4].Update(nValue=0, sValue=ipv4_addr)
            Devices[UNIT_IPV6].Update(nValue=0, sValue=ipv6_addr)

            if link_state == "Up":
                if Devices[UNIT_INTERNET].nValue != 1:
                    Devices[UNIT_INTERNET].Update(nValue=1, sValue="On")
            else:
                if Devices[UNIT_INTERNET].nValue != 0:
                    Devices[UNIT_INTERNET].Update(nValue=0, sValue="Off")
        except (KeyError, IndexError, TypeError) as exc:
            Domoticz.Error("_fetch_ip – données inattendues : {}".format(exc))

    def _fetch_summary(self):
        """v1/summary → état VoIP."""
        data = self._get("v1/summary")
        if not data:
            return
        try:
            voip_status = data[0]["voip"][0]["status"]
            Domoticz.Debug("VoIP : {}".format(voip_status))

            if voip_status == "Up":
                if Devices[UNIT_VOIP].nValue != 1:
                    Devices[UNIT_VOIP].Update(nValue=1, sValue="On")
            else:
                if Devices[UNIT_VOIP].nValue != 0:
                    Devices[UNIT_VOIP].Update(nValue=0, sValue="Off")
        except (KeyError, IndexError, TypeError) as exc:
            Domoticz.Error("_fetch_summary – données inattendues : {}".format(exc))

    # ─── Reboot ───────────────────────────────────────────────────────────────

    def _do_reboot(self):
        """Authentification puis reboot de la Bbox via l'API REST."""
        session = requests.Session()
        try:
            r = session.post(
                self._base_url + "v1/login",
                data={"password": self._password},
                verify=self._verify_ssl,
                timeout=10
            )
            Domoticz.Log("Login Bbox : HTTP {}".format(r.status_code))
            if r.status_code not in (200, 204):
                Domoticz.Error("Échec authentification (HTTP {})".format(r.status_code))
                return
            r2 = session.post(
                self._base_url + "v1/device/reboot",
                verify=self._verify_ssl,
                timeout=10
            )
            Domoticz.Log("Reboot Bbox : HTTP {}".format(r2.status_code))
        except Exception as exc:
            Domoticz.Error("_do_reboot – erreur : {}".format(exc))


# ─── Callbacks Domoticz ───────────────────────────────────────────────────────

_plugin = BasePlugin()

def onStart():
    global _plugin
    _plugin.onStart()

def onStop():
    global _plugin
    _plugin.onStop()

def onHeartbeat():
    global _plugin
    _plugin.onHeartbeat()

def onCommand(Unit, Command, Level, Hue):
    global _plugin
    _plugin.onCommand(Unit, Command, Level, Hue)
