import time
import canal
import stuffing

import binascii
import zlib

TAILLE_MAX_DONNEES = 100

# fonction qui découpe un message en trame de 100 octets max
def segmenter(message):
    trames = []

    for i in range(0, len(message), TAILLE_MAX_DONNEES):
        trame = message[i: i + TAILLE_MAX_DONNEES]
        trames.append(trame)
    return trames

# fonction qui prend des trames et les numérote (modulo 8 car sur 3 bits)
def numeroter_trames(trames):
    trames_numerotees = []

    for i, trame in enumerate(trames):
        numero = i % 8 # trames numérotées de 0 a 7
        trames_numerotees.append((numero, trame))

    return trames_numerotees

# fonction qui convertit un numéro de séquence de trame en binaire
def numeroter_entete(numero):
    numero_binaire= format(numero, "03b")
    
    return numero_binaire

# fonction qui construit une trame (FLAG + entete + donnees + crc + FLAG) 
# en appliquant le bit stuffing sur toute la trame sauf les flag
FLAG = "01111110"
def construire_trame(numero, donnees):
    entete = numeroter_entete(numero)
    contenu = entete + donnees
    crc = calculer_crc(contenu)

    contenu = contenu + crc
    contenu = stuffing.bit_stuffing(contenu)

    trame = FLAG + contenu + FLAG
    return trame
 
# fonction qui calcule un crc sur les donnees d'une trame
def calculer_crc(donnees):
    polynome = "10001000000100001" # CRC-16
    bits = donnees + "0" * 16 # ajouter 16 zéros
    reste = list(bits) # convertit la chaîne de bits en une liste pour faire la division CRC

    for i in range(len(donnees)):
        if reste[i] == "1": # lorsque le premier bit est 1
            for j in range(len(polynome)):
                # on applique le XOR sur les 2 bits
                reste[i+j] = str(int(reste[i+j]) ^ int(polynome[j])) 

    crc = ""
    for bit in reste[-16:]:
        crc += bit

    return crc 

# fonction qui prend un message et le transforme en chaine de bits
def convertir_en_bits(message):
    bits=""

    for caractere in message:
        # ord(caractere) permet de trouver l'encodage ASCII
        # on convertit le code ASCII de ch caract. en 8 bits
        bits += format(ord(caractere), "08b") 

    return bits   

# fonction qui prend un message de bits et le convertit en caracteres
def convertir_en_ASCII(message):
    message_construit=""

    for i in range(0 , len(message), 8):
        octet = message[i: i+ 8]
        message_construit += chr(int(octet, 2)) # conversion en ASCII

    return message_construit    

#  fonction qui vérifie le crc d'une trame et son entete (doublon possible, etc.)
def verifier_trame(trame, numero_attendu):
    
 
    # vérifier que les flag sont présents
    if len(trame) < 16 or not trame.startswith(FLAG) or not trame.endswith(FLAG):
        return False

    # on applique le destuffing sur toute la trame sauf fanions
    try:
        contenu = stuffing.bit_destuffing(trame[8:-8])
    except Exception:
        return False

    # vérifier que la trame est assez longue (16 bits de crc 
    # et 3 bits entete, donnees possiblement vides)
    if len(contenu) < 19:
        return False
    
    entete_et_donnees = contenu[:-16]
    crc_recu = contenu[-16:]

    crc_calcule = calculer_crc(entete_et_donnees)

    if crc_recu == crc_calcule:
        # vérifier l'entete
        numero = int(contenu[:3], 2) # convertir binaire en entier

        if numero == numero_attendu :
            return True

    return False


