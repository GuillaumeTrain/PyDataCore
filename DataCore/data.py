import os
import struct
import numpy as np
import os
import tracemalloc

class Data:
    def __init__(self, data_id, data_type, data_name, data_size_in_bytes, num_samples, in_file=False, sample_type='float'):
        """
        initialise une instance de données.
        :param data_id: identifiant unique de données.
        :param data_type: type de données (par exemple, temporal, freq, etc.).
        :param data_name: nom des données.
        :param data_size_in_bytes: taille des données en octets.
        :param num_samples: nombre de samples.
        :param in_file: indique si les données sont stockées dans un fichier ou en mémoire.
        :param sample_type: type de données (float32, float64, int32, int64, str).
        """
        self.data_id = data_id
        self.data_type = data_type
        self.data_name = data_name
        self.data_size_in_bytes = data_size_in_bytes
        self.num_samples = num_samples
        self.in_file = in_file
        self.sample_type = sample_type
        self.data = None
        self.file_path = None
        self.sample_format, self.sample_size = self._get_sample_format_and_size(sample_type)

    def _get_sample_format_and_size(self, sample_type):
        """
        Retourne le format struct et la taille en octets en fonction du type de sample.
        :param sample_type: Le type de données (float32, float64, int32, int64, str).
        :return: format_struct (char pour struct.pack/unpack), taille en octets (ou par caractère pour les chaînes).
        """
        if sample_type == 'float32':
            return 'f', 4  # 'f' pour float (32 bits)
        elif sample_type == 'float64':
            return 'd', 8  # 'd' pour double (64 bits)
        elif sample_type == 'int32':
            return 'i', 4  # 'i' pour int32 (32 bits)
        elif sample_type == 'int64':
            return 'q', 8  # 'q' pour int64 (64 bits)
        elif sample_type == 'str':
            return 's', 1  # 's' pour chaîne de caractères, chaque caractère est 1 octet en utf-8
        else:
            raise ValueError(f"Unsupported sample type: {sample_type}")

    def store_data_from_data_generator(self, data_generator, folder=None):
        """
        Stocke les données chunk par chunk depuis un générateur.
        :param data_generator: Générateur fournissant des chunks de données (par exemple des flottants ou des chaînes).
        :param folder: Dossier où stocker le fichier (si in_file est True).
        """
        if self.in_file:
            if folder is None:
                raise ValueError("Folder must be specified for file-based storage.")
            self.file_path = os.path.join(folder, f"{self.data_id}.dat")

            # Ouvre le fichier en mode écriture binaire (chunk par chunk)
            with open(self.file_path, 'wb') as f:
                for chunk in data_generator:
                    if self.sample_type == 'str':
                        # Écrire chaque chunk de chaînes de caractères directement
                        f.write(''.join(chunk).encode('utf-8'))
                    else:
                        # Écrire chaque chunk de données numériques directement dans le fichier
                        packed_chunk = struct.pack(f'{len(chunk)}{self.sample_format}', *chunk)
                        f.write(packed_chunk)
        else:
            # Stockage en RAM en collectant tous les chunks
            self.data = []
            for chunk in data_generator:
                if self.sample_type == 'str':
                    self.data.extend(list(chunk))  # Ajout des caractères à la liste
                else:
                    self.data.extend(chunk)  # Ajout des éléments numériques à la liste

    def store_data_from_object(self, data_object, folder=None):
        """
        Stocke les données depuis un objet contenant les données.
        :param data_object: Objet contenant les données (liste, np.array, etc.).
        :param folder: Dossier où stocker le fichier (si data_is_in_file est True).
        """
        if self.in_file:
            if folder is None:
                raise ValueError("Folder must be specified for file-based storage.")
            self.file_path = os.path.join(folder, f"{self.data_id}.dat")
            with open(self.file_path, 'wb') as f:
                packed_data = struct.pack(f'{len(data_object)}{self.sample_format}', *data_object)
                f.write(packed_data)
        else:
            # Stockage en RAM
            self.data = data_object

    def read_chunked_data(self, chunk_size=1024):
        """
        Générateur qui lit les données chunk par chunk, soit depuis la RAM, soit depuis un fichier.
        :param chunk_size: Nombre de samples par chunk pour la lecture de fichiers.
        :yield: Un chunk de données à la fois.
        """
        if self.in_file and self.file_path:
            with open(self.file_path, 'rb') as f:
                while True:
                    chunk = f.read(chunk_size * self.sample_size)
                    if not chunk:
                        break
                    if self.sample_type == 'str':
                        yield chunk.decode('utf-8')  # Décoder les bytes en chaîne de caractères
                    else:
                        unpacked_chunk = struct.unpack(f'{len(chunk) // self.sample_size}{self.sample_format}', chunk)
                        yield unpacked_chunk
        else:
            for i in range(0, len(self.data), chunk_size):
                if self.sample_type == 'str':
                    yield ''.join(self.data[i:i + chunk_size])
                else:
                    yield self.data[i:i + chunk_size]

    def read_overlapped_chunked_data(self, chunk_size=1024, overlap=0):
        """
        Générateur qui lit les données chunk par chunk avec un chevauchement, soit depuis la RAM, soit depuis un fichier.
        :param chunk_size: Nombre de samples par chunk pour la lecture de fichiers.
        :param overlap: Chevauchement entre les chunks en % (entre 0 et 100).
        :yield: Un chunk de données à la fois.
        """
        step_size = int(chunk_size * (1 - overlap / 100))  # Taille du pas de lecture en fonction du chevauchement

        if self.in_file and self.file_path:
            with open(self.file_path, 'rb') as f:
                while True:
                    chunk = f.read(chunk_size * self.sample_size)
                    if not chunk:
                        break

                    if self.sample_type == 'str':
                        yield chunk.decode('utf-8')  # Décoder les bytes en chaînes de caractères
                    else:
                        unpacked_chunk = struct.unpack(f'{len(chunk) // self.sample_size}{self.sample_format}', chunk)
                        yield unpacked_chunk

                    f.seek(-int(overlap / 100 * chunk_size * self.sample_size), 1)  # Reculer pour chevauchement
        else:
            for i in range(0, len(self.data), step_size):
                if self.sample_type == 'str':
                    # Pour les chaînes de caractères, on retourne une partie de la chaîne avec chevauchement
                    yield ''.join(self.data[i:i + chunk_size])
                else:
                    # Pour les types numériques, on retourne un tableau de données
                    yield self.data[i:i + chunk_size]

    def read_data(self):
        """
        Lit toutes les données stockées, soit en RAM, soit depuis un fichier.
        :return: Les données stockées.
        """
        if self.in_file and self.file_path:
            with open(self.file_path, 'rb') as f:
                data = f.read()
                unpacked_data = struct.unpack(f'{len(data) // self.sample_size}{self.sample_format}', data)
                return unpacked_data
        else:
            return self.data

    def delete_data(self):
        """Supprime les données, soit en RAM, soit en supprimant le fichier sur le disque."""
        if self.in_file and self.file_path:
            os.remove(self.file_path)
        del self.data
        self.data = None

    def convert_ram_to_file(self, folder):
        """
        Convertit les données stockées en RAM en fichier.
        :param folder: Dossier où stocker le fichier.
        """
        if not self.in_file:
            if folder is None:
                raise ValueError("Folder must be specified for file-based storage.")
            self.file_path = os.path.join(folder, f"{self.data_id}.dat")

            with open(self.file_path, 'wb') as f:
                if self.sample_type == 'str':
                    # Pour les chaînes de caractères, il faut écrire les données caractère par caractère
                    packed_data = ''.join(self.data).encode('utf-8')  # Convertir la chaîne en bytes
                    f.write(packed_data)
                else:
                    # Pour les autres types de données, on utilise struct.pack
                    packed_data = struct.pack(f'{len(self.data)}{self.sample_format}', *self.data)
                    f.write(packed_data)

            self.in_file = True
            del self.data
            self.data = None

    def convert_file_to_ram(self):
        """Convertit les données stockées dans un fichier en RAM."""
        if self.in_file and self.file_path:
            with open(self.file_path, 'rb') as f:
                data = f.read()
                self.data = struct.unpack(f'{len(data) // self.sample_size}{self.sample_format}', data)
            self.in_file = False
            self.file_path = None
        else:
            raise ValueError("File path is not set or data is already in RAM.")


