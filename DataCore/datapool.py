import numpy as np
import pandas as pd
from enum import Enum
from uuid import uuid4
import os

from PySide6.scripts.project import is_python_file
from tabulate import tabulate

from data import Data, data_generator


class Data_Type(Enum):
    PATHS = 0
    TEMPORAL_SIGNAL = 1
    FREQ_SIGNAL = 2
    FREQ_LIMITS = 3
    TEMP_LIMITS = 4
    FFT_STREAM = 5
    CONSTANT = 6


import os
import pandas as pd
from uuid import uuid4
from data import Data


class DataPool:
    def __init__(self):
        # DataFrame pour enregistrer les informations sur les données (Data)
        self.data_registry = pd.DataFrame(columns=[
            'data_id', 'data_type', 'data_name', 'storage_type', 'data_object'
        ])

        # DataFrame pour lier les sources aux données et gérer les verrous et la protection
        self.source_to_data = pd.DataFrame(columns=[
            'source_id', 'data_id', 'locked', 'protected'
        ])

        # DataFrame pour gérer les abonnés (subscribers) et les acquittements
        self.subscriber_to_data = pd.DataFrame(columns=[
            'subscriber_id', 'data_id', 'acquitements'
        ])

    def generate_unique_id(self):
        """ Génère un identifiant unique pour une nouvelle donnée """
        return str(uuid4())

    def add_data(self, data_type, data_name, source_id, protected=False, storage_type='ram'):
        """
        Ajoute une nouvelle donnée au DataPool et l'associe à une source.

        :param data_type: Le type de la donnée (utilise Data_Type)
        :param data_name: Nom de la donnée
        :param source_id: ID de la source (un seul pour chaque donnée)
        :param protected: Si la donnée est protégée contre l'effacement
        :param storage_type: 'ram' ou 'file' pour spécifier le type de stockage
        :return: L'ID unique de la donnée
        """
        data_id = self.generate_unique_id()

        # Ajouter à data_registry
        new_data = {
            'data_id': data_id,
            'data_type': data_type,
            'data_name': data_name,
            'storage_type': storage_type,
            'data_object': None  # Sera défini lors du stockage
        }
        self.data_registry = pd.concat([self.data_registry, pd.DataFrame([new_data])], ignore_index=True)

        # Ajouter à source_to_data
        source_mapping = {
            'source_id': source_id,
            'data_id': data_id,
            'locked': True,  # Verrouillé jusqu'à ce que l'écriture soit terminée
            'protected': protected
        }
        self.source_to_data = pd.concat([self.source_to_data, pd.DataFrame([source_mapping])], ignore_index=True)

        return data_id

    def add_subscriber(self, data_id, subscriber_id):
        """Ajoute un subscriber à la donnée."""
        subscriber_mapping = {
            'subscriber_id': subscriber_id,
            'data_id': data_id,
            'acquitements': 0  # Pas encore d'acquittement
        }
        self.subscriber_to_data = pd.concat([self.subscriber_to_data, pd.DataFrame([subscriber_mapping])],
                                            ignore_index=True)

    def acknowledge_data(self, data_id, subscriber_id):
        # Vérifier si la donnée est bien dans le registre
        if data_id not in self.data_registry['data_id'].values:
            raise ValueError(f"Data {data_id} not found in registry")

        # Mettre à jour l'acquittement pour le subscriber
        for index, row in self.subscriber_to_data.iterrows():
            if row['data_id'] == data_id and row['subscriber_id'] == subscriber_id:
                # Incrémenter l'acquittement pour ce subscriber
                self.subscriber_to_data.at[index, 'acquitements'] += 1
                break
        else:
            raise ValueError(f"Subscriber {subscriber_id} not found for data {data_id}")

        # Si tous les subscribers ont acquitté, vous pouvez choisir de libérer ou supprimer la donnée ici
        if self._all_subscribers_acknowledged(data_id):
            self._release_data(data_id)

    def _all_subscribers_acknowledged(self, data_id):
        # Vérifier si tous les subscribers ont acquitté
        total_subscribers = self.subscriber_to_data[self.subscriber_to_data['data_id'] == data_id].shape[0]
        acquitted_subscribers = self.subscriber_to_data[
            (self.subscriber_to_data['data_id'] == data_id) & (self.subscriber_to_data['acquitements'] > 0)].shape[0]

        return total_subscribers == acquitted_subscribers

    def _release_data(self, data_id):
        # Vérification si la donnée existe dans le registre
        if data_id not in self.data_registry['data_id'].values:
            raise ValueError(f"Data {data_id} not found in registry during release process")

        # Si la donnée est en RAM, la supprimer et nettoyer la référence
        for index, row in self.data_registry.iterrows():
            if row['data_id'] == data_id:
                storage_type = row['storage_type']

                if storage_type == 'ram':
                    # Supprimer l'objet data de la RAM
                    self.data_registry.at[index, 'data_object'] = None

                # Retirer la donnée du registre
                self.data_registry.drop(index, inplace=True)

                # Supprimer l'entrée dans le tableau des sources et subscribers
                self.source_to_data = self.source_to_data[self.source_to_data['data_id'] != data_id]
                self.subscriber_to_data = self.subscriber_to_data[self.subscriber_to_data['data_id'] != data_id]

                print(f"Donnée {data_id} libérée et retirée du registre")
                break
        else:
            raise ValueError(f"Data {data_id} not found for release")

    # def acknowledge_data(self, data_id, subscriber_id):
    #     if data_id not in self.data_registry:
    #         raise ValueError(f"Data {data_id} not found in registry")
    #
    #     data_entry = self.data_registry.loc[self.data_registry['data_id'] == data_id]
    #     if data_entry.empty:
    #         raise ValueError(f"Data {data_id} not found in the pool")
    #
    #     # Vérification de la présence du subscriber avant de l'acquitter
    #     if subscriber_id not in self.subscribers.get(data_id, []):
    #         raise ValueError(f"Subscriber {subscriber_id} not found for data {data_id}")
    #
    #     self.subscribers[data_id].remove(subscriber_id)
    #
    #     # Si tous les subscribers ont acquitté, libérer les ressources
    #     if not self.subscribers[data_id]:
    #         del self.subscribers[data_id]
    #         print(f"All subscribers have acknowledged data {data_id}. Data can be deleted or kept based on policy.")

    def lock_data(self, data_id):
        """Verrouille la donnée pour prévenir l'accès pendant l'écriture."""
        self.source_to_data.loc[self.source_to_data['data_id'] == data_id, 'locked'] = True

    def unlock_data(self, data_id):
        """Déverrouille la donnée après écriture."""
        self.source_to_data.loc[self.source_to_data['data_id'] == data_id, 'locked'] = False

    def store_data(self, data_id, data_source, folder=None):
        """
        Stocke la donnée soit en RAM, soit sur disque en utilisant la classe Data.
        Si data_source est une liste ou un tableau, elle sera stockée en RAM. Si c'est un générateur, elle sera stockée en chunks.

        :param data_id: L'ID unique de la donnée dans le DataPool.
        :param data_source: Soit un générateur de chunks de données, soit une variable contenant les données en RAM.
        :param folder: Dossier où stocker le fichier si nécessaire.
        """
        # Récupération de la ligne correspondante dans data_registry
        data_row = self.data_registry[self.data_registry['data_id'] == data_id].iloc[0]
        storage_type = data_row['storage_type']

        # Si le data_source est un générateur, on ne peut pas utiliser len(data_source)
        if hasattr(data_source, '__len__'):
            data_size_in_bytes = len(
                data_source) * 4  # Taille estimée des données, modifiable selon les types de données
            num_samples = len(data_source)
        else:
            data_size_in_bytes = None  # On ne connaît pas à l'avance la taille des générateurs
            num_samples = None

        # Créer un objet Data correspondant à cette donnée
        data_obj = Data(
            data_id=data_id,
            data_type=data_row['data_type'],
            data_name=data_row['data_name'],
            data_size_in_bytes=data_size_in_bytes if data_size_in_bytes is not None else 0,
            num_samples=num_samples if num_samples is not None else 0,
            in_file=(storage_type == 'file'),
            sample_type='float32'  # Exemple, modifiable selon le type de données
        )

        # Si le stockage est en fichier, vérifier que le dossier est fourni
        if storage_type == 'file':
            if folder is None:
                raise ValueError("Folder must be specified for file-based storage.")
            # Utilisation de store_data_from_data_generator pour un générateur ou store_data_from_object pour des données RAM
            if isinstance(data_source, (list, np.ndarray)):
                data_obj.store_data_from_object(data_source, folder=folder)
            else:
                data_obj.store_data_from_data_generator(data_source, folder=folder)
        else:
            # Si les données sont stockées en RAM
            data_obj.store_data_from_object(data_source)

        # Mise à jour de la référence à l'objet Data dans data_registry
        self.data_registry.loc[self.data_registry['data_id'] == data_id, 'data_object'] = data_obj

    def delete_data(self, data_id):
        """Supprime la donnée si elle n'est pas protégée et que tous les acquittements sont reçus."""
        # Vérifier la protection dans source_to_data
        source_row = self.source_to_data[self.source_to_data['data_id'] == data_id]
        if not source_row.empty and not source_row['protected'].values[0]:
            # Récupérer l'objet Data avant de supprimer la ligne du registre
            data_row = self.data_registry[self.data_registry['data_id'] == data_id]

            if not data_row.empty:
                data_obj = data_row['data_object'].values[0]  # Récupérer l'objet Data

                # Supprimer la relation source-to-data
                self.source_to_data = self.source_to_data[self.source_to_data['data_id'] != data_id]

                # Supprimer la relation subscriber-to-data
                self.subscriber_to_data = self.subscriber_to_data[self.subscriber_to_data['data_id'] != data_id]

                # Supprimer la ligne du DataFrame principal après récupération de l'objet
                self.data_registry = self.data_registry[self.data_registry['data_id'] != data_id]

                # Appeler la méthode de suppression de l'objet Data
                if data_obj is not None:
                    data_obj.delete_data()  # Suppression des données (RAM ou fichier)

                # Supprimer l'objet Data explicitement
                del data_obj

    def get_data_info(self, data_id):
        """Retourne les informations de la donnée via son ID, si elle n'est pas verrouillée."""
        # Vérifier si la donnée est verrouillée
        is_locked = self.source_to_data.loc[self.source_to_data['data_id'] == data_id, 'locked'].values[0]

        if is_locked:
            raise PermissionError(f"Data {data_id} is locked and cannot be read.")

        # Si la donnée n'est pas verrouillée, renvoyer ses informations
        return self.data_registry.loc[self.data_registry['data_id'] == data_id]

    def read_data(self, data_id, subscriber_id):
        """
        Permet à un subscriber de lire les données complètes.
        Prend en compte le verrouillage de la donnée et gère l'acquittement après lecture.

        :param data_id: L'ID de la donnée à lire.
        :param subscriber_id: L'ID du subscriber qui lit les données.
        :return: Les données complètes si disponibles.
        """
        # Vérifier si la donnée est verrouillée
        is_locked = self.source_to_data.loc[self.source_to_data['data_id'] == data_id, 'locked'].values[0]
        if is_locked:
            raise PermissionError(f"Data {data_id} is locked and cannot be read.")

        # Récupérer l'objet Data
        data_obj = self.data_registry.loc[self.data_registry['data_id'] == data_id, 'data_object'].values[0]

        if data_obj is None:
            raise ValueError(f"Data {data_id} has not been stored yet.")

        # Lire les données depuis l'objet Data
        data = data_obj.read_data()

        # Acquitter la donnée après la lecture
        self.acknowledge_data(data_id, subscriber_id)

        return data

    def get_chunk_generator(self, data_id, chunk_size=1024, subscriber_id=None):
        """
        Retourne un générateur de données chunk par chunk (sans chevauchement).
        L'acquittement est effectué lorsque tous les chunks ont été traités.

        :param data_id: L'ID unique de la donnée dans le DataPool.
        :param chunk_size: La taille de chaque chunk.
        :param subscriber_id: L'ID du subscriber effectuant la lecture (pour l'acquittement).
        :yield: Chaque chunk sans chevauchement.
        """
        # Vérifier si la donnée est verrouillée
        source_row = self.source_to_data[self.source_to_data['data_id'] == data_id]
        if source_row['locked'].values[0]:
            raise ValueError(f"Data with ID {data_id} is locked and cannot be read.")

        # Récupérer l'objet Data à partir de data_registry
        data_obj = self.data_registry.loc[self.data_registry['data_id'] == data_id, 'data_object'].values[0]

        # Lire les données via la méthode de la classe Data (chunk par chunk sans chevauchement)
        chunked_data = data_obj.read_chunked_data(chunk_size=chunk_size)

        # Fournir les chunks au subscriber un par un
        for chunk in chunked_data:
            yield chunk

        # Lorsque tous les chunks ont été traités, envoyer l'acquittement
        if subscriber_id is not None:
            print(f"Acquitting data {data_id} for subscriber {subscriber_id}")
            print(tabulate(self.subscriber_to_data, headers='keys', tablefmt='pretty'))
            print(tabulate(self.data_registry, headers='keys', tablefmt='pretty'))

            self.acknowledge_data(data_id, subscriber_id)

    def get_overlapped_chunk_generator(self, data_id, chunk_size=1024, overlap=50, subscriber_id=None):
        """
        Retourne un générateur de données chunk par chunk avec chevauchement.
        L'acquittement est effectué lorsque tous les chunks ont été traités.

        :param data_id: L'ID unique de la donnée dans le DataPool.
        :param chunk_size: La taille de chaque chunk.
        :param overlap: Le pourcentage de chevauchement entre les chunks.
        :param subscriber_id: L'ID du subscriber effectuant la lecture (pour l'acquittement).
        :yield: Chaque chunk avec chevauchement.
        """
        # Vérifier si la donnée est verrouillée
        source_row = self.source_to_data[self.source_to_data['data_id'] == data_id]
        if source_row['locked'].values[0]:
            raise ValueError(f"Data with ID {data_id} is locked and cannot be read.")

        # Récupérer l'objet Data à partir de data_registry
        data_obj = self.data_registry.loc[self.data_registry['data_id'] == data_id, 'data_object'].values[0]

        # Lire les données avec chevauchement via la méthode de la classe Data
        chunked_data = data_obj.read_overlapped_chunked_data(chunk_size=chunk_size, overlap=overlap)

        # Fournir les chunks au subscriber un par un
        for chunk in chunked_data:
            yield chunk

        # Lorsque tous les chunks ont été traités, envoyer l'acquittement
        if subscriber_id is not None:
            self.acknowledge_data(data_id, subscriber_id)


