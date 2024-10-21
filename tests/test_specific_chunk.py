import os
import numpy as np
from src.PyDataCore.data import TemporalSignalData, FreqSignalData, ChunkableMixin


def print_chunk_info(chunk, chunk_type=""):
    """ Affiche les premières et dernières valeurs d'un chunk de données """
    if len(chunk) > 10:  # Si le chunk est trop grand, afficher seulement les premières et dernières valeurs
        print(f"{chunk_type} - Premieres valeurs: {chunk[:5]}, Dernieres valeurs: {chunk[-5:]}")
    else:
        print(f"{chunk_type} - Valeurs completes: {chunk}")


def test_read_specific_chunk_for_temporal_signal():
    print("Test: Lire des chunks de tailles différentes pour TemporalSignalData")

    # Créer un signal temporel fictif
    signal_length = 10500  # Signal non multiple des tailles de chunk testées
    signal_data = np.sin(np.linspace(0, 100, signal_length))  # Exemple de données
    data_id = "test_temporal_signal"

    # Créer une instance de TemporalSignalData en fichier
    temp_signal = TemporalSignalData(data_id, "Test Signal", data_size_in_bytes=signal_length * 4,
                                     number_of_elements=signal_length, time_step=0.01, unit="V", in_file=True)

    # Créer un répertoire temporaire pour stocker les données
    test_folder = "./test_data_folder"
    if not os.path.exists(test_folder):
        os.makedirs(test_folder)

    # Stocker les données dans le fichier
    temp_signal.store_data_from_object(signal_data, folder=test_folder)

    # Tester différentes tailles de chunk
    chunk_sizes_to_test = [1000, 2000, 3000,
                           1500]  # Différentes tailles, y compris non multiples du nombre total de samples
    for chunk_size in chunk_sizes_to_test:
        print(f"\nTesting chunk size: {chunk_size}")
        num_chunks = (signal_length + chunk_size - 1) // chunk_size  # Calculer le nombre de chunks à lire

        for chunk_index in range(num_chunks):
            specific_chunk = temp_signal.read_specific_chunk(chunk_index, chunk_size)

            # Données d'origine correspondant au chunk
            start_idx = chunk_index * chunk_size
            end_idx = min(start_idx + chunk_size, signal_length)
            expected_chunk = signal_data[start_idx:end_idx]

            # Afficher les informations des chunks
            print(f"Chunk #{chunk_index}")
            print_chunk_info(expected_chunk, chunk_type="Chunk d'origine")
            print_chunk_info(specific_chunk, chunk_type="Chunk lu")

            # Valider que les données correspondent
            np.testing.assert_array_almost_equal(specific_chunk, expected_chunk, decimal=6)

    # Nettoyage des fichiers temporaires
    temp_signal.delete_data()
    os.rmdir(test_folder)

    print("Test pour TemporalSignalData terminé avec succès\n")


def test_read_specific_chunk_for_freq_signal():
    print("Test: Lire des chunks de tailles différentes pour FreqSignalData")

    # Test similaire pour les signaux fréquentiels
    signal_length = 20500  # Signal non multiple des tailles de chunk testées
    freq_data = np.cos(np.linspace(0, 50, signal_length))  # Exemple de données
    data_id = "test_freq_signal"

    # Créer une instance de FreqSignalData en fichier
    freq_signal = FreqSignalData(data_id, "Test Freq Signal", data_size_in_bytes=signal_length * 4,
                                 number_of_elements=signal_length, freq_step=0.1, unit="Hz", in_file=True)

    test_folder = "./test_data_folder"
    if not os.path.exists(test_folder):
        os.makedirs(test_folder)

    # Stocker les données dans le fichier
    freq_signal.store_data_from_object(freq_data, folder=test_folder)

    # Tester différentes tailles de chunk
    chunk_sizes_to_test = [1500, 2500, 5000, 1234]  # Tailles de chunks variées et non multiples

    for chunk_size in chunk_sizes_to_test:
        print(f"\nTesting chunk size: {chunk_size}")
        num_chunks = (signal_length + chunk_size - 1) // chunk_size  # Calculer le nombre de chunks à lire

        for chunk_index in range(num_chunks):
            specific_chunk = freq_signal.read_specific_chunk(chunk_index, chunk_size)

            # Données d'origine correspondant au chunk
            start_idx = chunk_index * chunk_size
            end_idx = min(start_idx + chunk_size, signal_length)
            expected_chunk = freq_data[start_idx:end_idx]

            # Afficher les informations des chunks
            print(f"Chunk #{chunk_index}")
            print_chunk_info(expected_chunk, chunk_type="Chunk d'origine")
            print_chunk_info(specific_chunk, chunk_type="Chunk lu")

            # Valider que les données correspondent
            np.testing.assert_array_almost_equal(specific_chunk, expected_chunk, decimal=6)

    # Nettoyage des fichiers temporaires
    freq_signal.delete_data()
    os.rmdir(test_folder)

    print("Test pour FreqSignalData terminé avec succès\n")


if __name__ == "__main__":
    test_read_specific_chunk_for_temporal_signal()
    test_read_specific_chunk_for_freq_signal()
    print("Tous les tests sont passés avec succès")
