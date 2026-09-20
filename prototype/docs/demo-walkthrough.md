# Demo walkthrough

## 1. Build the RFx from a conversation - 90 sec

Open **RFx Builder**.

Say: “The buyer starts with a sentence, not a form. The co-pilot holds a category-independent RFx
checklist — the ten things any RFx needs before a supplier can quote it — and drives the conversation
until every required item is captured.”

Type a partial requirement (“We need corrugated packaging for the Bengaluru and Hosur plants for FY27”)
and send it. Point out:
- the checklist on the right marks what was captured, what is partial and what is still missing
- the co-pilot asks the two highest-value questions back, as clickable follow-ups
- nothing is marked captured unless the buyer actually said it

Answer with the full brief. The checklist reaches 8 of 8 required, and the co-pilot presents the whole
thing back for confirmation: **“Should I share this with the relevant suppliers?”**

## 2. Find, map and share - 45 sec

Click **Yes — find & share**. The overlay narrates the deterministic match:
directory scan → capability and capacity → certifications and compliance → mapping your 30 lines and
questionnaire to each supplier → sharing.

Each supplier card shows its match score and the reasons behind it — category fit, certifications held,
capacity against annual volume, distance to the plants, and previous award history. No model decides
who receives an RFx.

## 3. Show suppliers did not follow a template - 60 sec

Open **Responses**, click **Load demo messages**, and open the source files:
- PackRight: XLSX with multiple sheets and mixed quote basis.
- CorrPro: PDF in USD / 100 pcs; 3% rebate hidden in the footnote.
- BoxWorks: Word quote with only 27/30 lines and freight extra.
- AlphaPack: angled phone photo; one obscured rate; FSC failure.
- GreenCarton: email with INR/kg and four `same as last year` lines.

Then click **+ Add supplier proposal** to show that anyone can be tested the same way: supplier name,
email ID, message body and attachments go in, and **Add & extract information** runs the identical
pipeline. Run **Extract & normalize** to explain native-first routing and the multimodal fallback.

## 4. Make trust visible - 2 min

Open **Review & Compare**.

Start with **Scenario-wise supplier standings**: one row per buying priority — best price, best value
against last year, most complete quote, fastest delivery, quality and compliance, proven relationship,
previous deals, cleanest data. The supplier leading each row is highlighted in light green, the runner-up
in light blue, and a supplier blocked by qualification in amber. The bottom row counts how often each
supplier comes first. A factor with no reviewed value reads “Not available”, never zero.

Then drop into the line-by-line **Normalized comparison** below it and point out:
- all prices are landed INR/piece
- AlphaPack is visibly failed by qualification
- BoxWorks can be compared but is pending and excluded from qualified award scenarios
- unquoted lines display `Not quoted`, never zero
- the Exception Inbox ranks issues by decision risk

Click a CorrPro value. In the Evidence Drawer show:
- PDF + page reference
- source text `USD 23.51 / 100 pcs`
- confidence
- conversion steps
- final `INR 19.56 landed / piece`

Then open the low-confidence AlphaPack exception and explain why the system stops rather than pretending
the smudged rate is certain.

## 5. Ask the sourcing event - 2 min

Open **Analysis Room**. Answers come back in whatever form reads fastest — a chart where a chart is
clearer, text where text is enough.

Award questions run the optimizer and come back with a donut of award share and a bar of lines won:
1. `Cheapest qualified supplier per line.`
2. `Qualified only, no supplier above 45% of award spend.`
3. `Qualified suppliers with delivery within 14 days.`
4. `Qualified suppliers with delivery within 1 day.` — infeasible, and it says so instead of relaxing.

Factor questions come back as a comparison chart with the leader lifted out and the gap to the leader
on every other bar:
5. `Compare the average landed cost of each supplier.`
6. `Show me previous deals with each supplier.`
7. `Which supplier has the best on-time delivery record?`

Explain the boundary: the model compiles the question into a ScenarioSpec or picks a metric and a chart
form; SciPy MILP and the metric registry compute every number. The model never supplies a value.

## 6. Close on the better problem - 30 sec

“Quote extraction is already becoming table stakes. The product advantage is the trust layer between
extraction and award: guided intake, provenance, exception handling, reversible assumptions and
deterministic scenarios. That is what makes a buyer comfortable acting on an AI-generated comparison
with crores at stake.”
