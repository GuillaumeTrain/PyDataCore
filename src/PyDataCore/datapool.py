import numpy as np
import os
import pandas as pd
from uuid import uuid4
from .data import Data, data_generator, Data_Type, FilePathListData, FolderPathListData, FileListData, \
    TemporalSignalData, FreqSignalData, FFTSData, ConstantsData, StrData, IntsData, FreqLimitsData, TempLimitsData


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

    def register_data(self, data_type, data_name, source_id, protected=False, in_file=False, **kwargs):
        """
        Enregistre une nouvelle donnée dans le DataPool et l'associe à une source.

        :param data_type: Type de la donnée (ex. Data_Type)
        :param data_name: Nom de la donnée
        :param source_id: ID de la source associée à cette donnée
        :param protected: True si la donnée est protégée contre la suppression
        :param in_file: Si True, la donnée sera stockée dans un fichier. Si False, elle sera stockée en RAM.
        :param kwargs: Paramètres supplémentaires requis par certaines classes de données (ex: time_step, unit)
        :return: L'ID unique de la donnée créée
        """
        data_id = self.generate_unique_id()

        # Déterminer le type de stockage : 'ram' ou 'file'
        storage_type = 'file' if in_file else 'ram'

        # Mapping des types de données vers les classes correspondantes
        data_class_mapping = {
            Data_Type.FILE_PATHS.value: FilePathListData,
            Data_Type.FOLDER_PATHS.value: FolderPathListData,
            Data_Type.FILE_LIST.value: FileListData,
            Data_Type.TEMPORAL_SIGNAL.value: TemporalSignalData,
            Data_Type.FREQ_SIGNAL.value: FreqSignalData,
            Data_Type.FFTS.value: FFTSData,
            Data_Type.CONSTANTS.value: ConstantsData,
            Data_Type.STR.value: StrData,
            Data_Type.INTS.value: IntsData,
            Data_Type.FREQ_LIMITS.value: FreqLimitsData,
            Data_Type.TEMP_LIMITS.value: TempLimitsData,
        }

        # Debugging: print the available data mappings
        print(f"Available data class mappings: {list(data_class_mapping.keys())}")
        print(f"Registering data of type: {data_type}")

        # Comparer en utilisant la valeur de l'énumération
        try:
            data_class = data_class_mapping[data_type.value]
            print(f"Instantiating data class: {data_class}")
        except KeyError:
            raise ValueError(f"Data type {data_type} is not supported.")

        try:
            # Instanciation de la classe de donnée avec les paramètres optionnels
            data_size_in_bytes = 0  # Taille par défaut à 0, sera mise à jour lors du stockage
            number_of_elements = 0  # À ajuster également lors du stockage

            # Passe les kwargs à l'instanciation
            data_obj = data_class(
                data_id=data_id,
                data_name=data_name,
                data_size_in_bytes=data_size_in_bytes,
                number_of_elements=number_of_elements,
                in_file=in_file,
                **kwargs  # Transfert des paramètres optionnels (time_step, unit, etc.)
            )

            print(f"Data object created: {data_obj}")

        except Exception as e:
            raise ValueError(f"Failed to instantiate data class {data_class} with error: {e}")

        # Ajouter la donnée au registre de données
        new_data_entry = {
            'data_id': data_id,
            'data_type': data_type.name,  # Use the name instead of full enum
            'data_name': data_name,
            'storage_type': storage_type,
            'data_object': data_obj  # Objet de donnée instancié
        }
        self.data_registry = pd.concat([self.data_registry, pd.DataFrame([new_data_entry])], ignore_index=True)

        # Ajouter la donnée au registre source_to_data
        source_entry = {
            'source_id': source_id,
            'data_id': data_id,
            'locked': True,  # Verrouiller pendant la phase d'écriture
            'protected': protected
        }
        self.source_to_data = pd.concat([self.source_to_data, pd.DataFrame([source_entry])], ignore_index=True)

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
                self.subscriber_to_data.at[index, 'acquitements'] = True
                break
        else:
            raise ValueError(f"Subscriber {subscriber_id} not found for data {data_id}")

        # Si tous les subscribers ont acquitté
        if self._all_subscribers_acknowledged(data_id):
            source_row = self.source_to_data[self.source_to_data['data_id'] == data_id]
            if not source_row['protected'].values[0]:  # Si la donnée n'est pas protégée
                print(f"All subscribers acknowledged and data {data_id} is not protected. Deleting data...")
                self._release_data(data_id)  # Supprimer la donnée si elle n'est pas protégée
            else:
                print(f"Data {data_id} is protected, not deleting.")

    def _all_subscribers_acknowledged(self, data_id):
        # Vérifier si tous les subscribers ont acquitté
        #récupérer une liste de tous les subscribers pour la donnée contenant les acquittements
        subscribers = self.subscriber_to_data[self.subscriber_to_data['data_id'] == data_id]
        print(f"subscribers : {subscribers}")
        #faire une fonction logique et entre tous les acquittements
        acquittements = subscribers['acquitements']
        is_all_acquitted = acquittements.all()

        return is_all_acquitted

    def _release_data(self, data_id):
        # Vérification si la donnée existe dans le registre
        if data_id not in self.data_registry['data_id'].values:
            raise ValueError(f"Data {data_id} not found in registry during release process")

        # Si la donnée est en RAM ou en fichier, la supprimer et nettoyer la référence
        for index, row in self.data_registry.iterrows():
            if row['data_id'] == data_id:
                data_obj = row['data_object']
                storage_type = row['storage_type']

                if storage_type == 'ram':
                    # Supprimer l'objet data de la RAM
                    self.data_registry.at[index, 'data_object'] = None
                elif storage_type == 'file':
                    # Supprimer le fichier si la donnée est stockée en fichier
                    if data_obj.file_path and os.path.exists(data_obj.file_path):
                        print(f"Deleting file {data_obj.file_path} associated with data {data_id}")
                        os.remove(data_obj.file_path)

                # Retirer la donnée du registre
                self.data_registry.drop(index, inplace=True)

                # Supprimer l'entrée dans le tableau des sources et subscribers
                self.source_to_data = self.source_to_data[self.source_to_data['data_id'] != data_id]
                self.subscriber_to_data = self.subscriber_to_data[self.subscriber_to_data['data_id'] != data_id]

                print(f"Donnée {data_id} libérée et retirée du registre")
                break
        else:
            raise ValueError(f"Data {data_id} not found for release")

    def lock_data(self, data_id):
        """Verrouille la donnée pour prévenir l'accès pendant l'écriture."""
        self.source_to_data.loc[self.source_to_data['data_id'] == data_id, 'locked'] = True

    def unlock_data(self, data_id):
        """Déverrouille la donnée après écriture."""
        self.source_to_data.loc[self.source_to_data['data_id'] == data_id, 'locked'] = False

    # Vérification des définitions spécifiques pour TemporalSignalData et FreqSignalData
    def _check_signal_data_definitions(self, data_obj):
        """
        Vérifie si les définitions de données sont valides pour les signaux temporels et fréquentiels.
        """
        if isinstance(data_obj, TemporalSignalData):
            # Pour les signaux temporels
            if data_obj.dt is None or data_obj.unit is None:
                raise ValueError(f"Data {data_obj.data_id} is missing required definitions (time_step, unit)")
        elif isinstance(data_obj, FreqSignalData):
            # Pour les signaux fréquentiels
            if data_obj.df is None or data_obj.unit is None:
                raise ValueError(f"Data {data_obj.data_id} is missing required definitions (freq_step, unit)")

    def store_data(self, data_id, data_source, source_id, folder=None):
        """
        Stocke la donnée dans le DataPool en vérifiant les définitions de la donnée et son type de stockage.

        :param data_id: L'ID unique de la donnée dans le DataPool.
        :param data_source: Source des données (liste, tableau ou générateur).
        :param source_id: ID de la source qui donne la donnée.
        :param folder: Dossier où stocker le fichier si nécessaire (pour les données en fichier).
        """
        # Vérifier que la donnée existe dans le registre
        data_row = self.data_registry[self.data_registry['data_id'] == data_id]
        if data_row.empty:
            raise ValueError(f"Data {data_id} not found in registry")

        # Vérifier que la source est bien celle qui a enregistré la donnée
        source_row = self.source_to_data[self.source_to_data['data_id'] == data_id]
        if source_row.empty or source_row['source_id'].values[0] != source_id:
            raise PermissionError(f"Source {source_id} is not authorized to store data for {data_id}")

        # Vérifier que la donnée est verrouillée avant de la stocker
        if not source_row['locked'].values[0]:
            raise PermissionError(f"Data {data_id} is not locked and cannot be stored")

        # Récupérer l'objet Data correspondant à cette donnée
        data_obj = data_row['data_object'].values[0]

        # Vérifier les définitions requises
        self._check_signal_data_definitions(data_obj)

        # Stocker les données en RAM ou en fichier selon le type
        if data_obj.in_file:
            if folder is None:
                raise ValueError("Folder must be specified for file-based storage")
            if isinstance(data_source, (list, np.ndarray)):
                data_obj.store_data_from_object(data_source, folder=folder)
            else:
                data_obj.store_data_from_data_generator(data_source, folder=folder)
        else:
            if isinstance(data_source, (list, np.ndarray, str)):
                data_obj.store_data_from_object(data_source)
            else:
                data_obj.store_data_from_data_generator(data_source)

        # Mise à jour de l'objet dans le registre
        self.data_registry.loc[self.data_registry['data_id'] == data_id, 'data_object'] = data_obj

        # Déverrouiller la donnée après le stockage
        self.unlock_data(data_id)

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

    def get_data(self, data_id, subscriber_id):
        """
        Permet à un subscriber de lire les données complètes.
        Prend en compte le verrouillage de la donnée et gère l'acquittement après lecture.

        :param data_id: L'ID de la donnée à lire.
        :param subscriber_id: L'ID du subscriber qui lit les données.
        :return: Les données complètes si disponibles.
        """
        data = None
        # Vérifier si la donnée est verrouillée
        is_locked = self.source_to_data.loc[self.source_to_data['data_id'] == data_id, 'locked'].values[0]
        if is_locked:
            raise PermissionError(f"Data {data_id} is locked and cannot be read.")
        #verifier si le subscriber est autorisé à lire la donnée
        if subscriber_id not in self.subscriber_to_data.loc[
            self.subscriber_to_data['data_id'] == data_id, 'subscriber_id'].values:
            raise PermissionError(f"Subscriber {subscriber_id} is not authorized to read data {data_id}")
        #vérifier si la donnée est sous forme de fichier
        data_obj = self.data_registry.loc[self.data_registry['data_id'] == data_id, 'data_object'].values[0]
        if data_obj is None:
            raise ValueError(f"Data {data_id} has not been stored yet.")
        data = data_obj.read_data()  #la méthode read_data() de la classe Data gère le cas de fichier ou de RAM

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
        # Vérifier si la donnée existe et est verrouillée
        source_row = self.source_to_data[self.source_to_data['data_id'] == data_id]
        if source_row.empty:
            raise ValueError(f"Data with ID {data_id} not found in source_to_data.")

        if source_row['locked'].values[0]:
            raise PermissionError(f"Data {data_id} is locked and cannot be read.")

        # Vérifier si le subscriber est autorisé à lire la donnée
        if subscriber_id not in self.subscriber_to_data.loc[
            self.subscriber_to_data['data_id'] == data_id, 'subscriber_id'].values:
            raise PermissionError(f"Subscriber {subscriber_id} is not authorized to read data {data_id}")

        # Récupérer l'objet Data à partir de data_registry
        data_obj = self.data_registry.loc[self.data_registry['data_id'] == data_id, 'data_object'].values[0]
        if not data_obj:
            raise ValueError(f"Data object for {data_id} not found or has been deleted.")

        # Lire les données via la méthode de la classe Data (chunk par chunk sans chevauchement)
        chunked_data = data_obj.read_chunked_data(chunk_size=chunk_size)

        # Fournir les chunks au subscriber un par un
        for chunk in chunked_data:
            yield chunk

        # Lorsque tous les chunks ont été traités, envoyer l'acquittement
        if subscriber_id is not None:
            self.acknowledge_data(data_id, subscriber_id)

    def get_data_chunk(self, data_id, chunk_index, chunk_size=1024):
        """
        Récupère un chunk spécifique des données depuis un fichier ou la RAM.
        :param data_id: L'ID unique de la donnée dans le DataPool.
        :param chunk_index: Index du chunk à récupérer.
        :param chunk_size: Taille du chunk (en nombre de samples).
        :return: Le chunk de données.
        """
        # Vérifier si la donnée existe dans le registre
        data_row = self.data_registry[self.data_registry['data_id'] == data_id]
        if data_row.empty:
            raise ValueError(f"Data {data_id} not found in registry")

        # Récupérer l'objet Data correspondant
        data_obj = data_row['data_object'].values[0]

        if data_row['storage_type'].values[0] == 'file':
            # Si la donnée est stockée dans un fichier, utiliser la méthode read_specific_chunk
            return data_obj.read_specific_chunk(chunk_index, chunk_size)
        else:
            # Si la donnée est en RAM, extraire simplement le segment correspondant
            start_idx = chunk_index * chunk_size
            end_idx = min(start_idx + chunk_size, len(data_obj.data))
            return data_obj.data[start_idx:end_idx]

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

    def convert_data_to_ram(self, data_id):
        """
        Convertit les données stockées dans un fichier en RAM, en agrégeant tous les chunks si les données sont sous forme de générateur.

        :param data_id: L'ID unique de la donnée dans le DataPool.
        """
        # locker la donnée pour éviter les accès concurrents
        self.lock_data(data_id)
        # Récupérer l'objet Data à partir du data_registry
        data_row = self.data_registry[self.data_registry['data_id'] == data_id].iloc[0]
        data_obj = data_row['data_object']

        if data_obj.in_file and data_obj.file_path:
            print(f"Conversion des données de fichier vers RAM pour {data_id}...")

            # Si les données sont dans un fichier, les lire en une seule fois
            data_obj.convert_file_to_ram()

            # Mise à jour du type de stockage
            self.data_registry.loc[self.data_registry['data_id'] == data_id, 'storage_type'] = 'ram'
            print(f"Les données {data_id} sont maintenant en RAM.")
        else:
            print(f"Les données {data_id} sont déjà en RAM ou le fichier est manquant.")
        #unlocker la donnée après la conversion
        self.unlock_data(data_id)

    def convert_data_to_file(self, data_id, folder=None):
        """
        Convertit les données stockées en RAM dans un fichier sans passer par des chunks.

        :param data_id: L'ID unique de la donnée dans le DataPool.
        :param folder: Le dossier où stocker le fichier de données.
        """
        # Récupérer l'objet Data à partir du data_registry
        # locker la donnée pour éviter les accès concurrents
        self.lock_data(data_id)
        data_row = self.data_registry[self.data_registry['data_id'] == data_id].iloc[0]
        data_obj = data_row['data_object']

        if not data_obj.in_file:
            print(f"Conversion des données de RAM vers fichier pour {data_id}...")

            # Si les données sont en RAM, les convertir en fichier directement
            if folder is None:
                raise ValueError("Le dossier où stocker les fichiers doit être spécifié.")
            data_obj.convert_ram_to_file(folder)

            # Mise à jour du type de stockage
            self.data_registry.loc[self.data_registry['data_id'] == data_id, 'storage_type'] = 'file'
            print(f"Les données {data_id} sont maintenant stockées dans un fichier.")
        else:
            print(f"Les données {data_id} sont déjà dans un fichier.")
        #unlocker la donnée après la conversion
        self.unlock_data(data_id)



