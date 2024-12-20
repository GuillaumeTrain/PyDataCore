import asyncio
import struct
from enum import Enum
import numpy as np
import os
from termcolor import colored


class Data:
    def __init__(self, data_id, data_type, data_name, data_size_in_bytes, number_of_elements=None, in_file=False,
                 sample_type='float32'):
        """
        initialise une instance de données.
        :param data_id: identifiant unique de données.
        :param data_type: type de données (par exemple, temporal, freq, etc.).
        :param data_name: nom des données.
        :param data_size_in_bytes: taille des données en octets.
        :param number_of_elements: nombre d'éléments contenu dans la data par exemple nombre de samples ou nombre d'item dans une liste.
        :param in_file: indique si les données sont stockées dans un fichier ou en mémoire.
        :param sample_type: type de données (float32, float64, int32, int64, str).
        """
        self.data_id = data_id
        self.data_type = data_type
        self.data_name = data_name
        self.data_size_in_bytes = None
        self.num_samples = number_of_elements
        self.in_file = in_file
        self.sample_type = sample_type
        self.data = None
        self.file_path = None
        self.data_ready = asyncio.Event()  # État de disponibilité de la donnée
        self.sample_format, self.sample_size = self._get_sample_format_and_size(sample_type)
        self.mark_data_unready()

    def mark_data_ready(self):
        """Marque la donnée comme prête."""
        self.data_ready.set()

    def mark_data_unready(self):
        """Réinitialise l'état de disponibilité de la donnée."""
        self.data_ready.clear()
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
        if self.in_file:
            if folder is None:
                raise ValueError("Folder must be specified for file-based storage.")
            folder = os.path.abspath(folder)
            self.file_path = os.path.join(folder, f"{self.data_id}.dat")

            with open(self.file_path, 'wb') as f:
                total_samples = 0
                for chunk in data_generator:
                    if self.sample_type == 'str':
                        f.write(''.join(chunk).encode('utf-8'))
                    else:
                        packed_chunk = struct.pack(f'{len(chunk)}{self.sample_format}', *chunk)
                        f.write(packed_chunk)

                        # Mettre à jour la taille des données et le nombre de samples
                        total_samples += len(chunk)

                # Définir la taille totale des données en bytes et le nombre total de samples
                self.data_size_in_bytes = total_samples * self.sample_size
                self.num_samples = total_samples

        else:
            # Stockage en RAM
            self.data = []
            total_samples = 0
            for chunk in data_generator:
                self.data.extend(chunk)
                total_samples += len(chunk)

            # Mettre à jour les informations de taille
            self.data_size_in_bytes = total_samples * self.sample_size
            self.num_samples = total_samples

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
                if self.sample_type == 'str':
                    # Pour les chaînes de caractères, stocker chaque chaîne telle qu'elle (pas par caractère)
                    f.write("\n".join(data_object).encode('utf-8'))
                    # Taille des données pour une chaîne de caractères
                    self.data_size_in_bytes = len("\n".join(data_object).encode('utf-8'))
                else:
                    packed_data = struct.pack(f'{len(data_object)}{self.sample_format}', *data_object)
                    f.write(packed_data)
                    # Définir la taille totale des données en bytes
                    self.data_size_in_bytes = len(data_object) * self.sample_size
                    print(colored(f"self.data_size_in_bytes: {self.data_size_in_bytes}", "green"))
                    # Définir le nombre total de samples
                    self.num_samples = len(data_object)
                    print(colored(f"self.num_samples: {self.num_samples}", "green"))
        else:
            # Stockage en RAM
            if isinstance(data_object, list) and self.sample_type == 'str':
                self.data = data_object  # Stocker la liste de chaînes telle quelle
                # Calculer la taille des données en bytes pour les chaînes
                self.data_size_in_bytes = len("\n".join(self.data).encode('utf-8'))
                self.num_samples = len(self.data)  # Nombre de chaînes
                print(colored(f"Data stored in RAM: {self.data}", "green"))
            else:
                self.data = data_object
                # Calculer la taille des données en bytes pour les données numériques
                self.num_samples = len(data_object)  # Nombre d'échantillons
                self.data_size_in_bytes = self.num_samples * self.sample_size
                print(colored(f"Data stored in RAM: {self.data}", "green"))

    def read_data(self):
        """
        Lit toutes les données stockées, soit en RAM, soit depuis un fichier.
        :return: Les données stockées.
        """
        if self.in_file and self.file_path:
            with open(self.file_path, 'rb') as f:
                if self.sample_type == 'str':
                    # Lire les chaînes de caractères comme des lignes complètes
                    data = f.read().decode('utf-8').split("\n")
                else:
                    data = f.read()
                    unpacked_data = struct.unpack(f'{len(data) // self.sample_size}{self.sample_format}', data)
                    return unpacked_data
        else:
            if isinstance(self.data, list) and self.sample_type == 'str':
                print(colored(f"Data read from RAM: {self.data}", "green"))
                return self.data  # Renvoyer la liste de chaînes telle quelle

            else:
                print(colored(f"Data read from RAM: {self.data}", "green"))
                return self.data

    def delete_data(self):
        """Supprime les données, soit en RAM, soit en supprimant le fichier sur le disque."""
        if self.in_file and self.file_path:
            os.remove(self.file_path)
        del self.data
        self.data = None


