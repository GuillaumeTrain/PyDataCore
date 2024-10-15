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


if __name__ == "__main__":
    test_datapool()
    print("All tests passed")
