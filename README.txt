IFT3325 - DEVOIR 2

Conception et implantation d'un protocole
de liaison fiable simplifié

1. ENVIRONNEMENT
--------------------------------------------------
Langage : Python 3.14.3
Système : Windows
Bibliothèques : modules standards de Python

2. INSTRUCTIONS D'EXÉCUTION
--------------------------------------------------
1. Installer Python 3.
2. Ouvrir un terminal dans le dossier code/.
3. Exécuter : py protocole.py

3. PARAMÈTRES DU PROTOCOLE
--------------------------------------------------
Taille maximale des données : 100 octets
Numérotation : 3 bits (modulo 8)
Fenêtre Go-Back-N : 4
Timeout : 500 ms
Détection d'erreurs : CRC-16
Fanion : 01111110
Encapsulation : bit-stuffing

4. PARAMÈTRES DU CANAL
--------------------------------------------------
Probabilité d'erreur : 0,05
Probabilité de perte : 0,10
Délai maximal : 200 ms

Ces paramètres peuvent être changés pour les
différents scénarios expérimentaux.
