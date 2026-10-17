# Interview Notes: likely questions and simple answers

Put these in your own words. Each answer is short on purpose.

## The project

**Q: What does it do, in one sentence?**
It reads invoices automatically with Azure AI, flags likely duplicates before they're paid, and lets finance users ask questions about spend in plain English.

**Q: Why did you build it?**
Accounts payable is still very manual. The two biggest pain points are data entry and duplicate payments, and those are exactly what the company automates.

**Q: Walk me through what happens when I upload an invoice.**
1. The file is checked: type, size, and whether it's really a PDF or image.
2. Azure Document Intelligence reads the fields.
3. The fields are compared with existing invoices for duplicates.
4. The file goes to Blob Storage and the data goes to Azure SQL.
5. Everything is logged to Application Insights.

## Azure

**Q: Which Azure services did you use, and why each?**
- **Document Intelligence**: a ready-made invoice model, so no training is needed.
- **Blob Storage**: cheap, private storage for the original files.
- **Azure SQL**: relational data, and separate logins for read and write.
- **App Service**: hosting with HTTPS and no servers to manage.
- **Key Vault**: holds all the secrets.
- **Application Insights**: monitoring.

**Q: Why Azure SQL and not Cosmos DB or PostgreSQL?**
Invoices, line items and duplicate pairs are relational data, and the chatbot writes SQL. Azure SQL's free offer stays free for the life of the subscription and auto-pauses instead of charging me. PostgreSQL is only free for 12 months.

**Q: How did you keep it free on a student account?**
- Document Intelligence F0 is free for 500 pages a month.
- The SQL free offer auto-pauses when the free amount is used up.
- App Service runs on the F1 free tier.
- Log ingestion is capped at 1 GB a day.
- Storage and Key Vault cost only cents.
- Sample data is loaded with an offline reader, so it doesn't use up free Azure pages.

**Q: What is a managed identity?**
An identity Azure gives to my web app. The app uses it to read Key Vault secrets, so there's no password stored anywhere to read the passwords. I gave it the narrowest role: *Key Vault Secrets User*.

**Q: What does Application Insights show you?**
Logins (including failed ones), uploads, rejected files, blocked SQL attempts, errors and response times. If someone tried a prompt-injection attack, I'd see a `sql_blocked` event.

**Q: What is Bicep?**
Infrastructure as code. All the Azure resources are defined in one file, so the whole environment can be recreated with one command, and every change is reviewable in git.

## Duplicate detection (your strongest area: link it to your 98.3% supplier-matching project)

**Q: How does duplicate detection work?**
I clean the data first, then score how similar four things are:

| Signal | Weight | What the cleaning does |
|---|---|---|
| Vendor name | 35% | Removes "Pvt Ltd", dots and case |
| Invoice number | 30% | Removes slashes, dashes and leading zeros |
| Amount | 25% | |
| Date | 10% | |

A score of 90% or more is *likely* a duplicate. 80–90% is *possible*, and a person reviews it.

**Q: Why those weights?**
Vendor plus invoice number is what identifies an invoice, so together they get 65%. The amount confirms it. The date gets the least weight because vendors often re-send an invoice with a new date.

**Q: How do you avoid false alarms?**
- Monthly bills are the classic false positive: same vendor, same amount every month. Their invoice numbers differ only in the digits (OSF/2026/07 vs /08). So if the digits differ, I cap the invoice-number score at 50%, which keeps those pairs at 75%, below the 80% threshold.
- Two quick gates run first: the currency must match, and the vendor names must be at least 75% similar.

**Q: What precision did you get?**
On the 39 sample invoices: 5 planted duplicates, all 5 found, and 0 false alarms. Recurring bills scored 0.75 and were correctly ignored. In my earlier supplier pipeline I measured 98.3% precision on real data. Precision mattered most there too, because false alarms make people ignore the tool.

**Q: How would you tune the thresholds on real data?**
1. Take a labelled sample of real duplicates and non-duplicates.
2. Plot precision and recall at different thresholds.
3. Pick the threshold based on the cost of each error. Paying a duplicate costs money, while a false flag costs about 30 seconds of a reviewer's time, so I'd lean towards catching more.