# Générateur de données pour différents types (int32, int64, float32, float64)
def data_generator(data_type, num_samples, chunk_size):
    """
    Génère un générateur de données du type spécifié.
    :param data_type: Le type de données (int32, int64, float32, float64, str).
    :param num_samples: Nombre total d'échantillons à générer.
    :param chunk_size: Taille des chunks en nombre d'échantillons ou de caractères (pour str).
    :return: Générateur qui produit des chunks de données.
    """
    if data_type == 'int32':
        data = np.arange(0, num_samples, dtype=np.int32)
    elif data_type == 'int64':
        data = np.arange(0, num_samples, dtype=np.int64)
    elif data_type == 'float32':
        data = np.arange(0, num_samples, dtype=np.float32) * 1.1
    elif data_type == 'float64':
        data = np.arange(0, num_samples, dtype=np.float64) * 1.1
    elif data_type == 'str':
        data = ''.join(chr(65 + (i % 26)) for i in range(num_samples))  # Génère des caractères A-Z
    else:
        raise ValueError("Type de données non supporté")

    for i in range(0, num_samples, chunk_size):
        yield data[i:i + chunk_size]  # Retourne un chunk de taille définie


def test_data_methods():
    """Test des méthodes de la classe Data avec différents types et tailles de données."""

    print("---- Test des méthodes de la classe Data ----")

    data_types = ['int32', 'int64', 'float32', 'float64', 'str']
    num_samples = 1000
    chunk_size = 100
    overlap = 50  # Pour les tests de chevauchement

    for data_type in data_types:
        print(f"\nTest des méthodes pour le type de données : {data_type}")

        # Calcul de la taille en octets en fonction du type de données
        sample_size = {'int32': 4, 'int64': 8, 'float32': 4, 'float64': 8, 'str': 1}[data_type]
        data_size_in_bytes = num_samples * sample_size

        # Création de l'objet Data
        data_id = f"test_{data_type}"
        data_store = Data(data_id=data_id, data_type="SIGNAL", data_name=f"test_{data_type}",
                          data_size_in_bytes=data_size_in_bytes, num_samples=num_samples,
                          in_file=False, sample_type=data_type)

        # Vérification de la méthode _get_sample_format_and_size
        print(f"Test _get_sample_format_and_size pour {data_type}")
        sample_format, sample_size = data_store._get_sample_format_and_size(data_type)
        print(f"Sample format: {sample_format}, Sample size: {sample_size} octets")

        # Test de store_data_from_data_generator
        print(f"Test store_data_from_data_generator pour {data_type} (RAM)")
        generator = data_generator(data_type, num_samples, chunk_size)
        data_store.store_data_from_data_generator(generator)

        # Test de read_chunked_data (RAM)
        print(f"Test read_chunked_data pour {data_type} (RAM)")
        data_read = []
        for chunk in data_store.read_chunked_data(chunk_size):
            data_read.extend(chunk)
        print(f"Nombre de chunks lus : {len(data_read) // chunk_size}")

        # Test de read_overlapped_chunked_data (RAM)
        print(f"Test read_overlapped_chunked_data pour {data_type} (RAM, overlap {overlap}%)")
        overlapped_data_read = []
        for chunk in data_store.read_overlapped_chunked_data(chunk_size, overlap=overlap):
            overlapped_data_read.extend(chunk)
        print(f"Nombre de chunks lus avec chevauchement : {len(overlapped_data_read) // chunk_size}")

        # Test de read_data (RAM)
        print(f"Test read_data pour {data_type} (RAM)")
        full_data = data_store.read_data()
        print(f"Taille des données lues : {len(full_data)}")

        # Conversion RAM vers Fichier
        folder = "./test_files"
        print(f"Test convert_ram_to_file pour {data_type}")
        data_store.convert_ram_to_file(folder=folder)

        # Conversion Fichier vers RAM
        print(f"Test convert_file_to_ram pour {data_type}")
        data_store.convert_file_to_ram()

        # Test delete_data
        print(f"Test delete_data pour {data_type}")
        data_store.delete_data()
        print(f"Données supprimées : {'Aucune donnée' if data_store.data is None else 'Données présentes'}")

        # Re-test avec stockage en fichier
        print(f"Test store_data_from_data_generator pour {data_type} (Fichier)")
        generator = data_generator(data_type, num_samples, chunk_size)
        data_store.store_data_from_data_generator(generator, folder=folder)

        # Test de read_chunked_data (Fichier)
        print(f"Test read_chunked_data pour {data_type} (Fichier)")
        data_read = []
        for chunk in data_store.read_chunked_data(chunk_size):
            data_read.extend(chunk)
        print(f"Nombre de chunks lus (Fichier) : {len(data_read) // chunk_size}")

        # Test de read_overlapped_chunked_data (Fichier)
        print(f"Test read_overlapped_chunked_data pour {data_type} (Fichier, overlap {overlap}%)")
        overlapped_data_read = []
        for chunk in data_store.read_overlapped_chunked_data(chunk_size, overlap=overlap):
            overlapped_data_read.extend(chunk)
        print(f"Nombre de chunks lus avec chevauchement (Fichier) : {len(overlapped_data_read) // chunk_size}")

        # Test de read_data (Fichier)
        print(f"Test read_data pour {data_type} (Fichier)")
        full_data = data_store.read_data()
        print(f"Taille des données lues (Fichier) : {len(full_data)}")

        # Suppression des données
        print(f"Test delete_data (Fichier) pour {data_type}")
        data_store.delete_data()
        print(f"Données supprimées : {'Aucune donnée' if data_store.data is None else 'Données présentes'}")

    print("---- Fin des tests des méthodes de la classe Data ----")