# Fonctions de test
def test_locking_mechanism():
    print("\n==== Test du mécanisme de verrouillage ====\n")
    pool = DataPool()

    # Ajout d'une donnée verrouillée
    print("\n---- Ajout de la première donnée (verrouillée automatiquement à l'ajout) ----")
    data_id_1 = pool.add_data(data_type="Data_Type.TEMPORAL_SIGNAL", data_name="Temp_Signal_RAM", source_id="Source_1", storage_type='ram')
    print(tabulate(pool.data_registry, headers='keys', tablefmt='pretty'))
    print(tabulate(pool.source_to_data, headers='keys', tablefmt='pretty'))

    # Vérifier que la donnée est bien verrouillée
    assert pool.source_to_data.loc[pool.source_to_data['data_id'] == data_id_1, 'locked'].values[0] == True
    print("\n---- Vérification : La donnée est bien verrouillée ----")

    # Tentative de lecture (devrait échouer)
    try:
        pool.get_data_info(data_id_1)
        print("\nTentative de lecture réussie (non attendue)")
    except PermissionError as e:
        print(f"\nTentative de lecture échouée comme prévu : {e}")

    # Déverrouiller la donnée
    print("\n---- Déverrouillage de la donnée ----")
    pool.unlock_data(data_id_1)
    print(tabulate(pool.source_to_data, headers='keys', tablefmt='pretty'))

    # Vérifier que la donnée est déverrouillée
    assert pool.source_to_data.loc[pool.source_to_data['data_id'] == data_id_1, 'locked'].values[0] == False
    print("\n---- Vérification : La donnée est déverrouillée ----")

    # Lecture de la donnée après déverrouillage
    try:
        data_info = pool.get_data_info(data_id_1)
        print("\nLecture réussie après déverrouillage")
        print(tabulate(data_info, headers='keys', tablefmt='pretty'))
    except Exception as e:
        print(f"\nErreur inattendue lors de la lecture : {e}")