def go_back_N(trames):

    # Lien est un objet créé a partir de la classe Canal
    lien = canal.Canal(
        delaiMax=380,
        probErreur=0,
        probPerte=0
    )

    derniere_trame_non_confirmee = 0
    prochaine_trame = 0

    fenetre = 4
    numero_attendu = 0 # modulo 8
    premiere_trame_recue = False

    timeout=0.2
    temps_debut = None

    # Statistiques
    nb_trames_envoyees = 0
    nb_trames_recues = 0
    nb_retransmissions = 0
    trames_deja_envoyees = set()
    nb_ack_recus = 0
    debut_transmission = lien.debut

    DETAILS = True
    def journal(message):
        if DETAILS:
            temps = time.monotonic() - debut_transmission
            print(f"[{temps:.3f} s] {message}")

    donnees_recues = []

    # tant que la derniere trame non confirmee n'a pas dépassé le nombre total de trames
    while derniere_trame_non_confirmee < len(trames):

        # tant qu'on a dépassé 4 trames émises et que prochaine_trame n'a
        # pas dépassé le nombre total de trames
        while (prochaine_trame - derniere_trame_non_confirmee < fenetre and
            prochaine_trame < len(trames)):

            if temps_debut is None:
                # on demarre le temporisateur (chrono)
                temps_debut = time.monotonic()

            if prochaine_trame in trames_deja_envoyees:
                nb_retransmissions+=1
            else:
                trames_deja_envoyees.add(prochaine_trame)

            journal(f"Envoi trame : {prochaine_trame % 8}")

            lien.envoyer(trames[prochaine_trame], "forward")

            prochaine_trame+=1
            nb_trames_envoyees+=1

        # Récupérer les trames arrivées dans le canal
        trame_recue = lien.recevoir("forward")

        while trame_recue is not None:

            nb_trames_recues+=1

            # verifier la trame
            if verifier_trame(trame_recue, numero_attendu):
                premiere_trame_recue = True

                journal(f"Trame reçue et acceptée : {numero_attendu}")

                # enlever les fanions
                contenu = stuffing.bit_destuffing(trame_recue[8:-8])

                # on prend les donnees (entete (3 bits) - donnees - crc (16 bits))
                donnees = contenu[3:-16]

                # garder les donnees
                donnees_recues.append(donnees)

                numero_attendu = (numero_attendu + 1) % 8

            else:
                journal("Trame rejetée ou corrompue")

            if premiere_trame_recue:
                # ack cumulatif de toutes les trames envoyées
                ack = (numero_attendu-1) % 8

                # conversion de l'ack en 3 bits
                ack_binaire = format(ack, "03b")

                # ajout d'un crc-16 pour les cas de corruption d'un ack
                ack_binaire = ack_binaire + calculer_crc(ack_binaire)

                journal(f"Envoi ACK : {ack}")

                # on transmet l'ack
                lien.envoyer(ack_binaire, "reverse")

            # Vérifier si une autre trame est arrivée
            trame_recue = lien.recevoir("forward")

        # Récupérer les ACK arrivés dans le canal
        ack_recu = lien.recevoir("reverse")

        while ack_recu is not None:

            nb_ack_recus+=1

            # vérifier la longueur du crc et le crc
            if len(ack_recu) == 19 and calculer_crc(ack_recu) == "0" *16:

                # conversion des 3 bits du numéro de l'ack en entier
                ack_recu = int(ack_recu[:3], 2)
                journal(f"ACK valide reçu : {ack_recu}")

                # avancer la fenetre
                for i in range(derniere_trame_non_confirmee, prochaine_trame):
                    if i % 8 == ack_recu:
                        derniere_trame_non_confirmee = i + 1

                        # on met a jour le chrono
                        # s'il ne reste plus de trames a confirmer, on met none
                        if derniere_trame_non_confirmee == prochaine_trame:
                            temps_debut = None
                        else:
                            # sinon, il reste des trames a confirmer
                            temps_debut = time.monotonic()
                        break
                else:
                    # Ignorer l'ACK arrivé trop tard
                    pass

            else:
                journal("ACK corrompu ignoré")

            # Vérifier si un autre ACK est arrivé
            ack_recu = lien.recevoir("reverse")

        # Scenario : si la fenetre est pleine et qu'une trame est perdue,
        # on doit débloquer la situation avec le timeout. Donc si temps_debut n'est PAS none,
        # c'est qu'il reste des trames a verifier. On met ce code en dehors de la petite boucle
        # dans le cas ou la fenetre est pleine, mais qu'on a pas fini de transmettre toutes les
        # trames.

        if temps_debut is not None:
            # on verifie que le timeout n'est pas depassé
            if time.monotonic() - temps_debut >= timeout:
                journal(f"Timeout ! Retransmission à partir de : {derniere_trame_non_confirmee % 8}")

                # on retransmet a partir de la derniere trame non confirmee
                prochaine_trame = derniere_trame_non_confirmee

                # Redémarrer le timeout
                temps_debut = time.monotonic()

                # Recommencer l'envoi
                continue

        # Éviter que la boucle utilise inutilement le processeur
        time.sleep(0.001)

    # Rassembler toutes les données reçues
    message_binaire = "".join(donnees_recues)

    message_final = convertir_en_ASCII(message_binaire)

    duree_totale = time.monotonic() - debut_transmission
    print("\n- Statistiques Go-Back-N -")
    print("Trames envoyées :", nb_trames_envoyees)
    print("Trames reçues :", nb_trames_recues)
    print("Retransmissions :", nb_retransmissions)
    print("ACK reçus :", nb_ack_recus)
    print("Durée totale :", round(duree_totale, 2), "secondes")

    return message_final

