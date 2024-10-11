
## PyDataCore: Detailed Class and Method Descriptions

### Overview
`PyDataCore` is a Python framework designed to handle various types of data (temporal signals, frequency signals, file paths, etc.) through a centralized `DataPool` interface. This framework supports chunk-based processing, memory management, and efficient file/RAM conversions.

The key feature is the `DataPool` class, which acts as the main interface for handling different `Data` objects. It manages locking mechanisms, subscribers, and provides tools to manage data storage in RAM or file.

---

## Detailed Class and Method Descriptions

### 1. Data Class
The `Data` class is the base class for all types of data. It handles basic attributes and methods common across all data types, such as `data_id`, `data_name`, `data_type`, `in_file`, and methods to store and retrieve data.

#### Methods:
- **`__init__`**: Initializes the object, including type, name, size, and whether the data is stored in RAM or a file.
- **`store_data_from_data_generator`**: Stores data chunk by chunk from a generator. If in a file, it writes data to the file; otherwise, it aggregates in RAM.
- **`store_data_from_object`**: Stores data from a list, array, or object, either in RAM or in a file.
- **`read_data`**: Reads the stored data, either from RAM or a file.
- **`delete_data`**: Deletes the data from either RAM or a file.

---

### 2. Data_Type Enum
Defines the different data types supported by `PyDataCore`. Each value corresponds to a specific data type, such as `FILE_PATHS`, `TEMPORAL_SIGNAL`, etc.

---

### 3. ChunkableMixin Class
A mixin to enable chunk-based reading and writing for compatible data types. This class provides additional functionality to handle data chunk by chunk.

#### Methods:
- **`store_data_from_data_generator`**: Stores data chunk by chunk, supporting both file and RAM storage.
- **`read_chunked_data`**: A generator method that reads data chunk by chunk.

---

### 4. FileRamMixin Class
A mixin for managing data conversions between RAM and file storage. It provides methods to convert data from RAM to a file and vice versa.

#### Methods:
- **`convert_ram_to_file`**: Converts data stored in RAM to a file.
- **`convert_file_to_ram`**: Converts data stored in a file back into RAM.

---

### 5. FilePathListData Class
This class inherits from `Data` and represents a list of file paths. The data is stored as strings.

#### Usage:
Ideal for scenarios where multiple file paths are processed.

---

### 6. FolderPathListData Class
Similar to `FilePathListData`, but handles folder paths instead of files.

#### Usage:
For managing directories.

---

### 7. FileListData Class
This class represents a list of files and inherits from `Data`.

#### Usage:
Suitable for managing a list of files in different contexts.

---

### 8. TemporalSignalData Class
A specialized class for storing temporal signals, like time-series data. This class also uses `ChunkableMixin` and `FileRamMixin` to handle chunked data and file-RAM conversions.

#### Methods:
- **`get_sampling_rate`**: Returns the sampling rate based on the time step.
- **`set_sampling_rate`**: Sets the sampling rate, modifying the time step.

#### Usage:
Best used when dealing with large temporal signals, like sensor data or time-series analysis.

---

### 9. FreqSignalData Class
This class manages frequency signals. It also inherits from `ChunkableMixin` and `FileRamMixin`.

#### Attributes:
- **`freq_step`**: Frequency step resolution.
- **`fmin`**: Minimum frequency in Hz.
- **`timestamp`**: Optional timestamp for the signal.

#### Usage:
Used in frequency domain analysis, like FFT results.

---

### 10. FFTSData Class
This class represents a collection of frequency signals (each being a `FreqSignalData` instance) that correspond to FFTs.

#### Methods:
- **`add_fft_signal`**: Adds a `FreqSignalData` object to the collection.

#### Usage:
For managing collections of FFT data derived from temporal signals.

---

### 11. ConstantsData Class
Represents a list of constant values, inheriting from `Data`.

#### Usage:
Useful when dealing with numerical constants.

---

### 12. StrData Class
Represents a string or a list of strings.

#### Usage:
For managing text data.

---

### 13. IntsData Class
Represents a list of integers.

#### Usage:
For managing numerical integer data.

---

### 14. FreqLimitsData Class
Represents frequency limit data, with associated units.

#### Usage:
Ideal for applications that define frequency bands with upper and lower limits.

---

### 15. TempLimitsData Class
Similar to `FreqLimitsData`, but for temporal limits.

#### Usage:
For applications dealing with time boundaries.

---

### 16. DataPool Class
The `DataPool` class serves as an interface to manage and store different `Data` objects. It acts as a central registry for handling data, providing better control, locking mechanisms, and managing subscribers.

#### Methods:
- **`register_data`**: Registers a new data object in the pool and associates it with a source. This method also locks the data until it's fully stored.
- **`store_data`**: Stores data into the pool after verifying the source and ensuring the object is locked for writing.
- **`add_subscriber`**: Adds a subscriber to the data, allowing it to read or process the data later.
- **`acknowledge_data`**: Marks the data as acknowledged by the subscriber. If all subscribers acknowledge, the data can be released.
- **`delete_data`**: Deletes the data from the pool if it’s not protected and after all subscribers have acknowledged it.
- **`convert_data_to_ram`**: Converts data from file storage to RAM.
- **`convert_data_to_file`**: Converts data from RAM to file storage.

#### Usage:
This is the primary interface for managing all `Data` objects. It ensures safe access, tracks data across multiple sources and subscribers, and provides chunk-based data processing.

### Example Usage of DataPool

```python
# Initialize a DataPool instance
pool = DataPool()

# Register a temporal signal
data_id = pool.register_data(
    data_type=Data_Type.TEMPORAL_SIGNAL,
    data_name='sensor_signal',
    source_id='sensor_01',
    protected=True
)

# Store data into the DataPool
temporal_data = [0.1, 0.2, 0.3, 0.4]  # Example data
pool.store_data(data_id, temporal_data, source_id='sensor_01')

# Get information about the data
info = pool.get_data_info(data_id)
print(info)

# Read the data
retrieved_data = pool.get_data(data_id, subscriber_id='subscriber_01')
print(retrieved_data)

# Convert data from RAM to file storage
pool.convert_data_to_file(data_id, folder='./storage')

# Delete data after acknowledgment
pool.delete_data(data_id)
```

In the example above, `DataPool` acts as the interface, allowing users to register, store, and retrieve data with full control over access and storage management. Each data object is properly managed by the pool, ensuring data consistency and security.
