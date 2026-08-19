**You:**

Neurotype Take-Home 1 of 2 - The Brief.pdf

I am doing a second-stage interview, where the interviewers gave me some take-home work to finish. I attach their requirements here. Please summerize/ explain it with proper English to me so that I can make sure I understand them.

* * *

**ChatGPT:**

Yes. I’ve read the brief carefully. It is intentionally written as a **product/engineering challenge rather than a detailed technical specification**: they want you to make reasonable engineering decisions, while demonstrating that you understand the core workflow and can deliver a narrow end-to-end slice.

The brief is one page and explicitly says that **the brief itself is the source of truth** for the invented assessment/scoring system.

## 1. What are you actually being asked to build?

In simple terms:

> **Build a small web application that allows a clinician to review neurodevelopmental assessments, filter a queue of assessments, inspect an individual assessment, and issue its report.**

The system has:

* **Python backend**
* **React + TypeScript frontend**
* Docker Compose for running everything
* Frontend available at `:5173`
* Backend health endpoint at `:8000/health` returning HTTP 200

Everything else—database, framework details, API design, UI library, persistence mechanism, etc.—is your choice.

The most important sentence in the brief is near the end:

> A reviewer should be able to **open the queue → narrow it → open an assessment → issue the report**, end to end.

They explicitly prefer this **small but fully working workflow** over a much larger system with incomplete functionality.

* * *

# 2. The business scenario

Imagine a clinician has assessed a young person.

The assessment produces:

1. A score for several neurodevelopmental domains.
2. A written summary.

A second clinician—the **reviewing clinician**—looks at the assessment.

If they are satisfied, they **issue the report**.

After issuing:

* The report is considered fixed because copies have already been sent to the family, school and GP.
* Actually sending those copies is **outside your system**.
* However, clinicians may subsequently need to correct a typo in the written summary.
* The calculated percentages, support-need bands and review flag are **not fixed values**; they are calculated values and may change.

That last distinction is important from a data-model perspective.

* * *

# 3. The input data

You are given an `assessments.jsonl` file containing around 100 assessments.

JSONL means:

> **One JSON object per line.**

An assessment roughly looks like this:

```JSON
{
  "assessment_id": "a-00001",
  "client": {
    "date_of_birth": "2014-03-02",
    "nhs_number": "999 476 5919",
    "guardian_contact": "j.okafor@example.com",
    "safeguarding_notes": "Contact via mother only. Father not to be given dates."
  },
  "assessed_at": "2026-03-02T09:30:00+00:00",
  "clinician_id": "c-005",
  "domains": [
    {
      "domain": "social_communication",
      "items": [
        {
          "code": "SC1",
          "raw": 12,
          "max": 20,
          "completed": true
        },
        {
          "code": "SC2",
          "raw": null,
          "max": 20,
          "completed": false
        }
      ]
    }
  ],
  "summary": "Free text..."
}
```

There are **five domains**:

* `social_communication`
* `sensory_processing`
* `executive_function`
* `emotional_regulation`
* `motor_coordination`

Each domain has **3–6 items**.

An item can be incomplete because the young person was unable or unwilling to complete it.

* * *

# 4. You have to calculate the scores

The input JSON does **not** contain the calculated domain scores or support-need bands. Your application needs to calculate them.

For each domain:

### Percentage

The brief defines it as:

> mean of `(raw / max) × 100` across its items.

For example, suppose a domain has:

| Item | raw | max |
| --- | --- | --- |
| A | 10 | 20 |
| B | 15 | 20 |
| C | 12 | 20 |

Then:

```
A = 10 / 20 × 100 = 50
B = 15 / 20 × 100 = 75
C = 12 / 20 × 100 = 60

Domain percentage = (50 + 75 + 60) / 3
                   = 61.67
```

### Support-need band

Then convert the percentage into:

| Percentage | Band |
| --- | --- |
| 0–39 | Minimal |
| 40–54 | Mild |
| 55–84 | Moderate |
| 85–100 | Substantial |

These calculations are explicitly specified in the brief.

### One important ambiguity

There is an interesting detail here that I would **not silently assume**:

> What happens when an item is incomplete and therefore has `raw: null`?

The brief says the domain percentage is the mean across its items, but an incomplete item has no `raw` value.

So you need to make an explicit engineering decision, probably something like:

> Exclude incomplete items from the percentage calculation, while allowing their presence to trigger the review flag.

I would document this assumption in your second document because the brief does not explicitly define the treatment of `null` scores.

That is exactly the kind of ambiguity they may be deliberately testing.

* * *

# 5. Calculate the young person's age

The report should show the young person's:

> **age in years and months at the date of assessment**

So, given:

```
date_of_birth = 2014-03-02
assessed_at   = 2026-03-02
```

the result is:

```
12 years, 0 months
```

This should be calculated rather than stored as a fixed field.

* * *

# 6. Calculate the review flag

Every assessment gets a **review flag: on/off**.

The flag is **ON if any one of these conditions is true**:

### Condition 1 — Substantial domain

Any domain has:

```
band = Substantial
```

### Condition 2 — Incomplete item

Any assessment item has:

```
completed = false
```

### Condition 3 — Short summary

The summary has fewer than:

```
200 characters
```

So logically:

```
review_flag =
    any_substantial_domain
    OR any_incomplete_item
    OR summary_length < 200
```

This is a particularly important part of the UI because the reviewer needs to be able to filter the queue based on this flag.

* * *

# 7. The main screen: the review queue

This is probably the most important UI.

The reviewer starts with a **queue of assessments**.

The queue is supposed to represent assessments from **everything the service holds**, rather than just the 100 sample records you have been given.

For the take-home, obviously the sample data is what you have available.

The reviewer needs to be able to narrow the queue by:

1. **How an assessment scored**
2. **Whether it is flagged**
3. **Which clinician performed the assessment**

The brief doesn't prescribe exactly what "how an assessment scored" means.

I would interpret this primarily as filtering by **support-need band / domain score**, because those are the calculated scoring concepts defined in the brief.

This is another area where you should make your interpretation explicit rather than pretending the requirement is more precise than it actually is.

* * *

# 8. Opening an assessment

When the reviewer clicks an assessment, they need to see the **whole assessment**.

At minimum:

### Client information

* Date of birth
* NHS number
* Guardian contact
* Safeguarding notes

### Assessment information

* Assessment ID
* Assessment date/time
* Clinician

### Domain results

For each of the five domains:

* Items
* Raw/max scores
* Completion status
* Calculated percentage
* Support-need band

### Summary

The full written summary.

The brief explicitly says:

> Opening one shows the whole thing: the client, the results per domain, the summary.

* * *

# 9. Issuing the report

The reviewer needs an **Issue Report** action.

The happy path is:

```
Review queue
     ↓
Filter/narrow queue
     ↓
Open assessment
     ↓
Review assessment
     ↓
Issue report
     ↓
Assessment becomes issued
```

Once issued, the report is considered fixed because copies have already gone out.

You **do not need to implement**:

* email delivery
* printing
* sending to GP
* sending to school
* sending to family

Those are explicitly somebody else's responsibility.

* * *

# 10. But there's an interesting exception after issuing

The brief says clinicians sometimes need to correct an occasional typo in the summary **after the report has been issued**.

So the system needs some mechanism for:

```
Edit summary
```

even after issuing.

However:

> **The percentages, bands and review flag are calculated values and can change.**

So you shouldn't think of the report as simply:

```
Assessment → immutable forever
```

Instead, there are two concepts:

### Source data

Things such as:

* assessment data
* item scores
* summary
* client information

### Derived data

Things such as:

* percentages
* bands
* review flag
* age

The latter should be calculated from the former.

This distinction is likely intentional and is worth reflecting in your architecture.

* * *

# 11. Audit trail

This is another significant requirement.

Client records are audited.

The system must be able to answer:

> **Who looked at what, when, and what changed?**

So you need some kind of audit history.

For example, conceptually:

```
AUDIT LOG

10:31  Reviewer A opened assessment a-00001
10:35  Reviewer A issued assessment a-00001
14:22  Clinician B changed summary of a-00001
14:22  Previous summary → New summary
```

The brief doesn't prescribe:

* audit-log database schema
* API
* UI
* whether every read must be audited
* authentication mechanism
* exact actor identity mechanism

Those are engineering decisions for you.

But **the capability itself is definitely required**.

* * *

# 12. Testing

They deliberately leave testing to you:

> "Tests are your call: tell us what you thought worth testing."

This is actually an opportunity to demonstrate engineering maturity.

I would expect at least:

### Unit tests

For the scoring logic:

```
raw/max → percentage
percentage → band
assessment → review flag
DOB + assessment date → age
```

Especially test boundary conditions:

```
39 → Minimal
40 → Mild
54 → Mild
55 → Moderate
84 → Moderate
85 → Substantial
```

And:

```
summary length = 199 → flagged
summary length = 200 → not flagged (assuming no other condition)
```

Also test incomplete items.

### API/integration tests

For things such as:

```
GET assessments
GET assessment/{id}
POST issue
PATCH summary
GET audit history
```

### Frontend tests

Potentially test:

