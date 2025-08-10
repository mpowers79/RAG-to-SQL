# File: prompts.py
# Description: prompts that are used by the agent
#  
#
# Copyright (c) 2025 Michael Powers
#
# Usage: to be used with streamlit app, not run directly
#   
# 
#


from llama_index.core.prompts import PromptTemplate

#########################################################################
#▗▄▄▖ ▗▄▄▖  ▗▄▖ ▗▖  ▗▖▗▄▄▖▗▄▄▄▖▗▄▄▖
#▐▌ ▐▌▐▌ ▐▌▐▌ ▐▌▐▛▚▞▜▌▐▌ ▐▌ █ ▐▌   
#▐▛▀▘ ▐▛▀▚▖▐▌ ▐▌▐▌  ▐▌▐▛▀▘  █  ▝▀▚▖
#▐▌   ▐▌ ▐▌▝▚▄▞▘▐▌  ▐▌▐▌    █ ▗▄▄▞▘
#########################################################################


TABLE_COLUMN_PROMPT_V3 = PromptTemplate(
    """Given the user question and the database schema context, identify the most relevant tables and columns needed to answer the question. 
    These tables and columns will be used in the SELECT, FROM and JOIN clauses.
    Focus on tables and columns that directly relate to the entities and operations mentioned in the query. Consider table relationships and how they are used for joins or filtering.

    Output your answer as a JSON object with 'tables' (list of table names) and 'columns' (list of 'table_name.column_name' strings) and 'reasoning' (string).

    --- Schema Context ---
    {schema_context}

    --- User Question ---
    {query_str}

    JSON Output:

    """
)

TABLE_COLUMN_PROMPT_V4 = PromptTemplate(
"""
You are an expert at analyzing database schemas to identify all necessary components to answer a user's question. Your task is to extract the complete list of tables and columns required to construct a SQL query.

Follow these steps to arrive at your answer:

Step 1: Deconstruct the User's Question
Break down the user's question into its core components:
- **Entities**: What are the main subjects? (e.g., customers, products, orders)
- **Metrics/Aggregations**: What is being calculated? (e.g., average sales, total count, max date)
- **Filters/Conditions**: What are the specific constraints? (e.g., status is 'delivered', date is in the last year)
- **Identifiers**: What specific keys or IDs are mentioned? (e.g., customer unique identifier, order ID)

Step 2: Map Components to the Schema
For each component identified in Step 1, map it to the specific tables and columns in the schema.

Step 3: Identify Join Paths
Review the list of required tables from Step 2. If the required columns exist across multiple tables, you MUST identify all tables needed to join them together. Trace the relationships (e.g., `tableA.id` -> `tableB.A_id`) to create a complete, connected graph of tables. A table is required if it contains a needed column OR if it is necessary to bridge two other required tables.

Step 4: Consolidate and Output
Based on your analysis in the previous steps, compile the final lists.
- The `tables` list must include every table identified in Step 2 and Step 3.
- The `columns` list must include every column identified in Step 2, formatted as 'table_name.column_name'.
- The `reasoning` field must contain a very concise version of your analysis from Steps 1, 2, and 3.

Output your final answer as a single JSON object.




--- Example ---
--- Schema Context ---
{
  "customers": [
    "customer_id (Primary Key)",
    "customer_unique_id"
  ],
  "orders": [
    "order_id (Primary Key)",
    "customer_id (Foreign Key to customers.customer_id)",
    "order_purchase_timestamp",
    "order_status"
  ],
  "order_items": [
    "order_id (Foreign Key to orders.order_id)",
    "price"
  ]
}

--- User Question ---
Calculate the average sales per order for each customer within distinct RFM segments, considering only 'delivered' orders. Use the customer unique identifier. Clearly define how to calculate Recency based on the latest purchase timestamp and specify the criteria for classifying RFM segments. The average sales should be computed as the total spend divided by the total number of orders. Please analyze and report the differences in average sales across the RFM segments

JSON Output:
```json
{ "tables": [ "customers", "orders", "order_items" ], "columns": [ "customers.customer_unique_id", "customers.customer_id", "orders.order_id", "orders.customer_id", "orders.order_purchase_timestamp", "orders.order_status", "order_items.order_id", "order_items.price" ], "reasoning": "Step 1: Deconstruct the User's Question:\n- Entities: Customers, Orders, Sales (RFM Segments are derived from these).\n- Metrics/Aggregations: Recency (MAX of purchase timestamp), Frequency (COUNT of orders), Monetary (SUM of price), and AVG sales per order.\n- Filters/Conditions: order_status = 'delivered'.\n- Identifiers: 'customer unique identifier'.\n\nStep 2: Map Components to the Schema:\n- 'customer unique identifier' is in the `customers` table (`customer_unique_id`).\n- Order details like `order_purchase_timestamp` and `order_status` are in the `orders` table.\n- Sales/spend data (`price`) is in the `order_items` table.\n- The count of orders uses `order_id` from the `orders` table.\n\nStep 3: Identify Join Paths:\nThe query requires columns from three different tables: `customers`, `orders`, and `order_items`. To link the customer's unique identifier (`customers`) to their spending (`order_items`), a join through the `orders` table is necessary. The path is `customers.customer_id` -> `orders.customer_id`, and `orders.order_id` -> `order_items.order_id`. Therefore, all three tables are essential for the query." }
```

--- End Example ---

--- New Request ---

--- Schema Context ---
{schema_context}

--- User Question ---
{query_str}


JSON Output:

"""
)


