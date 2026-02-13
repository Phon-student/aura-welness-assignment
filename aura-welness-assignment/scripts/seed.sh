#!/bin/bash
# Seed script to load sample data

API_URL="${API_URL:-http://localhost:8000}"

echo "Waiting for API to be ready..."
until curl -s "$API_URL/health" > /dev/null 2>&1; do
    sleep 2
done
echo "API is ready!"

echo ""
echo "Creating tenant..."
TENANT_RESPONSE=$(curl -s -X POST "$API_URL/tenants" \
  -H "Content-Type: application/json" \
  -d '{"name": "Acme Corporation", "slug": "acme"}')
echo "Tenant created: $TENANT_RESPONSE"

TENANT_ID=1

echo ""
echo "Ingesting Employee Handbook..."
curl -s -X POST "$API_URL/documents" \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: $TENANT_ID" \
  -d '{
    "title": "Employee Handbook",
    "content": "# Vacation Policy\n\nAll full-time employees receive 20 days of paid time off (PTO) per year. PTO accrues monthly at a rate of 1.67 days per month. Unused PTO can roll over to the next year, up to a maximum of 5 days. Any PTO beyond 5 days will be forfeited at year end.\n\n# Sick Leave\n\nEmployees have unlimited sick leave with manager approval. For absences longer than 3 consecutive days, a doctor note may be required. Sick leave should not be used for vacation purposes.\n\n# Remote Work\n\nEmployees may work remotely up to 3 days per week with manager approval. Core collaboration hours are 10am-3pm in your local timezone. All remote work must be logged in the HR system.\n\n# Performance Reviews\n\nPerformance reviews are conducted twice per year in June and December. Self-assessments are due two weeks before the review meeting. Managers provide written feedback and discuss career development goals.",
    "source": "hr/employee-handbook.md"
  }'

echo ""
echo "Ingesting IT Security Policy..."
curl -s -X POST "$API_URL/documents" \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: $TENANT_ID" \
  -d '{
    "title": "IT Security Policy",
    "content": "# Password Requirements\n\nAll passwords must be at least 12 characters long and include uppercase, lowercase, numbers, and special characters. Passwords must be changed every 90 days. Do not reuse your last 5 passwords.\n\n# Two-Factor Authentication\n\n2FA is required for all company systems. Use the approved authenticator app (Google Authenticator or Authy). Hardware security keys are available for high-security roles.\n\n# Data Classification\n\nData is classified as Public, Internal, Confidential, or Restricted. Confidential and Restricted data must be encrypted at rest and in transit. Never share Restricted data via email.\n\n# Incident Reporting\n\nReport security incidents immediately to security@company.com. Do not attempt to investigate on your own. Preserve all evidence and document what you observed.",
    "source": "it/security-policy.md"
  }'

echo ""
echo "Ingesting Expense Policy..."
curl -s -X POST "$API_URL/documents" \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: $TENANT_ID" \
  -d '{
    "title": "Expense Reimbursement Policy",
    "content": "# Eligible Expenses\n\nThe company reimburses reasonable business expenses including travel, meals with clients, office supplies, and professional development. All expenses over $50 require a receipt.\n\n# Travel Policy\n\nBook flights at least 14 days in advance when possible. Economy class is standard for flights under 6 hours. Hotel rates should not exceed $200/night without VP approval.\n\n# Meal Limits\n\nDaily meal limits: Breakfast $20, Lunch $30, Dinner $50. Client entertainment meals up to $100/person with director approval.\n\n# Submission Process\n\nSubmit expenses within 30 days of incurrence via the expense system. Include itemized receipts and business justification. Approvals are required from your direct manager for expenses under $500, and VP for expenses above.",
    "source": "finance/expense-policy.md"
  }'

echo ""
echo ""
echo "Seed data loaded successfully!"
echo ""
echo "Test with:"
echo "curl -X POST $API_URL/ask -H 'Content-Type: application/json' -H 'X-Tenant-ID: 1' -d '{\"question\": \"How many vacation days do I get?\"}'"
