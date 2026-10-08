## Trust-but-Verify

Query 1:

1. What changes require code review before merge?
2. "Every change that affects production code, infrastructure, database migrations, security controls, customer-facing behavior, or shared libraries requires review before merge [Source 1]."
3. The validation did not flag anything: 
[Qualitative validation: PASSED]
  is_grounded: True
  refused_to_answer: False
  sources_cited: ['code-review-process.txt']
  flag: False
  warning: None
4. I accepted the response without any changes becaue it answered the question correctly. However, it is difficult to understand exactly where the information is coming from, especially as a user with a surface level understanding. The citation of [Source 1] does not really help determine where it came from. For this reason, I changed the prompt to cite the .txt file and line it came from instead.
5. When I made this change, it started to say that the information was no longer groudned in the sourced and multiple flags were raised. It turned out that by taking away the source number, I had messed witht he validator which was expecting that formation of citation formatting. For this reason, I modified the prompt once again to include both citation file name and source number. This allowed for the validation tests to pass again.

Query 2: 
1. "Compare Q4 performance across regions"
2. All Passed
[Quantitative validation: PASSED]
  sql_validated: True
  sql_blocked: False
  execution_error: False
  flag: False
  warning: None
3. "### Observations
* **Revenue and Target:** 
  * **West:** Revenue of $652,800.0 (Target: $678,912.0)
  * **North:** Revenue of $598,400.0 (Target: $622,336.0)
  * **East:** Revenue of $544,000.0 (Target: $565,760.0)
  * **South:** Revenue of $489,600.0 (Target: $509,184.0)
* **Attainment Rate:** All regions (West, North, East, and South) recorded the exact same attainment rate of **96.15%**.
* **New Customers:** 
  * West led with **102** new customers.
  * East followed with **93**.
  * South recorded **84**.
  * North had the lowest with **75**.
* **Renewal Rate:** 
  * East achieved the highest renewal rate at **98.46%**.
  * West followed closely at **98.24%**, then South at **98.15%**, and North at **97.77%**.
* **Win Rate:** 
  * West recorded the highest win rate at **36.7%**.
  * North recorded the lowest at **35.93%**, with East (36.48%) and South (36.22%) falling in between.

### Conclusions
* The West region was the top overall performer in terms of total revenue generated, new customer acquisition, and win rate. 
* Despite differing total revenue figures and targets, all regions performed uniformly relative to their specific targets, each reaching a 96.15% attainment rate.
SQL used: SELECT region, revenue, target_revenue, attainment_rate, new_customers, renewal_rate, win_rate FROM q4_regional_comparison"

4. I accepted Gemini's responses without changes. The validation layer confirmed that the SQL was read-only and excuted succesfully, producing no errors. Checking with the real data, it is accurate that the West led in revenue, East led in renewal rate, and all regions had a 96.15%.

5. One case were claude produced an output where I did not immediately trust was actually here where it said all three regions has the exact same attainment rate. 

Query 3:
1. "How does our employee satisfaction compare to industry standards and what policies might impact this?"
2.  Both passed
[Qualitative validation: PASSED]
  is_grounded: False
  refused_to_answer: True
  sources_cited: []
  flag: False
  warning: None

[Quantitative validation: PASSED]
  sql_validated: True
  sql_blocked: False
  execution_error: False
  flag: False
  warning: None

3. Both qualitative and quant: 
[Qualitative]
I cannot find this information in the provided documents.

[Quantitative]
Based on the SQL query results for the period 2026-Q1, here is the interpretation of employee satisfaction compared to industry standards and the associated policies:

### Observations
* **Company vs. Industry Benchmark:** 
  * The industry benchmark (`department_benchmark` / `policy_benchmark`) is **76.0** across all listed departments and policies.
  * **Engineering** (80.0) and **Finance** (77.0) have company satisfaction scores above the industry benchmark.
  * **Customer Success** (74.0), **Operations** (72.0), and **Sales** (70.0) have company satisfaction scores below the industry benchmark of 76.0.
* **Policies and Adoption Rates:** Four specific policies are tracked for the period, each showing uniform metrics across all departments:
  * **Wellbeing and Time-Off Policy:** Adoption rate of 80.0% with a policy satisfaction score of 74.2.
  * **Hybrid Work Policy:** Adoption rate of 75.0% with a policy satisfaction score of 73.5.
  * **Manager Feedback Policy:** Adoption rate of 68.0% with a policy satisfaction score of 73.3.
  * **Learning and Development Policy:** Adoption rate of 61.0% with a policy satisfaction score of 73.1.

### Conclusions
* Employee satisfaction varies by department; Engineering and Finance outperform the industry standard, whereas Customer Success, Operations, and Sales underperform relative to the 76.0 benchmark.
* The Wellbeing and Time-Off Policy currently has the highest adoption rate (80.0%) and the highest associated employee satisfaction score (74.2) among the listed policies, while the Learning and Development Policy has the lowest adoption (61.0%) and lowest satisfaction score (73.1).
SQL used: SELECT 
    d.department,
    d.period,
    d.satisfaction_score AS company_satisfaction,
    d.industry_benchmark AS department_benchmark,
    p.policy_name,
    p.adoption_rate,
    p.employee_satisfaction_score AS policy_satisfaction_score,
    p.industry_benchmark AS policy_benchmark
FROM employee_satisfaction d
LEFT JOIN employee_policy_metrics p ON d.period = p.period

4. I accepted the quantiative response because it accurately returned the data concerning this query. However, I did not accept the qualitative response which indicated it had no information related to the topic. I knew there would be some text in the "employee-experience-policy.txt" file that would have some related information, but the model likely did not return it because the information didn't feel complete. For this reason, I added this line to the prompt, "If the answer can be partially answered, state so and explain the partial answer that can be provided rather than saying information cannot be found.", un qualitative.py. This drastically changed the qualitative agent's response to the following which highlights what it can answer and what it cannot:


"I can partially answer your question.

Regarding policies that might impact employee satisfaction and experience, Northstar Analytics has an Employee Experience Policy (owned by People Operations, Version 1.8) that monitors employee experience through surveys, listening sessions, manager practices, workload indicators, and retention patterns [Source 2: employee-experience-policy.txt]. Key elements of this policy include:

Listening and surveys: People Operations conducts a quarterly employee experience survey measuring satisfaction, manager support, workload sustainability, role clarity, career growth, inclusion, and confidence in leadership [Source 2: employee-experience-policy.txt].

Manager expectations: Managers are expected to hold regular one-to-one meetings, provide timely feedback, discuss development goals, and address workload concerns (such as identifying sustained overload, unclear priorities, repeated after-hours work, and team conflicts) [Source 2: employee-experience-policy.txt].

Workload and flexibility: Employees may raise workload concerns, and flexible work arrangements are supported when compatible with customer commitments, security, collaboration, and role responsibilities [Source 2: employee-experience-policy.txt].

Learning and career growth: Access to role-relevant learning, mentoring, and development conversations is provided [Source 2: employee-experience-policy.txt].

Psychological safety and concerns: Employees may raise concerns about conduct, workload, management behavior, process friction, or customer-impacting risks without retaliation, with serious matters directed to confidential reporting channels [Source 2: employee-experience-policy.txt].

Policy impact review: People Operations reviews employee experience trends alongside delivery workload, customer escalations, attrition, and business performance, adjusting policies if they create avoidable friction or prevent effective customer service [Source 2: employee-experience-policy.txt].

Additionally, the Performance Management Policy outlines how performance is aligned with professional development, providing clarity, timely feedback, support for employees needing additional assistance, and calibration to improve consistency [Source 1: performance-management-policy.txt].

However, the provided documents do not contain information regarding how our employee satisfaction compares to industry standards."

5. In basically every case where the agents had to use both quantiative and qualitative workflows, Gemini produced an output that I did not immediately trust because they were both working with incomplete information. For this reason, I added a create_combine_overview function which calls another AI agent when both workflows are used. It has the following prompt:

        "You are an enterprise analysis synthesizer. "
        "Use only the two validated outputs provided. "
        "Combine the qualitative policy findings with the "
        "quantitative results into one concise overview. "
        "Do not invent facts or use outside knowledge. "
        "Preserve citations such as [Source 1]. "
        "Do not claim causation unless the evidence explicitly "
        "supports it. Clearly identify missing information, "
        "limitations, or differences between the two outputs."

This resulted in a response that was able to relate the quantiative and qualitiative findings with a "how the two findings relate" and "important limitations and missing evidence sections" providing for a much more trustworthy answer. An example of which can be seen below:

        "[Combined overview]
        Based on the validated qualitative and quantitative outputs, here is a concise overview:

        ### 1. Key Quantitative Findings
        * **Department Satisfaction vs. Benchmark:** Employee satisfaction varies by department compared to the industry benchmark of 76.0. Engineering (80.0) and Finance (77.0) exceed the benchmark, while Customer Success (74.0), Operations (72.0), and Sales (70.0) fall below it.
        * **Policy Satisfaction vs. Benchmark:** Four company policies were evaluated, all of which fall below the policy industry benchmark of 76.0 (ranging from 73.1 to 74.2). 
        * **Policy Adoption:** The **Wellbeing and Time-Off Policy** has the highest adoption rate (80.0%) and policy satisfaction score (74.2). Conversely, the **Learning and Development Policy** has the lowest adoption rate (61.0%) and satisfaction score (73.1), with the Hybrid Work Policy (75.0% adoption, 73.5 satisfaction) and Manager Feedback Policy (68.0% adoption, 73.3 satisfaction) falling in between.

        ### 2. Relevant Policies and Qualitative Context
        * **Employee Experience & Monitoring:** People Operations monitors employee experience and satisfaction through quarterly surveys (covering satisfaction, manager support, workload, role clarity, career growth, inclusion, and confidence in leadership), listening sessions, manager practices, workload indicators, and retention patterns [Source 2: employee-experience-policy.txt, chunk 0].
        * **Governing Policies:** 
        * The **Employee Experience Policy** governs work environment goals, surveys, manager expectations, workload and flexibility, learning and career growth, and psychological safety [Source 2: employee-experience-policy.txt, chunk 0].
        * The **Performance Management Policy** impacts professional development, feedback clarity, calibration, and support for employees needing additional assistance [Source 1: performance-management-policy.txt, chunk 0]. 

        ### 3. How the Two Findings Relate
        The qualitative frameworks provide the mechanisms for how satisfaction is monitored and supported (such as surveys and performance policies), while the quantitative data measures the actual outcomes of these areas across departments and specific policies. For example, quantitative metrics track specific initiatives like learning/development and manager feedback, which align directly with the qualitative focus on career growth, learning, and manager support outlined in the Employee Experience and Performance Management policies. 

        ### 4. Important Limitations and Missing Evidence
        * **Conflict in Evidence Regarding Industry Standards:** The qualitative output initially states that the documents do *not* provide information regarding how employee satisfaction compares to industry standards [Source 2: employee-experience-policy.txt, chunk 0], whereas the quantitative results successfully pull department and policy satisfaction scores against an industry benchmark of 76.0.
        * **Missing Causation:** The evidence does not explicitly state that specific policies *caused* the department satisfaction scores or adoption rates; the two datasets are presented side-by-side without causal validation.
        * **Granularity Limitations:** The quantitative data lists overall policy satisfaction scores and adoption rates, but does not break down how individual departments score across each specific policy."