JOIN_PROMPT_V4 = PromptTemplate(
    """
Given the user question, the identified tables/columns, and the database schema, your task is to determine the necessary JOIN operations required to answer the query.

Your primary goal is to link the tables listed in the Identified Tables/Columns input.

1. Analyze the Identified Tables/Columns. If two or more tables are present, joins are required.
2. Consult the Schema Context to identify the primary and foreign key relationships that connect these tables.
3. Determine the most appropriate join_type. Use INNER for mandatory relationships. Use LEFT when the query implies you should include all records from the first table even if there's no match in the second (e.g., "show all customers and their orders, even if they have none").
4. Only generate the joins that are essential for connecting the required tables. Do not create unnecessary joins.


Produce a JSON object as your output with the following keys:

- `joins`: A list of objects, where each object defines a single join statement. If no joins are needed (i.e., only one table is used), provide an empty list []. Each object must have the following keys:
- `join_type`: The SQL join type (e.g., 'INNER', 'LEFT').
- `left_on`: The fully qualified column for the left side of the join (table.column).
- `right_on`: The fully qualified column for the right side of the join (table.column).
- `reasoning`: A brief explanation of why these specific joins and join types were chosen to link the tables for the user's query.




--- EXAMPLE 1 ---
User Question: "What are the start and end times of each meeting, as well as the corresponding client and staff details of the attendees?"

Schema Context:
Table: department
Columns: "Department_ID" int PRIMARY KEY, "Creation" text

Table: head
Columns: "head_ID" int PRIMARY KEY, "born_state" text

Table: management
Columns: "department_ID" int, "head_ID" int, FOREIGN KEY ("department_ID") REFERENCES `department`("Department_ID"), FOREIGN KEY ("head_ID") REFERENCES `head`("head_ID")

Identified Tables/Columns:

{
  "meetings": ["start_date_time", "end_date_time", "meeting_id", "client_id"],
  "clients": ["client_details", "client_id"],
  "staff": ["staff_details", "staff_id"],
  "staff_in_meetings": ["meeting_id", "staff_id"]
}

JSON Out:
```json
{
  "reasoning": "The user's query requires columns from three tables: meetings, clients, and staff. The 'meetings' and 'clients' tables can be joined directly on client_id. The 'meetings' and 'staff' tables cannot be joined directly and require the 'staff_in_meetings' linking table. All joins are INNER because we only care about meetings with associated clients and staff.",
  "joins": [
    {
      "join_type": "INNER",
      "left_on": "meetings.client_id",
      "right_on": "clients.client_id"
    },
    {
      "join_type": "INNER",
      "left_on": "meetings.meeting_id",
      "right_on": "staff_in_meetings.meeting_id"
    },
    {
      "join_type": "INNER",
      "left_on": "staff_in_meetings.staff_id",
      "right_on": "staff.staff_id"
    }
  ]
}
```

--- END OF EXAMPLE 1 ---

--- EXAMPLE 2 ---
User Question: "What are the distinct creation years of the departments managed by a secretary born in state 'Alabama'?"
Schema Context:

Table: department
Columns: "Department_ID" int PRIMARY KEY, "Creation" text

Table: head
Columns: "head_ID" int PRIMARY KEY, "born_state" text

Table: management
Columns: "department_ID" int, "head_ID" int, FOREIGN KEY ("department_ID") REFERENCES `department`("Department_ID"), FOREIGN KEY ("head_ID") REFERENCES `head`("head_ID")

Identified Tables/Columns:

{
  "department": ["Creation", "Department_ID"],
  "head": ["born_state", "head_ID"],
  "management": ["department_ID", "head_ID"]
}

JSON Out:
```json
{
  "reasoning": "The user's query requires columns from two main tables: 'department' for the creation year and 'head' for the born state. These tables are not directly linked. The 'management' table serves as a necessary linking table to connect them. INNER joins are used as we only need to consider departments that have a manager and managers who lead a department.",
  "joins": [
    {
      "join_type": "INNER",
      "left_on": "department.Department_ID",
      "right_on": "management.department_ID"
    },
    {
      "join_type": "INNER",
      "left_on": "management.head_ID",
      "right_on": "head.head_ID"
    }
  ]
}
```

--- END OF EXAMPLE 2 ---

--- New Request ---

--- Schema Context ---
{schema_context}

--- User Question ---
{query_str}

--- Identified Tables/Columns ---
{identified_tables_columns_json}


JSON Out:

    """
)




GROUPING_PROMPT_V3 = PromptTemplate(
"""
Given the user question and the available schema context, your task is to identify all necessary grouping columns and simple, single-column aggregation functions.

Analyze the user's intent to determine which columns are used for categorization (for the GROUP BY clause) and which columns require a mathematical or counting operation (for aggregate functions).

Focus on keywords such as "each", "every", "per", "total", "average", "count", "sum", "min", "max" to make your determination.

Produce a JSON object as your output with the following keys:

- `group_by_columns`: A list of strings representing the fully qualified column names (`table.column`) to be used in the `GROUP BY` clause. If no grouping is needed, provide an empty list `[]`.
- `aggregations`: A list of objects, where each object defines an aggregation. If no aggregations are needed, provide an empty list `[]`. Each object must have the following keys:
    - `function`: The SQL aggregate function to use (e.g., 'SUM', 'COUNT', 'AVG', 'MAX', 'MIN').
    - `column`: The fully qualified column name (`table.column`) to apply the function to. For `COUNT(*)`, you can use `"*"`.
    - `alias`: A descriptive, lowercase snake_case name for the resulting aggregated column (e.g., 'total_sales', 'average_price').
- `reasoning`: A brief explanation of why the specific grouping columns and aggregations were chosen, based on the user's question.



--- EXAMPLE ---
User Question: "What is the total number of orders and average order value for each customer?"
Identified Tables/Columns: {"users": ["id", "name"], "orders": ["id", "user_id", "order_value"]}

JSON Out:
```json
{
  "group_by_columns": [
    "users.name"
  ],
  "aggregations": [
    {
      "function": "COUNT",
      "column": "orders.id",
      "alias": "total_orders"
    },
    {
      "function": "AVG",
      "column": "orders.order_value",
      "alias": "average_order_value"
    }
  ],
  "reasoning": "The user asks for metrics 'for each customer', which requires grouping by the customer's name. The question also asks for the 'total number of orders' (requiring a COUNT on orders) and the 'average order value' (requiring an AVG on the order value)."
}
```
--- END OF EXAMPLE ---


--- New Request ---

--- Schema Context ---
{schema_context}

--- Business Terms Context ---
{business_terms_context}

--- User Question ---
{query_str}

--- Identified Tables/Columns ---
{identified_tables_columns_json}


JSON Out:

"""
)

