# PyDataCore
A basic library that can manage signalprocessing data as a datapool ,it handles asynchronuous acces and chunk stream as well as direct ram storage 

## Data Class

The `Data` class is designed to manage data storage and retrieval for various types of data (e.g., `int32`, `int64`, `float32`, `float64`, `str`). It allows for storing data in either memory (RAM) or a file on disk, and offers methods for reading, writing, and converting data between RAM and file-based storage.

### Features
- Support for multiple data types: `int32`, `int64`, `float32`, `float64`, `str`
- Ability to store data in RAM or in files
- Chunk-based reading and writing for large datasets
- Support for overlapping chunks when reading data
- Conversion between RAM and file-based storage
- Memory management, including cleanup and data deletion

### Class Definition

#### Initialization
```python
def __init__(self, data_id, data_type, data_name, data_size_in_bytes, num_samples, in_file=False, sample_type='float'):
```
- **data_id**: Unique identifier for the data.
- **data_type**: Type of data (e.g., "temporal", "freq", etc.).
- **data_name**: Name of the data.
- **data_size_in_bytes**: Size of the data in bytes.
- **num_samples**: Number of samples in the data.
- **in_file**: Boolean indicating if the data is stored in a file or in memory.
- **sample_type**: Type of the data samples (`float32`, `float64`, `int32`, `int64`, `str`).

#### Methods

##### `_get_sample_format_and_size`
```python
def _get_sample_format_and_size(self, sample_type)
```
Returns the format (struct) and size in bytes for a given sample type.

##### `store_data_from_data_generator`
```python
def store_data_from_data_generator(self, data_generator, folder=None)
```
Stores data chunk by chunk from a data generator. The data can be stored in RAM or in a file (if `in_file=True`).

##### `store_data_from_object`
```python
def store_data_from_object(self, data_object, folder=None)
```
Stores data directly from a data object (e.g., list, numpy array). Can store in RAM or in a file.

##### `read_chunked_data`
```python
def read_chunked_data(self, chunk_size=1024)
```
Reads the data chunk by chunk. If stored in a file, reads from the file; otherwise, reads from RAM.

##### `read_overlapped_chunked_data`
```python
def read_overlapped_chunked_data(self, chunk_size=1024, overlap=0)
```
Reads the data chunk by chunk with overlap. Supports overlapping chunks to read portions of data multiple times.

##### `read_data`
```python
def read_data(self)
```
Reads all the data, either from RAM or from a file.

##### `delete_data`
```python
def delete_data(self)
```
Deletes the data, either from RAM or by deleting the file from disk.

##### `convert_ram_to_file`
```python
def convert_ram_to_file(self, folder)
```
Converts the data stored in RAM into a file and clears the data from RAM.

##### `convert_file_to_ram`
```python
def convert_file_to_ram(self)
```
Converts the data stored in a file back into RAM.

### Usage Examples

#### Example 1: Storing Data in RAM
```python
data_store = Data(data_id="test_int32", data_type="SIGNAL", data_name="test_data", 
                  data_size_in_bytes=4000, num_samples=1000, in_file=False, sample_type="int32")

data_gen = data_generator("int32", 1000, 100)
data_store.store_data_from_data_generator(data_gen)

## Reading data in chunks
for chunk in data_store.read_chunked_data(chunk_size=100):
    print(chunk)

## Delete data
data_store.delete_data()
```

#### Example 2: Storing Data in a File
```python
data_store = Data(data_id="test_float64", data_type="SIGNAL", data_name="test_data", 
                  data_size_in_bytes=8000, num_samples=1000, in_file=True, sample_type="float64")

data_gen = data_generator("float64", 1000, 100)
data_store.store_data_from_data_generator(data_gen, folder="./data_files")

## Convert back to RAM
data_store.convert_file_to_ram()

## Delete data
data_store.delete_data()
```

#### Example 3: Reading Data with Overlapping Chunks
```python
data_store = Data(data_id="test_str", data_type="SIGNAL", data_name="test_data", 
                  data_size_in_bytes=1000, num_samples=1000, in_file=False, sample_type="str")

data_gen = data_generator("str", 1000, 100)
data_store.store_data_from_data_generator(data_gen)

# Reading data with 50% overlap
for chunk in data_store.read_overlapped_chunked_data(chunk_size=100, overlap=50):
    print(chunk)
```

### Memory Management
The class handles memory management and can store large data sets efficiently by allowing conversion between RAM and file-based storage. Use the `delete_data()` method to clear data when it is no longer needed.

