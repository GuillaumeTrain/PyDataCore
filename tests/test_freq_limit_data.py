# Création du DataPool
from src.PyDataCore import Data_Type, DataPool, FreqLimitsData

data_pool = DataPool()

# Enregistrement des données de limites de fréquence dans le DataPool
source_id = 'source1'
data_id = data_pool.register_data(
    data_type=Data_Type.FREQ_LIMIT,
    data_name='FreqLimitTest',
    source_id=source_id,
    unit='dB'
)

# Ajout des points de limite dans l'objet FreqLimitsData
data_obj : FreqLimitsData= data_pool.data_registry.loc[data_pool.data_registry['data_id'] == data_id, 'data_object'].values[0]
data_obj.add_limit_point(10, -20)
data_obj.add_limit_point(20, -10)
data_obj.add_limit_point(40, -5)

# Test de l'interpolation linéaire
data_obj.set_interpolation_type('linear')

# Stocker l'objet mis à jour dans le DataPool
data_pool.store_data(data_id, data_obj.data, source_id)

# Ajouter le subscriber
subscriber_id = 'sub1'
subscriber_id2 = 'sub2'
data_pool.add_subscriber(data_id, subscriber_id)
data_pool.add_subscriber(data_id, subscriber_id2)

# Récupérer les données de limites de fréquence depuis le DataPool
retrieved_data = data_pool.get_data(data_id, subscriber_id=subscriber_id)
print("Retrieved data (linear interpolation):", retrieved_data)

# Tester l'interpolation linéaire
freq_to_interpolate_linear = 15
interpolated_level_linear = data_obj.interpolate(freq_to_interpolate_linear)
print(f"Interpolated level at {freq_to_interpolate_linear} Hz (linear):", interpolated_level_linear)

# Reconfigurer pour l'interpolation logarithmique
data_obj.set_interpolation_type('log')

# Stocker les données mises à jour dans le DataPool avec interpolation logarithmique
data_pool.lock_data(data_id)
data_obj.clear_limit_points()
data_obj.add_limit_point(10, -20)
data_obj.add_limit_point(1000, -10)
data_pool.store_data(data_id, data_obj.data, source_id)
data_pool.unlock_data(data_id)

# Tester l'interpolation logarithmique
freq_to_interpolate_log = 100
interpolated_level_log = data_obj.interpolate(freq_to_interpolate_log)
print(f"Interpolated level at {freq_to_interpolate_log} Hz (logarithmic):", interpolated_level_log)