GROUPING_PROMPT_V4 = PromptTemplate(
"""
Given the user question and the available schema context, your task is to identify all necessary grouping columns and aggregation expressions.

First, mentally deconstruct the user's request. For each metric requested:
1.  **Is it a direct column?** If yes, no aggregation is needed.
2.  **Is it a simple aggregation?** (A single function like SUM, COUNT, AVG on a single column). Example: "Total sales" -> `SUM(sales)`.
3.  **Is it a conditional aggregation?** (Counting or summing different categories within the *same* column). Example: "Count shipped and cancelled orders" -> `SUM(CASE WHEN ...)`
4.  **Is it a calculated metric?** (A ratio, percentage, or formula involving multiple fields/aggregations). Example: "Average items per order" -> `SUM(item_count) / COUNT(order_id)`.

Use this deconstruction to decide whether to use the `aggregations` or `complex_aggregations` key for each metric. Pay close attention to keywords indicating grouping ("each", "per"), aggregation ("total", "average"), and distinctness ("unique", "distinct").

Produce a JSON object as your output with the following keys:

- `group_by_columns`: A list of strings representing the fully qualified column names (`table.column`) to be used in the `GROUP BY` clause. If no grouping is needed, provide an empty list `[]`.
- `aggregations`: A list of objects for **simple, single-function aggregations**. If none are needed, provide an empty list `[]`. Each object must have:
    - `function`: The SQL aggregate function to use (e.g., 'SUM', 'COUNT', 'AVG', 'MAX', 'MIN').
    - `column`: The fully qualified column name (`table.column`) to apply the function to. For `COUNT(*)`, use `"*"`.
    - `alias`: A descriptive, lowercase snake_case name for the resulting aggregated column.
- `complex_aggregations`: A list of objects for aggregations that require **calculations or conditional logic**. If none are needed, provide an empty list `[]`. Each object must have:
    - `expression`: A string representing the complete SQL expression for the aggregation (e.g., 'SUM(CASE WHEN t1.status = 'delivered' THEN 1 ELSE 0 END)', 'SUM(t1.runs_scored) / COUNT(DISTINCT t1.match_id)').
    - `alias`: A descriptive, lowercase snake_case name for the resulting column.
- `reasoning`: A brief explanation of why the specific grouping columns and aggregations were chosen. You must explicitly justify why an aggregation was classified as simple versus complex.



--- EXAMPLE ---
User Question: "For each customer, what is their total number of orders and their conversion rate (purchases per visit)?"
Identified Tables/Columns: {"users": ["id", "name"], "orders": ["id", "user_id"], "events": ["event_type", "user_id"]}
Business Terms: "A purchase is an order. A visit is a unique session."

JSON Out:
```json
{
  "group_by_columns": [
    "users.name"
  ],
  "aggregations": [
    {
      "function": "COUNT",
      "column": "DISTINCT orders.id",
      "alias": "total_orders"
    }
  ],
  "complex_aggregations": [
    {
      "expression": "COUNT(DISTINCT orders.id) / COUNT(DISTINCT events.session_id)",
      "alias": "conversion_rate"
    }
  ],
  "reasoning": "Grouping is required 'for each customer' (users.name). 'Total number of orders' is a simple distinct count on the orders table. 'Conversion rate' is a complex metric defined as purchases per visit, requiring a calculation between two aggregations, so it is placed in complex_aggregations."
}
```
--- END OF EXAMPLE ---

--- New Request ---

--- Schema Context ---
{schema_context}

--- Business Terms Context ---
{business_terms_context}

--- User Question ---
{query_str}

--- Identified Tables/Columns ---
{identified_tables_columns_json}

JSON Out:

"""
)





CALCULATIONS_PROMPT_V2 = PromptTemplate(
"""
Given the user question, the previously identified tables and columns, and the business terms context, determine only the core mathematical or aggregate calculations required to directly answer the user's question. 

Focus strictly on identifying the aggregation function (e.g., SUM, COUNT, AVG, MIN, MAX) and the specific columns from the identified tables and schema context that these functions should operate on. 
If the query requires a calculation based on a condition (like 'no less than 100'), identify the core aggregate and the condition separately, without constructing a full WHERE or HAVING clause.

For example, if the query is 'What is the total runs scored by player X?', the calculation identified should be `SUM(runs_score)` and the reasoning would state 'To calculate the total runs scored by a player.' 
If the query is 'Players who scored no less than 100 runs', the calculation should be `SUM(runs_score)` and the reasoning would indicate that this sum needs to be compared against 100.

**DO NOT include:**
* `GROUP BY` clauses
* `ORDER BY` clauses
* `HAVING` clauses
* `WHERE` clauses (these are for filtering, a separate step)
* Table joins or other structural SQL elements
* Incorrect or malformed SQL syntax
* Generic or hallucinated column names (use names from schema context or identified tables)

If no direct calculations are needed (e.g., the question is simply asking to retrieve raw data or identify entities without aggregation/arithmetic), state 'No calculations needed'.

Output as a JSON object with 'calculations' (a list of concise 'calculation_string' strings) and 'reasoning' (a string explaining *why* each listed calculation is necessary to answer the question, without describing the full SQL logic).

--- Schema Context ---
{schema_context}
--- Business Terms Context ---
{business_terms_context}
--- User Question ---
{query_str}
--- Identified Tables/Columns ---
{identified_tables_columns_json}

JSON Output:
"""

)
CALCULATIONS_PROMPT_V3 = PromptTemplate(
"""
Given a user question and a set of pre-defined aggregations, your task is to identify and construct complex mathematical formulas or metrics.

Your goal is to build these formulas by performing arithmetic operations (e.g., division, multiplication, subtraction, addition) on the provided aggregations.

--- Inputs ---
1.  **User Question**: The user's request, which specifies the required calculation (e.g., "what is the revenue per user?").
2.  **Aggregations Input**: A JSON object containing a list of pre-defined aggregations. Each aggregation in this list has a unique `alias` (e.g., `total_revenue`, `user_count`) that you must use as a variable.

--- Output Requirements ---
Produce a JSON object with "calculations" and "reasoning" (a string explaining why each calculation is necessary to answer the question, without describing the full SQL logic).

The value of "calculations" must be a list of objects. If no complex formulas are needed, this list should be empty. Each object in the list represents a single formula and must contain two keys:
1.  `alias`: A new, descriptive, lowercase, snake_case name for the calculated field (e.g., `revenue_per_user`).
2.  `formula`: The mathematical expression as a string. This string **must** use the aliases from the `Aggregations Input`.

--- Key Instructions & Constraints ---
*   **Use Aliases**: Your primary task is to combine the aliases from the `Aggregations Input`. Do not re-define the original aggregation functions (like `SUM()` or `COUNT()`).
*   **Focus on Formulas**: Only create an output entry if the user's question requires an arithmetic calculation between aggregations. For simple requests like "total sales," no calculated fields are necessary.
*   **Use Provided Inputs Only**: Do not hallucinate or invent aliases or column names. The formula must only contain aliases present in the `Aggregations Input`.

**DO NOT include:**
* `GROUP BY` clauses
* `ORDER BY` clauses
* `HAVING` clauses
* `WHERE` clauses (these are for filtering, a separate step)
* Table joins or other structural SQL elements

--- Example ---
**User Question:** "What is the revenue per transaction?"

**Aggregations Input:**
```json
{
  "aggregations": [
    {
      "alias": "total_revenue",
      "function": "SUM",
      "column": "sales.amount"
    },
    {
      "alias": "number_of_transactions",
      "function": "COUNT",
      "column": "sales.id"
    }
  ]
}

JSON Output:
```json
{
  "calculations": [
    {
      "alias": "revenue_per_transaction",
      "formula": "total_revenue / number_of_transactions"
    },
  "reasoning": "Revenue per transaction was defined in the business documment about revenue.",
  ]
}
```
--- End of Example ---

--- New Request ---

--- Schema Context ---
{schema_context}
--- Business Terms Context ---
{business_terms_context}
--- User Question ---
{query_str}
--- Identified Tables/Columns ---
{identified_tables_columns_json}
--- Aggregations Input ---
{aggregate_info}

JSON Output:

"""

)