* filtering
* displaying assessment details
* issue workflow
* editing summary

You don't necessarily need to test every pixel of the UI.

* * *

# 13. Docker requirement

They want the evaluator to be able to do essentially:

```Bash
docker compose up
```

on a machine that has **only Docker installed**.

And then:

```
http://localhost:5173
```

should give them the frontend.

And:

```
http://localhost:8000/health
```

should return HTTP 200.

This means you need to package the whole thing:

```
                Docker Compose
                      │
          ┌───────────┴───────────┐
          │                       │
     React frontend          Python backend
        :5173                    :8000
                                  │
                                  │
                              Data storage
```

You are free to choose whether that storage is:

* SQLite
* PostgreSQL
* files
* etc.

For a four-hour take-home, I would strongly favour **SQLite**, unless the supplied harness or second document gives you a reason to use something heavier.

* * *

# 14. What they are _not_ asking you to build

This is important because the brief says there is deliberately **more work than can fit into four hours**.

You don't need to build a complete clinical system.

In particular, you don't need to implement:

* actual clinical assessment collection
* authentication/SSO
* sending reports to families
* sending reports to schools
* sending reports to GPs
* sophisticated user/role management
* sophisticated deployment infrastructure
* production-grade cloud infrastructure
* a huge UI
* every conceivable filter
* every possible CRUD operation

The supplied JSONL is effectively your input.

* * *

# 15. What I think they are really evaluating

Reading between the lines, I think the exercise is testing considerably more than whether you can write React and Python.

They want to see whether you can take an **underspecified real-world requirement** and make sensible engineering decisions.

I'd break their evaluation into roughly these areas:

| Area | What they probably want to see |
| --- | --- |
| Requirements understanding | Correctly identify the core workflow |
| Backend | Clean API and sensible domain model |
| Frontend | Usable review workflow |
| Data modelling | Good separation between source and calculated data |
| Business logic | Correct scoring/banding/flag calculations |
| Edge cases | Boundary conditions and incomplete items |
| Auditability | Who/what/when/change history |
| Architecture | Reasonable choices without over-engineering |
| Testing | Testing the important business rules |
| Docker | One-command reproducible startup |
| Prioritisation | Deliver the critical path rather than 20 half-finished features |
| Documentation | Clearly explain assumptions and omissions |

The last two are particularly explicit. They say:

> **"A narrow path that works beats a broad one that does not."**

And:

> **"Write down what you left and why; the second document says where."**

So I would **not** try to impress them by building an enormous application.

* * *

# 16. My interpretation of the minimum viable submission

If I were implementing this take-home, my minimum target would be:

```
                    ┌──────────────────────┐
                    │   Review Queue       │
                    │                      │
                    │ Filters:             │
                    │ • Band               │
                    │ • Review flag        │
                    │ • Clinician          │
                    │                      │
                    │ Assessment list      │
                    └──────────┬───────────┘
                               │
                         select assessment
                               │
                               ▼
                    ┌──────────────────────┐
                    │ Assessment Detail    │
                    │                      │
                    │ Client information    │
                    │ Domain 1              │
                    │ Domain 2              │
                    │ ...                  │
                    │ Domain 5              │
                    │ Summary              │
                    │                      │
                    │ [Issue Report]       │
                    └──────────┬───────────┘
                               │
                             issue
                               │
                               ▼
                    ┌──────────────────────┐
                    │      Issued          │
                    │                      │
                    │ [Edit Summary]       │
                    └──────────────────────┘
```

Behind that:

```
JSONL
  ↓
Python backend
  ↓
persistent data
  ↓
REST API
  ↓
React/TypeScript
```

And separately:

```
Every relevant action
        ↓
    Audit log
```

* * *

## 17. The requirements I would explicitly clarify in your design document

There are several places where the brief **doesn't fully specify the behaviour**. Don't silently make these decisions. State them.

### A. Incomplete items and scoring

The biggest one.

If:

```JSON
{
  "raw": null,
  "completed": false
}
```

does that item participate in the domain mean?

The brief doesn't say.

I'd document your chosen interpretation.

### B. Meaning of "how an assessment scored"

Does this mean:

* overall band?
* any domain band?
* individual domain percentage?
* score range?

The brief doesn't define it precisely.

### C. What constitutes "looked at"

For audit purposes, does simply opening an assessment count as "looked at"?

I'd say yes and record the view.

### D. Authentication

The brief requires identifying clinicians in the audit trail but doesn't specify authentication.

For a take-home, you can probably use a simple development reviewer identity and explain that production authentication would be provided by an identity provider.

### E. Issued-state editing

They explicitly require correcting summaries after issue, so you need to make clear what can and cannot be edited after issuance.

I would make:

```
Summary → editable
Raw assessment items → not editable
Calculated results → derived
Issue status → cannot be undone
```

unless the second document gives different instructions.

* * *

## 18. In one sentence

If you want the shortest possible interpretation of the assignment:

> **Build a Dockerised Python + React application where a reviewing clinician can filter a queue of assessments, inspect calculated domain results and client information, issue a report, subsequently correct its summary, and where the system maintains an audit trail of who accessed or changed the record.**

And the **single most important deliverable** is the working end-to-end path:

**queue → filter → assessment → issue**.

Since this is **"1 of 2"**, I would expect the second document to be particularly important for telling you what they want documented about your implementation decisions and what you deliberately leave out. If you upload the second document, I can analyse how the two documents fit together and turn the requirements into a concrete implementation plan.

* * *

**You:**

Neurotype Take-Home 2 of 2 - How This Works.pdf

Here is the second part of the document. Please see if you have anything to update. I also want you to define/ explain the jargons, like queue, domains, items of the domain etc.

* * *

**ChatGPT:**

Yes. The second document changes my interpretation in a few important ways. In particular, **this is not primarily a test of whether you can build a large full-stack application**. It is explicitly a test of whether you can **use an AI coding agent effectively and then critically reason about its output**. Those two aspects are weighted approximately equally.

I'll first explain the terminology, then give you the updated understanding of the assignment.

* * *

# 1. The domain terminology

The brief uses some terminology that is natural to people working in clinical/assessment software but may be unfamiliar if you haven't worked in this area.

## Assessment

An **assessment** is one complete evaluation of a young person by a clinician.

Think of it as one record:

```
Assessment
├── Client information
├── Assessment date
├── Clinician
├── Domain 1
├── Domain 2
├── Domain 3
├── Domain 4
├── Domain 5
└── Written summary
```

For example:

```
assessment_id: a-00001
client: John
assessed_at: 2026-03-02
clinician: c-005
domains: [...]
summary: "..."
```

The input `assessments.jsonl` contains **100 separate assessments**, one assessment per line.

* * *

# 2. Domain

A **domain** is a broad area being assessed.

There are exactly five domains in this exercise:

1. **Social communication**
2. **Sensory processing**
3. **Executive function**
4. **Emotional regulation**
5. **Motor coordination**

You can think of a domain as a **category of related questions/items**.

For example:

```
Social communication
    ├── SC1
    ├── SC2
    ├── SC3
    └── SC4
```

The brief says each domain contains **3–6 items**.

Importantly, these are **invented domains for the exercise**. You don't need to understand the actual clinical meaning of them. The second document explicitly says that no clinical knowledge is required and that both the instrument and scoring are synthetic.

* * *

# 3. Item

An **item** is an individual question/measurement within a domain.

For example:

```
Domain: social_communication

Item SC1
    raw = 12
    max = 20
    completed = true

Item SC2
    raw = null
    max = 20
    completed = false
```

So the hierarchy is:

```
Assessment
   │
   ├── Domain: social_communication
   │      ├── Item SC1
   │      ├── Item SC2
   │      └── Item SC3
   │
   ├── Domain: sensory_processing
   │      ├── Item SP1
   │      ├── Item SP2
   │      └── ...
   │
   ├── Domain: executive_function
   │      └── ...
   │
   ├── Domain: emotional_regulation
   │      └── ...
   │
   └── Domain: motor_coordination
          └── ...
```

This hierarchy is probably the most important terminology to understand.

* * *

# 4. Raw score

`raw` is the actual score obtained for an item.

For example:

```
raw = 12
max = 20
```

means the person scored 12 out of a possible 20.

The **raw score is input data**. Your application should not modify it.

* * *

# 5. Max score

`max` is the maximum possible score for that item.

So:

```
raw = 12
max = 20
```

means:

```
12 / 20
```

The percentage calculation is then applied.

* * *

# 6. Completed

`completed` tells you whether the item was actually completed.

```JSON
"completed": true
```

means the item was completed.

```JSON
"completed": false
```

means the young person was unable or unwilling to complete it.

When it is incomplete, `raw` is `null`.

This distinction matters because **an incomplete item automatically causes the assessment to be flagged for review**, regardless of its score.

* * *

# 7. Domain score / percentage

The system calculates a percentage for each domain.

It is **not stored in the input JSON**.

The calculation is:

```
mean of (raw / max × 100)
```

across the domain's items.

For example:

```
Item 1: 10 / 20 = 50%
Item 2: 15 / 20 = 75%
Item 3: 12 / 20 = 60%

Domain percentage = mean(50, 75, 60)
                  = 61.67%
```