class ChunkableMixin:

    def store_data_from_data_generator(self, data_generator, folder=None):
        if self.in_file:
            if folder is None:
                raise ValueError("Folder must be specified for file-based storage.")
            self.file_path = os.path.join(folder, f"{self.data_id}.dat")

            with open(self.file_path, 'wb') as f:
                total_samples = 0
                for chunk in data_generator:
                    if self.sample_type == 'str':
                        f.write(''.join(chunk).encode('utf-8'))
                    else:
                        packed_chunk = struct.pack(f'{len(chunk)}{self.sample_format}', *chunk)
                        f.write(packed_chunk)

                        # Mettre à jour la taille des données et le nombre de samples
                        total_samples += len(chunk)

                # Définir la taille totale des données en bytes et le nombre total de samples
                self.data_size_in_bytes = total_samples * self.sample_size
                print(f"Data size in bytes: {self.data_size_in_bytes}")
                self.num_samples = total_samples
                print(f"Number of samples: {self.num_samples}")
        else:
            # Stockage en RAM
            self.data = []
            total_samples = 0
            for chunk in data_generator:
                self.data.extend(chunk)
                total_samples += len(chunk)

            # Définir la taille totale des données en bytes et le nombre total de samples
            self.data_size_in_bytes = total_samples * self.sample_size
            print(f"Data size in bytes: {self.data_size_in_bytes}")
            self.num_samples = total_samples
            print(f"Number of samples: {self.num_samples}")

    def read_chunked_data(self, chunk_size=1024):
        """
        Retourne un Générateur qui lit les données chunk par chunk.
        :param chunk_size: Nombre de samples par chunk pour la lecture.
        :yield: Un chunk de données à la fois.
        """
        print(type(self))
        if self.data is None and not self.in_file:
            raise ValueError("Data is not loaded in RAM.")

        if self.in_file and self.file_path:
            with open(self.file_path, 'rb') as f:
                while True:
                    chunk = f.read(chunk_size * self.sample_size)
                    if not chunk:
                        break
                    if self.sample_type == 'str':
                        yield chunk.decode('utf-8')  # Décodage si type 'str'
                    else:
                        unpacked_chunk = struct.unpack(f'{len(chunk) // self.sample_size}{self.sample_format}', chunk)
                        yield unpacked_chunk
        else:
            for i in range(0, len(self.data), chunk_size):
                if self.sample_type == 'str':
                    # Conversion en str si les éléments sont en bytes
                    chunk = [item.decode('utf-8') if isinstance(item, bytes) else item for item in
                             self.data[i:i + chunk_size]]
                    yield ''.join(chunk)
                else:
                    yield self.data[i:i + chunk_size]

    def read_overlapped_chunked_data(self, chunk_size=1024, overlap=50):
        """
        Retourne un Générateur qui lit les données chunk par chunk avec un overlap.
        :param chunk_size: Nombre de samples par chunk pour la lecture.
        :param overlap: Nombre de samples pour
        :yield: Un chunk de données à la fois.
        """
        if self.in_file and self.file_path:
            with open(self.file_path, 'rb') as f:
                while True:
                    chunk = f.read(chunk_size * self.sample_size)
                    if not chunk:
                        break
                    else:
                        unpacked_chunk = struct.unpack(f'{len(chunk) // self.sample_size}{self.sample_format}', chunk)
                        yield unpacked_chunk
        else:
            for i in range(0, len(self.data), chunk_size):
                if self.sample_type == 'str':
                    yield ''.join(self.data[i:i + chunk_size])
                else:
                    yield self.data[i:i + chunk_size]

    def read_specific_chunk(self, chunk_index, chunk_size=1024):
        """
        Retourne un chunk spécifique de données en accédant directement à sa position dans le fichier.
        :param chunk_index: Index du chunk à lire.
        :param chunk_size: Taille du chunk (en nombre de samples).
        :return: Le chunk de données lu.
        """
        if self.in_file and self.file_path:
            # Obtenir la taille du fichier
            file_size = os.path.getsize(self.file_path)
            # print(f"File size: {file_size} bytes")

            # Recalculer le nombre total de samples en fonction de la taille du fichier
            num_samples_from_file = file_size // self.sample_size
            # print(
            #     f"num_samples_from_file: {num_samples_from_file},file_size: {file_size}, sample_size: {self.sample_size}")
            # print(f"Data size in bytes: {self.data_size_in_bytes}")
            with open(self.file_path, 'rb') as f:
                # Calculer la position du chunk dans le fichier
                offset = chunk_index * chunk_size * self.sample_size
                # print(f"Offset: {offset}, Chunk size: {chunk_size}, Sample size: {self.sample_size}")
                f.seek(offset)  # Se déplacer à l'offset calculé

                # Lire les données, mais s'assurer de ne pas lire plus que ce qui reste dans le fichier
                remaining_bytes = self.data_size_in_bytes - offset
                # print(
                #     f"self.data_size_in_bytes: {self.data_size_in_bytes}, Offset: {offset}, Remaining bytes: {remaining_bytes}")
                if remaining_bytes <= 0:
                    # print(f"Warning: No remaining bytes to read at chunk {chunk_index}.")
                    return []  # Retourner un tableau vide si aucun octet restant à lire

                bytes_to_read = min(chunk_size * self.sample_size, remaining_bytes)

                # print(f"Offset: {offset}, Bytes to read: {bytes_to_read}, Remaining bytes: {remaining_bytes}")

                chunk_data = f.read(bytes_to_read)
                # print(f"Chunk {chunk_index}: Read {len(chunk_data)} bytes.")
                # Décoder les données en fonction de leur type
                if self.sample_type == 'str':
                    return chunk_data.decode('utf-8')
                else:
                    return struct.unpack(f'{len(chunk_data) // self.sample_size}{self.sample_format}', chunk_data)
        else:
            raise ValueError("Data is not stored in a file or file path is missing.")


