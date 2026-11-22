import time
import canal
import stuffing

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

# fonction qui prend un message et le transforme en chaine de bits
def convertir_en_bits(message):
    bits=""

    for caractere in message:
        # ord(caractere) permet de trouver l'encodage ASCII
        # on convertit le code ASCII de ch caract. en 8 bits
        bits += format(ord(caractere), "08b") 

    return bits 