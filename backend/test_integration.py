#!/usr/bin/env python3
"""
Test script to demonstrate the integration between telephony agent and backend system.
This script simulates function calls that would come from the telephony agent.
"""

import asyncio
import json
from backend_agent import process_function_call, backend_agent

async def test_full_call_flow():
    """Simulate a complete call flow with function calls"""
    print("🚀 Starting Integration Test - Simulating Full Call Flow")
    print("=" * 60)
    
    # Simulate session ID
    session_id = "test_session_12345"
    caller_id = "John_Doe_555-1234"
    
    # Test 1: Call start
    print("\n1. 📞 Call Start - Opening Script")
    result = await process_function_call(
        "share_information",
        {
            "information": "Call started - opening script delivered",
            "category": "conversation_flow",
            "caller_id": caller_id
        },
        session_id
    )
    print(f"Result: {result['message'] if result['success'] else result['error']}")
    
    # Test 2: Customer identity confirmation
    print("\n2. 👤 Customer Identity Confirmation")
    result = await process_function_call(
        "share_information",
        {
            "information": "Customer confirmed identity: John Doe",
            "category": "contact_details",
            "caller_id": caller_id
        },
        session_id
    )
    print(f"Result: {result['message'] if result['success'] else result['error']}")
    
    # Test 3: Debt qualification
    print("\n3. 💰 Debt Qualification")
    result = await process_function_call(
        "share_information",
        {
            "information": "Customer has debts over $10,000 - qualified for initial screening",
            "category": "qualification",
            "caller_id": caller_id
        },
        session_id
    )
    print(f"Result: {result['message'] if result['success'] else result['error']}")
    
    # Test 4: Debt type information
    print("\n4. 🏦 Debt Type Information")
    result = await process_function_call(
        "share_information",
        {
            "information": "Customer has both tax debt ($15,000) and credit card debt ($25,000)",
            "category": "debt_info",
            "caller_id": caller_id
        },
        session_id
    )
    print(f"Result: {result['message'] if result['success'] else result['error']}")
    
    # Test 5: Personal information
    print("\n5. 📍 Personal Information")
    result = await process_function_call(
        "share_information",
        {
            "information": "Customer lives in California, employed full-time, monthly income $4,500",
            "category": "personal_info",
            "caller_id": caller_id
        },
        session_id
    )
    print(f"Result: {result['message'] if result['success'] else result['error']}")
    
    # Test 6: Banking information
    print("\n6. 🏧 Banking Information")
    result = await process_function_call(
        "share_information",
        {
            "information": "Customer has active checking account with Chase Bank",
            "category": "personal_info",
            "caller_id": caller_id
        },
        session_id
    )
    print(f"Result: {result['message'] if result['success'] else result['error']}")
    
    # Test 7: Final qualification
    print("\n7. ✅ Final Qualification")
    result = await process_function_call(
        "share_information",
        {
            "information": "Customer qualified for debt relief program - meets all criteria",
            "category": "qualification",
            "caller_id": caller_id
        },
        session_id
    )
    print(f"Result: {result['message'] if result['success'] else result['error']}")
    
    # Test 8: Retrieve shared information
    print("\n8. 📋 Retrieve Shared Information")
    result = await process_function_call(
        "get_shared_information",
        {
            "caller_id": caller_id,
            "limit": 10
        },
        session_id
    )
    if result['success']:
        print(f"Retrieved {result['count']} information records:")
        for info in result['information'][:3]:  # Show first 3
            print(f"  - {info['category']}: {info['information']}")
        if result['count'] > 3:
            print(f"  ... and {result['count'] - 3} more records")
    else:
        print(f"Error: {result['error']}")
    
    # Test 9: End call successfully
    print("\n9. 🎯 End Call - Customer Qualified")
    result = await process_function_call(
        "end_call",
        {
            "reason": "customer_qualified_transfer",
            "caller_id": caller_id,
            "duration": 420  # 7 minutes
        },
        session_id
    )
    print(f"Result: {result['message'] if result['success'] else result['error']}")
    
    print("\n" + "=" * 60)
    print("📊 Call Flow Complete - Summary:")
    
    # Get session summary
    summary = backend_agent.get_shared_information_summary()
    print(f"  • Total Information Shared: {summary['total_information_shared']}")
    print(f"  • Total Sessions: {summary['total_sessions']}")
    print(f"  • Total Calls: {summary['total_calls']}")
    print(f"  • Categories: {', '.join(summary['category_breakdown'].keys())}")

async def test_disqualified_call():
    """Simulate a call where customer doesn't qualify"""
    print("\n\n🚫 Testing Disqualified Customer Flow")
    print("=" * 50)
    
    session_id = "test_session_67890"
    caller_id = "Jane_Smith_555-5678"
    
    # Customer doesn't have enough debt
    print("\n1. 📞 Call Start")
    await process_function_call(
        "share_information",
        {
            "information": "Call started - opening script delivered",
            "category": "conversation_flow",
            "caller_id": caller_id
        },
        session_id
    )
    
    print("\n2. ❌ Customer Disqualification")
    result = await process_function_call(
        "share_information",
        {
            "information": "Customer has only $8,000 in debt - does not meet $10,000 minimum",
            "category": "qualification",
            "caller_id": caller_id
        },
        session_id
    )
    print(f"Qualification recorded: {result['success']}")
    
    print("\n3. 🔚 End Call - Not Qualified")
    result = await process_function_call(
        "end_call",
        {
            "reason": "not_qualified_insufficient_debt",
            "caller_id": caller_id,
            "duration": 120  # 2 minutes
        },
        session_id
    )
    print(f"Call ended: {result['success']}")

async def test_error_scenarios():
    """Test error handling scenarios"""
    print("\n\n⚠️  Testing Error Scenarios")
    print("=" * 40)
    
    # Test 1: Missing required information
    print("\n1. Missing Information Parameter")
    result = await process_function_call(
        "share_information",
        {
            "category": "test",
            "caller_id": "test"
            # Missing 'information' parameter
        },
        "error_test_session"
    )
    print(f"Error handled correctly: {not result['success']}")
    
    # Test 2: Invalid function name
    print("\n2. Invalid Function Name")
    result = await process_function_call(
        "invalid_function_name",
        {"test": "data"},
        "error_test_session"
    )
    print(f"Error handled correctly: {not result['success']}")

async def main():
    """Run all tests"""
    print("🧪 Backend Integration Test Suite")
    print("Testing telephony agent <-> backend communication")
    
    try:
        # Run test scenarios
        await test_full_call_flow()
        await test_disqualified_call()
        await test_error_scenarios()
        
        print("\n\n✅ All tests completed successfully!")
        
        # Show final data state
        print("\n📁 Final Backend Data State:")
        with open("backend/shared_information.json", "r") as f:
            data = json.load(f)
        
        print(f"  • Sessions: {len(data['sessions'])}")
        print(f"  • Information Records: {len(data['shared_data']['information_shared'])}")
        print(f"  • Call Logs: {len(data['shared_data']['call_logs'])}")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