def test_chunked_read():
    print("\n==== Test de la lecture par chunks ====\n")
    pool = DataPool()

    # Ajout et stockage d'une donnée dans un fichier
    print("\n---- Ajout et stockage d'une donnée (Fichier) ----")
    data_id_2 = pool.add_data(data_type="Data_Type.FREQ_SIGNAL", data_name="Freq_Signal_File", source_id="Source_2", storage_type='file')

    # Générateur de données chunk par chunk
    data_gen = data_generator('float32', 500, 50)  # Générateur pour 500 éléments avec des chunks de taille 50
    pool.store_data(data_id_2, data_gen, folder="./test_files")
    print("\n---- Après stockage des données (Fichier) ----")
    print(tabulate(pool.data_registry, headers='keys', tablefmt='pretty'))

    # Déverrouiller la donnée avant de lire les chunks
    print("\n---- Déverrouillage de la donnée ----")
    pool.unlock_data(data_id_2)
    print(tabulate(pool.source_to_data, headers='keys', tablefmt='pretty'))

    # Ajout de deux subscribers
    print("\n---- Ajout de subscribers ----")
    pool.add_subscriber(data_id_2, "Subscriber_1")
    pool.add_subscriber(data_id_2, "Subscriber_2")

    # Utiliser le générateur de chunks sans chevauchement
    print("\n---- Lecture par chunks (sans chevauchement) ----")
    chunk_gen = pool.get_chunk_generator(data_id_2, chunk_size=50, subscriber_id="Subscriber_2")

    for chunk in chunk_gen:
        print(f"Chunk reçu : {chunk}")