class FileRamMixin:
    def convert_ram_to_file(self, folder):
        """
        Convertit les données stockées en RAM en fichier.
        :param folder: Dossier où stocker le fichier.
        """
        if not self.in_file:
            if folder is None:
                raise ValueError("Folder must be specified for file-based storage.")
            self.file_path = os.path.abspath(folder)
            print(f"File path: {self.file_path}")
            # si le dossier n'existe pas on le crée
            if not os.path.exists(folder):
                os.makedirs(folder)
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
            # remove file
            os.remove(self.file_path)
            self.file_path = None
        else:
            raise ValueError("File path is not set or data is already in RAM.")


class Data_Type(Enum):
    # a stocker systematiquement en ram
    FILE_PATHS = 0  # une liste de chemins de fichiers (doit pouvoir supporter une liste de chemins ou un seul chemin)
    FOLDER_PATHS = 1  # une liste de chemins de dossiers (doit pouvoir supporter une liste de dossiers ou un seul dossier)
    FILE_LIST = 2  # une liste de fichiers (doit pouvoir supporter une liste de fichiers ou un seul fichier)
    FREQ_LIMIT = 5  # une liste de points de fréquence (float32) et de niveau (float32) pour définir les limites d'une bande de fréquence et un nom commun et une unité commune (comporte au moins 2 points en fréquence avec un niveau associé)
    TEMP_LIMIT = 6  # une liste de points de temps (float32) et de niveau (float32) pour définir les limites d'une bande de temps et un nom commun et une unité commune(comporte au moins 2 points temporels avec un niveau associé)
    CONSTANTS = 8  # une liste de valeur constante (float32) avec leur nom (doit pouvoir supporter une liste de constantes ou une seule constante)
    STR = 9  # une chaîne de caractères avec son nom
    INTS = 10  # une liste d'entiers avec leurs noms (doit pouvoir supporter une liste d'entier ou un seul entier)
    # a stocker en ram ou en fichier
    TEMPORAL_SIGNAL = 3  # un signal temporel défini par son nom , sa résolution (time_step),le temps minimum en seconde (float32) par défault a 0, son unité (V, A, etc.) et ses valeurs (liste de valeurs en float32) si stoqué en ram ou un chemin de fichier si stocké en fichier
    FREQ_SIGNAL = 4  # un signal fréquentiel défini par son nom , sa résolution (freq_step),la fréquence minimum en Hz (float32) et par défaut a 0un timestamp (float32 optionnel par défaut a 0), son unité (V, A, etc.) et ses valeurs (liste de valeurs en float32) si stoqué en ram ou un chemin de fichier si stocké en fichier
    FFTS = 7  # une liste de FREQ_SIGNALs avec un nom commun , une unité commune , une résolution fréquentielle commune, une fréquence min commune , une unité commune(V,A,etc), chaque FREQ_SIGNAL est un FFT d'un TEMPORAL_SIGNAL et possède un timestamp (float32) correspondant au millieu de la fenêtre temporelle pour laquelle la FFT a été calculés


