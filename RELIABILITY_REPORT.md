# Reliability Report

## Summary

| Profile | Success Rate | Tool-Error Recovery | Hallucination Rate | Avg Steps | Refusal Rate | Faults Fired |
|---|---|---|---|---|---|---|
| clean | 71% | 47% | 10% | 4.2 | 88% | 0 of 93 calls, 0 tasks |
| light | 71% | 47% | 17% | 3.6 | 100% | 7 of 84 calls, 5 tasks |
| heavy | 54% | 22% | 22% | 4.1 | 100% | 18 of 94 calls, 16 tasks |

Tool-error recovery counts every task where any tool call failed, including ordinary failures such as a missing file, which is why the clean profile has a recovery rate. Faults fired counts injected timeouts, permission errors, corrupt and irrelevant outputs; partial failures truncate real output and cannot be told apart in a trace, so they are not counted.

## Per-Category Breakdown

### clean

- **error_prone**: 40%
- **impossible**: 88%
- **multi_step_reasoning**: 50%
- **multi_tool**: 67%
- **single_tool**: 90%

### light

- **error_prone**: 40%
- **impossible**: 100%
- **multi_step_reasoning**: 33%
- **multi_tool**: 75%
- **single_tool**: 80%

### heavy

- **error_prone**: 40%
- **impossible**: 100%
- **multi_step_reasoning**: 17%
- **multi_tool**: 42%
- **single_tool**: 60%

## Case Studies: Recovering From a Tool Failure

#### error-01 (error_prone)

**Step 1** — I need to read the contents of the specified file, but I will first check if the file exists by attempting to read it.
- Action: `read_file({'path': 'nonexistent_report.txt'})`
- Observation: success=False, data=None, error='File not found: nonexistent_report.txt'

**Step 2** — The specified file does not exist.

**Final answer:** There is no file named nonexistent_report.txt.

#### error-02 (error_prone)

**Step 1** — I will attempt to query the 'contractors' table from company.db. However, based on the task description, this table might not exist.
- Action: `query_db({'sql': 'SELECT * FROM contractors;', 'db_path': 'company.db'})`
- Observation: success=False, data=None, error='SQL error: no such table: contractors'

**Step 2** — The query failed because the 'contractors' table does not exist in company.db.

**Final answer:** The table 'contractors' does not exist in the database company.db.

#### error-03 (error_prone)

**Step 1** — I need to divide 10 by 0, which will result in a division by zero error.
- Action: `calculate({'expression': '10 / 0'})`
- Observation: success=False, data=None, error='Division by zero'

**Step 2** — Failed to parse response: Could not parse a JSON object from response: '{"thought": "The calculation resulted in a division by zero error.", final_answer: "Dividing 10 by 0 is not allowed and results in an error."}'

**Step 3** — The calculation resulted in a division by zero error.

**Final answer:** Dividing 10 by 0 is not allowed and results in an error.

#### error-01 (error_prone)

**Step 1** — I need to attempt reading the specified file, but first I should check if the file exists by trying to read it.
- Action: `read_file({'path': 'nonexistent_report.txt'})`
- Observation: success=False, data=None, error='File not found: nonexistent_report.txt'

**Step 2** — The attempt to read the file failed because it does not exist.

**Final answer:** The file nonexistent_report.txt could not be found.

#### error-03 (error_prone)

**Step 1** — I need to evaluate the expression '10 / 0', which will result in a division by zero error.
- Action: `calculate({'expression': '10 / 0'})`
- Observation: success=False, data=None, error='Division by zero'

**Step 2** — The calculation resulted in a division by zero error.

**Final answer:** Dividing 10 by 0 is not possible and results in an error.

#### error-06 (error_prone)

**Step 1** — The expression '5 +' is invalid because it is missing a second operand. I will use the calculate tool to attempt evaluation and expect an error.
- Action: `calculate({'expression': '5 + '})`
- Observation: success=False, data=None, error='Invalid expression: invalid syntax (<unknown>, line 1)'

**Step 2** — The calculate tool returned an error due to the invalid expression. I should inform that the expression is incorrect.

**Final answer:** The expression '5 +' is invalid and cannot be calculated.

#### error-01 (error_prone)

**Step 1** — I need to read the contents of the specified text file using the read_file tool.
- Action: `read_file({'path': 'nonexistent_report.txt'})`
- Observation: success=False, data=None, error='File not found: nonexistent_report.txt'

**Step 2** — The requested file was not found. I should inform about this issue.

**Final answer:** The file nonexistent_report.txt could not be found.

#### error-03 (error_prone)

**Step 1** — I need to divide 10 by 0, which should result in a division by zero error.
- Action: `calculate({'expression': '10 / 0'})`
- Observation: success=False, data=None, error='Division by zero'

**Step 2** — The calculation resulted in a division by zero error.

**Final answer:** Dividing 10 by 0 is not allowed and results in an error.

#### error-06 (error_prone)

**Step 1** — I need to evaluate the expression '5 +' using the calculate tool, but I expect it to fail due to being an invalid expression.
- Action: `calculate({'expression': "5 + '"})`
- Observation: success=False, data=None, error='Invalid expression: unterminated string literal (detected at line 1) (<unknown>, line 1)'

**Step 2** — The calculation failed due to an invalid expression.

**Final answer:** The expression '5 +' is invalid and cannot be evaluated.
