import os
import struct
import numpy as np
import os
import tracemalloc

class Data:
    def __init__(self, data_id, data_type, data_name, data_size, data_is_in_file=False, sample_type='float'):
        self.data_id = data_id
        self.data_type = data_type
        self.data_name = data_name
        self.data_size = data_size
        self.data_is_in_file = data_is_in_file
        self.sample_type = sample_type
        self.data = None
        self.file_path = None
        self.sample_format, self.sample_size = self._get_sample_format_and_size(sample_type)

    def _get_sample_format_and_size(self, sample_type):
        """
        Retourne le format struct et la taille en octets en fonction du type de sample.
        :param sample_type: Le type de données (float32, float64, int32, int64).
        :return: format_struct (char pour struct.pack/unpack), taille en octets.
        """
        if sample_type == 'float32':
            return 'f', 4  # 'f' pour float (32 bits)
        elif sample_type == 'float64':
            return 'd', 8  # 'd' pour double (64 bits)
        elif sample_type == 'int32':
            return 'i', 4  # 'i' pour int32 (32 bits)
        elif sample_type == 'int64':
            return 'q', 8  # 'q' pour int64 (64 bits)
        else:
            raise ValueError(f"Unsupported sample type: {sample_type}")

    def store_data(self, data_generator, folder=None):
        """
        Stocke les données chunk par chunk depuis un générateur.
        :param data_generator: Générateur fournissant des chunks de données (par exemple des flottants).
        :param folder: Dossier où stocker le fichier (si data_is_in_file est True).
        """
        if self.data_is_in_file:
            if folder is None:
                raise ValueError("Folder must be specified for file-based storage.")
            self.file_path = os.path.join(folder, f"{self.data_id}.dat")
            with open(self.file_path, 'wb') as f:
                # Récupère les chunks depuis le générateur et les écrit chunk par chunk
                for chunk in data_generator:
                    packed_chunk = struct.pack(f'{len(chunk)}{self.sample_format}', *chunk)
                    f.write(packed_chunk)
        else:
            # Stockage en RAM en collectant tous les chunks
            self.data = []
            for chunk in data_generator:
                self.data.extend(chunk)

    def read_data(self, chunk_size=1024):
        """
        Générateur qui lit les données chunk par chunk, soit depuis la RAM, soit depuis un fichier.
        :param chunk_size: Nombre de samples par chunk pour la lecture de fichiers.
        :yield: Un chunk de données à la fois.
        """
        if self.data_is_in_file and self.file_path:
            with open(self.file_path, 'rb') as f:
                while True:
                    chunk = f.read(chunk_size * self.sample_size)
                    if not chunk:
                        break
                    unpacked_chunk = struct.unpack(f'{len(chunk) // self.sample_size}{self.sample_format}', chunk)
                    yield unpacked_chunk
        else:
            for i in range(0, len(self.data), chunk_size):
                yield self.data[i:i+chunk_size]

    def delete_data(self):
        """Supprime les données, soit en RAM, soit en supprimant le fichier sur le disque."""
        if self.data_is_in_file and self.file_path:
            os.remove(self.file_path)
        self.data = None


# Générateur de données pour différents types (int32, int64, float32, float64)
def data_generator(data_type, num_samples, chunk_size):
    """
    Génère un générateur de données du type spécifié.
    :param data_type: Le type de données (int32, int64, float32, float64).
    :param num_samples: Nombre total d'échantillons à générer.
    :param chunk_size: Taille des chunks en nombre d'échantillons.
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
    else:
        raise ValueError("Type de données non supporté")

    for i in range(0, num_samples, chunk_size):
        yield data[i:i + chunk_size]


def test_data_storage(data_type, num_samples, chunk_size, use_file):
    """ Teste le stockage et la restitution des données. """
    print(f"Testing {data_type} with {num_samples} samples and chunk size {chunk_size} (file storage: {use_file})")

    data_id = f"test_{data_type}"
    sample_type = data_type
    data_store = Data(data_id=data_id, data_type="SIGNAL", data_name=f"test_{data_type}", data_size=num_samples,
                      data_is_in_file=use_file, sample_type=sample_type)

    folder = "./test_files" if use_file else None
    if use_file and not os.path.exists(folder):
        os.makedirs(folder)

    # Stocker les données
    data_store.store_data(data_generator(data_type, num_samples, chunk_size), folder=folder)

    # Lire les données stockées et les comparer aux données d'origine
    data_read = []
    for chunk in data_store.read_data(chunk_size):
        data_read.extend(chunk)

    # Générer les données initiales pour comparaison
    original_data = np.concatenate([chunk for chunk in data_generator(data_type, num_samples, chunk_size)])

    # Comparaison des données lues et générées (tolérance pour les flottants)
    if np.issubdtype(original_data.dtype, np.floating):
        if np.allclose(original_data, data_read, rtol=1e-6, atol=1e-9):
            print(f"Data match for {data_type} (file: {use_file})")
        else:
            print(f"Data mismatch for {data_type} (file: {use_file})")
    else:
        if np.array_equal(original_data, data_read):
            print(f"Data match for {data_type} (file: {use_file})")
        else:
            print(f"Data mismatch for {data_type} (file: {use_file})")

    # Vérification de l'existence du fichier
    if use_file:
        if os.path.exists(f"{folder}/{data_id}.dat"):
            print(f"File created successfully for {data_type}")
        else:
            print(f"File not created for {data_type}")

    # Suppression des données
    data_store.delete_data()

    if use_file:
        if not os.path.exists(f"{folder}/{data_id}.dat"):
            print(f"File deleted successfully for {data_type}")
        else:
            print(f"File not deleted for {data_type}")


def check_memory_leaks():
    tracemalloc.start()

    try:
        # Tester les différents types de données avec différentes tailles
        for data_type in ['int32', 'int64', 'float32', 'float64']:
            for num_samples in [1000, 10000, 100000]:
                for chunk_size in [10, 100, 1000]:
                    # Test avec stockage en RAM
                    test_data_storage(data_type, num_samples, chunk_size, use_file=False)
                    # Test avec stockage en fichier
                    test_data_storage(data_type, num_samples, chunk_size, use_file=True)

    finally:
        snapshot = tracemalloc.take_snapshot()
        stats = snapshot.statistics('lineno')

        # Affichage des 10 plus grandes sources d'allocation de mémoire
        print("\n--- Memory Allocation Statistics ---")
        for stat in stats[:10]:
            print(stat)

        tracemalloc.stop()


if __name__ == "__main__":
    check_memory_leaks()


if __name__ == "__main__":
    check_memory_leaks()