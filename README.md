
# PyDataCore Project

## Overview

The DataPool project is designed to manage various types of data (e.g., temporal signals, frequency signals, file paths, etc.) and handle data storage in both RAM and file-based systems. This project enables dynamic registration, storage, and retrieval of data, allowing flexible handling of data chunks and memory management.

The system is capable of storing data either in RAM or as files, with support for large datasets, concurrent data access, and chunked data retrieval.

## Use Cases

1. **Data Registration and Storage**: Register different types of data (e.g., temporal signals, frequency signals, file paths, etc.), store them either in RAM or files, and retrieve them when needed.
2. **Data Chunking**: Stream large datasets in chunks for memory-efficient processing, with both overlapped and non-overlapped chunk retrieval methods.
3. **Concurrent Access Management**: Handle multiple subscribers accessing the same data with proper acknowledgment and locking mechanisms to prevent data conflicts.
4. **RAM and File Conversion**: Dynamically convert data between RAM and file storage based on memory needs.
5. **Data Deletion**: Efficiently delete data when all subscribers have acknowledged it, with protection mechanisms in place to prevent unauthorized deletions.

## Classes and Methods

### 1. `DataPool`
The `DataPool` class manages the registration, storage, and access to various types of data. It supports concurrent access, locking mechanisms, and acknowledgment tracking for data subscribers.

#### Attributes:
- `data_registry`: A DataFrame that keeps track of registered data, including the data ID, type, name, storage type (RAM or file), and the corresponding data object.
- `source_to_data`: A DataFrame that links sources to the registered data, including locking and protection statuses.
- `subscriber_to_data`: A DataFrame that tracks subscribers and their acknowledgment of data.

#### Methods:
- `register_data()`: Registers a new data entry in the DataPool.
- `store_data()`: Stores the data from a source (RAM or file).
- `get_data()`: Retrieves the data for a given subscriber.
- `add_subscriber()`: Adds a new subscriber to a data entry.
- `acknowledge_data()`: Acknowledges that a subscriber has read the data.
- `get_chunk_generator()`: Returns a generator to retrieve data in chunks.
- `convert_data_to_ram()`: Converts data stored in a file to RAM.
- `convert_data_to_file()`: Converts data stored in RAM to a file.
- `delete_data()`: Deletes data once all acknowledgments are received.

#### Example:
```python
pool = DataPool()
data_id = pool.register_data(Data_Type.TEMPORAL_SIGNAL, 'TempSignal', 'source_1', time_step=0.01, unit='V')
pool.store_data(data_id, [0.1, 0.2, 0.3], 'source_1')
retrieved_data = pool.get_data(data_id, 'subscriber_1')
```

---

### 2. `Data`
This is the base class for all data types, which includes attributes and methods for managing data stored in RAM or files.

#### Attributes:
- `data_id`: Unique identifier for the data.
- `data_name`: Name of the data.
- `data_size_in_bytes`: Size of the data in bytes.
- `num_samples`: Number of elements in the data (e.g., number of samples or items).
- `in_file`: Boolean flag indicating if the data is stored in a file or RAM.

#### Methods:
- `store_data_from_object()`: Stores data directly from an object (list, array, etc.).
- `store_data_from_data_generator()`: Stores data chunk by chunk using a generator.
- `read_data()`: Reads and returns the entire data from RAM or file.
- `delete_data()`: Deletes the data from RAM or the file system.

#### Example:
```python
data = TemporalSignalData(data_id="unique_id", data_name="TempSignal", data_size_in_bytes=100, number_of_elements=3, time_step=0.01, unit='V')
data.store_data_from_object([0.1, 0.2, 0.3])
data_read = data.read_data()
```

---

### 3. `ChunkableMixin`
A mixin class that allows for reading and storing data in chunks. Used for large datasets.

#### Methods:
- `store_data_from_data_generator()`: Stores data chunk by chunk from a generator.
- `read_chunked_data()`: Reads data in chunks, yielding each chunk iteratively.
- `read_specific_chunk()` : Retourne un chunk spécifique de données en accédant directement à sa position dans le fichier.

#### Example:
```python
data = TemporalSignalData(...)
for chunk in data.read_chunked_data(chunk_size=1024):
    process(chunk)
```

---

### 4. `FileRamMixin`
This mixin allows for dynamic conversion between RAM and file-based storage for data.

#### Methods:
- `convert_ram_to_file()`: Converts data stored in RAM to a file.
- `convert_file_to_ram()`: Converts data stored in a file to RAM.

#### Example:
```python
data = TemporalSignalData(...)
data.convert_ram_to_file('/path/to/folder')
data.convert_file_to_ram()
```

---

### 5. `Data_Type`
An enum that defines the different types of data supported by the DataPool system.

- `FILE_PATHS`: A list of file paths.
- `FOLDER_PATHS`: A list of folder paths.
- `TEMPORAL_SIGNAL`: A temporal signal with a sampling rate and unit.
- `FREQ_SIGNAL`: A frequency-domain signal with a frequency resolution and unit.
- `FFTS`: A collection of frequency-domain signals.
- `CONSTANTS`: A list of constant values.
- `STR`: A string.
- `INTS`: A list of integers.
- `FREQ_LIMITS`: Frequency limits with levels.
- `TEMP_LIMITS`: Temporal limits with levels.

---

### Data Subclasses

#### `FilePathListData`, `FolderPathListData`, `FileListData`:
Handle lists of file or folder paths and file lists.

#### `TemporalSignalData`:
Manages temporal signals with a sampling rate, unit, and values.

#### `FreqSignalData`:
Manages frequency signals with a frequency step, unit, and optional timestamp.

#### `FFTSData`:
Handles multiple frequency signals (FFTs) with common properties such as frequency step, unit, and timestamp.

#### `ConstantsData`, `StrData`, `IntsData`:
Handle constants, strings, and integers, respectively.

#### `FreqLimitsData`, `TempLimitsData`:
Manage frequency and temporal limits with associated units.

## Conclusion

The DataPool project is a flexible and scalable system for handling various data types, supporting both RAM and file-based storage with dynamic conversion between the two. The system is designed to efficiently manage large datasets, with support for chunked data retrieval and concurrent access management.