def check_memory_leaks():
    """
    Teste les fuites de mémoire pour différents types de données en utilisant tracemalloc.
    """
    # Démarrer le suivi de la mémoire
    tracemalloc.start()

    try:
        print("\n--- Démarrage des tests de fuites de mémoire ---")

        # Liste des types de données à tester, incluant 'str'
        data_types = ['int32', 'int64', 'float32', 'float64', 'str']

        # Différentes tailles d'échantillons et tailles de chunk à tester
        for data_type in data_types:
            for num_samples in [1000, 10000, 100000]:
                for chunk_size in [10, 100, 1000]:
                    # Test avec stockage en RAM
                    print(f"\nTest mémoire pour {data_type}, {num_samples} samples, chunk_size {chunk_size} (RAM)")
                    test_data_storage(data_type, num_samples, chunk_size, use_file=False)

                    # Test avec stockage en fichier
                    print(f"Test mémoire pour {data_type}, {num_samples} samples, chunk_size {chunk_size} (Fichier)")
                    test_data_storage(data_type, num_samples, chunk_size, use_file=True)

        # Prendre un snapshot de la mémoire après les tests
        snapshot = tracemalloc.take_snapshot()

        # Statistiques des allocations de mémoire par ligne de code
        stats = snapshot.statistics('lineno')

        # Affichage des 10 plus grandes sources d'allocation de mémoire
        print("\n--- Statistiques des 10 plus grandes allocations de mémoire ---")
        for stat in stats[:10]:
            print(stat)

    finally:
        # Arrêter le suivi de la mémoire
        tracemalloc.stop()
        print("\n--- Fin des tests de fuites de mémoire ---")

