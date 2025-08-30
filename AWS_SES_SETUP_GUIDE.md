# 🚀 Coogi.com AWS SES Setup Guide

## Prerequisites
- AWS Account
- Domain `coogi.com` purchased and accessible
- Access to DNS management for coogi.com

## Step 1: AWS SES Console Setup

### 1.1 Access AWS SES
1. Login to [AWS Console](https://aws.amazon.com/console/)
2. Search for "SES" (Simple Email Service)
3. **Select Region: us-east-1** (recommended for best deliverability)

### 1.2 Domain Verification
1. Go to **SES Console > Identities**
2. Click **"Create Identity"**
3. Select **"Domain"**
4. Enter domain: `coogi.com`
5. Keep **"Easy DKIM"** enabled ✅
6. Click **"Create Identity"**

## Step 2: DNS Records Configuration

AWS will provide you with **4 DNS records** to add:

### Records You'll Get:
```
1. TXT Record (Domain Verification):
   Name: _amazonses.coogi.com
   Value: [long verification string]

2-4. CNAME Records (DKIM Authentication):
   Name: [random1]._domainkey.coogi.com
   Value: [random1].dkim.amazonses.com
   
   Name: [random2]._domainkey.coogi.com  
   Value: [random2].dkim.amazonses.com
   
   Name: [random3]._domainkey.coogi.com
   Value: [random3].dkim.amazonses.com
```

### Where to Add DNS Records:
1. Go to your **domain registrar** (where you bought coogi.com)
2. Find **DNS Management** or **DNS Settings**
3. Add all 4 records exactly as AWS provides
4. **Save changes**

⏱️ **DNS propagation takes 5-15 minutes**

## Step 3: Request Production Access

### 3.1 Exit Sandbox Mode
1. In SES Console, go to **"Account dashboard"**
2. Click **"Request production access"**
3. Fill out the form:

```
Mail Type: Transactional
Website URL: https://your-frontend-url.com
Use Case Description:
"AI-powered lead generation platform sending automated outreach emails 
and campaign notifications to verified business contacts. Daily volume 
approximately 2,000 emails. All recipients have opted in or are being 
contacted for legitimate business purposes."

Additional Details:
"Platform generates personalized job application emails and follow-up 
campaigns. All emails include unsubscribe options and comply with 
anti-spam regulations."
```

4. **Submit request**
5. ⏱️ **Approval usually takes 24-48 hours**

## Step 4: AWS Credentials Setup

### 4.1 Create IAM User for SES
1. Go to **AWS Console > IAM**
2. Click **"Users" > "Create user"**
3. Username: `coogi-ses-user`
4. Select **"Attach policies directly"**
5. Search and select: **`AmazonSESFullAccess`**
6. Click **"Create user"**

### 4.2 Generate Access Keys
1. Click on the created user
2. Go to **"Security credentials"** tab
3. Click **"Create access key"**
4. Select **"Application running on AWS service"** 
5. **Download** or copy:
   - Access Key ID
   - Secret Access Key

## Step 5: Backend Environment Configuration

### 5.1 Add Environment Variables
Add these to your **Render environment variables**:

```bash
# AWS SES Configuration
AWS_ACCESS_KEY_ID=AKIA...your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_access_key
AWS_REGION=us-east-1
AWS_SES_FROM_EMAIL=noreply@coogi.com
```

### 5.2 Update Render Deployment
1. Go to **Render Dashboard**
2. Select your backend service
3. Go to **Environment** tab
4. Add the AWS variables above
5. Click **"Save Changes"**
6. **Redeploy** the service

## Step 6: Test Email Configuration

### 6.1 Test API Endpoint
Once backend is deployed, test the email system:

```bash
curl -X POST "https://coogi-backend-7yca.onrender.com/email/test" \
  -H "Content-Type: application/json" \
  -d '{"test_email": "your-email@example.com"}'
```

### 6.2 Check Domain Status
```bash
curl "https://coogi-backend-7yca.onrender.com/email/domain-status"
```

### 6.3 Check Sending Quota
```bash
curl "https://coogi-backend-7yca.onrender.com/email/quota"
```

## Step 7: Verification Checklist

### ✅ Pre-Launch Checklist:
- [ ] Domain `coogi.com` DNS records added
- [ ] Domain verification status: **"Success"** in AWS SES
- [ ] Production access approved (out of sandbox)
- [ ] AWS credentials configured in Render
- [ ] Backend deployed with email endpoints
- [ ] Test email sent successfully
- [ ] Sending quota shows > 200 emails/day

### 📧 Email Addresses You Can Use:
- `noreply@coogi.com` - Default sending address
- `support@coogi.com` - Customer support
- `campaigns@coogi.com` - Marketing campaigns
- `notifications@coogi.com` - System notifications

## Step 8: Daily Usage (2k emails)

### 🎯 Perfect for Your Volume:
- **Sandbox limit**: 200 emails/day ❌
- **Production limit**: 10,000+ emails/day ✅
- **Your target**: 2,000 emails/day ✅

### 💰 Cost Estimation:
- **AWS SES**: $0.10 per 1,000 emails
- **2,000 emails/day**: ~$0.20/day = $6/month
- **Very affordable!** 💚

## Troubleshooting

### Common Issues:

1. **Domain not verified**:
   - Check DNS records are added correctly
   - Wait 15-30 minutes for propagation
   - Verify records using `dig` or online DNS checker

2. **Still in sandbox**:
   - Production access request pending
   - Fill out use case form more detailed
   - Contact AWS support if delayed

3. **Emails not sending**:
   - Check AWS credentials in Render
   - Verify `from_email` domain is verified
   - Check SES error logs in AWS CloudWatch

4. **High bounce rate**:
   - Use verified, valid email addresses
   - Implement email validation before sending
   - Monitor reputation in SES dashboard

## Support
- **AWS SES Documentation**: https://docs.aws.amazon.com/ses/
- **Render Environment Variables**: https://render.com/docs/environment-variables
- **DNS Checker**: https://mxtoolbox.com/dnscheck.aspx

---
**🎉 Once setup is complete, you'll have a production-ready email system capable of sending 2k+ personalized outreach emails daily!**
