
import random
import time
from collections import deque


class Canal:
    """Simule un canal avec pertes, corruptions et délais."""

    def __init__(self, delaiMax=200, seed=42,
                 probErreur=0, probPerte=0):

        # __init__ est exécutée lorsqu'on crée un objet Canal.
        # self désigne cet objet et permet de conserver ses paramètres.

        if delaiMax < 0:
            raise ValueError("Le délai maximal doit être positif ou nul.")

        if not 0 <= probErreur <= 1:
            raise ValueError("probErreur doit être entre 0 et 1.")

        if not 0 <= probPerte <= 1:
            raise ValueError("probPerte doit être entre 0 et 1.")

        self.delai_max = delaiMax / 1000   # conver en secondes 

        self.prob_erreur = probErreur
        self.prob_perte = probPerte
        self.generateur = random.Random(seed)

        # Enregistrer le début de la transmission
        self.debut = time.monotonic()

        # Une file indépendante pour chaque direction.
        # forward : émetteur vers récepteur, pour les données.
        # reverse : récepteur vers émetteur, pour les ACK.
        # Chaque élément stocké aura la forme : (date_de_livraison, trame)
        self.files = {
            "forward": deque(),
            "reverse": deque()
        }

    def envoyer(self, trame, sens="forward"):
        """Perd la trame ou programme sa livraison future."""

        if sens not in self.files:
            raise ValueError("Sens invalide.")

        # any() renvoie True si au moins un bit est invalide.
        if not trame or any(bit not in "01" for bit in trame):
            raise ValueError("La trame doit être binaire et non vide.")

        maintenant = time.monotonic()

        temps = maintenant - self.debut
        type_message = "ACK" if sens == "reverse" else "trame"

        # ÉTAPE 1 : décider si la trame est perdue.
        if self.generateur.random() < self.prob_perte:
            print(f"[{temps:.3f} s] CANAL : perte de {type_message} ({sens})")

            # On quitte sans ajouter la trame dans la file.
            # Elle ne sera donc jamais livrée.
            return

        # ÉTAPE 2 : décider si la trame non perdue est corrompue.
        if self.generateur.random() < self.prob_erreur:
            position = self.generateur.randrange(len(trame))

            # Inverse le bit choisi 
            bit_inverse = "1" if trame[position] == "0" else "0"

            trame = (
                trame[:position]
                + bit_inverse
                + trame[position + 1:]
            )

            print(f"[{temps:.3f} s] CANAL : corruption de {type_message} ({sens})")

        # ÉTAPE 3 : tirer un délai et programmer la livraison.
        # uniform() choisit un nombre entre les deux bornes.
        delai = self.generateur.uniform(0, self.delai_max)
        date_livraison = maintenant + delai

        # Sélectionne la file du sens demandé.
        file = self.files[sens]

        # Si une trame attend déjà la nouvelle ne doit pas être programmée avant la dernière trame de la file.
        if file:
            date_livraison = max(date_livraison, file[-1][0])

        file.append((date_livraison, trame))

    def recevoir(self, sens="forward"):
        """Retourne une trame prête, ou None si aucune n'est prête."""

        if sens not in self.files:
            raise ValueError("Sens invalide.")

        file = self.files[sens]
        maintenant = time.monotonic()

        # Deux conditions :
        # 1: la file n'est pas vide ;
        # 2: la date de la première trame est atteinte.
        if file and file[0][0] <= maintenant:
            _, trame = file.popleft()
            return trame

        return None


# Tests du canal
if __name__ == "__main__":

    #Livraison intacte et dans l'ordre.
    lien = Canal(delaiMax=0, probErreur=0, probPerte=0)

    lien.envoyer("0001", "forward")
    lien.envoyer("0010", "forward")

    print("Trame 1 :", lien.recevoir("forward"))
    print("Trame 2 :", lien.recevoir("forward"))
