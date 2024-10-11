
# PyDataCore

PyDataCore is a data management system designed to handle various types of data efficiently. It provides an organized way to manage large datasets, both in RAM and files, using a `DataPool` that acts as an interface for handling complex data types. PyDataCore supports chunk-based storage and reading, which is ideal for handling large datasets that cannot fit into memory at once.

## Key Components

### Data Classes

The core of PyDataCore consists of several data classes, each designed to handle a specific type of data. These classes inherit from the `Data` base class, which provides common methods for managing data storage, reading, and deletion.

#### Data Class Overview:

- **FilePathListData**: Manages a list of file paths. Can store multiple file paths or a single path.
- **FolderPathListData**: Manages a list of folder paths. Can store multiple folder paths or a single path.
- **FileListData**: Manages a list of files. Can store multiple files or a single file.
- **TemporalSignalData**: Represents a temporal signal with attributes such as time step, unit, and values. This class supports chunked storage and reading.
- **FreqSignalData**: Represents a frequency signal with attributes like frequency step, unit, timestamp, and values. Supports chunked storage and reading.
- **FFTSData**: Stores a list of frequency signals (FreqSignalData) representing FFTs of temporal signals. It manages multiple frequency signals, each associated with a timestamp.
- **ConstantsData**: Manages a list of constant values (e.g., calibration data or fixed parameters).
- **StrData**: Stores string data, either a single string or a list of strings.
- **IntsData**: Manages a list of integer values.
- **FreqLimitsData**: Stores frequency limits, defined by frequency points and levels.
- **TempLimitsData**: Stores temporal limits, defined by time points and levels.

### ChunkableMixin

For data types that support chunk-based operations, PyDataCore provides the `ChunkableMixin` class. This mixin allows for storing and reading data in chunks, which is useful for large datasets that cannot be processed at once.

### FileRamMixin

For data types that can switch between RAM and file storage, the `FileRamMixin` provides methods to convert data from RAM to a file and vice versa. This is particularly useful when managing memory constraints for large datasets.

## The DataPool Interface

`DataPool` serves as the central registry for all data objects. It acts as the interface through which users interact with the various data classes, ensuring efficient management and tracking of data. 

### Key Features of DataPool:
- **Centralized Management**: `DataPool` provides a registry to manage and keep track of all data objects.
- **Data Locking**: Prevents concurrent access to data while it's being written or read.
- **Subscribers**: Allows multiple subscribers to read and acknowledge data, ensuring that data is only released or deleted once all subscribers have processed it.
- **Data Storage**: Supports both RAM and file storage options for data objects. Users can convert data between RAM and file storage depending on their needs.

### How to Use DataPool

To ensure proper management and access control, users should always interact with data via the `DataPool`. Direct manipulation of `Data` objects is discouraged, as `DataPool` ensures locking, protection, and cleanup of data through its registry system.

Here’s an example workflow using `DataPool`:

1. **Register Data**:
   - Register a new data object in the `DataPool` by specifying its type, name, and source ID.
   ```python
   pool = DataPool()
   data_id = pool.register_data(data_type=Data_Type.TEMPORAL_SIGNAL, data_name="Signal1", source_id="Source1", in_file=False)
   ```

2. **Store Data**:
   - Store data in the `DataPool`, ensuring that the correct source is providing the data and that the data is locked during the process.
   ```python
   signal_data = [0.1, 0.2, 0.3, 0.4]  # Example signal data
   pool.store_data(data_id, data_source=signal_data, source_id="Source1")
   ```

3. **Read Data**:
   - Retrieve the stored data from the `DataPool` after it has been successfully stored.
   ```python
   retrieved_data = pool.get_data(data_id, subscriber_id="Subscriber1")
   ```

4. **Chunked Data Access**:
   - If dealing with large datasets, use chunked reading to process data in smaller segments.
   ```python
   for chunk in pool.get_chunk_generator(data_id, chunk_size=1024, subscriber_id="Subscriber1"):
       print(chunk)
   ```

5. **Convert Data Storage**:
   - Convert data between RAM and file storage based on available resources and requirements.
   ```python
   pool.convert_data_to_file(data_id, folder="./data")
   pool.convert_data_to_ram(data_id)
   ```

6. **Delete Data**:
   - Remove data from the `DataPool` after ensuring that all subscribers have acknowledged the data.
   ```python
   pool.delete_data(data_id)
   ```

## Installation

To install PyDataCore, simply clone the repository and run the setup script:

```bash
git clone https://github.com/your-repo/PyDataCore.git
cd PyDataCore
python setup.py install
```

## Contributing

If you would like to contribute to PyDataCore, feel free to submit issues or pull requests on the project's GitHub repository.

## License

PyDataCore is licensed under the MIT License.