def test_data_storage(data_type, num_samples, chunk_size, use_file):
    """ Teste le stockage et la restitution des données. """
    print(f"Testing {data_type} with {num_samples} samples and chunk size {chunk_size} (file storage: {use_file})")

    # Calcul de la taille en octets en fonction du type de données
    sample_size = {'int32': 4, 'int64': 8, 'float32': 4, 'float64': 8, 'str': 1}[data_type]
    data_size_in_bytes = num_samples * sample_size

    data_id = f"test_{data_type}"
    sample_type = data_type
    data_store = Data(data_id=data_id, data_type="SIGNAL", data_name=f"test_{data_type}",
                      data_size_in_bytes=data_size_in_bytes, num_samples=num_samples,
                      in_file=use_file, sample_type=sample_type)

    folder = "./test_files" if use_file else None
    if use_file and not os.path.exists(folder):
        os.makedirs(folder)

    generator = data_generator(data_type, num_samples, chunk_size)

    # Utiliser le bon stockage selon que les données viennent d'un générateur ou d'un objet
    if isinstance(generator, np.ndarray):
        data_store.store_data_from_object(np.array(list(data_generator(data_type, num_samples, chunk_size))),
                                          folder=folder)
    else:
        data_store.store_data_from_data_generator(data_generator(data_type, num_samples, chunk_size), folder=folder)

    # Lire les données stockées et les comparer aux données d'origine
    data_read = []
    for chunk in data_store.read_chunked_data(chunk_size):
        data_read.extend(chunk)

    # Générer les données initiales pour comparaison
    original_data = ''.join([chunk for chunk in data_generator(data_type, num_samples, chunk_size)]) \
        if data_type == 'str' else np.concatenate(
        [chunk for chunk in data_generator(data_type, num_samples, chunk_size)])

    # Comparaison des données lues et générées
    if data_type == 'str':
        if ''.join(data_read) == original_data:
            print(f"Data match for {data_type} (file: {use_file})")
        else:
            print(f"Data mismatch for {data_type} (file: {use_file})")
    elif np.issubdtype(original_data.dtype, np.floating):
        if np.allclose(original_data, data_read, rtol=1e-6, atol=1e-9):
            print(f"Data match for {data_type} (file: {use_file})")

def analyze_memory_leaks():
    """
    Analyse les fuites de mémoire en comparant les snapshots avant et après certaines opérations.
    """
    tracemalloc.start()

    # Capture du snapshot avant les opérations
    snapshot_before = tracemalloc.take_snapshot()

    # Effectuer des opérations, comme des tests de stockage et de suppression
    test_data_methods()

    # Capture du snapshot après les opérations
    snapshot_after = tracemalloc.take_snapshot()

    # Comparer les snapshots pour détecter les différences
    stats = snapshot_after.compare_to(snapshot_before, 'lineno')

    print("\n--- Comparaison des snapshots mémoire ---")
    for stat in stats[:10]:
        print(stat)

    tracemalloc.stop()

if __name__ == "__main__":
    test_data_methods()

    # Test avec différents types de données et stockage en fichier ou en RAM
    check_memory_leaks()
    analyze_memory_leaks()