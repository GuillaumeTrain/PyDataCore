from src.PyDataCore import DataPool, TempLimitsData, Data_Type
from tabulate import tabulate

# Créer une instance de DataPool
data_pool = DataPool()

# Enregistrer une instance de TempLimitsData dans le DataPool
temp_limits_data_id = data_pool.register_data(
    data_type=Data_Type.TEMP_LIMIT,
    data_name="Temperature Limits",
    source_id="source1",
    protected=True,
    data_size_in_bytes=1024,
    number_of_elements=5,
    unit="°C",
    in_file=False
)

# Déverrouiller et récupérer l'objet TempLimitsData pour lui ajouter des points de limites
data_pool.unlock_data(temp_limits_data_id)
data_pool.add_subscriber(temp_limits_data_id, "sub1")
temp_limits_data = data_pool.get_data_object(temp_limits_data_id, "sub1")

# Ajouter des points de limite avec (level, transparency_time, release_time)
points_to_add = [
    (10.5, 1.0, 2.0),
    (15.0, 3.0, 4.0),
    (20.0, 5.0, 6.0),
    (25.0, 7.0, 8.0),
    (30.0, 9.0, 10.0)
]

for level, transparency_time, release_time in points_to_add:
    temp_limits_data.add_limit_point(level, transparency_time, release_time)

# Afficher les points ajoutés dans TempLimitsData
print("\nAll limit points added to TempLimitsData:")
print(tabulate(temp_limits_data.data, headers=["Level", "Transparency Time", "Release Time"], tablefmt="pretty"))

# Tester la méthode get_limits_in_range avec une plage de temps
start_time = 3.5
end_time = 8.5
limits_in_range = temp_limits_data.get_limits_in_range(start_time, end_time)

# Afficher les points de limite dans l'intervalle spécifié
print(f"\nLimit points within the range {start_time} to {end_time}:")
print(tabulate(limits_in_range, headers=["Level", "Transparency Time", "Release Time"], tablefmt="pretty"))

# Vérifier que les limites min et max sont correctes
print(f"\nMinimum Transparency Time: {temp_limits_data.time_min}")
print(f"Maximum Release Time: {temp_limits_data.time_max}")