class FilePathListData(Data):
    def __init__(self, data_id, data_name, data_size_in_bytes, number_of_elements=1, in_file=False):
        super().__init__(data_id, Data_Type.FILE_PATHS, data_name, data_size_in_bytes, number_of_elements, in_file,
                         sample_type='str')


class FolderPathListData(Data):
    def __init__(self, data_id, data_name, data_size_in_bytes, number_of_elements=1, in_file=False):
        super().__init__(data_id, Data_Type.FOLDER_PATHS, data_name, data_size_in_bytes, number_of_elements, in_file,
                         sample_type='str')


class FileListData(Data):
    def __init__(self, data_id, data_name, data_size_in_bytes, number_of_elements=1, in_file=False):
        super().__init__(data_id, Data_Type.FILE_LIST, data_name, data_size_in_bytes, number_of_elements, in_file,
                         sample_type='str')


class TemporalSignalData(Data, ChunkableMixin, FileRamMixin):
    def __init__(self, data_id, data_name, data_size_in_bytes, number_of_elements, time_step, unit, tmin=0.0,
                 in_file=False):
        super().__init__(data_id, Data_Type.TEMPORAL_SIGNAL, data_name, data_size_in_bytes, number_of_elements, in_file,
                         sample_type='float32')
        self.dt = time_step
        self.unit = unit
        self.tmin = tmin  # temps minimum (par défaut à 0)

    def get_sampling_rate(self):
        return 1 / self.dt

    def set_sampling_rate(self, sampling_rate):
        self.dt = 1 / sampling_rate


class FreqSignalData(Data, ChunkableMixin, FileRamMixin):
    def __init__(self, data_id, data_name, data_size_in_bytes, number_of_elements, freq_step, unit, fmin=0.0,
                 timestamp=0.0, in_file=False):
        super().__init__(data_id, Data_Type.FREQ_SIGNAL, data_name, data_size_in_bytes, number_of_elements, in_file,
                         sample_type='float32')
        self.df = freq_step
        self.unit = unit
        self.fmin = fmin  # fréquence minimum (par défaut à 0)
        self.timestamp = timestamp  # timestamp optionnel (par défaut à 0)


