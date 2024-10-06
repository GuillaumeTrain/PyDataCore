import numpy as np
import pandas as pd
from enum import Enum
from uuid import uuid4
import os
from data import Data,data_generator

class Data_Type(Enum):
    PATHS = 0
    TEMPORAL_SIGNAL = 1
    FREQ_SIGNAL = 2
    FREQ_LIMITS = 3
    TEMP_LIMITS = 4
    FFT_STREAM = 5
    CONSTANT = 6


class DataPool:
    def __init__(self):
        # Le dataframe stockera les informations de chaque data :
        # id unique, type de data, source, statut, etc.
        self.data_registry = pd.DataFrame(columns=[
            'data_id', 'data_type', 'data_name', 'source_id', 'protected', 'locked', 'subscribers', 'acquitements',
            'storage_type', 'data_path_or_ram'
        ])

    def generate_unique_id(self):
        """ Génère un identifiant unique pour une nouvelle donnée """
        return str(uuid4())

    def add_data(self, data_type, data_name, source_id, protected=False, storage_type='ram'):
        """
        Ajoute une nouvelle donnée au DataPool.

        :param data_type: Le type de la donnée (utilise Data_Type)
        :param data_name: Nom de la donnée
        :param source_id: ID de la source (un seul pour chaque donnée)
        :param protected: Si la donnée est protégée contre l'effacement
        :param storage_type: 'ram' ou 'file' pour spécifier le type de stockage
        :return: L'ID unique de la donnée
        """
        data_id = self.generate_unique_id()
        new_data = {
            'data_id': data_id,
            'data_type': data_type,
            'data_name': data_name,
            'source_id': source_id,
            'protected': protected,
            'locked': True,  # Verrouillée jusqu'à la fin de l'écriture
            'subscribers': [],
            'acquitements': 0,  # Aucune acquitement tant que pas de lecture/écriture
            'storage_type': storage_type,
            'data_path_or_ram': None  # Sera défini lors du stockage
        }
        # Utilisation de pd.concat à la place de append pour éviter l'erreur
        self.data_registry = pd.concat([self.data_registry, pd.DataFrame([new_data])], ignore_index=True)
        return data_id

    def lock_data(self, data_id):
        """ Verrouille la donnée pour prévenir l'accès pendant l'écriture """
        self.data_registry.loc[self.data_registry['data_id'] == data_id, 'locked'] = True

    def unlock_data(self, data_id):
        """ Déverrouille la donnée après écriture """
        self.data_registry.loc[self.data_registry['data_id'] == data_id, 'locked'] = False

    def add_subscriber(self, data_id, subscriber_id):
        """ Ajoute un subscriber à la donnée """
        subscribers = self.data_registry.loc[self.data_registry['data_id'] == data_id, 'subscribers'].values[0]
        subscribers.append(subscriber_id)
        self.data_registry.loc[self.data_registry['data_id'] == data_id, 'subscribers'] = subscribers

    def acknowledge_data(self, data_id, subscriber_id):
        """
        Enregistre un acquitement de traitement pour un subscriber.
        Si tous les acquitements sont reçus et la donnée n'est pas protégée, elle est supprimée.
        """
        data_row = self.data_registry.loc[self.data_registry['data_id'] == data_id]

        # Vérifier si le subscriber existe et enregistrer l'acquitement
        if subscriber_id in data_row['subscribers'].values[0]:
            acquitements = data_row['acquitements'].values[0] + 1
            self.data_registry.loc[self.data_registry['data_id'] == data_id, 'acquitements'] = acquitements

            # Vérifier si tous les subscribers ont acquitté
            if acquitements == len(data_row['subscribers'].values[0]):
                self.delete_data(data_id)

    def delete_data(self, data_id):
        """
        Supprime la donnée si elle n'est pas protégée et que tous les acquitements sont reçus.
        """
        data_row = self.data_registry.loc[self.data_registry['data_id'] == data_id]
        if data_row['protected'].values[0] is False:
            # Supprimer la donnée du registre
            self.data_registry = self.data_registry[self.data_registry['data_id'] != data_id]
            # Si stockée sur disque, supprimer le fichier
            if data_row['storage_type'].values[0] == 'file' and data_row['data_path_or_ram'].values[0]:
                if os.path.exists(data_row['data_path_or_ram'].values[0]):
                    os.remove(data_row['data_path_or_ram'].values[0])

    def get_data_info(self, data_id):
        """ Retourne les informations de la donnée via son ID """
        return self.data_registry.loc[self.data_registry['data_id'] == data_id]

    def store_data(self, data_id, data_source, folder=None):
        """
        Stocke la donnée soit en RAM, soit sur disque en utilisant la classe Data.

        :param data_id: L'ID unique de la donnée dans le DataPool.
        :param data_source: Soit un générateur de chunks de données, soit une variable contenant les données en RAM.
        :param folder: Dossier où stocker le fichier si nécessaire.
        """
        data_row = self.get_data_info(data_id)
        storage_type = data_row['storage_type'].values[0]

        # Créer un objet Data correspondant à cette donnée
        data_obj = Data(
            data_id=data_id,
            data_type=data_row['data_type'].values[0],
            data_name=data_row['data_name'].values[0],
            data_size=data_row['data_path_or_ram'].values[0],
            # Utilisé pour la taille de la data (s'il est en RAM ou fichier)
            data_is_in_file=(storage_type == 'file'),
            sample_type='float32'  # Supposons que le type de sample soit du float32, adapte si nécessaire
        )

        if storage_type == 'file':
            # Si les données doivent être stockées dans un fichier
            if folder is None:
                raise ValueError("Folder must be specified for file-based storage.")
            file_path = os.path.join(folder, f"{data_id}.dat")
            # Stocker les données chunk par chunk via le générateur
            data_obj.store_data(data_source, folder=folder)
            self.data_registry.loc[self.data_registry['data_id'] == data_id, 'data_object'] = file_path
        else:
            # Si les données sont directement fournies sous forme de tableau (pas un générateur)
            if isinstance(data_source, np.ndarray):
                # On stocke directement la donnée en RAM
                data_obj.data = data_source.tolist()  # Convertir en liste pour que pandas puisse gérer

            else:
                # Si c'est un générateur, on l'utilise pour stocker les données en RAM chunk par chunk
                data_obj.store_data(data_source)
            self.data_registry.loc[self.data_registry['data_id'] == data_id, 'data_object'] = data_obj


