import os
import tracemalloc

import numpy as np

from src.PyDataCore import TemporalSignalData
from src.PyDataCore.data import Data, data_generator, Data_Type, ChunkableMixin, FileRamMixin


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
        data_object = Data(data_id=data_id,  data_name=f"test_{data_type}",
                          data_size_in_bytes=data_size_in_bytes, number_of_elements=num_samples,
                          in_file=False, data_type=data_type)

        # Vérification de la méthode _get_sample_format_and_size
        print(f"Test _get_sample_format_and_size pour {data_type}")
        sample_format, sample_size = data_object._get_sample_format_and_size(data_type)
        print(f"Sample format: {sample_format}, Sample size: {sample_size} octets")

        # Test de store_data_from_data_generator
        print(f"Test store_data_from_data_generator pour {data_type} (RAM)")
        generator = data_generator(data_type, num_samples, chunk_size)
        data_object.store_data_from_data_generator(generator)

        # Test de read_chunked_data (RAM)
        #atacher la méthode read_chunked_data dans data_object
        data_object.__class__ = type("ChunkableMixin", (data_object.__class__, ChunkableMixin), {})
        print(type(data_object))


        print(f"Test read_chunked_data pour {data_type} (RAM)")
        data_read = []
        for chunk in data_object.read_chunked_data(chunk_size):
            data_read.extend(chunk)
        print(f"Nombre de chunks lus : {len(data_read) // chunk_size}")

        # Test de read_overlapped_chunked_data (RAM)
        print(f"Test read_overlapped_chunked_data pour {data_type} (RAM, overlap {overlap}%)")
        overlapped_data_read = []
        for chunk in data_object.read_overlapped_chunked_data(chunk_size, overlap=overlap):
            overlapped_data_read.extend(chunk)
        print(f"Nombre de chunks lus avec chevauchement : {len(overlapped_data_read) // chunk_size}")

        # Test de read_data (RAM)
        print(f"Test read_data pour {data_type} (RAM)")
        full_data = data_object.read_data()
        print(f"Taille des données lues : {len(full_data)}")

        # Conversion RAM vers Fichier uniquement pour les data de type 'int32', 'int64', 'float32', 'float64'

        folder = "./test_files"
        print(f"Test convert_ram_to_file pour {data_type}")
        if data_type in ['int32', 'int64', 'float32', 'float64']:
            #attacher la méthode convert_ram_to_file dans data_object
            data_object.__class__ = type("FileRamMixin", (data_object.__class__, FileRamMixin), {})
            data_object.convert_ram_to_file(folder=folder)

            # Conversion Fichier vers RAM
            print(f"Test convert_file_to_ram pour {data_type}")
            data_object.convert_file_to_ram()

        # Test delete_data
        print(f"Test delete_data pour {data_type}")
        data_object.delete_data()
        print(f"Données supprimées : {'Aucune donnée' if data_object.data is None else 'Données présentes'}")

        # Re-test avec stockage en fichier
        print(f"Test store_data_from_data_generator pour {data_type} (Fichier)")
        generator = data_generator(data_type, num_samples, chunk_size)
        data_object.store_data_from_data_generator(generator, folder=folder)

        # Test de read_chunked_data (Fichier)
        print(f"Test read_chunked_data pour {data_type} (Fichier)")
        data_read = []
        for chunk in data_object.read_chunked_data(chunk_size):
            data_read.extend(chunk)
        print(f"Nombre de chunks lus (Fichier) : {len(data_read) // chunk_size}")

        # Test de read_overlapped_chunked_data (Fichier)
        print(f"Test read_overlapped_chunked_data pour {data_type} (Fichier, overlap {overlap}%)")
        overlapped_data_read = []
        for chunk in data_object.read_overlapped_chunked_data(chunk_size, overlap=overlap):
            overlapped_data_read.extend(chunk)
        print(f"Nombre de chunks lus avec chevauchement (Fichier) : {len(overlapped_data_read) // chunk_size}")

        # Test de read_data (Fichier)
        print(f"Test read_data pour {data_type} (Fichier)")
        full_data = data_object.read_data()
        print(f"Taille des données lues (Fichier) : {len(full_data)}")

        # Suppression des données
        print(f"Test delete_data (Fichier) pour {data_type}")
        data_object.delete_data()
        print(f"Données supprimées : {'Aucune donnée' if data_object.data is None else 'Données présentes'}")

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
                    dataram = test_data_storage(data_type, num_samples, chunk_size, use_file=False)

                    # Test avec stockage en fichier
                    print(f"Test mémoire pour {data_type}, {num_samples} samples, chunk_size {chunk_size} (Fichier)")
                    datafile = test_data_storage(data_type, num_samples, chunk_size, use_file=True)
                    dataram.delete_data()
                    datafile.delete_data()

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
    data_object = Data(data_id=data_id, data_type="SIGNAL", data_name=f"test_{data_type}",
                      data_size_in_bytes=data_size_in_bytes, number_of_elements=num_samples,
                      in_file=use_file, sample_type=sample_type)

    folder = "./test_files" if use_file else None
    if use_file and not os.path.exists(folder):
        os.makedirs(folder)

    generator = data_generator(data_type, num_samples, chunk_size)

    # Utiliser le bon stockage selon que les données viennent d'un générateur ou d'un objet
    if isinstance(generator, np.ndarray):
        data_object.store_data_from_object(np.array(list(data_generator(data_type, num_samples, chunk_size))),
                                          folder=folder)
    else:
        data_object.store_data_from_data_generator(data_generator(data_type, num_samples, chunk_size), folder=folder)

    # Lire les données stockées et les comparer aux données d'origine
    data_read = []
    #attacher la méthode read_chunked_data dans data_object
    data_object.__class__ = type("ChunkableMixin", (data_object.__class__, ChunkableMixin), {})
    for chunk in data_object.read_chunked_data(chunk_size):
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
    return data_object


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