def test_overlapped_chunked_read():
    print("\n==== Test de la lecture par chunks avec chevauchement ====\n")
    pool = DataPool()

    # Ajout et stockage d'une donnée dans un fichier
    print("\n---- Ajout et stockage d'une donnée (Fichier) ----")
    data_id_2 = pool.add_data(data_type="Data_Type.FREQ_SIGNAL", data_name="Freq_Signal_File", source_id="Source_2", storage_type='file')

    # Générateur de données chunk par chunk
    data_gen = data_generator('float32', 500, 50)  # Générateur de 500 éléments avec des chunks de taille 50
    pool.store_data(data_id_2, data_gen, folder="./test_files")
    print("\n---- Après stockage des données (Fichier) ----")
    print(tabulate(pool.data_registry, headers='keys', tablefmt='pretty'))

    # Déverrouiller la donnée avant de lire les chunks
    print("\n---- Déverrouillage de la donnée ----")
    pool.unlock_data(data_id_2)
    print(tabulate(pool.source_to_data, headers='keys', tablefmt='pretty'))

    # Ajouter un subscriber avant la lecture
    print("\n---- Ajout du subscriber ----")
    pool.add_subscriber(data_id_2, subscriber_id="Subscriber_2")
    print(tabulate(pool.source_to_data, headers='keys', tablefmt='pretty'))
    print(tabulate(pool.subscriber_to_data, headers='keys', tablefmt='pretty'))
    print(tabulate(pool.data_registry, headers='keys', tablefmt='pretty'))

    # Utiliser le générateur de chunks avec chevauchement
    print("\n---- Lecture par chunks avec chevauchement ----")
    chunk_gen = pool.get_overlapped_chunk_generator(data_id_2, chunk_size=50, overlap=25, subscriber_id="Subscriber_2")

    for chunk in chunk_gen:
        print(f"Chunk reçu avec chevauchement : {chunk}")



