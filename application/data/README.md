# RAG-to-SQL System: Data Ingestion Guide

This document explains how to add new database schema information and business terms to the RAG-to-SQL system. The system uses ChromaDB as its vector store to store and retrieve metadata for generating SQL queries and providing relevant business context.

The ingestion process is handled by running ```python injest.py``` from the application directory.

## How to Add a New Database

To add information for a new database, you need to provide its schema metadata in a specific directory structure.

### 1. Directory Structure

All database schema information should be placed within the `SCHEMA_DIR` (as defined in ```injest.py```). Each database should have its own subdirectory within `SCHEMA_DIR`.

For a database named `your_new_database`, the structure should look like this:


|SCHEMA_DIR/your_new_database/ | |
|------------------------------|-|
| | DDL.csv | 
| | table1.json |
| | ...         |
| | tablen.json |

### 2. DDL.csv File
Inside your new database directory (`your_new_database/`), create a file named `DDL.csv`. 
This CSV file should contain DDL (Data Definition Language) statements for your tables. 

The `DDL.csv` file **must** have at least the following columns: 
* `table_name`: The exact name of the table.
* `DDL`: The full DDL statement for creating that table.

**Example `DDL.csv`:** 
```table_name,DDL employees,"CREATE TABLE employees (employee_id INT PRIMARY KEY, first_name VARCHAR(50), last_name VARCHAR(50), hire_date DATE);" departments,"CREATE TABLE departments (department_id INT PRIMARY KEY, department_name VARCHAR(100));```

### 3. Table-Specific JSON Files
For each table in your new database, create a separate JSON file within its database directory (e.g., your_new_database/table1.json). 

These JSON files provide detailed metadata for each table and its columns.

Each JSON file must contain the following keys:
* **table_name**: The exact name of the table this file describes.
* **column_names**: A list of column names in the table, in order.
* **column_types**: A list of data types for the corresponding columns.
* **description**: A list of descriptive comments for each column. If a column has no description, an empty string "" can be used.
* **sample_rows**: (Optional) A list of sample data rows for the table. This can help the RAG system understand typical data patterns. It's recommended to include a few representative rows. The system will only ingest the first 2 sample rows for brevity in the RAG context.

Example **employees.json**:
```
{
  "table_name": "employees",
  "column_names": ["employee_id", "first_name", "last_name", "hire_date", "department_id"],
  "column_types": ["INT", "VARCHAR(50)", "VARCHAR(50)", "DATE", "INT"],
  "description": [
    "Unique identifier for each employee.",
    "Employee's first name.",
    "Employee's last name.",
    "Date when the employee was hired.",
    "Foreign key linking to the departments table."
  ],
  "sample_rows": [
    [1, "John", "Doe", "2020-01-15", 101],
    [2, "Jane", "Smith", "2019-07-22", 102]
  ]
}
```


### 4. How to Add Business Terms
Business terms provide contextual information that can help the RAG-to-SQL system better understand natural language queries and generate more accurate SQL.
They define how your company defines 'retention', for example.

1. **Business Terms Directory**
Business term markdown files should be placed in the BIZ_TERMS_DIR (as defined in y in ```injest.py```).

| BIZ_TERMS_DIR/| |
|---------------|-|
| |Customer_Lifetime_Value.md |
| |Annual_Revenue.md |
| | ... |

3. **Markdown Files**
Each business term should be defined in a Markdown (.md) file. The content of the Markdown file will be ingested as a document (and chunked if too large) into the business terms vector store.
The filename (without the .md extension) will be used to derive the term_name metadata, with underscores replaced by spaces and title-cased (e.g., Customer_Lifetime_Value.md becomes "Customer Lifetime Value").


### 5. Running the Ingestion
Once you have prepared the DDL.csv and JSON files for your new database, run the injestion, ```python injest.py``` from the application directory.

This will:
* Delete the existing vector stores
* Injest all of the documents into the appropriate vector store


**Optionally, to verify the contents of the vector store, run ```python view_chroma.py``` from the application directory.**
