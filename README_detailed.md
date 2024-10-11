
# PyDataCore

## Overview

**PyDataCore** is a Python framework designed to efficiently manage, store, and process various types of data, ranging from simple constants and lists to complex time-series and frequency signals. The core functionality revolves around the `DataPool` class, which acts as a centralized interface for managing different types of data in memory or files. Each type of data is encapsulated in its own specialized class that inherits from a base `Data` class.

### Why Use PyDataCore?

The framework provides an organized approach to handling data by using a `DataPool` that registers, stores, and retrieves data objects. It manages different sources, subscribers, and handles concurrency by using locking mechanisms. This allows for safe and efficient access to large datasets, whether they are stored in RAM or files, and facilitates working with chunked data.

## DataPool Class

The `DataPool` class serves as the main interface between the user and the data objects. It manages the registration, storage, and access control of various data objects. By using the `DataPool`, users can benefit from:

- Efficient handling of large datasets through chunked reading and writing.
- Support for both RAM and file-based storage, dynamically switching between the two as needed.
- A unified interface to access different types of data such as temporal signals, frequency signals, FFTs, and more.
- Subscriber and source management, including locking mechanisms to prevent race conditions during data storage and retrieval.

### DataPool Methods

#### `register_data`

Registers a new data object in the `DataPool`.

**Parameters:**
- `data_type`: The type of data to be registered (uses `Data_Type`).
- `data_name`: Name of the data object.
- `source_id`: The ID of the data's source.
- `protected`: If True, the data is protected from deletion.
- `in_file`: If True, the data will be stored in a file, otherwise in RAM.

**Returns:** The unique ID for the registered data.

#### `store_data`

Stores data into the `DataPool`. It handles the data based on whether it's stored in RAM or a file, and verifies the source ID to ensure only the source that registered the data can store it.

**Parameters:**
- `data_id`: The ID of the data to be stored.
- `data_source`: The data itself, can be a generator for chunked data or an array for in-memory storage.
- `source_id`: The ID of the source that is storing the data.
- `folder`: Optional, the folder where the file should be stored if the data is file-based.

#### `get_data`

Retrieves the full data stored in the `DataPool`.

**Parameters:**
- `data_id`: The ID of the data to retrieve.
- `subscriber_id`: The ID of the subscriber requesting the data.

**Returns:** The data stored for the given `data_id`.

#### `delete_data`

Deletes the data from the `DataPool` if it's not protected and all subscribers have acknowledged it.

**Parameters:**
- `data_id`: The ID of the data to delete.

---

## Data Class

The `Data` class serves as the base class for all types of data. It contains attributes and methods that are common across all data types, such as the ability to store data either in memory or in files.

### Attributes

- `data_id`: A unique identifier for the data.
- `data_type`: The type of data (e.g., `TEMPORAL_SIGNAL`, `FREQ_SIGNAL`).
- `data_name`: A user-friendly name for the data.
- `data_size_in_bytes`: The size of the data in bytes.
- `num_samples`: The number of elements or samples in the data.
- `in_file`: A boolean indicating whether the data is stored in a file.
- `sample_type`: The type of sample (e.g., `float32`, `int32`).

### Methods

#### `store_data_from_data_generator`

Stores the data chunk by chunk if the data is generated from a generator, either in RAM or a file depending on the `in_file` attribute.

**Parameters:**
- `data_generator`: The generator that provides the data chunks.
- `folder`: The folder where the data should be stored if it's in a file.

#### `store_data_from_object`

Stores the data directly from an object like a list or numpy array, either in RAM or a file.

**Parameters:**
- `data_object`: The object containing the data (e.g., list, numpy array).
- `folder`: The folder where the file should be stored if needed.

#### `read_data`

Reads all the stored data, either from RAM or a file.

**Returns:** The stored data.

---

## Data Types

### `Data_Type` Enum

The `Data_Type` enum defines all the possible types of data supported by the framework:

- `FILE_PATHS`: A list of file paths.
- `FOLDER_PATHS`: A list of folder paths.
- `FILE_LIST`: A list of files.
- `TEMPORAL_SIGNAL`: A time-domain signal.
- `FREQ_SIGNAL`: A frequency-domain signal.
- `FFTS`: A collection of FFT signals.
- `FREQ_LIMITS`: Frequency limits.
- `TEMP_LIMITS`: Temporal limits.
- `CONSTANTS`: A list of constants.
- `STR`: A string data type.
- `INTS`: A list of integers.

---

## Specialized Data Classes

### `TemporalSignalData`

Represents a temporal signal with attributes such as time step, unit, and minimum time.

#### Attributes

- `dt`: Time step (interval).
- `unit`: The unit of the signal (e.g., Volts, Amps).
- `tmin`: The minimum time (default is 0).

#### Methods

- `get_sampling_rate`: Returns the sampling rate of the signal.
- `set_sampling_rate`: Sets the sampling rate of the signal.

### `FreqSignalData`

Represents a frequency signal with attributes such as frequency step, unit, and minimum frequency.

#### Attributes

- `df`: Frequency step (interval).
- `unit`: The unit of the signal.
- `fmin`: The minimum frequency (default is 0).
- `timestamp`: An optional timestamp associated with the signal.

---

## Usage Example

Here is a basic usage example of the `PyDataCore` framework, focusing on the `DataPool` class:

```python
from PyDataCore import DataPool, Data_Type

# Create a new DataPool
pool = DataPool()

# Register a new temporal signal
data_id = pool.register_data(data_type=Data_Type.TEMPORAL_SIGNAL, data_name="MySignal", source_id="Source1")

# Store data in the pool (in RAM for this example)
data = [0.1, 0.2, 0.3, 0.4]
pool.store_data(data_id=data_id, data_source=data, source_id="Source1")

# Retrieve and read the data
retrieved_data = pool.get_data(data_id=data_id, subscriber_id="Subscriber1")
print(retrieved_data)

# Delete the data from the pool
pool.delete_data(data_id=data_id)
```

By using the `DataPool`, you can manage multiple types of data, store them efficiently in either RAM or files, and access them through a unified interface.

## Future Work

- Additional features for data visualization.
- Support for more complex data types like multidimensional arrays.
- Optimizations for large file handling.
