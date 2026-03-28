# Slack Integration Setup

**Bandit — Integration Guide**

The Slack integration sends formatted risk assessment alerts to designated channels, with escalation pings for High and Critical findings.

---

## Prerequisites

- Slack workspace admin access (to install an app)

---

## Step 1: Create a Slack App

1. Go to [api.slack.com/apps](https://api.slack.com/apps)
2. Click **Create New App → From Scratch**
3. Name: `Bandit` | Select your workspace
4. Go to **OAuth & Permissions**
5. Under **Bot Token Scopes**, add:
   - `chat:write`
   - `chat:write.public`
   - `incoming-webhook`
6. Click **Install to Workspace** and authorize
7. Copy the **Bot User OAuth Token** (starts with `xoxb-`)

---

## Step 2: Configure n8n Credential

1. In n8n: **Settings → Credentials → New → Slack OAuth2 API**
2. Paste the Bot User OAuth Token
3. Name the credential `Slack - Bandit`

---

## Step 3: Set Up Slack Channels

Create the following channels (or use existing ones):

| Channel | Purpose |
|---------|---------|
| `#privacy-assessments` | All completed assessments |
| `#privacy-alerts` | High and Critical risk alerts |
| `#dpo-escalations` | Critical only — DPO team |

Invite the Bandit bot to each channel: `/invite @Bandit`

---

## Step 4: Message Templates

The workflow sends different messages based on risk level.

### Low / Medium Assessment (to `#privacy-assessments`)
```
*Privacy Assessment Complete* ✅
*Vendor:* {{vendor_name}}
*Risk Score:* {{prs}} / 5.0
*Risk Level:* Low
*Date:* {{assessment_date}}
<{{drive_link}}|View Full Report>
```

### High Risk Alert (to `#privacy-alerts`)
```
*⚠️ HIGH RISK — Privacy Assessment*
*Vendor:* {{vendor_name}}
*Risk Score:* {{prs}} / 5.0
*Risk Level:* HIGH
*Top Risk:* {{top_risk_1}}
*Action Required:* Legal review + DPA negotiation before contract
<{{jira_link}}|Jira Ticket> | <{{drive_link}}|Full Report>
```

### Critical Risk Alert (to `#dpo-escalations`)
```
*🚨 CRITICAL — Do Not Proceed*
*Vendor:* {{vendor_name}}
*Risk Score:* {{prs}} / 5.0
@{{dpo_slack_handle}} — DPO sign-off required before any further steps.
*Key Findings:*
• {{top_risk_1}}
• {{top_risk_2}}
• {{top_risk_3}}
<{{jira_link}}|Jira Ticket> | <{{drive_link}}|Full Report>
```

---

## Step 5: Configure Workflow Nodes

In the **Slack Notification** node of each workflow:

| Parameter | Value |
|-----------|-------|
| Authentication | `Slack - Bandit` credential |
| Channel | Dynamic based on risk level (use Switch node output) |
| Message | Template from Step 4 |
| As User | `Bandit` |

---

## Optional: Slack Workflow Button (Approve/Reject)

For interactive approval flows, add Block Kit buttons to High risk messages that update the Jira ticket status when clicked. This requires the **Interactivity & Shortcuts** feature enabled in your Slack App settings and a public webhook URL in n8n.

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `channel_not_found` | Ensure bot is invited to the channel |
| `not_in_channel` | Use `chat:write.public` scope or invite bot |
| Messages not posting | Verify Bot Token scope includes `chat:write` |
| Mentions not working | Use member ID format `<@U1234567>` not `@username` |
