# RAG-to-SQL: A Trustworthy AI Data System
*This project demonstrates a systematic approach to building and evaluating a complex Text-to-SQL system. 
It builds user trust through transparency.*

## The problem
Business users need data to make decisions, but often lack the SQL skills and schema knowledge to move beyond pre-built BI dashboards. 
This creates a decision-making bottleneck, leaving critical hypotheses unexplored and assumptions unverified. 
While Text-to-SQL promises to democratize data access, standard models often fail on complex real-world queries.

## The solution
A multi-step RAG-to-SQL pipeline that breaks down complex query generation into a series of manageable tasks that performs better than a single LLM call. 
The core of this project is not just the pipeline itself, but the evaluation framework used to build and refine it. 
By systematically identifying why the system fails, we can create a data-driven roadmap for improvement.


# Key Features and Functionality
* **Evaluation Framework:** Diagnose the root cause of errors across a 9-point taxonomy.
* **Multi-Step RAG Pipeline:** Breaks down query generation into distinct phases: Query Interpretation, Logical Construction, and SQL Synthesis & Refinement.
* **Transparent UI:** A Streamlit application designed to build user trust by showing the critical information that is needed to trust the data, such as where did the data come from, and how are key metrics calculated.
* **Knowledge Base:** Ingest custom database schemas and business term definitions into a vector store to give the LLM context of your database setup.

# Performance Results
Baseline tests with a standard RAG pipeline yielded a ~4% execution accuracy on a challenging subset of the Spider 2.0 benchmark. 
This result was expected, but the simple accuracy score provided no guidance on how to improve.
After implementing the new multi-step architecture and optimizing, the system's performance improved significantly.

**Error Reduction (New Pipeline vs. Baseline with Gemini Flash):**

|Error Category	| Baseline Errors	| New Pipeline Errors	| Reduction|
|---------------|-----------------|---------------------|----------|
|Total Errors	| 113 |	96	| ~15% |
|Syntax Errors |	14 |	7 |	~50% |
|Aggregation Errors |	21 |	10	| ~52% |
|Join Errors	| 18 |	15 |	~17% |

# Tech Stack
- Python
- Jupyter Notebooks
- Streamlit
- Google Gemini
- Llama-index
- Ollama
- Chromadb

# How to get started
There are two main parts to running this project: populating the knowledge base with your db context and then running the user-facing Streamlit application.

## Step 1: Configure API Keys and/or Ollama
You will need to configure your Google Gemini API key. Alternatively you can configure Ollama with any model you wish.
API Keys are in gen_sql.py and all notebooks.

## Step 2: Populate RAG knowledgebase
The RAG system needs to know about your database schema and any specific business terminology. You must populate the vector store before running the main application.

1. **Prepare Your Data:** Add your database schema and business term files into the data/schemas and data/business_terms directories, respectively.
2. **Follow the Guide:** A detailed guide on the required file formats (DDL.csv, table JSON files, and business term .md files) is located in the ```application/data/``` directory. Please follow ```application/data/README.md``` to structure your files correctly.
4. **Run the Ingestion Script:** (from the application directory)
```python ingest_data.py```
## Step 3: Run the streamlit application
Once the knowledge base is populated, you can launch the client application.
```streamlit run client_app.py```

# Contact me
**Connect with me on Linkedin:** https://www.linkedin.com/in/michaelspowers/

**Email:** michael.sean.powers@gmail.com

*For professional inquiries, including job opportunities, please connect with me on Linkedin or send an email.*
