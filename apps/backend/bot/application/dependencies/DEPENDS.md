```python
from datetime import datetime
from dataclasses import asdict
import json

@router.post("/chat/stream")
async def chat(
    request: ChatStreamRequest,
    current_user=Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service),
    auth_service: AuthService = Depends(get_auth_service),
):
    # ===== DEBUG LOGGING =====
    print("=" * 60)
    print("🔍 CURRENT USER DATA")
    print("=" * 60)
    
    # Method 1: Direct print
    print(f"\n📌 Full Object:\n{current_user}\n")
    
    # Method 2: Individual fields
    print(f"👤 User Info:")
    print(f"  ├─ ID: {current_user.id}")
    print(f"  ├─ Public ID: {current_user.public_id}")
    print(f"  ├─ Email: {current_user.email}")
    print(f"  └─ Display Name: {current_user.display_name}")
    
    print(f"\n🔐 Auth Info:")
    print(f"  ├─ Type: {current_user.user_type}")
    print(f"  ├─ Provider: {current_user.auth_provider}")
    print(f"  ├─ Session ID: {current_user.session_id}")
    print(f"  └─ Expires At: {current_user.session_expires_at}")
    
    print(f"\n💬 Message Quota:")
    print(f"  ├─ Limit: {current_user.guest_message_limit}")
    print(f"  ├─ Used: {current_user.guest_messages_used}")
    print(f"  └─ Remaining: {current_user.remaining_guest_messages}")
    
    # Method 3: JSON format
    user_data = asdict(current_user)
    user_data['session_expires_at'] = str(current_user.session_expires_at)  # Convert datetime
    
    print(f"\n📋 JSON Format:")
    print(json.dumps(user_data, indent=2))
    
    print("=" * 60)
    
    # NOW continue with your logic
    try:
        current_user = auth_service.consume_chat_credit(current_user)
        # ... rest of code
```