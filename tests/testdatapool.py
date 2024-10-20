# Fonctions de test
from tabulate import tabulate
import os
import numpy as np
from src.PyDataCore.datapool import DataPool
from src.PyDataCore.data import Data_Type


# test de l'initialisation de la classe DataPool
def test_datapool():
    pool = DataPool()
    assert pool.data_registry.empty
    assert pool.source_to_data.empty
    assert pool.subscriber_to_data.empty
    print("DataPool initialization passed")

    data_id = pool.register_data(
        Data_Type.TEMPORAL_SIGNAL,
        "TempSignal_1",
        "source_1",
        protected=False,
        in_file=False,
        time_step=0.01,  # Exemple de time_step
        unit="V"  # Exemple d'unité
    )

    assert not pool.data_registry.empty
    # Comparer le nom du type de donnée avec la chaîne 'TEMPORAL_SIGNAL'
    assert pool.data_registry.iloc[0]['data_type'] == Data_Type.TEMPORAL_SIGNAL.name
    assert pool.source_to_data.loc[pool.source_to_data['data_id'] == data_id, 'locked'].values[0]
    #affichage de tous les registres
    print(tabulate(pool.data_registry, headers='keys', tablefmt='psql'))
    print(tabulate(pool.source_to_data, headers='keys', tablefmt='psql'))
    print(tabulate(pool.subscriber_to_data, headers='keys', tablefmt='psql'))


def test_datapool_all_data_types():
    pool = DataPool()
    print("DataPool initialization passed")

    test_cases = [
        (Data_Type.FILE_PATHS, ["path/to/file1", "path/to/file2"], [], "FilePaths"),
        (Data_Type.FOLDER_PATHS, ["path/to/folder1", "path/to/folder2"], [], "FolderPaths"),
        (Data_Type.FILE_LIST, ["file1.txt", "file2.txt"], [], "FileList"),
        (Data_Type.TEMPORAL_SIGNAL, [0.1, 0.2, 0.3], [0.01, "V"], "TemporalSignal"),
        (Data_Type.FREQ_SIGNAL, [1.0, 2.0, 3.0], [0.1, "Hz"], "FreqSignal"),
        (Data_Type.FFTS, [], [0.1, 0.0, "V"], "FFTS"),
        (Data_Type.CONSTANTS, [42.0, 3.14], [], "Constants"),
        (Data_Type.STR, "This is a test string", [], "StringData"),
        (Data_Type.INTS, [1, 2, 3, 4], [], "IntsData"),
        (Data_Type.FREQ_LIMITS, [100.0, 200.0], ["dB"], "FreqLimits"),  # Ajout de "dB" comme unité
        (Data_Type.TEMP_LIMITS, [0.0, 5.0], ["s"], "TempLimits"),  # Ajout de "s" comme unité
    ]

    for data_type, data_value, args, data_name in test_cases:
        print(f"Testing {data_type} with data value: {data_value}...")

        if data_type == Data_Type.TEMPORAL_SIGNAL:
            data_id = pool.register_data(data_type, data_name, "source_1", protected=False, in_file=False, time_step=args[0], unit=args[1])
            pool.store_data(data_id, data_value, "source_1")
        elif data_type == Data_Type.FREQ_SIGNAL:
            data_id = pool.register_data(data_type, data_name, "source_1", protected=False, in_file=False, freq_step=args[0], unit=args[1])
            pool.store_data(data_id, data_value, "source_1")
        elif data_type == Data_Type.FFTS:
            data_id = pool.register_data(data_type, data_name, "source_1", protected=False, in_file=False, freq_step=args[0], fmin=args[1], unit=args[2])
            pool.store_data(data_id, data_value, "source_1")
        elif data_type == Data_Type.FREQ_LIMITS or data_type == Data_Type.TEMP_LIMITS:
            data_id = pool.register_data(data_type, data_name, "source_1", protected=False, in_file=False, unit=args[0])
            pool.store_data(data_id, data_value, "source_1")
        else:
            data_id = pool.register_data(data_type, data_name, "source_1", protected=False, in_file=False)
            pool.store_data(data_id, data_value, "source_1")

        pool.add_subscriber(data_id, "subscriber_1")
        retrieved_data = pool.get_data(data_id, "subscriber_1")

        # Comparer les données récupérées avec les données d'origine
        assert retrieved_data == data_value, f"Data mismatch for {data_name}: expected {data_value}, got {retrieved_data}"

    print("All data types tested successfully")


