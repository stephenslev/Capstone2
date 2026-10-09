## Architecture
<!-- filename: README.md -->

```text
User Query (CLI)

      │

      ▼

┌─────────────────┐

│  Manager Agent  │  ── classifies query ──► qualitative / quantitative / both

└─────────────────┘

      │                          │

      ▼                          ▼

┌──────────────────┐    ┌───────────────────┐

│ Qualitative Agent│    │ Quantitative Agent │

│                  │    │                   │

│ • Vector DB      │    │ • SQLite DB        │

│   (ChromaDB)     │    │ • NL → SQL         │

│ • Semantic search│    │ • Query execution  │

│ • Claude for     │    │ • Claude for       │

│   generation     │    │   interpretation   │

└──────────────────┘    └───────────────────┘

      │                          │

      └──────────┬───────────────┘

                 ▼

      ┌─────────────────────┐

      │  Validation Layer   │  ── checks grounding, flags issues

      └─────────────────────┘

                 │

                 ▼

      ┌─────────────────────┐

      │  Tokenomics Logger  │  ── logs token usage and cost per query

      └─────────────────────┘

                 │

                 ▼

        Response to User
```

## Setup-and-Usage

# Spoonful Enterprise RAG System

## Overview

Spoonful is an enterprise question-answering system that combines document retrieval with quantitative database analysis.

A manager agent classifies each question as:

- **Qualitative** — answered using enterprise documents.
- **Quantitative** — answered using structured SQLite data.
- **Both** — answered using document context and quantitative analysis.

The system uses:

- Gemini through an OpenAI-compatible API endpoint
- ChromaDB for document retrieval
- `all-MiniLM-L6-v2` for document embeddings
- SQLite for quantitative analysis
- Validation checkpoints for document grounding and SQL safety
- Token usage logging through the project’s tokenomics logger

## Project Structure

- `main.py` — Starts the interactive command-line application.
- `agents/manager.py` — Classifies questions, coordinates agents, validates results, and creates combined overviews.
- `agents/qualitative.py` — Retrieves relevant document chunks and generates source-grounded responses.
- `agents/quantitative.py` — Generates, validates, executes, and interprets read-only SQL queries.
- `ingest.py` — Loads, chunks, embeds, and stores `.txt` documents in ChromaDB.
- `build_database.py` — Creates and populates the sample SQLite database.
- `test_validation.py` — Tests document grounding and SQL safeguards.
- `validation/validator.py` — Contains qualitative and quantitative validation logic.
- `tokenomics/logger.py` — Records token usage and estimated model costs.
- `data/documents/` — Stores qualitative source documents.
- `data/chroma/` — Stores the persistent ChromaDB collection.
- `data/database.sqlite` — Stores quantitative data.

## Prerequisites

The project requires:

- Python 3.9 or later
- A valid Gemini API key
- Permission to install Python packages
- `.txt` source documents for qualitative retrieval

The first ingestion or qualitative query may take longer because the embedding model may need to be downloaded.

## Installation

Run the following commands from the project root.

Create a virtual environment:

```bash
python -m venv .venv
```

Activate the environment on macOS or Linux:

```bash
source .venv/bin/activate
```

Activate the environment in Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install the required packages:

```bash
pip install chromadb openai python-dotenv sentence-transformers
```

If the repository includes a `requirements.txt` file, use:

```bash
pip install -r requirements.txt
```

## Environment Configuration

Create a `.env` file in the project root:

```dotenv
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-3.5-flash-lite
VALIDATION_DEBUG=false
```

`GEMINI_API_KEY` is required by the manager, qualitative agent, and quantitative agent.

`GEMINI_MODEL` is optional. If it is not provided, the application defaults to `gemini-3.5-flash-lite`.

Set `VALIDATION_DEBUG=true` when troubleshooting. This prints intermediate model outputs before validation.

Do not commit `.env`, API keys, or other secrets to source control.

Recommended `.gitignore` entries:

```gitignore
.env
.venv/
data/chroma/
```

## Add Source Documents

Place qualitative source documents in:

```text
data/documents/
```

The ingestion process searches this directory recursively and reads `.txt` files only.

Example source documents include:

- `employee-experience-policy.txt`
- `performance-management-policy.txt`
- `customer-complaints-policy.txt`
- `data-privacy-policy.txt`

## Build the SQLite Database

Run:

```bash
python build_database.py
```