class FFTSData(Data):
    def __init__(self, data_id, data_name, data_size_in_bytes, number_of_elements, freq_step, fmin, unit, datapool=None,
                 in_file=False):
        """
        Classe pour les données FFTS, stocke les data_id des objets FreqSignalData et utilise un DataPool pour
        accéder aux objets complets.
        """
        super().__init__(data_id, Data_Type.FFTS, data_name, data_size_in_bytes, number_of_elements, in_file,
                         sample_type='float32')
        self.df = freq_step
        self.fmin = fmin
        self.unit = unit
        self.data = []  # Liste des data_id des objets FreqSignalData
        self.datapool = datapool  # Référence au DataPool pour récupérer les objets FreqSignalData

    def add_fft_signal(self, fft_signal):
        """
        Ajoute un signal FFT en stockant uniquement son data_id, vérifie que l'objet est bien une instance de
        FreqSignalData.
        """
        if not isinstance(fft_signal, FreqSignalData):
            raise ValueError("L'élément ajouté doit être une instance de FreqSignalData")

        self.data.append(fft_signal.data_id)

    @property
    def fft_signals(self):
        """
        Récupère les objets FreqSignalData à partir de leurs data_id en interrogeant le DataPool.
        """
        return [self.datapool.get_data_info(data_id)['data_object'].values[0] for data_id in self.data]

    @property
    def fft_ids(self):
        """
        Récupère les objets FreqSignalData à partir de leurs data_id en interrogeant le DataPool.
        """
        return self.data


class ConstantsData(Data):
    def __init__(self, data_id, data_name, data_size_in_bytes, number_of_elements, in_file=False):
        super().__init__(data_id, Data_Type.CONSTANTS, data_name, data_size_in_bytes, number_of_elements, in_file,
                         sample_type='float32')


class StrData(Data):
    def __init__(self, data_id, data_name, data_size_in_bytes, number_of_elements, in_file=False):
        super().__init__(data_id, Data_Type.STR, data_name, data_size_in_bytes, number_of_elements, in_file,
                         sample_type='str')

    def store_data_from_object(self, data_object, folder=None):
        if isinstance(data_object, str):
            self.data = str(data_object)  # Stocker la chaîne entière
        else:
            raise ValueError("Expected a string for StrData")

    def read_data(self):
        if self.in_file and self.file_path:
            with open(self.file_path, 'r') as f:
                return f.read()  # Lire tout le contenu du fichier en tant que chaîne
        else:
            return str(self.data)  # Retourner la chaîne stockée


class IntsData(Data):
    def __init__(self, data_id, data_name, data_size_in_bytes, number_of_elements, in_file=False):
        super().__init__(data_id, Data_Type.INTS, data_name, data_size_in_bytes, number_of_elements, in_file,
                         sample_type='int32')