FILTERING_PROMPT_V2 = PromptTemplate (
"""
Given the user question, the previously identified tables and columns, and the business terms context, determine if any filtering is required to directly answer the query. 
If filtering is needed, list the specific filtering conditions that would be used in a WHERE or HAVING clause. 
For each filter, specify the column name, the comparison operator (e.g., '=', '>', '<', '>=', '<=', '!=', 'LIKE', 'IN', 'BETWEEN'), and the value(s) to filter by.

If no filtering is needed, state 'No filtering needed'.

Output the result as a JSON object with the following structure:
{  
    "filters": "[ {'column': 'column_name', 'operator': 'operator', 'value': 'filter_value'}  ]",  
    "reasoning": "Explanation of why these filters are needed or why no filters are needed."
}

Remember to only include filters directly implied by the user's question and supported by the schema context. 
Do not include join conditions, grouping logic, or ordering clauses.

--- Schema Context ---
{schema_context}
--- Business Terms Context ---
{business_terms_context}
--- User Question ---
{query_str}
--- Identified Tables/Columns ---
{identified_tables_columns_json}

JSON Output:

"""
)

FILTERING_PROMPT_V3 = PromptTemplate (
"""
You are an expert SQL analyst responsible for identifying filtering conditions within a user's query. Your task is to analyze the user's question and determine the appropriate `WHERE` and `HAVING` clauses based on the provided context.

**Crucial Distinction:**
- **`WHERE` clause:** Filters individual rows *before* any aggregation (e.g., `GROUP BY`). Conditions here apply directly to column values (`users.country = 'USA'`, `products.price > 100`).
- **`HAVING` clause:** Filters groups of rows *after* an aggregation has been applied. Conditions here *must* involve an aggregate function (`COUNT(orders.id) > 5`, `AVG(products.ratings) >= 4.5`).

Given the inputs below, identify all filtering conditions. For each condition, you must correctly classify it as either a `WHERE` or `HAVING` clause.

**Inputs:**
- **User Question:** The user's request, pre-processed for clarity.
- **Selected Columns:** The table columns identified as relevant to the question.
- **Aggregation Functions:** Any aggregate functions (`COUNT`, `SUM`, `AVG`, etc.) identified in the query.

**Output Requirements:**

Produce a single JSON object with the following structure:
- `filters`: A list of strings, where each entry represents a `where_clause` (pre-aggregation filter condition) or `having_clause` (post-aggregation filter condition).
- `reasoning`: Explanation of why these filters are needed or why no filters are needed.

Each filter string must contain:
- `column`: The column name for the condition.
- `operator`: The comparison operator (e.g., '=', '>', '<', 'LIKE', 'IN', 'BETWEEN').
- `value`: The value to filter by.

If no filtering is required, the `where_clauses` and `having_clauses` lists should be empty, and the `reasoning` should state this clearly. Do not invent filters not explicitly mentioned or directly implied by the user's question.

--- Schema Context ---
{schema_context}
--- Business Terms Context ---
{business_terms_context}
--- User Question ---
{query_str}
--- Selected Columns ---
{identified_tables_columns_json}
--- Aggregation Functions ---
{aggregation_functions_json}

JSON Output:


"""
)

#
# Restate the user's question into a well formed question
#


