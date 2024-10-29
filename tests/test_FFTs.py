import tabulate
from src.PyDataCore import DataPool, FFTSData, Data_Type
import numpy as np

# Créer une instance de DataPool
data_pool = DataPool()

# Paramètres pour les signaux FFT
data_name_ffts = "FFT Signals Data"
data_size_ffts = 1024
number_of_elements = 5
freq_step = 0.1
fmin = 0.0
unit = "V"

# Créer un tableau de signaux temporels (sinusoïdes)
temp_signals = []
for i in range(number_of_elements):
    freq = 10 * (i + 1)
    t = np.linspace(0, 1, data_size_ffts)
    signal = np.sin(2 * np.pi * freq * t)
    temp_signals.append(signal)

# Calculer la FFT de chaque signal pour obtenir des signaux fréquentiels
freq_signals = [np.fft.fft(signal) for signal in temp_signals]

# Enregistrer l'objet FFTSData dans le DataPool
ffts_data_id = data_pool.register_data(
    data_type=Data_Type.FFTS,
    data_name=data_name_ffts,
    source_id="source1",
    protected=True,
    data_size_in_bytes=data_size_ffts,
    number_of_elements=number_of_elements,
    freq_step=freq_step,
    fmin=fmin,
    unit=unit,
    in_file=False
)
# Déverrouiller, récupérer l'objet FFTSData et ajouter le signal
data_pool.unlock_data(ffts_data_id)
# Ajouter un abonné
data_pool.add_subscriber(ffts_data_id, "sub1")

# Enregistrer chaque signal fréquentiel et les ajouter à FFTSData
for freq_signal in freq_signals:
    # Enregistrement du signal fréquentiel dans le DataPool
    data_id = data_pool.register_data(
        data_type=Data_Type.FREQ_SIGNAL,
        data_name=data_name_ffts,
        source_id="source1",
        protected=True,
        data_size_in_bytes=data_size_ffts,
        number_of_elements=data_size_ffts,
        freq_step=freq_step,
        fmin=fmin,
        unit=unit,
        in_file=False
    )
    data_pool.store_data(data_id=data_id, data_source=freq_signal, source_id="source1")
    data_pool.add_subscriber(data_id, "sub1")

    #afficher l'état du registre data_pool avec tabulate
    print(tabulate.tabulate(data_pool.data_registry, headers='keys', tablefmt='pretty'))

    ffts_data = data_pool.get_data_object(ffts_data_id, "sub1")
    print(f"Objet FFTSData: {ffts_data}")
    if isinstance(ffts_data, FFTSData):
        ffts_data.add_fft_signal(data_pool.get_data_object(data_id, "sub1"))
        print(f"Signal ajouté à FFTSData: {ffts_data.fft_signals}")
        print(f"Fft_signals_ids: {ffts_data.fft_ids}")
    else:
        print("Erreur : Impossible de récupérer l'objet FFTSData.")