def test_acknowledgment():
    print("\n==== Test de la gestion des acquittements ====\n")
    pool = DataPool()

    # Ajout et stockage d'une donnée en RAM
    print("\n---- Ajout d'une donnée en RAM ----")
    data_id_1 = pool.add_data(data_type="Data_Type.TEMPORAL_SIGNAL", data_name="Temp_Signal_RAM", source_id="Source_1", storage_type='ram')
    pool.store_data(data_id_1, list(range(1000)))  # Stoker des données exemple
    print("\n---- Après stockage des données ----")
    print(tabulate(pool.data_registry, headers='keys', tablefmt='pretty'))

    # Ajout de deux subscribers
    print("\n---- Ajout de subscribers ----")
    pool.add_subscriber(data_id_1, "Subscriber_1")
    pool.add_subscriber(data_id_1, "Subscriber_2")
    print(tabulate(pool.subscriber_to_data, headers='keys', tablefmt='pretty'))

    # Acquittement de Subscriber_1
    print("\n---- Acquittement de Subscriber_1 ----")
    pool.acknowledge_data(data_id_1, "Subscriber_1")
    print(tabulate(pool.subscriber_to_data, headers='keys', tablefmt='pretty'))

    # Acquittement de Subscriber_2 (Suppression de la donnée attendue)
    print("\n---- Acquittement de Subscriber_2 (Suppression de la donnée) ----")
    pool.acknowledge_data(data_id_1, "Subscriber_2")
    print(tabulate(pool.subscriber_to_data, headers='keys', tablefmt='pretty'))
    print(tabulate(pool.data_registry, headers='keys', tablefmt='pretty'))  # La donnée devrait être supprimée