CLEAN_QUESTION_PROMPT_V3 = PromptTemplate(
"""
You are an intelligent assistant designed to rephrase user questions into well-formed, precise queries suitable for generating SQL.
Your role is to parse a user's raw input and transform it into a structured, unambiguous question suitable for a database query.
You must alsovalidate if the user's intent is to retreive factual information.

You have no knowledge of the database schema. Your goal is not to guess if the data is available, but to determine if the question's structure and intent are suitable for a database query.

Today's date is {current_date}. If the user's question contains relative timeframes (e.g., "last month," "next year," "yesterday"), you must convert them into explicit date ranges (e.g., "from 2025-06-01 to 2025-06-30").

--- Core Directives ---

**1. Infer and Clarify (Primary Directive)**
Your main goal is to rephrase the user's question to be clear, specific, andself-contained.
If a question uses subjective or ambiguous terms (e.g. "popular", "best", "top", "most"), you must infer the most likely business metric and explicitly state it in the rephrased question.
* "Popular" or "most" usually implies `highest count`.
* "Best" or "top" usually implies `highest revenue` or `highest count`.

Make a reasonable, common-sense assumption. The rephrased question should be something a data analyst could immediatly work with.

**2. Validate and Cancel (Secondary Directive)**
You must evaluate if the user's question can be plausibly answered by querying a structred database.

Set `cancel_process` to `true` only as a last resort if the question meets one of these strict criteria:
*   **Inherently Non-Factual or Conversational:** The user is not asking for data (e.g., "hello," "thank you," "tell me a joke").
*   **Instructs an Action:** The question asks the system to perform an action other than retrieving data (e.g., "email the sales report to my manager," "create a new user").
*   **Impossible to Rephrase:** The question is so fundamentally vague that no specific entities or reasonable metrics can be inferred from it (e.g., "summarize everything," "what about the data?"). 
**Crucially, do not cancel just because a term is subjective; your primary goal is to interpret it.**


--- Output Format ---
Your output **MUST** be a valid JSON object containing two keys:
1. `cancel_process`: A boolean value (`true` if the process should be cancelled, `false` otherwise).
2. `rephrased_question`: A string. If `cancel_process` is `false`, this contains the well-formed question. If `true`, provide a brief, clear explanation for the cancellation.



--- Examples---

Example 1: Valid Question (Implicit Metric - "Popular")
User Question: "what are the most popular movies?"
Output:
```json
{
   "cancel_process": false,
   "rephrased_question": "List the movies with the highest revenue." 
}
```

Example 2: Valid Question (Implicit Metric - "Best)
User Question: "Who are our best customers?"
Output:
```json
{
    "cancel_process": false,
    "rephrased_question": "List the customers with the highest total sales amount."
}
```


Example 3: Valid Question (Relative Time)
User Question: "Show me the total sales for the last quarter."
Output:
```json
{
  "cancel_process": false,
  "rephrased_question": "What is the total sales amount for the period from 2025-04-01 to 2025-06-30?"
}
```

Example 4: Invalid Question (Action-Oriented)
User Question: "Please order 10 more units of product SKU 12345."
Output:
```json
{
  "cancel_process": true,
  "rephrased_question": "The user's request is an instruction to perform an action (ordering a product), not to query data."
}
```

Example 5: Invalid Question (Impossible to Rephrase)
User Question: "Summarize everything"
Output:
```json
{
    "cancel_process":true,
    "rephrased_question": "The question is too vague andlacks specific entities or metrics for a SQL query."
}
```


--- End of Examples ---


You must now process the user's question. Provide your response exclusively in the valid JSON format described above.

--- User Question --- 
{original_question}

Output JSON:

"""
)

CLEAN_QUESTION_PROMPT_V4 = PromptTemplate(
"""
You are an expert data analyst. Your primary role is to translate a user's potentially vague question into a precise, unambiguous, and detailed set of analytical instructions suitable for a data query engine.

You have no direct knowledge of the database schema. Your goal is to deconstruct the user's intent into a logical plan that a junior analyst (or a downstream AI) could execute, regardless of the specific table and column names.

Today's date is {current_date}. All relative timeframes (e.g., "last month," "next year," "yesterday") MUST be converted into explicit date ranges (e.g., "from 2025-06-01 to 2025-06-30").

--- Core Directives ---

**1. Deconstruct and Define (Primary Directive)**
Your main goal is to rephrase the user's question into a self-contained analytical task. This involves three steps:

*   **A. Identify Grouping Dimensions:** Explicitly state how the results should be segmented. Look for keywords like "per," "for each," "by," or "across." If the user says "analyze sales by region and product category," the rephrased question must include "For each region and for each product category...".

*   **B. Resolve Ambiguous Metrics:** When a user asks for something subjective like "best," "top," "most popular," or "most active," do not assume a single metric. Instead, define the term using multiple, concrete analytical facets. A human analyst should be able to read your rephrased question and know exactly what to calculate.
    *   "**Best Customers**" should be deconstructed into key metrics like: `total sales amount`, `frequency of orders`, and `recency of last purchase`.
    *   "**Most Popular Products**" could mean: `highest number of units sold`, `highest total revenue`, or `most frequently included in orders`.

*   **C. Define Complex Calculations:** If a metric requires a formula, spell it out in plain English.
    *   "**Conversion Rate**" must become: "Calculate the number of unique users who made a purchase and divide it by the number of unique users who visited the site."
    *   "**Batting Average**" must become: "For each player, calculate the total number of runs scored and divide it by the total number of times they were out."

**2. Validate and Cancel (Secondary Directive)**
You must evaluate if the user's question can be plausibly answered by querying a structured database. Set `cancel_process` to `true` only if the question meets one of these strict criteria:
*   **Inherently Non-Factual or Conversational:** The user is not asking for data (e.g., "hello," "thank you," "tell me a joke").
*   **Instructs an Action:** The question asks the system to perform an action other than retrieving data (e.g., "email the sales report to my manager," "create a new user").
*   **Impossible to Deconstruct:** The question is so fundamentally vague that no specific entities or reasonable metrics can be inferred (e.g., "summarize everything," "what about the data?").
**Crucially, do not cancel just because a term is subjective; your primary directive is to deconstruct it.**


--- Output Format ---
Your output **MUST** be a valid JSON object containing two keys:
1.  `cancel_process`: A boolean value (`true` if the process should be cancelled, `false` otherwise).
2.  `rephrased_question`: A string. If `cancel_process` is `false`, this contains the detailed analytical instructions. If `true`, provide a brief explanation for the cancellation.


--- Examples ---

Example 1: Deconstructing "Best"
User Question: "Who are our best customers?"
Output:
```json
{
    "cancel_process": false,
    "rephrased_question": "List and rank customers based on three metrics: 1. Highest total sales amount, 2. Highest frequency of orders, and 3. Most recent last purchase date."
}
```

Example 2: Deconstructing a Complex Metric
User Question: "What's the product return rate?"
Output:
```json
{
  "cancel_process": false,
  "rephrased_question": "For each product, calculate the return rate by taking the total number of units returned and dividing it by the total number of units sold."
}
```

Example 3: Identifying Grouping and Ambiguity
User Question: "Show me the most popular movie categories by country."
Output:
```json
{
  "cancel_process": false,
  "rephrased_question": "For each country, list the movie categories ranked by the highest number of movies rented."
}
```

Example 4: Relative Time and Simple Metric
User Question: "Show me the total sales for last quarter."
Output:
```json
{
  "cancel_process": false,
  "rephrased_question": "Calculate the sum of total sales for the period from 2025-04-01 to 2025-06-30."
}
```

Example 5: Invalid Question (Action-Oriented)
User Question: "Please order 10 more units of product SKU 12345."
Output:
```json
{
  "cancel_process": true,
  "rephrased_question": "The user's request is an instruction to perform an action (ordering a product), not a request to query data."
}
```
--- End of Examples ---

You must now process the user's question. Provide your response exclusively in the valid JSON format described above.

--- User Question ---
{original_question}

Output JSON:

"""

)



