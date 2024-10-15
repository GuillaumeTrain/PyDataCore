# Fonctions de test
from tabulate import tabulate

from DataCore.data import data_generator, Data_Type
from DataCore.datapool import DataPool

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



if __name__ == "__main__":
    test_datapool()
    test_datapool_all_data_types()

    print("All tests passed")