The domain percentage is then converted into a **support-need band**.

* * *

# 8. Support-need band

A **band** is simply a category derived from the numerical percentage.

| Percentage | Band |
| --- | --- |
| 0–39 | Minimal |
| 40–54 | Mild |
| 55–84 | Moderate |
| 85–100 | Substantial |

So:

```
61.67%
   ↓
Moderate
```

This is another example of a **derived value**: the source data contains the item scores, while the percentage and band are calculated by your application.

* * *

# 9. Review flag

A **flag** is an indicator that tells the reviewer:

> "Pay particular attention to this assessment."

The flag is ON if **any** of these conditions is true:

```
1. Any domain has a Substantial band
OR
2. Any item is incomplete
OR
3. The summary has fewer than 200 characters
```

So this is essentially:

```Python
flagged = (
    has_substantial_domain
    or has_incomplete_item
    or summary_too_short
)
```

It's not itself a clinical diagnosis or score. It's a **workflow indicator for the reviewing clinician**.

* * *

# 10. Queue

This is probably the most important piece of terminology for understanding the UI.

A **queue** is a collection of things waiting to be processed.

For example, imagine a support ticket system:

```
Tickets waiting for support engineers

Ticket #1
Ticket #2
Ticket #3
...
```

That's a queue.

Here, the things waiting to be processed are **assessments waiting for review**.

So the review queue might look conceptually like:

| Assessment | Clinician | Score | Flag | Status |
| --- | --- | --- | --- | --- |
| a-00001 | c-005 | Moderate | ⚠ | Pending |
| a-00002 | c-003 | Mild |  | Pending |
| a-00003 | c-005 | Substantial | ⚠ | Pending |
| ... | ... | ... | ... | ... |

The reviewer opens this queue and decides which assessment to review.

The brief says reviewers work through a queue of assessments drawn from everything the service holds. They need to narrow that queue by score, flag status and clinician.

### Important distinction

"Queue" here does **not necessarily mean a technical message queue** such as RabbitMQ, Kafka, or Redis.

It means a **work queue / worklist** in the user interface.

So I would **not** build a message queue for this requirement.

* * *

# 11. Reviewer / reviewing clinician

There are two roles conceptually:

### Clinician

The person who performed the assessment.

That's represented by:

```
clinician_id
```

### Reviewer

The person who subsequently examines the assessment and decides whether to issue the report.

The brief says:

> "Reviewing clinicians work a queue of assessments..."

The input data only explicitly gives you the **assessment clinician ID**. It doesn't give you a complete authentication/user-management model for reviewers.

That is one of the things you can make an engineering judgement about.

* * *

# 12. Issue / issuing a report

**Issue** means the reviewing clinician has approved the assessment/report for release.

The workflow is:

```
Assessment completed
        ↓
Waiting for review
        ↓
Reviewer examines it
        ↓
Reviewer is satisfied
        ↓
REPORT ISSUED
```

Once issued, the report is considered fixed because copies are assumed to have already gone to the family, school and GP.

You don't have to actually send those copies.

* * *

# 13. Audit trail

An **audit trail** is a historical record of important actions.

Think:

```
WHO       DID WHAT             WHEN
------------------------------------------------
Alice     Opened assessment    10:32
Alice     Issued report        10:37
Bob       Edited summary       14:21
```

The requirement is specifically that an auditor must be able to determine:

> **who looked at what, when, and what changed.**

This is common in systems dealing with sensitive records.

* * *

# 14. Derived/calculated data

This is a useful architectural concept in the brief.

Some fields are **source data**:

```
date_of_birth
raw
max
completed
summary
clinician_id
```

Some are **derived data**:

```
age
domain percentage
support-need band
review flag
```

The brief explicitly says that percentages, bands and the flag are values that **you calculate**, and that they are subject to change.

That suggests you should avoid treating these calculated values as authoritative persisted data unless you have a good reason.

* * *

# 15. "Happy path"

The second document uses another common engineering term:

> "including away from the happy path."

The **happy path** is the normal scenario where everything goes right.

For this exercise:

```
Queue
 ↓
Filter
 ↓
Open assessment
 ↓
Everything is valid
 ↓
Issue report
```

A **non-happy path** could be:

```
No assessments match the filter
```

or:

```
Assessment has incomplete items
```

or:

```
Summary is missing
```

or:

```
Malformed JSON input
```

or:

```
Assessment has already been issued
```

They explicitly say they will consider correctness **outside the happy path**, including boundary values, empty results and missing/invalid data.

* * *

# 16. "Narrow path"

This phrase appears repeatedly:

> "A narrow path that works beats a broad one that does not."

It means:

**Don't implement 20 features badly. Implement the most important workflow completely.**

For example, this is good:

```
Queue
  ↓
Filter
  ↓
Assessment detail
  ↓
Issue
  ↓
Audit
```

working reliably.

This would be worse:

```
Queue
Filters
Dashboard
Authentication
User management
Notifications
Reports
Analytics
Export
Settings
...
```

where half the features don't actually work.

* * *

# 17. Now, what does the second document change?

Quite a lot in terms of **how you should approach the assignment**.

## A. AI coding agent is mandatory

This is probably the biggest new information.

They explicitly say:

> **"Required, not merely permitted."**

You are expected to use an AI coding agent such as:

* Claude Code
* Codex
* Cursor
* GitHub Copilot
* Aider
* etc.

And they want you to use it approximately as you would in your normal working environment.

So **don't try to hide your AI usage**.

It is actually part of the assessment.

* * *

# 18. They are evaluating two things approximately 50/50

This is extremely important.

### Half #1 — How you work with AI

They want to see whether you can:

* frame the problem
* provide useful context
* break the work into pieces
* direct the agent
* give it things to verify against
* inspect its output
* test it
* challenge it
* reject bad output
* make engineering decisions yourself

The second document explicitly lists these criteria.

### Half #2 — What you produce

They assess:

* Does it work?
* Is it correct?
* Does it handle edge cases?
* Is the architecture sensible?
* Are you careful with the data?
* Does it start cleanly with Docker?
* Can you explain what you built?

So they are **not merely evaluating your final code**.

They are evaluating you as an engineer who happens to use AI heavily.

* * *

# 19. Your AI conversation history is part of the submission

This is another unusual but important requirement.

You need to submit:

```
agent/
```

containing your AI-agent session transcripts and relevant configuration/skills. They explicitly say **raw and messy is correct; don't tidy them up**.

They want to see **how you worked with the agent**.

For example, a strong workflow might look like:

```
You:
  Analyse the requirements and identify ambiguities.

Agent:
  ...

You:
  Good. Now propose a domain model.
  But don't implement anything yet.

Agent:
  ...

You:
  I disagree with X because...
  Let's change the design.

Agent:
  ...

You:
  Implement the scoring logic and write tests
  for the boundary values.

Agent:
  ...

You:
  Run the tests and inspect the implementation.
```

That demonstrates engineering judgement.

Simply saying:

> "Build this application."

and accepting 5,000 lines of generated code would probably be a **bad strategy**, even if the application happens to work.

* * *

# 20. They specifically want evidence that you rejected AI output

This sentence is particularly revealing:

> "Evidence that you read, tested, questioned, and sometimes rejected the output rather than accepting it."

So if the agent makes a questionable architectural choice, **don't just accept it**.

For example:

```
Agent:
"Let's use Redis for the queue."

You:
"The requirement's 'queue' is a UI worklist, not
a distributed message queue. Redis adds unnecessary
infrastructure for this four-hour exercise. Use
database-backed assessment status instead."
```

That sort of reasoning is exactly what they're looking for.

* * *

# 21. The starter harness is important

They've already given you a starter project containing:

* Docker Compose
* Python stub
* Vite + React app
* PostgreSQL service
* sample data
* `verify.sh`

The PostgreSQL service can be deleted if you don't need it.

So you should probably **start from their harness**, rather than creating a completely independent project.

That gives you the required infrastructure and lets you spend your four hours on the actual problem.

* * *

# 22. What you have to submit

There are four important artefacts.

### 1. Git repository

They want the repository **with its `.git` directory/history intact**.

They explicitly say they will read the commit history, so don't squash everything into one final commit.

### 2. README.md

It should explain:

* how to run the application
* assuming a clean machine with only Docker
* how to access it

### 3. DECISIONS.md

Exactly **one page**.

This is important. It should explain:

* what you built
* what you deliberately didn't build
* why
* ambiguities in the requirements
* decisions you made about those ambiguities
* where you overrode the AI agent
* things you know are broken
* approximately how much time you spent and where

And they specifically want **you** to write this document rather than having the AI agent write it.

### 4. `agent/`

Your raw AI-agent sessions/configuration.

Don't clean them up unnecessarily.

* * *

# 23. There will be a second interview based on your submission

This is perhaps the most useful information for preparing.

The follow-up is **60 minutes over screenshare**.

They will:

