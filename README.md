# PyDataCore
A basic library that can manage signalprocessing data as a datapool ,it handles asynchronuous acces and chunk stream as well as direct ram storage 
Classe Data
La classe Data dans la bibliothèque PyDataCore permet de stocker et de lire des données efficacement, que ce soit en mémoire (RAM) ou dans un fichier sur disque. Elle est spécialement conçue pour gérer des données volumineuses en les stockant et en les récupérant sous forme de chunks afin de ne pas surcharger la mémoire.

# Data(data_id, data_type, data_name, data_size, data_is_in_file=False, sample_type='float')
Paramètres :
data_id (str) : Identifiant unique de la donnée.
data_type (str) : Type de la donnée (par exemple "SIGNAL").
data_name (str) : Nom de la donnée.
data_size (int) : Nombre total de samples.
data_is_in_file (bool) : Si True, les données seront stockées dans un fichier, sinon en RAM. Par défaut False.
sample_type (str) : Type de données (choix parmi float32, float64, int32, int64).
Méthodes
store_data(data_generator, folder=None)
Stocke les données chunk par chunk en fonction du type de stockage (RAM ou fichier).

data_generator (generator) : Générateur qui produit les chunks de données à stocker.
folder (str) : Chemin du dossier où stocker les fichiers si data_is_in_file est True. Si None, les données seront stockées en RAM.
Exemple d'utilisation :

python
Copier le code
data_store = Data(data_id="test_signal", data_type="SIGNAL", data_name="test", data_size=1000, data_is_in_file=True, sample_type='float32')
data_store.store_data(data_generator('float32', 1000, 100), folder="./test_files")
read_data(chunk_size=1024)
Lit les données chunk par chunk. Si les données sont stockées en RAM, elles sont lues directement depuis la mémoire. Si elles sont stockées dans un fichier, elles sont lues depuis le fichier.

chunk_size (int) : Nombre de samples par chunk lors de la lecture.
Exemple d'utilisation :

python
Copier le code
for chunk in data_store.read_data(chunk_size=100):
    print("Chunk:", chunk)
delete_data()
Supprime les données, soit de la RAM, soit du disque si elles sont stockées dans un fichier.

Exemple d'utilisation :

python
Copier le code
data_store.delete_data()
Exemple complet d'utilisation
Voici un exemple complet pour montrer comment utiliser la classe Data pour stocker des données, les lire et les comparer aux données d'origine.

python
Copier le code
import numpy as np
import os
from PyDataCore import Data

# Générateur de données pour différents types
def data_generator(data_type, num_samples, chunk_size):
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

# Tester le stockage et la lecture des données
def test_data_storage(data_type, num_samples, chunk_size, use_file):
    print(f"Testing {data_type} with {num_samples} samples and chunk size {chunk_size} (file storage: {use_file})")
    
    data_id = f"test_{data_type}"
    data_store = Data(data_id=data_id, data_type="SIGNAL", data_name=f"test_{data_type}", data_size=num_samples,
                      data_is_in_file=use_file, sample_type=data_type)

    folder = "./test_files" if use_file else None
    if use_file and not os.path.exists(folder):
        os.makedirs(folder)

    # Stocker les données
    data_store.store_data(data_generator(data_type, num_samples, chunk_size), folder=folder)

    # Lire les données stockées et vérifier leur correspondance avec les données d'origine
    data_read = []
    for chunk in data_store.read_data(chunk_size):
        data_read.extend(chunk)

    original_data = np.concatenate([chunk for chunk in data_generator(data_type, num_samples, chunk_size)])

    # Vérification avec une tolérance pour les flottants
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

    # Vérification des fichiers
    if use_file:
        if os.path.exists(f"{folder}/{data_id}.dat"):
            print(f"File created successfully for {data_type}")
        data_store.delete_data()
        if not os.path.exists(f"{folder}/{data_id}.dat"):
            print(f"File deleted successfully for {data_type}")

# Exemple de test
test_data_storage('float32', 1000, 100, use_file=True)
Ce code montre comment créer un générateur de données, les stocker en RAM ou sur le disque, les lire et vérifier leur intégrité en utilisant la classe Data de la bibliothèque PyDataCore.
