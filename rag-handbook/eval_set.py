"""A 20-question eval set over a constructed support knowledge base.

Each question has one `fact`: a string that must appear in a retrieved chunk for the
question to count as answered. Matching on text instead of chunk ids means the same
set still works after you change your chunking. The company, docs and numbers are made up.
"""

DOCS = [
    "Invoices are generated on the first day of each month and sent to the billing contact by email.",
    "Payment is due within 30 days of the invoice date, and late payments add a fee of 1.5 percent per month.",
    "Annual plans are refunded pro rata if cancelled within 60 days of purchase, and not after that.",
    "Usage above the plan quota is billed at 0.002 dollars per extra API call.",
    "Tax IDs can be added under Settings, Billing, Tax. VAT is applied to EU customers without a valid ID.",
    "API keys are created in the console under Settings, Keys. Each key can be limited to read-only access.",
    "A key that has not been used for 90 days is disabled automatically and an admin can re-enable it.",
    "Single sign-on is available on the Business plan using SAML 2.0. Okta and Entra ID are tested.",
    "Passwords must be at least 12 characters. Accounts lock for 15 minutes after five failed sign-ins.",
    "Two-factor authentication is required for all admin accounts and supports authenticator apps and hardware keys.",
    "The free plan allows 1,000 API calls per day. The Pro plan allows 100,000 per day.",
    "Requests above the rate limit receive HTTP 429 and a Retry-After header giving the seconds to wait.",
    "The maximum request body is 5 MB. Larger uploads must use the multipart upload endpoint.",
    "Batch jobs may contain up to 500 items and normally finish within 10 minutes.",
    "Webhooks are retried up to 8 times with exponential backoff, starting at 30 seconds.",
    "ERR-2041 means the API key is valid but lacks permission for the requested project.",
    "ERR-2014 means the request signature timestamp is more than 5 minutes out of date.",
    "ERR-2410 means the project has reached its storage quota and writes are paused.",
    "ERR-4021 means the webhook endpoint returned a non-2xx status on the last attempt.",
    "ERR-2104 means the uploaded file type is not on the allowed list.",
    "Deleted projects are kept for 30 days in a recovery state before permanent removal.",
    "Backups run every night at 02:00 UTC and are retained for 35 days.",
    "Data is stored in the region chosen at project creation. Moving regions needs a support request.",
    "Exports are available as CSV or Parquet. Large exports arrive as a download link valid for 48 hours.",
    "Audit logs record sign-ins and key changes. They are kept for 400 days on the Business plan and 30 days on Pro.",
    "Support replies within 1 business day on Pro and within 4 hours on Business for severity 1 tickets.",
    "Status updates are posted on the status page, and subscribers get an email within 10 minutes of an incident.",
    "Feature requests go to the public roadmap board, where customers vote on them.",
]

# (question, fact that must reach the prompt, kind)
QUESTIONS = [
    ("How many API calls per day does the Pro plan allow?", "100,000 per day", "plain"),
    ("How long are deleted projects recoverable?", "30 days in a recovery state", "plain"),
    ("When do I have to pay an invoice?", "due within 30 days", "plain"),
    ("How many times is a failed webhook retried?", "up to 8 times", "plain"),
    ("Which single sign-on standard is supported?", "SAML 2.0", "plain"),
    ("What is the largest request body I can send?", "maximum request body is 5 MB", "plain"),
    ("How long do you keep nightly backups?", "retained for 35 days", "plain"),
    ("How long are audit logs kept on Pro?", "30 days on Pro", "plain"),
    ("What export formats can I get?", "CSV or Parquet", "plain"),
    ("How soon will support answer an urgent ticket on Business?", "within 4 hours on Business", "plain"),
    ("What happens to a key I have not touched for three months?", "disabled automatically", "reworded"),
    ("Can I get my money back on a yearly subscription?", "refunded pro rata", "reworded"),
    ("How long do I wait after being throttled?", "Retry-After header", "reworded"),
    ("What happens if I enter the wrong password too many times?", "lock for 15 minutes", "reworded"),
    ("Can I move my data to a different region?", "Moving regions needs a support request", "reworded"),
    ("Why have my writes stopped working?", "storage quota and writes are paused", "reworded"),
    ("What does ERR-2041 mean?", "ERR-2041 means", "code"),
    ("What does ERR-2014 mean?", "ERR-2014 means", "code"),
    ("What does ERR-4021 mean?", "ERR-4021 means", "code"),
    ("What does ERR-2104 mean?", "ERR-2104 means", "code"),
]