1. Ask you to walk through what you built.
2. Ask what you deliberately left out.
3. Pick specific pieces of your code and ask **why you implemented them that way**.
4. Give you a **new change that wasn't in the original brief**.
5. Ask you to implement that change live using your AI agent.
6. Discuss what is missing, what could break, and what you would do next.

They expect the live change to take around 20 minutes and explicitly say that **not finishing it is okay**.

This means you should design the code so that **you can understand and modify it quickly**.

* * *

# 24. Updated interpretation of what they are really testing

After seeing both documents, I would characterize the assignment like this:

### They are NOT primarily asking:

> "Can you build a React/Python application?"

They are asking:

> **"Can you behave like a competent software engineer in an AI-assisted development environment?"**

The application is the evidence.

The process is also evidence.

And the interview afterwards tests whether **you actually understand what the AI produced**.

* * *

# 25. What I would therefore optimize for

Given the explicit four-hour guideline, I would aim for something like:

```
                MUST WORK
                    │
        ┌───────────┴───────────┐
        │                       │
   Review Queue             Assessment
        │                    Detail
        │                       │
   ┌────┼────┐                 │
   │    │    │                 │
 Score Flag Clinician        Results
 filter filter filter        Summary
                                │
                                ▼
                           Issue Report
                                │
                                ▼
                           Audit event
```

Then add, if time permits:

* summary editing after issue
* audit history UI
* better filtering
* additional tests
* better error handling
* polish

But **not at the expense of the core workflow**.

* * *

# 26. One thing I would change from my previous answer

After reading document 2, I would put **much more emphasis on the ambiguities**.

The interviewers explicitly say:

> "There are several places where the brief is unclear or incomplete. Clarifying the scope is part of the exercise."

So if you find something like the incomplete-item scoring issue we discussed, **that's not a problem with the assignment that you need to silently work around**.

It is actually part of the test.

You have two legitimate options:

1. **Ask them** on the interview email thread.
2. **Make a reasonable judgement and document it.**

They explicitly say either is acceptable.

* * *

## The mental model I'd keep in your head

If you're coming from a general software-engineering background, I'd reduce the whole problem to this:

```
                         ASSESSMENT
                              │
             ┌────────────────┼────────────────┐
             │                │                │
           Client          Domains          Summary
                              │
                   ┌──────────┼──────────┐
                   │          │          │
                 Items      Items      Items
                   │
              raw / max /
              completed
                   │
                   ▼
             CALCULATIONS
                   │
          ┌────────┼─────────┐
          │        │         │
      Percentage  Band      Flag
                              │
                              ▼
                       REVIEW QUEUE
                              │
                    ┌─────────┴─────────┐
                    │                   │
                  Filter              Open
                                        │
                                        ▼
                                  REVIEW ASSESSMENT
                                        │
                                        ▼
                                  ISSUE REPORT
                                        │
                                        ▼
                                   AUDIT TRAIL
```

That is the core of the assignment.

And the second document adds another layer around it:

```
                    YOU
                     │
                     ▼
               AI CODING AGENT
                     │
                     ▼
                  CODE
                     │
              ┌──────┴──────┐
              │             │
            TEST           REVIEW
              │             │
              └──────┬──────┘
                     ▼
              YOUR ENGINEERING
                 JUDGEMENT
```

**That second layer is almost as important as the application itself.**

* * *

**ChatGPT:**

You're right. There are two related issues:

1. `AuditEvent` needs the same `TYPE_CHECKING` treatment for `User`.
2. Since all three model modules need the SQLAlchemy declarative `Base`, we should create a central `app/database.py`.

I recommend making the database setup async from the beginning, since you're using async SQLAlchemy.

## `app/database.py`

```Python
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase


DATABASE_URL = "sqlite+aiosqlite:///./data/app.db"


class Base(DeclarativeBase):
    pass


engine = create_async_engine(
    DATABASE_URL,
    echo=False,
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session
```

This gives us:

```
Base
 ├── User
 ├── Assessment
 └── AuditEvent
```

and later all other SQLAlchemy models can inherit from the same `Base`.

### One dependency

Since you're using SQLite asynchronously, you'll need:

```
aiosqlite
```

alongside:

```
sqlalchemy
```

* * *

# `auth/model.py`

I'd now use:

```Python
from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.assessment.model import Assessment


class UserRole:
    CLINICIAN = "clinician"
    REVIEWER = "reviewer"


class User(Base):
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(
        String(100),
        primary_key=True,
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    roles: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )

    assessments: Mapped[list["Assessment"]] = relationship(
        "Assessment",
        foreign_keys="Assessment.clinician_username",
        back_populates="clinician",
    )
```

The important part is:

```Python
if TYPE_CHECKING:
    from app.assessment.model import Assessment
```

This makes `Assessment` available to static type checkers without creating a runtime circular import.

And:

```Python
relationship("Assessment", ...)
```

allows SQLAlchemy to resolve the model at runtime.

* * *

# `assessment/model.py`

```Python
from __future__ import annotations
        nullable=False,
        index=True,
    )

    guardian_contact: Mapped[str] = mapped_column(
        String(320),
        nullable=False,
    )

    safeguarding_notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    assessed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    clinician_username: Mapped[str] = mapped_column(
        String(100),
        ForeignKey("users.username"),
        nullable=False,
        index=True,
    )

    domains: Mapped[list[dict]] = mapped_column(
        JSON,
        nullable=False,
    )

    summary: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="pending_review",
        index=True,
    )

    issued_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    issued_by: Mapped[str | None] = mapped_column(
        String(100),
        ForeignKey("users.username"),
        nullable=True,
    )

    clinician: Mapped["User"] = relationship(
        "User",
        foreign_keys=[clinician_username],
        back_populates="assessments",
    )

    issuer: Mapped["User | None"] = relationship(
        "User",
        foreign_keys=[issued_by],
    )
```

Notice that `Assessment` has **two foreign keys to `users`**:

```
clinician_username → users.username
issued_by          → users.username
```

That's why we explicitly specify:

```Python
foreign_keys=[clinician_username]
```

and:

```Python
foreign_keys=[issued_by]
```

Otherwise SQLAlchemy wouldn't know which relationship should use which foreign key.

* * *

# `audit/model.py`

The same pattern applies here.

```Python
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.auth.model import User


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
    )

    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    actor_username: Mapped[str] = mapped_column(
        String(100),
        ForeignKey("users.username"),
        nullable=False,
        index=True,
    )

    action: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        index=True,
    )

    entity_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        index=True,
    )

    entity_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    changes: Mapped[list[dict[str, Any]] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    actor: Mapped["User"] = relationship(
        "User",
        foreign_keys=[actor_username],
    )
```

The crucial difference from the problematic version is:

```Python
if TYPE_CHECKING:
    from app.auth.model import User
```

and:

```Python
actor: Mapped["User"] = relationship(
    "User",
    foreign_keys=[actor_username],
)
```

* * *

## One more thing: model imports

There's one issue we should handle before we start creating tables.

Because the models reference each other, SQLAlchemy needs all three model modules imported before:

```Python
Base.metadata.create_all(...)
```

or the async equivalent.

I would create:

### `app/models.py`

```Python
from app.auth.model import User
from app.assessment.model import Assessment
from app.audit.model import AuditEvent

__all__ = [
    "User",
    "Assessment",
    "AuditEvent",
]
```

Then wherever we initialise the database:

```Python
import app.models  # noqa: F401
```

before accessing:

```Python
Base.metadata
```

This isn't strictly necessary if your application imports all the routers—which themselves import the models—but having an explicit model-registration module is clearer and prevents a subtle problem where a table isn't present in `Base.metadata` simply because its model module hasn't been imported yet.

* * *

### Resulting structure

```
app/
├── database.py
│
├── models.py
│
├── auth/
│   ├── api.py
│   ├── model.py
│   ├── schemas.py
│   └── service.py
│
├── assessment/
│   ├── api.py
│   ├── model.py
│   ├── schemas.py
│   └── service.py
│
└── audit/
    ├── api.py
    ├── model.py
    ├── schemas.py
    └── service.py
```

This gives us a clean foundation for the async repositories/services without introducing a separate database abstraction layer yet.

* * *

**You:**

Following is my assessment api implementation. Please write me a detailed readme file, in markdown, describing each api and their relationship to the database, such that if I gives the file to an LLM mode, it understands what needs to be done.

from fastapi import APIRouter, Query

from .schemas import (

    AssessmentDetailResponse,

    AssessmentListResponse,

    AssessmentSortField,

    AssessmentStatus,

    DomainName,

    IssueAssessmentResponse,

    SortOrder,

    SummaryUpdateRequest,

    SummaryUpdateResponse,

    SupportNeedBand,

)

router = APIRouter(prefix="/assessments", tags=["assessments"])


@router.get("", response_model=AssessmentListResponse)

async def list_assessments(

    status: AssessmentStatus | None = None,

    clinician_id: str | None = None,

    flagged: bool | None = None,

    domain: DomainName | None = None,

    band: SupportNeedBand | None = None,

    page: int = Query(default=1, ge=1),

    page_size: int = Query(default=25, ge=1, le=100),

    sort_by: AssessmentSortField = AssessmentSortField.ASSESSED_AT,

    sort_order: SortOrder = SortOrder.DESC,

) -> AssessmentListResponse:

    raise NotImplementedError


