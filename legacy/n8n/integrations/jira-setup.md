# Jira Integration Setup

**Bandit — Integration Guide**

The Jira integration automatically creates tickets for Medium+ risk assessments, assigns them to the appropriate reviewer, and tracks remediation status.

---

## Prerequisites

- Jira Cloud or Jira Server/Data Center account
- Project admin access to create custom fields

---

## Step 1: Create an API Token

**Jira Cloud:**
1. Go to [id.atlassian.com/manage-profile/security/api-tokens](https://id.atlassian.com/manage-profile/security/api-tokens)
2. Click **Create API token**
3. Name it `privacy-lens-n8n`
4. Copy the token — you won't see it again

**Jira Server / Data Center:**
1. Go to **Profile → Personal Access Tokens → Create token**

---

## Step 2: Configure n8n Credential

1. In n8n: **Settings → Credentials → New → Jira Software**
2. Fill in:
   - **Email**: your Jira account email
   - **API Token**: token from Step 1
   - **Domain**: `https://your-org.atlassian.net`
3. Name the credential `Jira - Bandit`

---

## Step 3: Set Up Jira Project

Create or designate a Jira project for privacy assessments. Recommended setup:

**Issue Type:** `Privacy Assessment`

**Custom Fields to Add:**

| Field Name | Type | Used For |
|------------|------|----------|
| `Privacy Risk Score` | Number | Overall PRS |
| `Risk Level` | Select (Low/Medium/High/Critical) | Routing |
| `Vendor Name` | Text | Vendor identifier |
| `Assessment Date` | Date | Tracking |
| `DPA Required` | Checkbox | Action tracking |
| `D7 AI Score` | Number | EU AI Act flag |

**Workflow Statuses:**
- `Open` → `In Review` → `Remediation Required` → `Approved` / `Rejected`

---

## Step 4: Configure Ticket Routing

The workflow creates Jira tickets based on risk level:

| Risk Level | Priority | Assignee | Labels |
|------------|----------|----------|--------|
| Medium-High (PRS 3.1–3.5) | Medium | Privacy Team | `privacy-review` |
| High (PRS 3.6–4.5) | High | DPO | `privacy-review`, `legal-required` |
| Critical (PRS 4.6–5.0) | Urgent | DPO | `privacy-review`, `legal-required`, `do-not-proceed` |

---

## Step 5: Configure Workflow Nodes

In the **Create Jira Ticket** node of each workflow:

```json
{
  "project": { "key": "PRIV" },
  "summary": "Privacy Assessment: {{vendor_name}} — PRS {{score}} ({{risk_level}})",
  "description": "{{assessment_summary}}\n\nFull report: {{drive_link}}",
  "issuetype": { "name": "Privacy Assessment" },
  "priority": { "name": "{{jira_priority}}" },
  "labels": ["privacy-lens", "vendor-assessment"],
  "customfield_privacy_risk_score": "{{prs}}",
  "customfield_risk_level": "{{risk_level}}",
  "customfield_vendor_name": "{{vendor_name}}",
  "customfield_dpa_required": "{{dpa_required}}"
}
```

Replace `customfield_*` names with your actual Jira custom field IDs (format: `customfield_10001`).

---

## Finding Custom Field IDs

```bash
curl -u your-email@example.com:your-api-token \
  https://your-org.atlassian.net/rest/api/3/field \
  | jq '.[] | select(.custom==true) | {id, name}'
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `401 Unauthorized` | Check API token and email in credential |
| `400 Bad Request` | Verify project key and issue type name are exact |
| Custom field error | Use numeric field IDs, not display names |
| Ticket created but missing fields | Ensure fields are on the project's create screen |