**Q: Won't comparing against every invoice be slow with millions of rows?**
Yes. I'd use "blocking": only compare invoices with the same currency and a similar vendor (for example the same normalised vendor key) within a date window. That cuts the comparisons enormously.

## The chatbot and security (the job description emphasises this)

**Q: How does the chatbot work?**
1. The LLM gets my question and a description of the tables (never the data or the passwords).
2. It writes one SQL query.
3. My code validates that query and runs it on a read-only connection.
4. The LLM turns the result rows into a sentence. The app also shows a table or chart, and the exact SQL, so the answer is auditable.

**Q: What stops the chatbot from deleting data?**
Two independent locks:
1. **A validator.** It allows exactly one SELECT statement, with no comments and no dangerous keywords. It parses the query into a syntax tree and checks that it really is a SELECT, and that every table is on the allow-list.
2. **A read-only database user.** It has SELECT permission on three tables, and writes are explicitly denied.

Even if the AI were tricked, both locks would have to fail at once.

**Q: What is SQL injection, and how is it prevented?**
SQL injection is when user input gets pasted into a SQL command and changes what the command does. Everywhere the app writes data, I use parameterised queries, where values are sent separately from the SQL, so they can never become commands. The chatbot's SQL is handled by the validator plus the read-only login.

**Q: What is prompt injection?**
It's when someone writes instructions in their question to hijack the AI, like "ignore your rules and…". My defence doesn't rely on the AI behaving, because the database layer enforces read-only access. I also treat result rows as untrusted when the LLM summarises them, since vendor names come from uploaded documents.

**Q: Why not just let the LLM answer from the data directly?**
SQL gives exact totals, while LLMs can be bad at arithmetic. The query is also auditable, and the data doesn't need to be sent to the AI provider in bulk.

**Q: What if the LLM writes a wrong query?**
If it fails validation or errors, the app sends the error back once so the LLM can correct itself. I also show the SQL so a user can sanity-check it. For production I'd add a set of test questions with known answers and run them on every change.

**Q: How do you handle mixed INR and GBP?**
Each invoice keeps its original currency, plus a `total_inr` column at a fixed demo rate, so totals across vendors are comparable. In production I'd store the FX rate as of the invoice date.

**Q: How is login secured?**
Passwords are stored as salted PBKDF2 hashes with 310,000 iterations, never in plain text. The comparison is constant-time, and 5 wrong attempts lock the account for 5 minutes. In production I'd switch to Microsoft Entra ID single sign-on.

**Q: How do you validate uploads?**
- File type and size (10 MB limit).
- Magic bytes, so a renamed .exe is rejected.
- PDFs containing JavaScript are blocked.
- Files are saved under a hash, not the user's filename.
- An identical re-upload is caught by its file hash.

## Engineering

**Q: How did you test it?**
67 automated tests (pytest):
- Duplicate scoring, including the full sample set at 100% precision and recall.
- More than 25 malicious SQL patterns, all of which must be blocked.
- That the read-only connection really refuses writes.
- End-to-end upload and chatbot runs with a fake LLM, so no API key is needed.

**Q: How do you switch LLM providers?**
Only through environment variables: base URL, model and key. Groq and xAI both offer OpenAI-compatible APIs, so the code doesn't change.

**Q: What would you improve next?**
- Microsoft Entra ID login.
- Managed identity for storage too.
- An approval workflow and ERP export.
- Vendor master data (GSTIN/VAT number matching for even better duplicate detection).
- Line-item-level checks, such as a price higher than the last invoice.
- Evaluation of extraction accuracy on real invoices.

**Q: What was the hardest part?**
*(Pick one that's true for you.)* Getting duplicate detection precise rather than just sensitive. Recurring bills looked like duplicates until I added the "different digits" rule. Or making the chatbot safe without making it useless.

**Q: How much did it cost to run?**
About ₹0 on the free tiers, plus a few rupees for storage and Key Vault operations.
