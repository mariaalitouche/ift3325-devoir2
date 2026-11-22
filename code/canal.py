import random
import time
from collections import deque


class Canal:
    """Simule un canal avec pertes, corruptions et délais."""

    def __init__(
        self,
        delaiMax=200,
        seed=42,
        probErreur=0.05,
        probPerte=0.10,
    ):
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

        # Une file indépendante pour chaque direction.
        # forward : émetteur vers récepteur, pour les données.
        # reverse : récepteur vers émetteur, pour les ACK.
        # Chaque élément stocké aura la forme : (date_de_livraison, trame)
        self.files = {
            "forward": deque(),
            "reverse": deque(),
        }

    def envoyer(self, trame: str, sens="forward"):
        """Perd la trame ou programme sa livraison future."""

        if sens not in self.files:
            raise ValueError("Le sens doit être 'forward' ou 'reverse'.")

        # any() renvoie True si au moins un bit est invalide.
        if not trame or any(bit not in "01" for bit in trame):
            raise ValueError("La trame doit être une chaîne binaire non vide.")

        maintenant = time.monotonic()

        # ÉTAPE 1 : décider si la trame est perdue.
        if self.generateur.random() < self.prob_perte:
            print(
                f"[{maintenant:.3f}] CANAL : trame perdue ({sens})"
            )

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
            print(
                f"[{maintenant:.3f}] CANAL : bit inversé "
                f"à la position {position} ({sens})"
            )

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
        print(
            f"[{maintenant:.3f}] CANAL : trame programmée "
            f"({sens}, attente prévue "
            f"{(date_livraison - maintenant) * 1000:.1f} ms)"
        )

    

    def recevoir(self, sens="forward"):
        """Retourne une trame prête, ou None si aucune n'est prête."""

        if sens not in self.files:
            raise ValueError("Le sens doit être 'forward' ou 'reverse'.")

        file = self.files[sens]
        maintenant = time.monotonic()

        # Deux conditions :
        # 1: la file n'est pas vide ;
        # 2: la date de la première trame est atteinte.
        if file and file[0][0] <= maintenant:
            _, trame = file.popleft()
            print(
                f"[{maintenant:.3f}] CANAL : trame livrée ({sens})"
            )

            return trame
        return None


def tester_transmission(prob_erreur):
    """Teste une trame complète : CRC, stuffing et passage dans le canal."""

    # Pas de perte dans ce test 
    canal = Canal(
        delaiMax=50,
        probErreur=prob_erreur,
        probPerte=0,
        seed=42,
    )

    # Deux octets d'en-tête d'exemple, suivis du texte allo.
    # Le préfixe b indique un objet bytes.
    original = b"\x01\x00allo"

    # Calcule le CRC sur l'en-tête et les données, avant stuffing.
    crc = crc16(original)

    # Convertit le CRC entier en deux octets.
    contenu = original + crc.to_bytes(2, byteorder="big")

    # Convertit en bits, applique le stuffing et ajoute les flags.
    trame = encapsulate(contenu)

    print("Trame envoyée :", trame)
    canal.envoyer(trame)
    limite = time.monotonic() + 1
    recue = None

    # Vérifie régulièrement si une trame est prête.
    while time.monotonic() < limite:
        recue = canal.recevoir()

        # Une chaîne reçue signifie qu'une livraison a eu lieu.
        if recue is not None:
            break

        # Petite pause pour éviter une boucle qui occupe constamment le processeur.
        time.sleep(0.001)

    # Si rien n'est arrivé avant la limite, le test échoue.
    if recue is None:
        raise TimeoutError("Aucune trame reçue pendant le test.")

    print("Trame reçue   :", recue)

    # Une corruption peut rendre les flags ou le stuffing invalides.
    # try/except permet de gérer ce rejet sans arrêter le programme.
    try:
        contenu_recu = decapsulate(recue)
    except ValueError as erreur:
        print("Trame rejetée à la décapsulation :", erreur)
        return False

    # Il faut au minimum deux octets pour contenir le CRC-16.
    if len(contenu_recu) < 2:
        print("Trame rejetée : CRC absent ou incomplet.")
        return False

    # Tout sauf les deux derniers octets : en-tête et données.
    donnees_recues = contenu_recu[:-2]

    # Les deux derniers octets : CRC transmis.
    # int.from_bytes() les transforme en un entier.
    crc_recu = int.from_bytes(contenu_recu[-2:], byteorder="big")

    # Recalcule le CRC sur l'en-tête et les données reçus.
    crc_calcule = crc16(donnees_recues)
    print(f"CRC reçu    : {crc_recu:04X}")
    print(f"CRC calculé : {crc_calcule:04X}")

    # Des CRC différents indiquent une corruption détectée.
    if crc_recu != crc_calcule:
        print("Trame rejetée : erreur détectée par le CRC.")
        return False

    # Vérification supplémentaire propre au test :
    # ici, on connaît le message original.
    # Dans le protocole, le récepteur n'en aurait pas besoin pour effectuer sa vérification du CRC.
    assert donnees_recues == original

    print("Trame acceptée : contenu identique à l'original.")
    return True







if __name__ == "__main__":
    for sens in ("forward", "reverse"):

        #Livraison intacte et dans l'ordre.
        print(f"\n=== Canal parfait : {sens} ===")
        canal = Canal(delaiMax=0, probErreur=0, probPerte=0)

        canal.envoyer("0001", sens)
        canal.envoyer("0010", sens)

        assert canal.recevoir(sens) == "0001"
        assert canal.recevoir(sens) == "0010"
        assert canal.recevoir(sens) is None

        # Une trame perdue ne doit pas être livrée.
        print(f"\n=== Perte certaine : {sens} ===")
        canal = Canal(delaiMax=0, probErreur=0, probPerte=1)

        canal.envoyer("0001", sens)
        assert canal.recevoir(sens) is None

        # Une corruption doit inverser exactement un bit.
        print(f"\n=== Corruption certaine : {sens} ===")
        canal = Canal(delaiMax=0, probErreur=1, probPerte=0)

        original = "0001"
        canal.envoyer(original, sens)
        recu = canal.recevoir(sens)

        assert recu is not None
        assert len(recu) == len(original)

        differences = sum(
            a != b for a, b in zip(original, recu)
        )

        print("Original :", original)
        print("Reçu     :", recu)
        print("Bits modifiés :", differences)
        assert differences == 1

        #Livraison avec délai, en conservant l'ordre.
        print(f"\n=== Délai et ordre : {sens} ===")
        canal = Canal(
            delaiMax=50,
            probErreur=0,
            probPerte=0,
            seed=42,
        )

        envoyees = ["0001", "0010", "0011"]
        recues = []
        debut = time.monotonic()

        for trame in envoyees:
            canal.envoyer(trame, sens)

        while len(recues) < len(envoyees):
            trame = canal.recevoir(sens)

            if trame is not None:
                recues.append(trame)

            if time.monotonic() - debut > 2:
                raise TimeoutError("Toutes les trames ne sont pas arrivées.")

            time.sleep(0.001)

        print("Ordre conservé :", recues == envoyees)
        assert recues == envoyees

    print("Tous les tests du canal ont réussi.")