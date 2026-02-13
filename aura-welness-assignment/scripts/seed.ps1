# Seed script for Windows PowerShell
$API_URL = if ($env:API_URL) { $env:API_URL } else { "http://localhost:8000" }

Write-Host "Waiting for API to be ready..."
do {
    Start-Sleep -Seconds 2
    try {
        $health = Invoke-RestMethod -Uri "$API_URL/health" -Method Get -ErrorAction SilentlyContinue
    } catch {
        $health = $null
    }
} while (-not $health)
Write-Host "API is ready!"

Write-Host ""
Write-Host "Creating tenant..."
$tenantBody = @{
    name = "Acme Corporation"
    slug = "acme"
} | ConvertTo-Json

try {
    $tenant = Invoke-RestMethod -Uri "$API_URL/tenants" -Method Post -Body $tenantBody -ContentType "application/json"
    Write-Host "Tenant created: $($tenant | ConvertTo-Json -Compress)"
} catch {
    Write-Host "Tenant may already exist, continuing..."
}

$TENANT_ID = 1

Write-Host ""
Write-Host "Ingesting Employee Handbook..."
$doc1 = @{
    title = "Employee Handbook"
    content = @"
# Vacation Policy

All full-time employees receive 20 days of paid time off (PTO) per year. PTO accrues monthly at a rate of 1.67 days per month. Unused PTO can roll over to the next year, up to a maximum of 5 days. Any PTO beyond 5 days will be forfeited at year end.

# Sick Leave

Employees have unlimited sick leave with manager approval. For absences longer than 3 consecutive days, a doctor note may be required. Sick leave should not be used for vacation purposes.

# Remote Work

Employees may work remotely up to 3 days per week with manager approval. Core collaboration hours are 10am-3pm in your local timezone. All remote work must be logged in the HR system.

# Performance Reviews

Performance reviews are conducted twice per year in June and December. Self-assessments are due two weeks before the review meeting. Managers provide written feedback and discuss career development goals.
"@
    source = "hr/employee-handbook.md"
} | ConvertTo-Json

Invoke-RestMethod -Uri "$API_URL/documents" -Method Post -Body $doc1 -ContentType "application/json" -Headers @{"X-Tenant-ID"=$TENANT_ID}

Write-Host ""
Write-Host "Ingesting IT Security Policy..."
$doc2 = @{
    title = "IT Security Policy"
    content = @"
# Password Requirements

All passwords must be at least 12 characters long and include uppercase, lowercase, numbers, and special characters. Passwords must be changed every 90 days. Do not reuse your last 5 passwords.

# Two-Factor Authentication

2FA is required for all company systems. Use the approved authenticator app (Google Authenticator or Authy). Hardware security keys are available for high-security roles.

# Data Classification

Data is classified as Public, Internal, Confidential, or Restricted. Confidential and Restricted data must be encrypted at rest and in transit. Never share Restricted data via email.

# Incident Reporting

Report security incidents immediately to security@company.com. Do not attempt to investigate on your own. Preserve all evidence and document what you observed.
"@
    source = "it/security-policy.md"
} | ConvertTo-Json

Invoke-RestMethod -Uri "$API_URL/documents" -Method Post -Body $doc2 -ContentType "application/json" -Headers @{"X-Tenant-ID"=$TENANT_ID}

Write-Host ""
Write-Host "Ingesting Expense Policy..."
$doc3 = @{
    title = "Expense Reimbursement Policy"
    content = @"
# Eligible Expenses

The company reimburses reasonable business expenses including travel, meals with clients, office supplies, and professional development. All expenses over 50 dollars require a receipt.

# Travel Policy

Book flights at least 14 days in advance when possible. Economy class is standard for flights under 6 hours. Hotel rates should not exceed 200 dollars per night without VP approval.

# Meal Limits

Daily meal limits: Breakfast 20 dollars, Lunch 30 dollars, Dinner 50 dollars. Client entertainment meals up to 100 dollars per person with director approval.

# Submission Process

Submit expenses within 30 days of incurrence via the expense system. Include itemized receipts and business justification. Approvals are required from your direct manager for expenses under 500 dollars, and VP for expenses above.
"@
    source = "finance/expense-policy.md"
} | ConvertTo-Json

Invoke-RestMethod -Uri "$API_URL/documents" -Method Post -Body $doc3 -ContentType "application/json" -Headers @{"X-Tenant-ID"=$TENANT_ID}

Write-Host ""
Write-Host ""
Write-Host "Seed data loaded successfully!"
Write-Host ""
Write-Host "Test with:"
Write-Host 'Invoke-RestMethod -Uri "http://localhost:8000/ask" -Method Post -Body ''{"question": "How many vacation days do I get?"}'' -ContentType "application/json" -Headers @{"X-Tenant-ID"="1"}'