def test_datapool():
    import numpy as np
    from pprint import pprint
    from tabulate import tabulate

    """
    Fonction de test pour vérifier le fonctionnement de la classe DataPool avec des données stockées en RAM ou en fichier.
    """

    # Initialisation du DataPool
    pool = DataPool()

    # Ajout d'une donnée temporaire (en RAM)
    print("Test RAM :")
    print("-----------> déclaration de la donnée dans le registre :")
    data_id_1 = pool.add_data(data_type=Data_Type.TEMPORAL_SIGNAL, data_name="Temp_Signal_1", source_id="Source_1", storage_type='ram')
    print(tabulate(pool.data_registry, headers='keys', tablefmt='pretty'))
    print("-----------> génération et stockage de la donnée :")
    # Stockage des données pour la première donnée (en RAM, avec tableau complet)
    print("\nStockage des données pour la première donnée (en RAM) :")
    temp_data = np.arange(0, 1000, dtype=np.float32)
    pool.store_data(data_id_1, temp_data)  # On passe directement les données
    print(tabulate(pool.data_registry, headers='keys', tablefmt='pretty'))

    # Ajout d'une donnée fréquence (stockée sur disque)
    print("\nAjout d'une donnée fréquentielle stockée en fichier :")
    data_id_2 = pool.add_data(data_type=Data_Type.FREQ_SIGNAL, data_name="Freq_Signal_1", source_id="Source_2", storage_type='file')
    pprint(pool.data_registry)



    # Stockage des données pour la deuxième donnée (en fichier, avec un générateur)
    print("\nStockage des données pour la deuxième donnée (en fichier) :")
    pool.store_data(data_id_2, data_generator('float32', 500, 50), folder="./test_files")
    pprint(pool.data_registry)

    # Ajout de subscribers pour la première donnée
    print("\nAjout de subscribers pour la première donnée :")
    pool.add_subscriber(data_id_1, "Subscriber_1")
    pool.add_subscriber(data_id_1, "Subscriber_2")
    pprint(pool.data_registry)

    # Acquittement de Subscriber_1
    print("\nAcquittement de Subscriber_1 pour la première donnée :")
    pool.acknowledge_data(data_id_1, "Subscriber_1")
    pprint(pool.data_registry)

    # Acquittement de Subscriber_2
    print("\nAcquittement de Subscriber_2 pour la première donnée (et suppression si non protégée) :")
    pool.acknowledge_data(data_id_1, "Subscriber_2")
    pprint(pool.data_registry)

    # Vérification des fichiers générés (et suppression après lecture)
    print("\nVérification de la suppression du fichier après lecture et acquittement de tous les subscribers :")
    pool.delete_data(data_id_2)
    pprint(pool.data_registry)


if __name__ == "__main__":



    # Appel de la fonction test pour vérifier le fonctionnement
    test_datapool()