This creates `data/database.sqlite` and populates it with sample data for:

- Revenue
- Customers
- Sales
- Customer success
- Employee satisfaction
- Policy metrics

> **Warning:** `build_database.py` deletes and recreates `data/database.sqlite` if it already exists. Do not run it against production or irreplaceable data.

## Ingest Documents

After adding or updating source documents, run:

```bash
python ingest.py
```

The ingestion process:

1. Finds `.txt` files under `data/documents/`.
2. Splits each document into 500-word chunks.
3. Uses a 50-word overlap between chunks.
4. Generates embeddings using `all-MiniLM-L6-v2`.
5. Stores the documents and metadata in the `enterprise-docs` ChromaDB collection.

The resulting ChromaDB data is stored in:

```text
data/chroma/
```

If documents are deleted or substantially changed, remove the existing `data/chroma/` directory before running ingestion again. This prevents obsolete document chunks from remaining in the collection.

## Run Validation Tests

Run the validation tests with:

```bash
python test_validation.py
```

The tests verify that:

- Unsupported qualitative answers are flagged.
- Unsafe SQL statements such as `DELETE FROM sales` are blocked.
- Blocked SQL is not executed.
- Failed quantitative queries return no database rows.

## Start the Application

Start the interactive application with:

```bash
python main.py
```

The application displays:

```text
Spoonful Enterprise RAG System
Type 'exit' to quit.

Ask a question:
```

Enter `exit` or `quit` to close the application.

## Query Routing

### Qualitative

This route is used for questions about policies, processes, procedures, or documentation.

The qualitative agent:

1. Retrieves the five most relevant document chunks from ChromaDB.
2. Sends the retrieved context to Gemini.
3. Generates an answer using only the supplied documents.
4. Includes source citations in the response.
5. Returns a grounded refusal when the information is unavailable.

### Quantitative

This route is used for questions involving numbers, metrics, trends, comparisons, or SQL-queryable data.

The quantitative agent:

1. Generates a read-only SQLite query.
2. Validates the generated SQL.
3. Executes the query if it passes validation.
4. Sends the returned columns and rows to Gemini.
5. Generates an interpretation based only on the SQL results.

### Both

This route is used when a question requires document context and numerical analysis.

The manager:

1. Runs the qualitative agent.
2. Runs the quantitative agent.
3. Validates both results.
4. Creates a combined overview only if both results pass validation.
5. Withholds the combined overview if either result fails validation.

## Example Questions

### Qualitative question

```text
What does the employee experience policy say about workload concerns?
```

### Quantitative question

```text
Which region had the highest revenue in 2026-Q4?
```

### Combined question

```text
How does our employee satisfaction compare to industry standards and what policies might impact this?
```

## Validation Behavior

Qualitative validation checks whether the response is supported by the retrieved document chunks and includes appropriate source citations.

A justified refusal may pass validation when the requested information is not present in the supplied documents. A refusal is treated differently from an unsupported factual answer because it does not make an ungrounded claim.

Quantitative validation checks whether:

- SQL is present.
- SQL is limited to one read-only `SELECT` or `WITH` query.
- SQL does not contain blocked commands.
- SQL does not contain comments or multiple statements.
- SQL execution succeeds.
- The quantitative result is available for interpretation.

The combined overview is withheld if either the qualitative or quantitative result fails validation.

The combined overview uses only the validated agent outputs. It is instructed to preserve source citations, avoid unsupported causal claims, and identify missing evidence or limitations.

## SQL Safeguards

The quantitative agent permits only a single read-only `SELECT` or `WITH` query.

The following operations are blocked:

- `DROP`
- `DELETE`
- `UPDATE`
- `INSERT`
- `ALTER`
- `TRUNCATE`
- `CREATE`
- `REPLACE`
- `ATTACH`
- `DETACH`
- `PRAGMA`
- `VACUUM`
- `REINDEX`

SQL comments and multiple statements are also blocked.

## Expected Output

For each question, the application displays:

- The original question
- The selected route
- Qualitative validation results, when applicable
- Quantitative validation results, when applicable
- Validation warnings
- The qualitative response, quantitative response, or both
- Generated SQL for quantitative questions
- A combined overview for validated `both` queries
- Token usage and estimated model cost

## Troubleshooting

### Missing API Key

Confirm that `GEMINI_API_KEY` is present in `.env` and that the file is located in the project root.