# 
# Generate the SQL
# 
SQL_GEN_PROMPT_TEMPLATE = """
You are an expert SQL query generator. Your task is to translate natural language questions into SQL queries.
You have access to the following database schema information and business definitions:

--- Database Schema Context ---
{schema_context}

--- Business Terms & Definitions Context ---
{business_terms_context}

--- Instructions ---
1.  **Analyze the User Question and Context:** Carefully read the user's question and use ONLY the provided schema and business context to formulate the SQL query.
2.  **Prioritize Business Logic:** If the question involves business terms, ensure the SQL query correctly implements the described business logic (e.g., calculation formulas).
3.  **Use Valid SQL:** Generate a valid SQL query for a PostgreSQL database.
4.  **Select relevant columns:** Only select the columns that are explicitly requested or absolutely necessary to answer the question.
5.  **Be Specific:** If the user mentions specific values (e.g., 'Airlines' database, 'last quarter'), incorporate them into the query using appropriate WHERE clauses or date functions.
6.  **Avoid Explanations:** Only output the SQL query. Do NOT add any natural language explanations, preambles, or epilogues.
7.  **Return an empty string if SQL cannot be generated:** If the question cannot be answered from the provided context, return an empty string.

--- User Question ---
{query_str}

--- Generated SQL Query ---
"""

#
# Clean the SQL
#
CLEAN_SQL_PROMPT = PromptTemplate(
    """You are a SQL query validator and refiner. Your task is to review a given SQL query and identify any syntax errors, common logical flaws, or potential improvements.
You have access to the following database schema information and business definitions for context, but focus primarily on the SQL itself.

--- Database Schema Context ---
{schema_context}

--- Business Terms & Definitions Context ---
{business_terms_context}

--- SQL Query to Review ---
{generated_sql}

--- Instructions ---
1.  **Review Syntax:** Check for common SQL syntax errors (e.g., missing commas, incorrect keywords, mismatched parentheses, invalid JOIN types).
2.  **Schema Adherence:** Ensure table and column names used in the query are plausible given the provided schema context. *Do not invent tables or columns*.
3.  **Logical Consistency:** Check for obvious logical flaws that might lead to incorrect results (e.g., joining on incompatible columns, incorrect aggregation).
4.  **Refine & Improve:** If minor issues are found, correct them. If significant issues are found (e.g., completely malformed or irrelevant to the question), try to correct it based on the user's original intent as inferred from the context.
5.  **Output:** Return ONLY the corrected/refined SQL query. Do not include any prefixes (like 'sql'), suffixes, conversational text, or markdown code block formatting. Return it as a raw, plain string. If the query is perfectly fine, return it as is. If it's fundamentally unfixable or nonsensical given the context, return an empty string.

--- Refined SQL Query ---
"""
)

CLEAN_SQL_PROMPT_V4 = PromptTemplate(
"""
You are a meticulous SQL Syntax Validator. Your primary role is to act as a linter, identifying and correcting only objective, undeniable syntax errors in a given SQL query. You must preserve the original logic of the query at all costs.

--- Database Schema Context ---
{schema_context}

--- Business Terms & Definitions Context ---
{business_terms_context}

--- SQL Query to Review ---
{generated_sql}

--- Primary Directive ---
Your only task is to fix clear syntax errors. If the query is syntactically valid, you MUST return it exactly as it is, even if you suspect a logical flaw.

--- Instructions ---

1.  **Identify Objective Syntax Errors:** Scrutinize the query for common SQL syntax mistakes. This includes, but is not limited to:
    *   Misspelled keywords (e.g., `SELCT`, `GRUP BY`).
    *   Incorrect or missing punctuation (e.g., missing commas, unbalanced parentheses).
    *   Incorrect use of aliases.
    *   Invalid syntax for specific SQL functions.

2.  **What NOT To Change (Strict Prohibition):**
    *   **DO NOT** alter the query's logic.
    *   **DO NOT** add, remove, or change the tables being queried.
    *   **DO NOT** change the `JOIN` type (e.g., `INNER` to `LEFT`).
    *   **DO NOT** alter the `ON` conditions of a join.
    *   **DO NOT** change the columns in the `SELECT` statement.
    *   **DO NOT** add or remove conditions in the `WHERE` or `HAVING` clauses.
    *   **DO NOT** change the values used in a `WHERE` clause (e.g., `WHERE amount > 100` must not become `WHERE amount > 500`).

3.  **Output Rules:**
    *   If you correct one or more syntax errors, return **only** the corrected, valid SQL query as a raw string.
    *   If the input query is already syntactically perfect, return the original, unchanged SQL query.
    *   If the query is so fundamentally broken that its intent cannot be understood for a simple syntax fix, return the original, unchanged query for manual review.

--- Refined SQL Query ---
"""
)

SQL_GEN_PROMPT_TEMPLATE_V3 = PromptTemplate(
    """You are an expert SQL query generator. Your task is to translate natural language questions into a PostgreSQL SQL query.
You have been provided with the user's question, relevant database schema context, and business definitions.
Crucially, you also have specific decisions about the SQL query's components that were derived in previous steps.
Strictly adhere to these decisions when constructing the final SQL query.

--- Database Schema Context ---
{schema_context}

--- Business Terms & Definitions Context ---
{business_terms_context}

--- Original User Question ---
{original_question}

--- SQL Query Component Decisions ---
1.  **Identified Tables and Columns:**
    {identified_tables_columns}

2. **Joins (if applicable):**
    {join_info} 

3.  **Grouping (if applicable):**
    {grouping_details}

4. **Aggregations (if applicable):**
    {aggregate_info}

5.  **Key Calculations (if applicable):**
    {calculation_details}

6.  **Filtering and Conditions (if applicable):**
    {filtering_details}

--- Instructions ---
1.  **Generate SQL:** Combine all the provided "SQL Query Component Decisions" with the schema and business context to construct a single, valid PostgreSQL SQL query.
2.  **Strict Adherence:** Do NOT deviate from the identified tables, columns, grouping, calculations, and filtering conditions provided. If a component is marked "N/A" or empty, do not include it.
3.  **No Explanations:** Only output the SQL query. Do NOT add any natural language explanations, preambles, or epilogues.
4.  **Return empty string if SQL cannot be generated:** If, despite the provided components, a syntactically valid and logical SQL query cannot be formed, return an empty string.

--- Generated SQL Query ---
"""
)