@router.get("/{assessment_id}", response_model=AssessmentDetailResponse)

async def get_assessment(assessment_id: str) -> AssessmentDetailResponse:

    raise NotImplementedError


@router.post(

    "/{assessment_id}/issue",

    response_model=IssueAssessmentResponse,

)

async def issue_assessment(assessment_id: str) -> IssueAssessmentResponse:

    raise NotImplementedError


@router.patch(

    "/{assessment_id}/summary",

    response_model=SummaryUpdateResponse,

)

async def update_assessment_summary(

    assessment_id: str,

    request: SummaryUpdateRequest,

) -> SummaryUpdateResponse:

    raise NotImplementedError

* * *

**ChatGPT:**

# Assessment API — Implementation Guide

## 1. Purpose

This document describes the REST API for the assessment module and defines how each endpoint should interact with the SQLAlchemy database models and the assessment business logic.

The purpose of this document is to provide enough context for an implementation agent to implement the assessment service layer without having to infer the intended behaviour from the FastAPI route definitions alone.

The assessment API is the core business API of the application. It supports the reviewer's workflow:

1. Retrieve the assessment review queue.
2. Filter and sort the queue.
3. Open an individual assessment.
4. Review the calculated results.
5. Issue the report.
6. Correct the summary when necessary, including after the report has been issued.

The API itself should remain thin. Business rules and database operations belong in the assessment service/repository layers rather than inside the FastAPI route functions.

* * *

# 2. Current API

The router is defined as:

```
router = APIRouter(
    prefix="/assessments",
    tags=["assessments"],
)
```

Therefore the endpoints are:

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/assessments` | Retrieve and filter the assessment review queue |
| `GET` | `/assessments/{assessment_id}` | Retrieve one complete assessment |
| `POST` | `/assessments/{assessment_id}/issue` | Issue an assessment/report |
| `PATCH` | `/assessments/{assessment_id}/summary` | Correct the assessment summary |

All endpoint functions are asynchronous and should remain `async`.

* * *

# 3. Database model

The current design intentionally keeps the database simple.

There is one primary assessment table:

```
assessments
```

The assessment contains both ordinary scalar columns and a JSON column containing the original domain/item structure.

Conceptually:

```
Assessment
├── id
├── date_of_birth
├── nhs_number
├── guardian_contact
├── safeguarding_notes
├── assessed_at
├── clinician_username
├── domains              <-- JSON
├── summary
├── status
├── issued_at
└── issued_by
```

The assessment does **not** have separate database tables for:

* clients
* domains
* assessment items

The reason is that domains and items are structural parts of an assessment rather than independent business entities for this application.

The `domains` JSON field preserves the structure received from the clinician application.

Example:

```
[
  {
    "domain": "social_communication",
    "items": [
      {
        "code": "SC1",
        "raw": 12,
        "max": 20,
        "completed": true
      },
      {
        "code": "SC2",
        "raw": null,
        "max": 20,
        "completed": false
      }
    ]
  }
]
```

The database should therefore be treated as the source of the assessment's raw/source data.

* * *

# 4. Derived assessment values

The following values are **calculated by the business logic** and should not be treated as authoritative database fields:

* Young person's age
* Domain percentage
* Domain support-need band
* Review flag

The scoring rules are defined by the original take-home brief.

For each domain:

```
domain percentage =
    mean(raw / max * 100)
```

The percentage is converted into a support-need band:

| Percentage | Band |
| --- | --- |
| 0–39 | Minimal |
| 40–54 | Mild |
| 55–84 | Moderate |
| 85–100 | Substantial |

The review flag is ON when:

* any domain has the `Substantial` band;
* any item is incomplete; or
* the summary contains fewer than 200 characters.

These calculations should live in the assessment service/business-logic layer, not in the API route and preferably not in the SQLAlchemy model.

* * *

# 5. Assessment status

An assessment has a lifecycle status.

The currently supported statuses are:

```
pending_review
issued
```

The normal lifecycle is:

```
pending_review
      |
      | POST /assessments/{id}/issue
      v
   issued
```

An issued assessment must not be returned to `pending_review`.

The brief states that once a report is issued, it is fixed because copies have already been sent.

However, the summary may still be corrected after issuance. Therefore:

* issuing the report is effectively irreversible;
* the summary remains editable;
* calculated values may change when the underlying summary changes.

* * *

# 6. `GET /assessments`

## Purpose

Retrieve the reviewer's assessment queue.

This is the primary endpoint for the application's main screen.

The reviewer needs to be able to narrow the queue by:

* assessment status;
* clinician;
* review flag;
* score/domain;
* support-need band.

The endpoint also supports pagination and sorting.

## Signature

```
@router.get(
    "",
    response_model=AssessmentListResponse,
)
async def list_assessments(
    status: AssessmentStatus | None = None,
    clinician_id: str | None = None,
    flagged: bool | None = None,
    domain: DomainName | None = None,
    band: SupportNeedBand | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    sort_by: AssessmentSortField = AssessmentSortField.ASSESSED_AT,
    sort_order: SortOrder = SortOrder.DESC,
) -> AssessmentListResponse:
    ...
```

* * *

## Query parameters

### `status`

Optional assessment status filter.

Possible values are defined by `AssessmentStatus`, currently:

```
pending_review
issued
```

Example:

```
GET /assessments?status=pending_review
```

This should filter the database by:

```
Assessment.status
```

* * *

### `clinician_id`

Filters assessments by the clinician who performed the assessment.

In the current database model, the clinician is represented by:

```
Assessment.clinician_username
```

Therefore the service should map the API parameter to that database field.

Example:

```
GET /assessments?clinician_id=c-005
```

If the implementation ultimately changes the API parameter name to `clinician_username`, the service/schema/API should be kept internally consistent.

Do not introduce a separate clinician table solely for this endpoint.

* * *

### `flagged`

Filters assessments according to the calculated review flag.

Example:

```
GET /assessments?flagged=true
```

Important:

`flagged` is not a database field.

It must be calculated from the assessment's source data:

```
any substantial domain
OR
any incomplete item
OR
summary length < 200
```

For the current small take-home dataset, it is acceptable to retrieve the relevant assessments and perform this calculation in Python before applying the filter.

Do not add a persisted `flagged` column merely to make this query easier unless there is a strong implementation reason.

* * *

### `domain`

Identifies a particular assessment domain.

The supported domain names are:

```
social_communication
sensory_processing
executive_function
emotional_regulation
motor_coordination
```

The domain exists inside the `Assessment.domains` JSON structure.

Example:

```
GET /assessments?domain=social_communication
```

When `domain` is combined with `band`, the intended meaning is:

> Return assessments where the specified domain has the specified support-need band.

* * *

### `band`

Filters by support-need band:

```
minimal
mild
moderate
substantial
```

Example:

```
GET /assessments?domain=social_communication&band=substantial
```

This means:

> Return assessments whose `social_communication` domain has a `Substantial` calculated band.

If `band` is supplied without `domain`, it can mean:

> Return assessments where any domain has the specified band.

There is no overall assessment score defined by the requirements, so the implementation should not invent one.

* * *

## Pagination

The endpoint supports:

```
page
page_size
```

with:

```
page >= 1
1 <= page_size <= 100
```

The default is:

```
page = 1
page_size = 25
```

The response should include:

```
items
page
page_size
total
```

The database query should ideally use pagination at the database level for filters that can be performed directly in SQL.

However, because the domain scoring and review flag are calculated from JSON data, some filtering may need to occur in Python for this take-home implementation.

The implementation should favour correctness and simplicity over premature database optimisation.

* * *

## Sorting

The endpoint supports:

```
sort_by
sort_order
```

The current default is:

```
sort_by = assessed_at
sort_order = desc
```

Therefore, the default queue should show the most recently assessed records first.

Sorting should be implemented against the corresponding database field where possible.

* * *

## Response

The endpoint returns:

```
AssessmentListResponse
```

The list response should be relatively lightweight.

It should contain enough information for the queue UI, but should not unnecessarily return the complete item-level assessment structure.

A queue item should conceptually contain:

```
assessment_id
assessed_at
clinician
status
flagged
domain results
```

The domain results should contain:

```
domain
percentage
band
```

but not necessarily the individual items.

* * *

# 7. `GET /assessments/{assessment_id}`

## Purpose

Retrieve the complete assessment for review.

This endpoint is called when the reviewer opens an assessment from the queue.

## Signature

```
@router.get(
    "/{assessment_id}",
    response_model=AssessmentDetailResponse,
)
async def get_assessment(
    assessment_id: str,
) -> AssessmentDetailResponse:
    ...
