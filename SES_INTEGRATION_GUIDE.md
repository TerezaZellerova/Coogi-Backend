# Amazon SES Integration Guide for COOGI Backend

## Overview
The COOGI backend now includes comprehensive Amazon SES (Simple Email Service) integration for robust email delivery. This provides an alternative to Instantly.ai and Smartlead.ai for email campaigns.

## 🚀 Features Added

### 1. SES Manager (`utils/ses_manager.py`)
- **Email sending**: Single and bulk email delivery
- **Template management**: Create and use email templates
- **Bounce/complaint handling**: Automatic processing of delivery issues
- **Statistics tracking**: Monitor send rates, bounce rates, and reputation
- **Quota monitoring**: Track daily sending limits

### 2. API Endpoints (`api/routers/campaigns.py`)
- `POST /api/ses/send-email` - Send individual emails
- `POST /api/ses/send-bulk-email` - Send bulk personalized emails
- `POST /api/ses/create-template` - Create email templates
- `GET /api/ses/stats` - Get account statistics and reputation
- `POST /api/ses/create-campaign` - Create SES-powered recruiting campaigns
- `POST /api/ses/bounce-complaint` - Handle webhook notifications

### 3. New Models (`api/models.py`)
- `SESEmailRequest` - Single email sending
- `SESBulkEmailRequest` - Bulk email with personalization
- `SESCampaignRequest` - Full recruiting campaign with SES
- `SESCampaignResponse` - Campaign creation results
- `EmailProviderStats` - Provider statistics and health

## 🔧 Environment Setup

### Required Environment Variables
Add these to your Render environment or `.env` file:

```bash
# Amazon SES Configuration
AWS_ACCESS_KEY_ID=your_aws_access_key_id
AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key
AWS_REGION=us-east-1  # or your preferred region
```

### AWS SES Setup Steps

1. **Create AWS Account** (if not exists)
2. **Enable SES Service** in your chosen region
3. **Verify Domain/Email Addresses**:
   - Go to SES Console → Verified identities
   - Add your sending domain or email address
   - Complete verification process

4. **Create IAM User** for COOGI:
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Action": [
           "ses:SendEmail",
           "ses:SendBulkTemplatedEmail",
           "ses:SendTemplatedEmail",
           "ses:CreateTemplate",
           "ses:GetSendStatistics",
           "ses:GetSendQuota",
           "ses:GetReputation",
           "ses:GetIdentityVerificationAttributes"
         ],
         "Resource": "*"
       }
     ]
   }
   ```

5. **Move out of Sandbox** (for production):
   - Request production access in SES Console
   - Required for sending to unverified email addresses

## 📊 Usage Examples

### 1. Create SES-Powered Campaign
```bash
curl -X POST "https://your-backend.com/api/ses/create-campaign" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_token" \
  -d '{
    "query": "software engineer jobs in San Francisco",
    "campaign_name": "SF_Engineers_Q1_2025",
    "max_leads": 50,
    "min_score": 0.7,
    "from_email": "recruiting@yourcompany.com",
    "subject": "Exciting Software Engineering Opportunity at {company}",
    "email_template": "Hi {name}, I saw your role at {company} for {job_title}...",
    "send_immediately": false
  }'
```

### 2. Send Bulk Personalized Emails
```bash
curl -X POST "https://your-backend.com/api/ses/send-bulk-email" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_token" \
  -d '{
    "emails_data": [
      {
        "email": "john@company.com",
        "template_data": {"name": "John", "company": "TechCorp", "position": "Senior Developer"}
      }
    ],
    "template_name": "recruiting_outreach",
    "from_email": "recruiting@yourcompany.com"
  }'
```

### 3. Check SES Statistics
```bash
curl -X GET "https://your-backend.com/api/ses/stats" \
  -H "Authorization: Bearer your_token"
```

## 🔄 Integration with Existing Workflow

### Multi-Provider Campaign Strategy
The backend now supports multiple email providers:

1. **SES**: High volume, reliable delivery, cost-effective
2. **Instantly.ai**: Advanced automation, follow-up sequences
3. **Smartlead.ai**: AI-powered personalization

### Recommended Usage:
- **Initial outreach**: Use SES for cost-effective bulk sending
- **Follow-ups**: Use Instantly.ai for automated sequences
- **High-value prospects**: Use Smartlead.ai for AI personalization

## 📈 Benefits of SES Integration

### Cost Efficiency
- $0.10 per 1,000 emails (vs $30-50/month for other providers)
- No monthly subscription fees
- Pay-per-use model

### Reliability
- AWS infrastructure (99.9% uptime)
- Global delivery network
- Automatic bounce/complaint handling

### Scalability
- Start with 200 emails/day (sandbox)
- Scale to 10M+ emails/day (production)
- Rate limits: up to 14 emails/second

### Compliance
- Built-in suppression list management
- Automatic bounce/complaint processing
- GDPR/CAN-SPAM compliance features

## 🚨 Important Notes

### Testing
- Use the provided test script: `python test_ses_integration.py`
- Always test in sandbox mode first
- Verify email addresses during development

### Monitoring
- Monitor bounce rates (<5% recommended)
- Watch complaint rates (<0.1% recommended)
- Track reputation scores regularly

### Best Practices
- Use verified domains for better deliverability
- Implement proper email templates
- Set up SNS notifications for bounces/complaints
- Maintain clean email lists

## 🔗 Related Files
- `utils/ses_manager.py` - SES implementation
- `api/routers/campaigns.py` - API endpoints
- `api/models.py` - Data models
- `requirements.txt` - Dependencies (boto3, botocore)
- `render-env-vars.template` - Environment configuration