def test_file_storage_data_types():
    pool = DataPool()

    # Dossier de test
    test_folder = "test_folder"

    # Vérifier si le dossier existe, sinon le créer
    if not os.path.exists(test_folder):
        os.makedirs(test_folder)
        print(f"Directory {test_folder} created")

    # Test TEMPORAL_SIGNAL stored in file
    data_value = [0.1, 0.2, 0.3]
    data_name = "TempSignal_File"
    data_id = pool.register_data(Data_Type.TEMPORAL_SIGNAL, data_name, "source_1", protected=False, in_file=True, time_step=0.01, unit='V')

    # Ajouter un subscriber pour cette donnée
    pool.add_subscriber(data_id, "subscriber_1")

    # Stocker les données
    pool.store_data(data_id, data_value, "source_1", folder=test_folder)

    # Vérifier l'existence du fichier
    data_obj = pool.data_registry.loc[pool.data_registry['data_id'] == data_id, 'data_object'].values[0]
    assert data_obj.file_path is not None, f"File path for {data_name} should not be None"
    assert os.path.exists(data_obj.file_path), f"File for {data_name} does not exist at {data_obj.file_path}"

    # Lire les données
    retrieved_data = pool.get_data(data_id, "subscriber_1")

    # Comparer les données originales et récupérées
    np.testing.assert_allclose(retrieved_data, data_value, rtol=1e-5, atol=1e-8, err_msg=f"Data mismatch for {data_name}: expected {data_value}, got {retrieved_data}")
    print(f"Data comparison successful for {data_name}")

    # Suppression du fichier après test
    if os.path.exists(data_obj.file_path):
        os.remove(data_obj.file_path)
        print(f"File {data_obj.file_path} deleted after test")

    # Test FREQ_SIGNAL stored in file
    data_value = [1.0, 2.0, 3.0]
    data_name = "FreqSignal_File"
    data_id = pool.register_data(Data_Type.FREQ_SIGNAL, data_name, "source_1", protected=False, in_file=True, freq_step=0.1, unit='Hz')

    # Ajouter un subscriber pour cette donnée
    pool.add_subscriber(data_id, "subscriber_1")

    # Stocker les données
    pool.store_data(data_id, data_value, "source_1", folder=test_folder)

    # Vérifier l'existence du fichier
    data_obj = pool.data_registry.loc[pool.data_registry['data_id'] == data_id, 'data_object'].values[0]
    assert data_obj.file_path is not None, f"File path for {data_name} should not be None"
    assert os.path.exists(data_obj.file_path), f"File for {data_name} does not exist at {data_obj.file_path}"

    # Lire les données
    retrieved_data = pool.get_data(data_id, "subscriber_1")

    # Comparer les données originales et récupérées
    np.testing.assert_allclose(retrieved_data, data_value, rtol=1e-5, atol=1e-8, err_msg=f"Data mismatch for {data_name}: expected {data_value}, got {retrieved_data}")
    print(f"Data comparison successful for {data_name}")

    # Suppression du fichier après test
    if os.path.exists(data_obj.file_path):
        os.remove(data_obj.file_path)
        print(f"File {data_obj.file_path} deleted after test")


def test_chunk_storage_and_read():
    pool = DataPool()

    # Cas de test pour signal temporel avec chunk
    data_value = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    chunk_size = 3
    folder = "test_folder"

    # S'assurer que le dossier existe
    if not os.path.exists(folder):
        os.makedirs(folder)

    print(f"Testing Data_Type.TEMPORAL_SIGNAL with data value: {data_value}...")
    data_id = pool.register_data(Data_Type.TEMPORAL_SIGNAL, "TempSignal_Chunk_File", "source_1", in_file=True,
                                 time_step=0.01, unit="V")

    # Ajout d'un subscriber
    pool.add_subscriber(data_id, "subscriber_1")

    # Stockage par chunks
    pool.store_data(data_id, data_value, "source_1", folder=folder)

    print(f"Testing with chunk size {chunk_size} for both storage and read...")

    # Lecture des chunks
    read_chunks = list(pool.get_chunk_generator(data_id, chunk_size=chunk_size, subscriber_id="subscriber_1"))

    # Comparaison des chunks lus avec ceux d'origine
    stored_chunks = [data_value[i:i + chunk_size] for i in range(0, len(data_value), chunk_size)]

    # Comparer chaque chunk avec une tolérance
    for stored_chunk, read_chunk in zip(stored_chunks, read_chunks):
        assert np.allclose(stored_chunk, read_chunk, rtol=1e-5, atol=1e-8), \
            f"Chunk mismatch: expected {stored_chunk}, got {read_chunk}"

    print("Data comparison for chunked storage and read successful")

    # Supprimer le fichier après la lecture et l'acquittement
    file_path = os.path.join(folder, f"{data_id}.dat")
    if os.path.exists(file_path):
        print(f"File {file_path} still exists.")
    else:
        print(f"File {file_path} was deleted after all subscribers acknowledged.")


if __name__ == "__main__":
    # test_datapool()
    # test_datapool_all_data_types()
    # test_file_storage_data_types()
    test_chunk_storage_and_read()
    print("All tests passed")