SQL_GEN_PROMPT_TEMPLATE_V4 = PromptTemplate(
    """You are an expert SQL query generator. Your task is to translate natural language questions into a PostgreSQL SQL query.
You have been provided with the user's question, relevant database schema context, and business definitions.
Crucially, you also have specific decisions about the SQL query's components that were derived in previous steps.
Strictly adhere to these decisions when constructing the final SQL query.



--- Instructions ---
1. **Generate SQL:** Combine all the provided "SQL Query Component Decisions" to construct a single, valid SQL query.
2. **Use CTEs for Complexity:** For complex queries that involve window functions (e.g., RANK(), ROW_NUMBER(), LAG()), sequential calculations (e.g., calculating a subtotal and then using it in another calculation), or multiple distinct aggregations that need to be joined, you must use Common Table Expressions (CTEs) with the `WITH` clause to ensure the logic is clear and correct.
3. **Strict Adherence to Components:** The logic within your CTEs and the final SELECT statement must still strictly use the tables, columns, joins, aggregations, and filters defined in the "SQL Query Component Decisions". Do not invent new logic.
4. **No Explanations:** Only output the SQL query. Do NOT add any natural language explanations, preambles, or epilogues.
5. **Return empty string if SQL cannot be generated:** If, despite the provided components, a syntactically valid and logical SQL query cannot be formed, return an empty string.


--- Examples ---

--- Example 1 ---

--- Database Schema Context ---
Table: Agencies
Columns: agency_id INTEGER PRIMARY KEY, agency_details VARCHAR(255) NOT NULL
Table: Staff
Columns: staff_id INTEGER PRIMARY KEY, agency_id INTEGER NOT NULL, staff_details VARCHAR(255) NOT NULL
Table: Clients
Columns: client_id INTEGER PRIMARY KEY, agency_id INTEGER NOT NULL, sic_code VARCHAR(10) NOT NULL,client_details VARCHAR(255) NOT NULL
FOREIGN KEY (agency_id ) REFERENCES Agencies(agency_id )
Table: Invoices
Columns: invoice_id INTEGER PRIMARY KEY,client_id INTEGER NOT NULL,invoice_status VARCHAR(10) NOT NULL,invoice_details VARCHAR(255) NOT NULL
FOREIGN KEY (client_id ) REFERENCES Clients(client_id )
Table: Meetings
Columns: meeting_id INTEGER PRIMARY KEY, client_id INTEGER NOT NULL, meeting_outcome VARCHAR(10) NOT NULL,meeting_type VARCHAR(10) NOT NULL,billable_yn VARCHAR(1),start_date_time DATETIME,end_date_time DATETIME,purpose_of_meeting VARCHAR(255),other_details VARCHAR(255) NOT NULL
FOREIGN KEY (client_id ) REFERENCES Clients(client_id )
Table: Payments
Columns: payment_id INTEGER NOT NULL ,invoice_id INTEGER NOT NULL,payment_details VARCHAR(255) NOT NULL
FOREIGN KEY (invoice_id ) REFERENCES Invoices(invoice_id )
Table: Staff_in_Meetings
Columns: meeting_id INTEGER NOT NULL,staff_id INTEGER NOT NULL
FOREIGN KEY (meeting_id ) REFERENCES Meetings(meeting_id )
FOREIGN KEY (staff_id ) REFERENCES Staff(staff_id )

--- Business Terms & Definitions Context (if applicable) ---


-- Original User Question --
What are the start and end times of each meeting, as well as the corresponding client and staff details of the attendees?

--- SQL Query Component Decisions ---
1.  **Identified Tables and Columns:**
{
  "tables": ["meetings", "clients", "staff", "staff_in_meetings"],
  "columns": ["meetings.start_date_time", "meetings.end_date_time", "clients.client_details", "staff.staff_details"],
  "reasoning": "The user requires start and end times from the 'meetings' table, client details from the 'clients' table, and staff details from the 'staff' table. The 'staff_in_meetings' table is necessary to link the staff to the meetings."
}

2. **Joins (if applicable):**
{
  "reasoning": "The query needs to connect meetings to their client and the staff who attended. 'meetings' joins to 'clients' on `client_id`. 'meetings' joins to 'staff_in_meetings' on `meeting_id`, which then joins to 'staff' on `staff_id` to get staff details. INNER joins are used as we only want to see meetings that have both a client and staff attendees.",
  "joins": [
    {
      "join_type": "INNER",
      "left_on": "meetings.client_id",
      "right_on": "clients.client_id"
    },
    {
      "join_type": "INNER",
      "left_on": "meetings.meeting_id",
      "right_on": "staff_in_meetings.meeting_id"
    },
    {
      "join_type": "INNER",
      "left_on": "staff_in_meetings.staff_id",
      "right_on": "staff.staff_id"
    }
  ]
}

3.  **Grouping (if applicable):**
{
  "group_by_columns": [],
  "reasoning": "The user's question asks for specific details for each meeting record, not for aggregated metrics. Therefore, no grouping is needed."
}

4. **Aggregations (if applicable):**
{
  "aggregations": [],
  "reasoning": "The user's question does not ask for any mathematical summaries like COUNT, SUM, or AVG. It asks for raw data details."
}

5.  **Key Calculations (if applicable):**
{
  "calculations": [],
  "reasoning": "No aggregations were identified, so no calculations or formulas are necessary."
}

6.  **Filtering and Conditions (if applicable):**
{
  "filters": [],
  "reasoning": "The user's question does not contain any keywords or conditions that imply filtering the results (e.g., by a specific date, client, or staff member)."
}

--- Generated SQL Query ---
```sql
SELECT T1.start_date_time , T1.end_date_time , T2.client_details , T4.staff_details FROM meetings AS T1 JOIN clients AS T2 ON T1.client_id = T2.client_id JOIN staff_in_meetings AS T3 ON T1.meeting_id = T3.meeting_id JOIN staff AS T4 ON T3.staff_id = T4.staff_id
```


--- End Example 1 ---

--- Example 2 : Complex Query with CTE ---
--- Database Schema Context ---
Table: employees
Columns: employee_id INTEGER PRIMARY KEY, employee_name VARCHAR(255) NOT NULL, department VARCHAR(100) NOT NULL
Table: sales
Columns: sale_id INTEGER PRIMARY KEY, employee_id INTEGER NOT NULL, sale_amount DECIMAL(10, 2) NOT NULL
FOREIGN KEY (employee_id) REFERENCES employees(employee_id)

--- Business Terms & Definitions Context ---

--- Original User Question ---
Who are the top 3 employees in each department by total sales amount?

--- SQL Query Component Decisions ---

1.  **Identified Tables and Columns:**
{"tables": ["employees", "sales"], "columns": ["employees.employee_name", "employees.department", "sales.sale_amount"]}

2. **Joins (if applicable):**
{"joins": [{"join_type": "INNER", "left_on": "employees.employee_id", "right_on": "sales.employee_id"}]}

3.  **Grouping (if applicable):**
{"group_by_columns": ["employees.employee_name", "employees.department"], "reasoning": "We need to calculate sales per employee."}

4. **Aggregations (if applicable):**
{"aggregations": [{"function": "SUM", "column": "sales.sale_amount", "alias": "total_sales"}], "reasoning": "The query requires summing up the sale_amount for each employee."}

5.  **Key Calculations (if applicable):**
{"calculations": [], "reasoning": "No further calculations between aggregations are needed."}

6.  **Filtering and Conditions (if applicable):**
{"filters": [{"clause_type": "window_ranking", "condition": "RANK() OVER (PARTITION BY department ORDER BY total_sales DESC) <= 3"}], "reasoning": "The user asks for the 'top 3' within 'each department', which requires a window function to rank employees within each department by sales and then filter for the top 3."}


--- Generated SQL Query ---
```sql
WITH employee_sales AS (
  SELECT
    T1.employee_name,
    T1.department,
    SUM(T2.sale_amount) AS total_sales
  FROM employees AS T1
  JOIN sales AS T2
    ON T1.employee_id = T2.employee_id
  GROUP BY
    T1.employee_name,
    T1.department
), ranked_sales AS (
  SELECT
    employee_name,
    department,
    total_sales,
    RANK() OVER (PARTITION BY department ORDER BY total_sales DESC) as sales_rank
  FROM employee_sales
)
SELECT
  employee_name,
  department,
  total_sales
FROM ranked_sales
WHERE
  sales_rank <= 3
```
--- End Example 2 ---
--- End Examples ---


--- New Request ---

--- Database Schema Context ---
{schema_context}

--- Business Terms & Definitions Context ---
{business_terms_context}

--- Original User Question ---
{original_question}

--- SQL Query Component Decisions ---
1.  **Identified Tables and Columns:**
    {identified_tables_columns}

2. **Joins (if applicable):**
    {join_info} 

3.  **Grouping (if applicable):**
    {grouping_details}

4. **Aggregations (if applicable):**
    {aggregate_info}
    {complex_aggregate_info}

5.  **Key Calculations (if applicable):**
    {calculation_details}

6.  **Filtering and Conditions (if applicable):**
    {filtering_details}

--- Generated SQL Query ---

"""
)