```

* * *

## Database operation

Retrieve:

```
Assessment
WHERE Assessment.id == assessment_id
```

If no assessment exists, the service should cause the API to return:

```
404 Not Found
```

Do not silently return an empty object.

* * *

## Response

The detail response should contain the complete information required by the reviewer:

### Client information

```
date_of_birth
nhs_number
guardian_contact
safeguarding_notes
```

### Assessment information

```
assessment_id
assessed_at
clinician
status
```

### Calculated age

Calculate age from:

```
date_of_birth
assessed_at
```

The result should be expressed as:

```
years
months
```

Do not store the calculated age in the database.

### Domain results

For every domain:

```
domain
percentage
band
items
```

The items come directly from the `Assessment.domains` JSON structure.

Each item contains:

```
code
raw
max
completed
```

### Summary

Return the current assessment summary.

### Review flag

Calculate it from the current assessment data.

### Issue information

For an issued assessment:

```
issued_at
issued_by
```

should be populated.

For an unissued assessment:

```
issued_at = null
issued_by = null
```

* * *

# 8. Audit behaviour when opening an assessment

Opening an individual assessment represents viewing sensitive client information.

Therefore, after successfully retrieving an assessment, the service layer should create an audit event representing:

```
action = VIEW
entity_type = assessment
entity_id = assessment_id
actor = current user
```

The API route itself should not directly construct or persist the audit event.

Instead, the assessment service should coordinate with the audit service.

Conceptually:

```
GET /assessments/{id}
        |
        v
AssessmentService.get_assessment()
        |
        +---- retrieve assessment
        |
        +---- calculate response
        |
        +---- record VIEW audit event
        |
        v
AssessmentDetailResponse
```

The exact transaction strategy can be decided when implementing the service layer.

* * *

# 9. `POST /assessments/{assessment_id}/issue`

## Purpose

Issue the assessment/report after the reviewer is satisfied.

This is a business operation rather than a generic update, so it is represented by `POST`.

## Signature

```
@router.post(
    "/{assessment_id}/issue",
    response_model=IssueAssessmentResponse,
)
async def issue_assessment(
    assessment_id: str,
) -> IssueAssessmentResponse:
    ...
```

* * *

## Database operation

Retrieve:

```
Assessment
WHERE Assessment.id == assessment_id
```

If it doesn't exist:

```
404 Not Found
```

If its status is already:

```
issued
```

the operation must not issue it again.

A suitable response is:

```
409 Conflict
```

because the requested business operation conflicts with the current state.

* * *

## Issuing behaviour

When successfully issuing:

```
Assessment.status = issued
Assessment.issued_at = current UTC timestamp
Assessment.issued_by = current user's username
```

The current user must have the appropriate permission, which should be checked by the authentication/authorization layer.

For the current role model, the intended role is:

```
reviewer
```

* * *

## Audit event

Issuing the assessment must create an audit event:

```
action = ISSUE
entity_type = assessment
entity_id = assessment_id
actor = current user
```

The audit event should be created as part of the same logical operation.

* * *

## Response

Return:

```
IssueAssessmentResponse
```

containing at least:

```
assessment_id
status
issued_at
issued_by
```

* * *

# 10. `PATCH /assessments/{assessment_id}/summary`

## Purpose

Correct the written summary.

The requirements explicitly allow clinicians to correct an occasional typo in the summary **after the report has been issued**.

Therefore this endpoint must work for both:

```
pending_review
```

and:

```
issued
```

assessments.

## Signature

```
@router.patch(
    "/{assessment_id}/summary",
    response_model=SummaryUpdateResponse,
)
async def update_assessment_summary(
    assessment_id: str,
    request: SummaryUpdateRequest,
) -> SummaryUpdateResponse:
    ...
```

* * *

## Request

The request contains:

```
summary
```

The maximum summary length is 8000 characters according to the supplied assessment format.

Pydantic validation should enforce the maximum length.

* * *

## Database operation

Retrieve:

```
Assessment
WHERE Assessment.id == assessment_id
```

If it does not exist:

```
404 Not Found
```

Then replace:

```
Assessment.summary
```

with the new summary.

The operation must not modify:

```
Assessment.status
Assessment.issued_at
Assessment.issued_by
Assessment.domains
```

* * *

## Recalculation

Changing the summary may change the calculated review flag.

For example:

```
old summary length = 150
```

means:

```
flagged = true
```

If the new summary contains 300 characters and there are no other flag conditions:

```
flagged = false
```

Therefore the response must calculate the flag from the updated assessment rather than relying on a persisted value.

* * *

## Audit event

The update must create an audit event:

```
action = UPDATE
entity_type = assessment
entity_id = assessment_id
actor = current user
```

The audit event should record the change:

```
[
  {
    "field": "summary",
    "before": "...",
    "after": "..."
  }
]
```

Do not expose or log sensitive information unnecessarily elsewhere.

* * *

## Response

Return:

```
SummaryUpdateResponse
```

containing:

```
assessment_id
summary
flagged
```

The updated `flagged` value should be calculated using the new summary.

* * *

# 11. Authentication and authorization

The assessment API should not implement authentication itself.

The application has an authentication module providing:

```
GET /auth/login
GET /auth/me
```

and users have two possible roles:

```
clinician
reviewer
```

The assessment endpoints should obtain the current authenticated user through FastAPI dependency injection.

Conceptually:

```
current_user = Depends(get_current_user)
```

The exact authentication implementation is outside this module.

The intended permissions are:

| Operation | Clinician | Reviewer |
| --- | --- | --- |
| View assessment queue | Yes | Yes |
| View assessment | Yes | Yes |
| Issue assessment | No | Yes |
| Update summary | Yes | Yes |

If the actual authorization policy changes, it should be implemented in the authorization/service layer rather than by duplicating role checks throughout the route functions.

* * *

# 12. Service-layer responsibility

The FastAPI routes should remain thin.

For example, `list_assessments()` should conceptually become:

```
API endpoint
    ↓
AssessmentService.list_assessments(...)
    ↓
repository/database access
    ↓
business calculations
    ↓
AssessmentListResponse
```

Similarly:

```
issue_assessment()
    ↓
AssessmentService.issue_assessment(...)
    ↓
load assessment
    ↓
validate state
    ↓
update status
    ↓
create audit event
    ↓
return result
```

The API layer should **not** contain:

* SQLAlchemy queries
* scoring algorithms
* review-flag logic
* status-transition rules
* audit-record construction
* transaction management

Those belong in the appropriate lower layers.

* * *

# 13. Important implementation rules

## Do not persist calculated values unnecessarily

Do not add these columns to `Assessment` merely because they appear in API responses:

```
age
flagged
percentage
band
```

They are derived from the source data.

* * *

## Keep the raw domain structure

The `domains` JSON field should preserve the source assessment structure:

```
domain
  └── items
       ├── code
       ├── raw
       ├── max
       └── completed
```

The service layer transforms this structure into API response models containing calculated results.

* * *

## Do not create independent CRUD APIs for domains/items

There is no requirement for:

```
GET /domains
GET /items
POST /items
PATCH /items
DELETE /items
```

Domains and items are components of an assessment, not independent resources in the current design.

* * *

## Do not allow arbitrary assessment updates

There should not be a generic:

```
PATCH /assessments/{assessment_id}
```

endpoint.

The requirements distinguish between different business operations.

Currently the supported mutation is specifically:

```
PATCH /assessments/{assessment_id}/summary
```

and issuing is a separate business action:

```
POST /assessments/{assessment_id}/issue
```

This makes the allowed state transitions explicit.

* * *

# 14. Expected endpoint workflow

The main user workflow should be:

```
1. GET /assessments
        |
        | reviewer filters queue
        v
2. GET /assessments/{assessment_id}
        |
        | reviewer reviews details
        v
3. POST /assessments/{assessment_id}/issue
        |
        v
   Report is issued
```

A later summary correction follows:

```
PATCH /assessments/{assessment_id}/summary
        |
        v
Summary updated
        |
        v
Derived values recalculated
        |
        v
Audit event recorded
```

This is the primary end-to-end path required by the take-home.

* * *

# 15. Error handling expectations

The service implementation should translate normal business failures into appropriate HTTP errors.

At minimum:

| Situation | HTTP status |
| --- | --- |
| Assessment does not exist | `404 Not Found` |
| Assessment already issued | `409 Conflict` |
| User not authenticated | `401 Unauthorized` |
| User lacks required role | `403 Forbidden` |
| Invalid request data | `422 Unprocessable Entity` |

FastAPI/Pydantic will handle most request-validation errors automatically.

Business validation should remain in the service layer.

* * *

# 16. Async implementation

All database access must use the asynchronous SQLAlchemy stack.

The expected architecture is:

```
FastAPI async endpoint
        ↓
async service method
        ↓
async repository/database operation
        ↓
AsyncSession
```

Do not introduce synchronous SQLAlchemy sessions into the assessment module.

The endpoint definitions are already asynchronous and should remain so.

* * *

# 17. Design philosophy

This module deliberately favours a simple design appropriate for the take-home exercise.

The important architectural boundaries are:

```
API
 ↓
Service / business logic
 ↓