def test_datapool_methods():
    print("\n==== Démarrage des tests pour la classe DataPool ====\n")

    pool = DataPool()

    # Ajout et stockage d'une donnée en RAM
    print("\n---- Ajout de la première donnée (RAM) ----")
    data_id_1 = pool.add_data(data_type="Data_Type.TEMPORAL_SIGNAL", data_name="Temp_Signal_RAM", source_id="Source_1", storage_type='ram')
    print(tabulate(pool.subscriber_to_data, headers='keys', tablefmt='pretty'))
    print(tabulate(pool.data_registry, headers='keys', tablefmt='pretty'))
    print(tabulate(pool.source_to_data, headers='keys', tablefmt='pretty'))

    temp_data = list(range(1000))  # Exemple de données à stocker
    pool.store_data(data_id_1, temp_data)
    print("\n---- Après stockage des données (RAM) ----")
    print(tabulate(pool.subscriber_to_data, headers='keys', tablefmt='pretty'))
    print(tabulate(pool.data_registry, headers='keys', tablefmt='pretty'))
    print(tabulate(pool.source_to_data, headers='keys', tablefmt='pretty'))

    # Ajout et stockage d'une donnée dans un fichier
    print("\n---- Ajout de la deuxième donnée (Fichier) ----")
    data_id_2 = pool.add_data(data_type="Data_Type.FREQ_SIGNAL", data_name="Freq_Signal_File", source_id="Source_2", storage_type='file')
    print(tabulate(pool.subscriber_to_data, headers='keys', tablefmt='pretty'))
    print(tabulate(pool.data_registry, headers='keys', tablefmt='pretty'))
    print(tabulate(pool.source_to_data, headers='keys', tablefmt='pretty'))

    # Générateur de données chunk par chunk
    data_gen = data_generator('float32', 500, 50)  # Générateur pour 500 éléments avec des chunks de taille 50
    pool.store_data(data_id_2, data_gen, folder="./test_files")
    print("\n---- Après stockage des données (Fichier) ----")
    print(tabulate(pool.subscriber_to_data, headers='keys', tablefmt='pretty'))
    print(tabulate(pool.data_registry, headers='keys', tablefmt='pretty'))
    print(tabulate(pool.source_to_data, headers='keys', tablefmt='pretty'))

    # Ajout de subscribers
    print("\n---- Ajout de subscribers pour la première donnée ----")
    pool.add_subscriber(data_id_1, "Subscriber_1")
    pool.add_subscriber(data_id_2, "Subscriber_2")
    print(tabulate(pool.subscriber_to_data, headers='keys', tablefmt='pretty'))
    print(tabulate(pool.data_registry, headers='keys', tablefmt='pretty'))
    print(tabulate(pool.source_to_data, headers='keys', tablefmt='pretty'))

    # Acquittement des subscribers
    print("\n---- Acquittement de Subscriber_1 ----")
    pool.acknowledge_data(data_id_1, "Subscriber_1")
    print(tabulate(pool.subscriber_to_data, headers='keys', tablefmt='pretty'))
    print(tabulate(pool.data_registry, headers='keys', tablefmt='pretty'))
    print(tabulate(pool.source_to_data, headers='keys', tablefmt='pretty'))

    print("\n---- Acquittement de Subscriber_2 (Suppression de la donnée) ----")
    pool.acknowledge_data(data_id_2, "Subscriber_2")
    print(tabulate(pool.subscriber_to_data, headers='keys', tablefmt='pretty'))
    print(tabulate(pool.data_registry, headers='keys', tablefmt='pretty'))
    print(tabulate(pool.source_to_data, headers='keys', tablefmt='pretty'))

if __name__ == "__main__":

    # Appel de la fonction test
    test_locking_mechanism()
    test_chunked_read()
    test_overlapped_chunked_read()
    test_acknowledgment()
    # test_datapool_methods()