ASSISTANT_PROMPT_TEMPLATE = """
You are an expert AI assistant named 'Insight Guide'. Your primary role is to help non-technical business users formulate a clear data analysis question. 
You will accomplish this by guiding them through a short, structured conversation, asking only one question at a time.

Your ultimate goal is to populate a JSON object with the core components of their analytical query. 
Once populated, this JSON will be passed to a data analysis pipeline.

**CRITICAL CONSTRAINTS:**
1.  **Zero Context:** You have NO knowledge of the user's specific business, their database schemas, or their business term definitions (e.g., how 'churn' is calculated). You must ask general questions that do not assume any prior context.
2.  **JSON Output ONLY:** Your response MUST ALWAYS be a single, valid JSON object. Do not include any text, notes, or markdown outside of the JSON structure.

**CONVERSATION PROCESS:**
You must manage the conversation state to gather three key pieces of information from the user, in this order:

1.  **The Business Problem:** Start by asking the user to state the general topic or business problem they want to investigate (e.g., customer retention, sales performance).
2.  **The Primary Segment:** Once the problem is identified, ask the user to describe the main group or segment of interest. Prompt them to use descriptive attributes or behaviors in their own words (e.g., "users from the new marketing campaign," "customers who bought product X," "employees in the engineering department").
3.  **The Metric to Measure:** After the segment is defined, ask what specific outcome or calculation they want to measure for that group. Encourage them to use business terms if they know them ("revenue," "conversion rate") or to describe what they want to know in plain language ("how much they spent," "how many of them are still active").

**JSON OUTPUT STRUCTURE:**
You must use the following JSON format for all your responses.

{
  "is_ready_for_pipeline": boolean,
  "message_to_user": "string",
  "query_components": {
    "business_problem": "string or null",
    "primary_segment_description": "string or null",
    "metric_to_measure": "string or null"
  }
}

**JSON FIELD LOGIC:**
-   `query_components`: Fill these fields with the user's answers as you receive them. Unanswered fields should be `null`.
-   `message_to_user`: This is the string that will be displayed to the user. It should contain your next question or a final confirmation.
-   `is_ready_for_pipeline`:
    -   Set this to `false` as long as any `query_components` field is `null`.
    -   Once all three `query_components` have been filled, set this to `true` in your final response. Your final message should confirm the request and let the user know the process is starting.

**Initial User Message:**
The user's first message to you will be the `user_query`. This is your cue to begin the conversation. Your first JSON response should populate `business_problem` with their query, and `message_to_user` should contain your question to define the primary segment.

--- User Query ---


"""
    
