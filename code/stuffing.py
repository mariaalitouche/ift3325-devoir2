def bit_stuffing(bits: str) -> str:
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


def bit_destuffing(bits: str) -> str:
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


if __name__ == "__main__":

    original = "011111 1011111 011111 1011111 0".replace(" ", "")
    stuffed = bit_stuffing(original)
    restored = bit_destuffing(stuffed)

    print("========= Test du stuffing ============")
    print("Avant stuffing    :", original)
    print("Après stuffing    :", stuffed)
    print("Après dé-stuffing :", restored)
    print("Restauration exacte :", restored == original)

    assert stuffed == "0111110101111100111110101111100"
    assert restored == original

    #Corruption du zéro inséré après cinq 1.
    stuffed = bit_stuffing("11111")
    corrupted = stuffed[:-1] + "1"

    print("\nFlux stuffed  :", stuffed)
    print("Flux corrompu :", corrupted)

    try:
        bit_destuffing(corrupted)
    except ValueError as erreur:
        print("Corruption détectée :", erreur)
    else:
        raise AssertionError("La corruption aurait dû être détectée.")

    print("Tous les tests de stuffing ont réussi.")

   