class FreqLimitsData(Data):
    def __init__(self, data_id, data_name, data_size_in_bytes, number_of_elements, unit, in_file=False):
        super().__init__(data_id, Data_Type.FREQ_LIMIT, data_name, data_size_in_bytes, number_of_elements, in_file,
                         sample_type='float32')
        self.unit = unit
        self.data = []  # Liste de tuples (fréquence, niveau limite)
        self.interpolation_type = None
        self.freq_min = None
        self.freq_max = None

    def set_interpolation_type(self, interpolation_type):
        """
        Définit le type d'interpolation pour les limites de fréquence : 'linear' ou 'log'.
        """
        if interpolation_type not in ('linear', 'log'):
            raise ValueError("Interpolation type must be either 'linear' or 'log'.")
        self.interpolation_type = interpolation_type

    def add_limit_point(self, frequency, level):
        """
        Ajoute un point de limite avec une fréquence et un niveau.
        :param frequency: Fréquence (en Hz) pour le point de limite.
        :param level: Niveau limite correspondant à la fréquence.
        """
        # if self.data and frequency <= self.data[-1][0]:
        #     raise ValueError("Frequency points must be in strictly increasing order.")
        self.data.append((frequency, level))
        #récupérer les fréquences max et min
        if self.freq_min is None or frequency < self.freq_min:
            self.freq_min = frequency
        if self.freq_max is None or frequency > self.freq_max:
            self.freq_max = frequency

    def clear_limit_points(self):
        """
        Efface tous les points de limite de fréquence.
        """
        self.data.clear()

    def interpolate(self, freq):
        """
        Interpole le niveau limite pour une fréquence donnée en fonction du type d'interpolation spécifié.
        :param freq: La fréquence pour laquelle interpoler le niveau limite.
        :return: Le niveau limite interpolé.
        """
        if not self.data:
            raise ValueError("No frequency limit points have been added.")
        if self.interpolation_type is None:
            raise ValueError("Interpolation type is not set.")

        # Extraire les fréquences et niveaux limites
        frequencies, levels = zip(*self.data)

        if freq <= frequencies[0]:
            return levels[0]  # En dessous de la première fréquence, renvoyer le premier niveau
        elif freq >= frequencies[-1]:
            return levels[-1]  # Au-dessus de la dernière fréquence, renvoyer le dernier niveau

        # Interpolation entre les points
        for i in range(1, len(frequencies)):
            if frequencies[i] >= freq:
                f0, l0 = frequencies[i - 1], levels[i - 1]
                f1, l1 = frequencies[i], levels[i]
                if self.interpolation_type == 'linear':
                    # Interpolation linéaire
                    return l0 + (l1 - l0) * (freq - f0) / (f1 - f0)
                elif self.interpolation_type == 'log':
                    # Interpolation logarithmique
                    if f0 <= 0 or f1 <= 0:
                        raise ValueError("Frequencies must be positive for logarithmic interpolation.")
                    return l0 + (l1 - l0) * (np.log(freq / f0) / np.log(f1 / f0))

        raise ValueError("Interpolation failed. Frequency range not found.")


class TempLimitsData(Data):
    def __init__(self, data_id, data_name, data_size_in_bytes, number_of_elements, unit, in_file=False):
        """
        Initializes an instance of TempLimitsData.

        :param data_id: Unique identifier for the data.
        :param data_name: Name of the data.
        :param data_size_in_bytes: Size of the data in bytes.
        :param number_of_elements: Number of elements (points) in the data.
        :param unit: Unit of the limit values (e.g., V, A).
        :param in_file: Whether the data is stored in a file or in RAM.
        """
        super().__init__(data_id, Data_Type.TEMP_LIMIT, data_name, data_size_in_bytes, number_of_elements, in_file,
                         sample_type='float32')
        self.unit = unit
        self.data = []  # List of tuples (level, transparency_time, release_time)
        self.time_min = None
        self.time_max = None

    def add_limit_point(self, level, transparency_time, release_time):
        """
        Adds a limit point to the temporal limits data.

        :param level: Level of the limit.
        :param transparency_time: Transparency time of the limit.
        :param release_time: Release time of the limit.
        """
        if self.data and transparency_time <= self.data[-1][1]:
            raise ValueError("Transparency times must be in strictly increasing order.")

        self.data.append((level, transparency_time, release_time))

        # Update minimum and maximum time ranges
        if self.time_min is None or transparency_time < self.time_min:
            self.time_min = transparency_time
        if self.time_max is None or release_time > self.time_max:
            self.time_max = release_time

    def clear_limit_points(self):
        """Clears all limit points from the temporal limits data."""
        self.data.clear()
        self.time_min = None
        self.time_max = None

    def get_limits_in_range(self, start_time, end_time):
        """
        Retrieves all limit points within a specified time range.

        :param start_time: Start time of the range.
        :param end_time: End time of the range.
        :return: List of limit points (level, transparency_time, release_time) within the specified range.
        """
        if start_time > end_time:
            raise ValueError("Start time must be less than or equal to end time.")

        # Filter data points based on the specified time range
        limits_in_range = [
            (level, transparency_time, release_time)
            for level, transparency_time, release_time in self.data
            if transparency_time >= start_time and release_time <= end_time
        ]

        return limits_in_range


# Obsolète Générateur de données pour différents types (int32, int64, float32, float64)
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