### No Qualitative Results

Confirm that:

- Source documents are stored under `data/documents/`.
- The files use the `.txt` extension.
- `python ingest.py` completed successfully.
- The `data/chroma/` directory exists.

### Missing ChromaDB Collection

Run `python ingest.py` and confirm that the `enterprise-docs` collection is created.

### Database Not Found

Confirm that `data/database.sqlite` exists. If necessary, run:

```bash
python build_database.py
```

### SQL Errors

Confirm that the database schema matches the tables and columns defined in `SCHEMA_CONTEXT` in `agents/quantitative.py`.

### Unexpected Validation Results

Set `VALIDATION_DEBUG=true` in `.env`, rerun the application, and review the captured model output before validation.

## Security and Data Handling

Do not place sensitive information in prompts, source documents, logs, or the local SQLite database unless the environment has been approved for that information.

Protect the Gemini API key and do not commit `.env` to source control.

The quantitative agent is restricted to read-only SQL, but generated responses should still be reviewed before being used for consequential decisions.


<!-- filename: README.md -->

## Query 1:

1. **What changes require code review before merge?**

2. > "Every change that affects production code, infrastructure, database migrations, security controls, customer-facing behavior, or shared libraries requires review before merge [Source 1]."

3. The validation did not flag anything:

   > `[Qualitative validation: PASSED] is_grounded: True refused_to_answer: False sources_cited: ['code-review-process.txt'] flag: False warning: None`

4. I accepted the response without any changes becaue it answered the question correctly. However, it is difficult to understand exactly where the information is coming from, especially as a user with a surface level understanding. The citation of [Source 1] does not really help determine where it came from. For this reason, I changed the prompt to cite the .txt file and line it came from instead.

5. When I made this change, it started to say that the information was no longer groudned in the sourced and multiple flags were raised. It turned out that by taking away the source number, I had messed witht he validator which was expecting that formation of citation formatting. For this reason, I modified the prompt once again to include both citation file name and source number. This allowed for the validation tests to pass again.

## Query 2:

1. **"Compare Q4 performance across regions"**

2. **Response**

   ### Observations

   **Revenue and Target:**

   - West: Revenue of $652,800.0 (Target: $678,912.0)
   - North: Revenue of $598,400.0 (Target: $622,336.0)
   - East: Revenue of $544,000.0 (Target: $565,760.0)
   - South: Revenue of $489,600.0 (Target: $509,184.0)

   **Attainment Rate:** All regions (West, North, East, and South) recorded the exact same attainment rate of 96.15%.

   **New Customers:**

   - West led with 102 new customers.
   - East followed with 93.
   - South recorded 84.
   - North had the lowest with 75.

   **Renewal Rate:**

   - East achieved the highest renewal rate at 98.46%.
   - West followed closely at 98.24%, then South at 98.15%, and North at 97.77%.

   **Win Rate:**

   - West recorded the highest win rate at 36.7%.
   - North recorded the lowest at 35.93%, with East (36.48%) and South (36.22%) falling in between.

   ### Conclusions

   The West region was the top overall performer in terms of total revenue generated, new customer acquisition, and win rate.

   Despite differing total revenue figures and targets, all regions performed uniformly relative to their specific targets, each reaching a 96.15% attainment rate.

   **SQL used:**

   `SELECT region, revenue, target_revenue, attainment_rate, new_customers, renewal_rate, win_rate FROM q4_regional_comparison`

3. All Passed `[Quantitative validation: PASSED] sql_validated: True sql_blocked: False execution_error: False flag: False warning: None`

4. I accepted Gemini's responses without changes. The validation layer confirmed that the SQL was read-only and excuted succesfully, producing no errors. Checking with the real data, it is accurate that the West led in revenue, East led in renewal rate, and all regions had a 96.15%.

5. One case were claude produced an output where I did not immediately trust was actually here where it said all three regions has the exact same attainment rate. I did not immediately accept the statement that all four regions had the exact same attainment rate of `96.15%`. I manually checked the regional revenue and target values before accepting the conclusion.

The calculation was consistent across the regions because each target was generated using the same relationship to revenue. As a result, every region had the same percentage attainment even though the revenue and target amounts differed.

## Query 3:

1. **"How does our employee satisfaction compare to industry standards and what policies might impact this?"**