SQLAlchemy / persistence
```

The assessment itself is the primary aggregate. Its domain/item structure is stored as JSON because those objects are not independently managed resources in this application.

The implementation should prioritize:

1. Correct business logic.
2. The complete review workflow.
3. Clear separation of API and business logic.
4. Auditability.
5. Correct handling of edge cases.
6. Simplicity appropriate to the four-hour scope.

Do not introduce additional infrastructure or database normalization unless a concrete requirement justifies it.

* * *

**You:**

Please also summerise all the requirements of the project, also in markdown format. I will give it to a coding LLM to provide context.

* * *

**ChatGPT:**

# Neurotype Engineering Take-Home — Requirements Summary

## 1. Project Overview

Build a small web application for reviewing neurodevelopmental assessments.

The system represents a simplified clinical workflow:

1. A clinician performs a structured assessment of a young person.
2. The assessment contains scores across several domains and a written summary.
3. A reviewing clinician reviews the assessment.
4. The reviewer can filter/narrow a queue of assessments.
5. The reviewer opens an individual assessment and sees the complete assessment information.
6. When satisfied, the reviewer issues the report.
7. Issuing the report is effectively final because copies are assumed to have already been sent to the family, school and GP.
8. A summary may nevertheless be corrected later if an occasional typo is discovered.
9. Client records must be auditable: the system must be able to show who looked at what, when, and what changed.

The clinical instrument and scoring system are **invented for this exercise**, and all supplied data is synthetic. No clinical knowledge is required.

* * *

# 2. Technology Requirements

The application must contain:

* Python backend
* React + TypeScript frontend
* Docker Compose

The application must run on a clean machine with only Docker installed.

The following must work:

```
docker compose up
```

and:

```
http://localhost:8000/health
```

must return HTTP `200`.

The frontend must be available at:

```
http://localhost:5173
```

Everything else is an engineering choice.

The project uses:

* FastAPI for the backend
* Async Python / async SQLAlchemy
* SQLite initially
* SQLAlchemy ORM
* React + TypeScript frontend

The database model should remain database-agnostic so that SQLite can later be replaced by another relational database.

* * *

# 3. Supplied Assessment Data

The clinician application produces assessments as JSONL:

```
assessments.jsonl
```

JSONL means there is one JSON assessment object per line.

The supplied sample contains approximately 100 assessments.

An assessment has approximately this structure:

```
{
  "assessment_id": "a-00001",
  "client": {
    "date_of_birth": "2014-03-02",
    "nhs_number": "999 476 5919",
    "guardian_contact": "j.okafor@example.com",
    "safeguarding_notes": "Contact via mother only. Father not to be given dates."
  },
  "assessed_at": "2026-03-02T09:30:00+00:00",
  "clinician_id": "c-005",
  "domains": [
    {
      "domain": "social_communication",
      "items": [
        {
          "code": "SC1",
          "raw": 12,
          "max": 20,
          "completed": true
        },
        {
          "code": "SC2",
          "raw": null,
          "max": 20,
          "completed": false
        }
      ]
    }
  ],
  "summary": "Free text, up to 8000 characters."
}
```

There are five fixed domains:

```
social_communication
sensory_processing
executive_function
emotional_regulation
motor_coordination
```

Each domain contains between three and six items.

An item can be incomplete if the young person was unable or unwilling to complete it.

* * *

# 4. Assessment Terminology

## Assessment

One complete evaluation of a young person.

An assessment contains:

* client information
* assessment date/time
* clinician
* domains and their items
* written summary

## Domain

A broad area being assessed.

There are exactly five domains:

* Social communication
* Sensory processing
* Executive function
* Emotional regulation
* Motor coordination

## Item

An individual scored element within a domain.

An item contains:

* `code`
* `raw`
* `max`
* `completed`

## Raw score

The actual score obtained for an item.

## Max score

The maximum possible score for the item.

## Queue

The review queue is a **worklist of assessments waiting to be reviewed**.

It is not a technical message queue such as Kafka, RabbitMQ or Redis.

## Reviewer

The clinician who reviews an assessment and can issue its report.

* * *

# 5. Scoring Rules

The scoring rules are not contained in the JSONL input. The application must calculate them.

## Domain percentage

Each domain receives a percentage calculated as:

```
mean(raw / max * 100)
```

across its items.

Example:

```
Item 1: 10 / 20 = 50%
Item 2: 15 / 20 = 75%
Item 3: 12 / 20 = 60%

Domain percentage = mean(50, 75, 60)
                  = 61.67%
```

### Important ambiguity

The brief does not explicitly specify how an incomplete item with:

```
raw = null
completed = false
```

should participate in the percentage calculation.

The implementation must make an explicit judgement about this and document it.

* * *

# 6. Support-Need Bands

Each domain percentage maps to a support-need band:

| Percentage | Band |
| --- | --- |
| 0–39 | Minimal |
| 40–54 | Mild |
| 55–84 | Moderate |
| 85–100 | Substantial |

There is no overall assessment score defined by the brief.

Bands are calculated per domain.

* * *

# 7. Review Flag

Each assessment has a calculated review flag.

The flag is ON if **any** of these conditions is true:

```
1. Any domain has the Substantial band
OR
2. Any item is incomplete
OR
3. The summary contains fewer than 200 characters
```

Conceptually:

```
flagged = (
    has_substantial_domain
    or has_incomplete_item
    or len(summary) < 200
)
```

The flag is a derived value and should not be treated as authoritative stored data.

* * *

# 8. Age Calculation

The report must show the young person's age in:

```
years and months
```

at the date of assessment.

Age should be calculated from:

```
date_of_birth
assessed_at
```

It should not be stored as a permanent database value.

* * *

# 9. Assessment Review Queue

Reviewing clinicians work through a queue containing assessments from the service.

The queue must allow reviewers to narrow assessments by:

1. **How the assessment scored**
2. **Whether it is flagged**
3. **Which clinician performed the assessment**

The current API interprets "how it scored" using the per-domain support-need bands.

Supported filters are therefore:

```
status
clinician
flagged
domain
band
```

Example:

```
GET /assessments?domain=social_communication&band=substantial
```

means:

> Find assessments where the social communication domain has a Substantial band.

If `band` is supplied without `domain`, it can mean:

> Find assessments where any domain has that band.

The application should not invent an overall assessment score because the brief does not define one.

The queue should support pagination and sorting.

* * *

# 10. Assessment Lifecycle

The current assessment statuses are:

```
pending_review
issued
```

Normal lifecycle:

```
pending_review
      |
      | issue report
      v
   issued
```

Once issued:

* the report cannot be un-issued;
* the status should remain `issued`;
* `issued_at` should record when it was issued;
* `issued_by` should record who issued it.

However, the written summary may still be corrected after issuance.

* * *

# 11. Core User Workflow

The most important end-to-end workflow is:

```
Open review queue
      |
      v
Narrow/filter queue
      |
      v
Open an assessment
      |
      v
Review client information,
domain results and summary
      |
      v
