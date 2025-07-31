from fastapi import APIRouter, Request, HTTPException
import json
import secrets
from datetime import datetime
import stripe

router = APIRouter()

@router.post("/webhook")
async def stripe_webhook(request: Request):
    """Handle Stripe webhook events"""
    try:
        payload = await request.body()
        event = json.loads(payload)
        
        print(f"\n🎉 Webhook received: {event.get('type', 'unknown')}")
        
        # Handle different event types
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            
            # Get customer details
            customer_email = session.get('customer_email') or session.get('customer_details', {}).get('email')
            customer_id = session.get('customer')
            subscription_id = session.get('subscription')
            
            # Generate API key
            api_key = f"kbi_{secrets.token_urlsafe(32)}"
            
            print(f"✅ New customer: {customer_email}")
            print(f"💳 Customer ID: {customer_id}")
            print(f"📊 Subscription ID: {subscription_id}")
            print(f"🔑 Generated API key: {api_key}")
            
            # TODO: Save to your database
            # db.save_customer(customer_email, api_key, subscription_id)
            
        elif event['type'] == 'customer.subscription.deleted':
            subscription = event['data']['object']
            print(f"❌ Subscription cancelled: {subscription.get('id')}")
            # TODO: Deactivate API key
            
        elif event['type'] == 'invoice.payment_failed':
            invoice = event['data']['object']
            print(f"⚠️ Payment failed for customer: {invoice.get('customer_email')}")
            # TODO: Suspend API key
            
        return {"status": "success"}
        
    except Exception as e:
        print(f"❌ Webhook error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/webhook/test")
async def test_webhook():
    """Test endpoint to verify webhook is working"""
    return {"status": "Webhook endpoint is active"}