2. **Both qualitative and quant:**

   **[Qualitative]** I cannot find this information in the provided documents.

   **[Quantitative]** Based on the SQL query results for the period 2026-Q1, here is the interpretation of employee satisfaction compared to industry standards and the associated policies:

   ### Observations

   **Company vs. Industry Benchmark:**

   The industry benchmark (department_benchmark / policy_benchmark) is 76.0 across all listed departments and policies.

   - Engineering (80.0) and Finance (77.0) have company satisfaction scores above the industry benchmark.
   - Customer Success (74.0), Operations (72.0), and Sales (70.0) have company satisfaction scores below the industry benchmark of 76.0.

   **Policies and Adoption Rates:** Four specific policies are tracked for the period, each showing uniform metrics across all departments:

   - Wellbeing and Time-Off Policy: Adoption rate of 80.0% with a policy satisfaction score of 74.2.
   - Hybrid Work Policy: Adoption rate of 75.0% with a policy satisfaction score of 73.5.
   - Manager Feedback Policy: Adoption rate of 68.0% with a policy satisfaction score of 73.3.
   - Learning and Development Policy: Adoption rate of 61.0% with a policy satisfaction score of 73.1.

   ### Conclusions

   Employee satisfaction varies by department; Engineering and Finance outperform the industry standard, whereas Customer Success, Operations, and Sales underperform relative to the 76.0 benchmark.

   The Wellbeing and Time-Off Policy currently has the highest adoption rate (80.0%) and the highest associated employee satisfaction score (74.2) among the listed policies, while the Learning and Development Policy has the lowest adoption (61.0%) and lowest satisfaction score (73.1).

   **SQL used:**

   `SELECT d.department, d.period, d.satisfaction_score AS company_satisfaction, d.industry_benchmark AS department_benchmark, p.policy_name, p.adoption_rate, p.employee_satisfaction_score AS policy_satisfaction_score, p.industry_benchmark AS policy_benchmark FROM employee_satisfaction d LEFT JOIN employee_policy_metrics p ON d.period = p.period`

   Both passed `[Qualitative validation: PASSED] is_grounded: False refused_to_answer: True sources_cited: [] flag: False warning: None`

   `[Quantitative validation: PASSED] sql_validated: True sql_blocked: False execution_error: False flag: False warning: None`

3. I accepted the quantiative response because it accurately returned the data concerning this query. However, I did not accept the qualitative response which indicated it had no information related to the topic. I knew there would be some text in the "employee-experience-policy.txt" file that would have some related information, but the model likely did not return it because the information didn't feel complete. For this reason, I added this line to the prompt, "If the answer can be partially answered, state so and explain the partial answer that can be provided rather than saying information cannot be found.", un qualitative.py. This drastically changed the qualitative agent's response to the following which highlights what it can answer and what it cannot:

4. > "I can partially answer your question.
   >
   > Regarding policies that might impact employee satisfaction and experience, Northstar Analytics has an Employee Experience Policy (owned by People Operations, Version 1.8) that monitors employee experience through surveys, listening sessions, manager practices, workload indicators, and retention patterns [Source 2: employee-experience-policy.txt]. Key elements of this policy include:
   >
   > **Listening and surveys:** People Operations conducts a quarterly employee experience survey measuring satisfaction, manager support, workload sustainability, role clarity, career growth, inclusion, and confidence in leadership [Source 2: employee-experience-policy.txt].
   >
   > **Manager expectations:** Managers are expected to hold regular one-to-one meetings, provide timely feedback, discuss development goals, and address workload concerns (such as identifying sustained overload, unclear priorities, repeated after-hours work, and team conflicts) [Source 2: employee-experience-policy.txt].
   >
   > **Workload and flexibility:** Employees may raise workload concerns, and flexible work arrangements are supported when compatible with customer commitments, security, collaboration, and role responsibilities [Source 2: employee-experience-policy.txt].
   >
   > **Learning and career growth:** Access to role-relevant learning, mentoring, and development conversations is provided [Source 2: employee-experience-policy.txt].
   >
   > **Psychological safety and concerns:** Employees may raise concerns about conduct, workload, management behavior, process friction, or customer-impacting risks without retaliation, with serious matters directed to confidential reporting channels [Source 2: employee-experience-policy.txt].
   >
   > **Policy impact review:** People Operations reviews employee experience trends alongside delivery workload, customer escalations, attrition, and business performance, adjusting policies if they create avoidable friction or prevent effective customer service [Source 2: employee-experience-policy.txt].
   >
   > Additionally, the Performance Management Policy outlines how performance is aligned with professional development, providing clarity, timely feedback, support for employees needing additional assistance, and calibration to improve consistency [Source 1: performance-management-policy.txt].
   >
   > However, the provided documents do not contain information regarding how our employee satisfaction compares to industry standards."