Issue report
```

This workflow must work end to end.

The brief explicitly prioritises:

> A narrow path that works beats a broad one that does not.

Do not sacrifice the core workflow in order to implement a large number of secondary features.

* * *

# 12. Assessment Detail

Opening an assessment must show the whole assessment:

## Client

* date of birth
* NHS number
* guardian contact
* safeguarding notes

## Assessment

* assessment ID
* assessment date/time
* clinician
* status

## Age

Calculated age in years and months.

## Domains

For each domain:

* domain name
* calculated percentage
* calculated support-need band
* individual items

For each item:

* code
* raw score
* maximum score
* completion status

## Summary

The complete written summary.

## Review flag

The current calculated review flag.

## Issue information

If issued:

* issued timestamp
* user who issued it

* * *

# 13. Summary Editing

Clinicians may need to correct an occasional typo in the summary after the report has been issued.

Therefore the summary must remain editable.

The API exposes:

```
PATCH /assessments/{assessment_id}/summary
```

Only the summary should be changed by this operation.

It must not:

* un-issue the report;
* modify the raw assessment items;
* modify the issue timestamp;
* modify who issued the report.

Because the review flag depends partly on summary length, changing the summary may change the calculated review flag.

* * *

# 14. Audit Requirements

Client records must be auditable.

The system must be able to answer:

```
Who looked at what?
When?
What changed?
```

Important actions should create audit events.

At minimum, the assessment workflow should audit:

```
VIEW
ISSUE
UPDATE
```

For a summary update, the audit event should preserve the change, conceptually:

```
[
  {
    "field": "summary",
    "before": "old summary",
    "after": "new summary"
  }
]
```

Opening an individual assessment should generate a `VIEW` audit event.

Issuing an assessment should generate an `ISSUE` audit event.

Updating the summary should generate an `UPDATE` audit event.

The audit implementation should be kept separate from the assessment API implementation.

* * *

# 15. Authentication and Users

The application has two fixed user roles:

```
clinician
reviewer
```

Users are provisioned and managed manually for this exercise.

There is no need to implement a user-management CRUD API.

The authentication API is deliberately simple:

```
POST /auth/login
GET  /auth/me
```

The current user must be available to the service layer so that:

* permissions can be checked;
* audit events can identify the actor;
* issue operations can record `issued_by`.

Intended permissions:

| Operation | Clinician | Reviewer |
| --- | --- | --- |
| View assessment queue | Yes | Yes |
| View assessment | Yes | Yes |
| Issue assessment | No | Yes |
| Update summary | Yes | Yes |

Authentication and authorization should be implemented separately from assessment business logic.

* * *

# 16. Database Design

The current database intentionally uses a simple model.

There are three main tables:

```
users
assessments
audit_events
```

## Users

The user model contains only:

```
username
password_hash
roles
assessments
```

`username` is the user identifier.

Roles are the two fixed values:

```
clinician
reviewer
```

Roles can be stored as a JSON list.

* * *

## Assessments

The assessment is the main business aggregate.

It contains:

```
id
date_of_birth
nhs_number
guardian_contact
safeguarding_notes
assessed_at
clinician_username
domains
summary
status
issued_at
issued_by
```

The nested domain/item structure is stored in the `domains` JSON field.

Example:

```
[
  {
    "domain": "social_communication",
    "items": [
      {
        "code": "SC1",
        "raw": 12,
        "max": 20,
        "completed": true
      }
    ]
  }
]
```

There are deliberately no separate database tables for:

* clients
* assessment domains
* assessment items

These are considered components of an assessment rather than independent resources.

This keeps the implementation simple and appropriate for the scope of the exercise.

* * *

# 17. Derived Values and Database Source of Truth

The database stores the assessment's source facts.

The following should be calculated by the business logic:

```
age
domain percentage
support-need band
review flag
```

Do not create redundant persistent columns for these values unless there is a compelling reason.

The API should calculate them when constructing its response.

This avoids stale derived values, particularly because the summary can change after an assessment has been issued.

* * *

# 18. REST API Summary

## Authentication

```
POST /auth/login
GET  /auth/me
```

## Assessments

```
GET   /assessments
GET   /assessments/{assessment_id}
POST  /assessments/{assessment_id}/issue
PATCH /assessments/{assessment_id}/summary
```

## Audit

```
GET /audit/events
```

* * *

# 19. Assessment API Details

### `GET /assessments`

Returns the review queue.

Supported query parameters:

```
status
clinician_id
flagged
domain
band
page
page_size
sort_by
sort_order
```

Default pagination:

```
page = 1
page_size = 25
```

Maximum page size:

```
100
```

Default sorting:

```
assessed_at DESC
```

The queue response should contain lightweight domain results rather than all item-level details.

* * *

### `GET /assessments/{assessment_id}`

Returns the complete assessment.

It should:

1. Retrieve the assessment from the database.
2. Calculate age.
3. Calculate domain percentages.
4. Calculate domain bands.
5. Calculate the review flag.
6. Return the complete domain/item structure.
7. Record an audit `VIEW` event.

Return `404` if the assessment does not exist.

* * *

### `POST /assessments/{assessment_id}/issue`

Issues the report.

It should:

1. Retrieve the assessment.
2. Check that it exists.
3. Check that it is not already issued.
4. Check the current user's permission.
5. Set status to `issued`.
6. Set `issued_at`.
7. Set `issued_by`.
8. Record an audit `ISSUE` event.
9. Return the issue result.

If already issued, return `409 Conflict`.

There is no un-issue operation.

* * *

### `PATCH /assessments/{assessment_id}/summary`

Updates only the written summary.

It should:

1. Retrieve the assessment.
2. Check that it exists.
3. Replace the summary.
4. Leave issue status unchanged.
5. Recalculate the review flag when constructing the response.
6. Record an audit `UPDATE` event containing the before/after summary.
7. Return the updated summary and review flag.

This endpoint must work even if the assessment has already been issued.

* * *

# 20. Backend Architecture

The backend should maintain a clear separation between:

```
FastAPI API
      |
      v
Service / Business Logic
      |
      v
SQLAlchemy ORM / Database
```

The API layer should be thin.

Do not put:

* SQL queries
* scoring algorithms
* state-transition rules
* audit persistence
* complex business logic

directly into FastAPI route functions.

The service layer should own the business rules.

Database access should use asynchronous SQLAlchemy.

Expected flow:

```
async FastAPI endpoint
        |
        v
async service
        |
        v
Async SQLAlchemy session
        |
        v
SQLite
```

The ORM models should avoid database-specific features so the application can later move from SQLite to another relational database.

* * *

# 21. Error Handling

At minimum:

| Situation | HTTP status |
| --- | --- |
| Assessment not found | `404 Not Found` |
| Already issued | `409 Conflict` |
| Not authenticated | `401 Unauthorized` |
| Insufficient permission | `403 Forbidden` |
| Invalid request | `422 Unprocessable Entity` |

FastAPI/Pydantic should handle request-schema validation.

Business errors should be handled by the service layer and translated into appropriate HTTP responses.

* * *

# 22. Edge Cases to Consider

The implementation should not only handle the happy path.

Important cases include:

* assessment does not exist;
* assessment is already issued;
* no assessments match a filter;
* incomplete assessment items;
* incomplete items with `raw = null`;
* summary shorter than 200 characters;
* summary exactly 200 characters;
* summary at the maximum length;
* domain score exactly on band boundaries;
* malformed or unexpected input JSON;
* missing assessment fields;
* invalid domain names;
* invalid status values;
* invalid clinician/user references;
* empty result sets;
* pagination beyond the available results.

The scoring boundaries are particularly important:

```
39 → Minimal
40 → Mild
54 → Mild
55 → Moderate
84 → Moderate
85 → Substantial
```

* * *

# 23. Explicit Requirements vs Engineering Decisions

The following are explicitly required by the brief:

* Python backend
* React + TypeScript frontend
* Docker Compose
* `/health` returns 200
* frontend on port 5173
* assessment queue
* queue filtering
* assessment detail view
* domain scoring
* support-need bands
* review flag
* age calculation
* report issuing
* post-issue summary correction
* auditability
* working end-to-end reviewer workflow

The following are implementation decisions rather than explicit requirements:

* FastAPI
* async SQLAlchemy
* SQLite
* simple login implementation
* two roles: clinician and reviewer
* flat assessment database model
* storing domains/items as JSON
* Python-side calculation/filtering for the small dataset
* exact API structure
* exact audit schema
* exact authentication mechanism

Where the original brief is unclear, make a reasonable judgement and document it rather than pretending the requirement is unambiguous.

* * *

# 24. Scope and Prioritisation

The exercise is intentionally larger than what can reasonably be completed in approximately four hours.

The expected approach is therefore to prioritise.

The most important functionality is:

```
Reviewer opens queue
        ↓
Reviewer narrows queue
        ↓
Reviewer opens assessment
        ↓
Reviewer issues report
```

A smaller, reliable implementation is preferable to a larger implementation with incomplete functionality.

Do not spend significant time implementing features that do not contribute to this workflow.

* * *

# 25. Docker / Submission Requirements

The final repository must work from a clean clone on a machine with only Docker installed.

The evaluator should be able to run:

```
docker compose up
```

and then:

```
http://localhost:5173
```

should serve the frontend.

```
http://localhost:8000/health
```

should return HTTP 200.

The repository should retain its Git history.

The submission should contain:

```
README.md
DECISIONS.md
agent/
```

`README.md` should explain how to run the application.

`DECISIONS.md` should be one page or less and explain:

* what was built;
* what was intentionally omitted;
* why;
* ambiguous/incomplete requirements;
* judgement calls;
* places where the AI-generated implementation was overridden;
* known problems;
* approximate time spent and where it went.

The `agent/` directory should contain the AI coding-agent session transcripts/configuration as requested by the interviewers.

* * *

# 26. AI-Assisted Development Requirement

Use of an AI coding agent is **required**, not merely permitted.

The interviewers are evaluating approximately equally:

1. The quality of the resulting software.
2. The ability to work effectively with an AI coding agent.

The agent should be used as part of normal development.

The developer is expected to:

* provide useful context;
* decompose the problem;
* direct the agent;
* verify generated code;
* test the implementation;
* identify incorrect assumptions;
* reject bad output;
* make engineering decisions independently;
* understand and defend the final implementation.

Do not blindly accept generated code.

The follow-up interview will specifically examine how the solution was produced and whether the developer understands the resulting code.

* * *

# 27. Follow-Up Interview

The second-stage interview includes approximately 60 minutes of screen sharing.

The interviewers may:

1. Ask for a walkthrough of the implementation.
2. Ask what was deliberately left out.
3. Select specific code and ask why it was implemented that way.
4. Ask for a new change that was not in the original requirements.
5. Ask the candidate to implement that change live using their normal AI coding setup.
6. Discuss missing functionality, failure modes and future improvements.

Therefore the implementation should be understandable and easy to modify.

The candidate should be able to explain the important architectural and business-logic decisions without relying on the AI agent.

* * *

# 28. Key Design Principle

The implementation should be **simple but deliberate**.

The goal is not to build a production-scale clinical information system within four hours.

The goal is to demonstrate that the developer can:

* understand an ambiguous problem;
* choose sensible boundaries;
* implement the core workflow;
* use AI effectively;
* verify AI-generated code;
* handle important edge cases;
* make reasonable trade-offs;
* explain those trade-offs clearly.

The primary success criterion is therefore:

```
Queue
  ↓
Filter
  ↓
Assessment
  ↓
Issue
  ↓
Audit
```

working correctly end to end.