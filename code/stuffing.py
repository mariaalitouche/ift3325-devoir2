import binascii
import zlib


# Flag HDLC : marque le début et la fin d'une trame.
FLAG = "01111110"


def stuff_bits(bits: str) -> str:
    #Insère un zéro après chaque groupe de cinq 1 consécutifs.
    resultat = []
    # Nombre de 1 consécutifs rencontrés.
    compteur = 0

    for bit in bits:
        # Refuse les caractères autres que "0" et "1".
        if bit not in "01":
            raise ValueError(
                "Le flux doit contenir seulement des 1 et des 0."
            )
        resultat.append(bit)
        if bit == "1":
            compteur += 1

            # Après cinq 1, on ajoute obligatoirement un zéro, même si on est à la fin du flux.
            if compteur == 5:
                resultat.append("0")
                # Le zéro ajouté interrompt la suite de 1.
                compteur = 0
        else:
            compteur = 0
    return "".join(resultat)


def destuff_bits(bits: str) -> str:
    #Retire les zéros insérés et refuse un stuffing invalide.

    resultat = []
    compteur = 0
    i = 0

    # On utilise while pour pouvoir avancer d'un bit supplémentaire lorsqu'il faut sauter un zéro inséré.
    while i < len(bits):
        bit = bits[i]
        if bit not in "01":
            raise ValueError(
                "Le flux doit contenir seulement des 1 et des 0."
            )
        resultat.append(bit)

        if bit == "1":
            compteur += 1
        else:
            compteur = 0
        i += 1

        if compteur == 5:
            # Après cinq 1, le stuffing impose un zéro.
            if i >= len(bits) or bits[i] != "0":
                raise ValueError(
                    "Stuffing invalide : zéro attendu après cinq 1."
                )
            # Saute le zéro sans l'ajouter au résultat.
            i += 1
            compteur = 0

    return "".join(resultat)


def bytes_to_bits(data: bytes) -> str:
    return "".join(format(octet, "08b") for octet in data)


def bits_to_bytes(bits: str) -> bytes:
    #Transforme une chaîne binaire en octets."""

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


def encapsulate(data: bytes) -> str:
    #Applique le stuffing et ajoute les deux flags.
    bits = bytes_to_bits(data)

    # Le stuffing porte sur tout : en-tête, données et CRC.
    stuffed = stuff_bits(bits)
    return FLAG + stuffed + FLAG


def decapsulate(frame: str) -> bytes:
    #Retire les flags et le stuffing
    if len(frame) < 2 * len(FLAG):
        raise ValueError("Trame trop courte.")
    # Vérifie que la chaîne commence et finit par le bon flag.
    if not frame.startswith(FLAG) or not frame.endswith(FLAG):
        raise ValueError("Flag de début ou de fin invalide.")
    contenu = frame[len(FLAG):-len(FLAG)]
    # Retire les zéros ajoutés au stuffing.
    bits = destuff_bits(contenu)
    # Convertit le contenu restauré en octets.
    return bits_to_bytes(bits)


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




if __name__ == "__main__":
    original = "011111 1011111 011111 1011111 0".replace(" ", "")
    stuffed = stuff_bits(original)
    restored = destuff_bits(stuffed)

    print("========= Test du stuffing ============")
    print("Avant stuffing    :", original)
    print("Après stuffing    :", stuffed)
    print("Après dé-stuffing :", restored)
    print("Restauration exacte :", restored == original)

    assert stuffed == "0111110101111100111110101111100"
    assert restored == original

    #Corruption du zéro inséré après cinq 1.
    stuffed = stuff_bits("11111")
    corrupted = stuffed[:-1] + "1"

    print("\nFlux stuffed  :", stuffed)
    print("Flux corrompu :", corrupted)

    try:
        destuff_bits(corrupted)
    except ValueError as erreur:
        print("Corruption détectée :", erreur)
    else:
        raise AssertionError("La corruption aurait dû être détectée.")

    #Comparaison expérimentale pour justifier le choix du CRC.
    comparer_crc()

    #Encapsulation complète avec un CRC ajouté avant stuffing.
    original = b"\x01\x00Bonjour\xff"
    crc_original = crc16(original)
    contenu = original + crc_original.to_bytes(2, byteorder="big")

    trame = encapsulate(contenu)
    contenu_recu = decapsulate(trame)

    donnees_recues = contenu_recu[:-2]
    crc_transmis = int.from_bytes(contenu_recu[-2:], byteorder="big")
    crc_recalcule = crc16(donnees_recues)

    print("\n========== CRC et encapsulation ============")
    print("Avant stuffing    :", bytes_to_bits(contenu))
    print("Après stuffing    :", trame[len(FLAG):-len(FLAG)])
    print("Après dé-stuffing :", bytes_to_bits(contenu_recu))
    print(f"CRC original      : {crc_original:04X}")
    print(f"CRC recalculé     : {crc_recalcule:04X}")
    print("CRC identiques    :", crc_original == crc_recalcule)

    assert contenu_recu == contenu
    assert crc_transmis == crc_recalcule

    copie = bytearray(donnees_recues)
    copie[0] ^= 1
    corruption_detectee = crc16(bytes(copie)) != crc_transmis

    print("Corruption détectée par le CRC :", corruption_detectee)
    assert corruption_detectee

    print("Tous les tests de stuffing ont réussi.")