5. In basically every case where the agents had to use both quantiative and qualitative workflows, Gemini produced an output that I did not immediately trust because they were both working with incomplete information. For this reason, I added a create_combine_overview function which calls another AI agent when both workflows are used. It has the following prompt:

   > "You are an enterprise analysis synthesizer. "
   >
   > "Use only the two validated outputs provided. "
   >
   > "Combine the qualitative policy findings with the "
   >
   > "quantitative results into one concise overview. "
   >
   > "Do not invent facts or use outside knowledge. "
   >
   > "Preserve citations such as [Source 1]. "
   >
   > "Do not claim causation unless the evidence explicitly "
   >
   > "supports it. Clearly identify missing information, "
   >
   > "limitations, or differences between the two outputs."

   This resulted in a response that was able to relate the quantiative and qualitiative findings with a "how the two findings relate" and "important limitations and missing evidence sections" providing for a much more trustworthy answer. An example of which can be seen below:

   > **[Combined overview]**
   >
   > Based on the validated qualitative and quantitative outputs, here is a concise overview:
   >
   > ### 1. Key Quantitative Findings
   >
   > * **Department Satisfaction vs. Benchmark:** Employee satisfaction varies by department compared to the industry benchmark of 76.0. Engineering (80.0) and Finance (77.0) exceed the benchmark, while Customer Success (74.0), Operations (72.0), and Sales (70.0) fall below it.
   >
   > * **Policy Satisfaction vs. Benchmark:** Four company policies were evaluated, all of which fall below the policy industry benchmark of 76.0 (ranging from 73.1 to 74.2).
   >
   > * **Policy Adoption:** The **Wellbeing and Time-Off Policy** has the highest adoption rate (80.0%) and policy satisfaction score (74.2). Conversely, the **Learning and Development Policy** has the lowest adoption rate (61.0%) and satisfaction score (73.1), with the Hybrid Work Policy (75.0% adoption, 73.5 satisfaction) and Manager Feedback Policy (68.0% adoption, 73.3 satisfaction) falling in between.
   >
   > ### 2. Relevant Policies and Qualitative Context
   >
   > * **Employee Experience & Monitoring:** People Operations monitors employee experience and satisfaction through quarterly surveys (covering satisfaction, manager support, workload, role clarity, career growth, inclusion, and confidence in leadership), listening sessions, manager practices, workload indicators, and retention patterns [Source 2: employee-experience-policy.txt, chunk 0].
   >
   > * **Governing Policies:**
   >
   > * The **Employee Experience Policy** governs work environment goals, surveys, manager expectations, workload and flexibility, learning and career growth, and psychological safety [Source 2: employee-experience-policy.txt, chunk 0].
   >
   > * The **Performance Management Policy** impacts professional development, feedback clarity, calibration, and support for employees needing additional assistance [Source 1: performance-management-policy.txt, chunk 0].
   >
   > ### 3. How the Two Findings Relate
   >
   > The qualitative frameworks provide the mechanisms for how satisfaction is monitored and supported (such as surveys and performance policies), while the quantitative data measures the actual outcomes of these areas across departments and specific policies. For example, quantitative metrics track specific initiatives like learning/development and manager feedback, which align directly with the qualitative focus on career growth, learning, and manager support outlined in the Employee Experience and Performance Management policies.
   >
   > ### 4. Important Limitations and Missing Evidence
   >
   > * **Conflict in Evidence Regarding Industry Standards:** The qualitative output initially states that the documents do *not* provide information regarding how employee satisfaction compares to industry standards [Source 2: employee-experience-policy.txt, chunk 0], whereas the quantitative results successfully pull department and policy satisfaction scores against an industry benchmark of 76.0.
   >
   > * **Missing Causation:** The evidence does not explicitly state that specific policies *caused* the department satisfaction scores or adoption rates; the two datasets are presented side-by-side without causal validation.
   >
   > * **Granularity Limitations:** The quantitative data lists overall policy satisfaction scores and adoption rates, but does not break down how individual departments score across each specific policy.