# ==============================================
# TESTS: Comparaison entre cr16 et crc32
# ==============================================

def bits_to_bytes(bits: str) -> bytes:
    #Transforme une chaîne binaire en octets.

    # any() retourne True si au moins un caractère est invalide.
    if any(bit not in "01" for bit in bits):
        raise ValueError(
            "Le flux doit contenir seulement des 0 et des 1"
        )

    # Un octet contient exactement 8 bits.
    # % donne le reste de la division.
    # Un reste différent de zéro indique un groupe incomplet.
    if len(bits) % 8 != 0:
        raise ValueError(
            "Le nombre de bits doit être un multiple de 8"
        )
    return bytes(
        int(bits[i:i + 8], 2)
        for i in range(0, len(bits), 8)
    )


def crc16(data: bytes) -> int:
    #Calcule le CRC-16
    return binascii.crc_hqx(data, 0xFFFF)


def crc32(data: bytes) -> int:
    #Calcule le CRC-32 standard fourni par zlib.
    return zlib.crc32(data) & 0xFFFFFFFF


def comparer_crc():
    # Message binaire de 16 bits, soit deux octets.
    original_bits = "0111111010101010"
    original = bits_to_bytes(original_bits)

    # Inverse le dernier bit : 0 devient 1.
    modifie_bits = original_bits[:-1] + "1"
    modifie = bits_to_bytes(modifie_bits)

    print("\n=== Comparaison des CRC ===")
    print("Bits originaux :", original_bits)
    print("Bits modifiés  :", modifie_bits)

    # Calcul des CRC-16.
    crc16_original = crc16(original)
    crc16_modifie = crc16(modifie)

    print("\nCRC-16 :")
    print(f"CRC original : {crc16_original:016b}")
    print(f"CRC modifié  : {crc16_modifie:016b}")
    print("Erreur détectée :", crc16_original != crc16_modifie)
    print("Taille du CRC : 16 bits, soit 2 octets")

    # Calcul des CRC-32.
    crc32_original = crc32(original)
    crc32_modifie = crc32(modifie)

    print("\nCRC-32 :")
    print(f"CRC original : {crc32_original:032b}")
    print(f"CRC modifié  : {crc32_modifie:032b}")
    print("Erreur détectée :", crc32_original != crc32_modifie)
    print("Taille du CRC : 32 bits, soit 4 octets")

    assert crc16_original != crc16_modifie
    assert crc32_original != crc32_modifie       


# Programme princial
if __name__ == "__main__":

    # Avec fichier message.txt
    with open("../message.txt", "r", encoding="ascii") as fichier:
        message = fichier.read()

    # Segmenter le message
    trames = segmenter(message)

    # Numéroter les trames
    trames_numerotees = numeroter_trames(trames)

    # TEST GO-BACK-N  
    trames_preparees = []

    for numero, donnees in trames_numerotees:
        bits = convertir_en_bits(donnees)
        trame = construire_trame(numero, bits)
        trames_preparees.append(trame)

    message_recu = go_back_N(trames_preparees)

    print("Go-Back-N terminé !")
    print("Message identique :", message_recu == message)

    # AUTRES TESTS DÉSACTIVÉS

    # Test CRC(original) = CRC(destuffed)

    # original = "011111101111101111110111110"
    # destuffed = stuffing.bit_destuffing(stuffing.bit_stuffing(original))

    # print("CRC original :", calculer_crc(original))
    # print("CRC destuffed :", calculer_crc(destuffed))
    # print("CRC identiques :", calculer_crc(original) == calculer_crc(destuffed))

    # print()

    # Test de corruption

    # original = construire_trame(0, convertir_en_bits("ABC"))

    # position = 12
    # corrompu = original[:position] + (
    #     "1" if original[position] == "0" else "0"
    # ) + original[position + 1:]

    # print("Trame originale :", original)
    # print("Trame corrompue :", corrompu)
    # print("Trame originale valide :", verifier_trame(original, 0))
    # print("Trame corrompue valide :", verifier_trame(corrompu, 0))
    # print("Corruption détectée :", not verifier_trame(corrompu, 0))

    # Comparaison expérimentale pour justifier le choix du CRC.
    comparer_crc()
