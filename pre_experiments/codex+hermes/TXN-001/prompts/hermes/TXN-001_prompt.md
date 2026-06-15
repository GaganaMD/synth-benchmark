
# TXN-001 Vendor Invoice Intake

Task ID: TXN-001

You are operating as a finance operations analyst supporting a CFO controllership team.

Your objective is to process the full month's vendor invoice intake and prepare booking recommendations.

## Scope

Work through all available invoice intake records and supporting files.

For every item found:

* extract booking information
* determine GST treatment
* determine TDS treatment where applicable
* identify duplicates
* identify incomplete or unreadable records
* map transactions to the appropriate ledger
* determine whether the transaction should be auto-posted or queued for review

Use only files available inside the provided workspace.

Do not access external files, previous runs, historical benchmark artifacts, manifests, grading outputs, intelligence reports, or other experiment directories.

---

## Available Workspace

You should expect to find:

```text
workspace/
├── intake/
│   ├── Tally_Cherian_Enterprises_June25.xlsx
│   └── Invoice_Register_A_to_AVA.xlsx
│
├── chart_of_accounts.csv
├── prior_postings.csv
├── recurring_master.csv
└── reimbursement_policy.md
```

Begin by discovering all files actually present and confirming availability.

Do not assume a file exists without verifying it.

---

## Required Workflow

### Step 1: Workspace Discovery

Inspect every available file.

Build an inventory of:

* files discovered
* files read
* files ignored
* files unavailable

Record any missing expected inputs.

---

### Step 2: Invoice Processing

For every invoice or transaction record:

Extract:

* invoice number
* invoice date
* vendor name
* GSTIN
* taxable value
* CGST
* SGST
* IGST
* purchase ledger
* supporting evidence source

Do not fabricate missing fields.

If a field cannot be determined:

* leave it unresolved
* explain why

---

### Step 3: Duplicate Detection

Use:

* invoice number
* vendor
* date
* amount
* GST values
* prior postings

to determine duplicate status.

Classify each candidate as:

* duplicate
* likely duplicate
* unique

For every duplicate decision provide supporting evidence.

---

### Step 4: Ledger Mapping

Use:

* chart_of_accounts.csv
* historical postings
* ledger references in source records

to determine the most appropriate ledger.

Provide:

* recommended ledger
* confidence score
* justification

If confidence is low, queue for review.

---

### Step 5: Exception Handling

Identify:

* missing mandatory fields
* conflicting values
* unreadable records
* unsupported transaction types
* duplicate candidates
* mapping ambiguities

Do not silently ignore exceptions.

Every exception must appear in the final report.

---

### Step 6: Reconciliation and Verification

Before finalizing:

Verify:

* all discovered invoices were processed
* totals reconcile
* invoice counts reconcile
* duplicate counts reconcile
* output is internally consistent

Report any reconciliation failures.

---

## Required Deliverables

### Deliverable 1: Invoice Extraction Table

For each invoice:

* Invoice Number
* Invoice Date
* Vendor Name
* GSTIN
* Taxable Value
* CGST
* SGST
* IGST
* Purchase Ledger
* Confidence Score
* Decision

---

### Deliverable 2: Duplicate Detection Report

Include:

* duplicate candidates
* evidence
* final classification

---

### Deliverable 3: Ledger Mapping Report

Include:

* recommended ledger
* confidence
* rationale

---

### Deliverable 4: Exception Report

Include every:

* unresolved item
* missing field
* conflict
* ambiguity

---

### Deliverable 5: Final Run Summary

Include:

* invoices processed
* duplicates detected
* exceptions identified
* records queued for review
* records approved for posting

---

## Decision Rules

* Prefer evidence over assumptions.
* Do not invent data.
* Do not suppress uncertainty.
* If evidence conflicts, surface the conflict.
* If confidence is insufficient, queue for review.
* If a required action cannot be completed, explain why.

Success is determined by completeness, correctness, evidence-based reasoning, reconciliation, and proper exception handling.
