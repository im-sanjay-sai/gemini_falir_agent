import asyncio
import logging
import sys
import os
from dotenv import load_dotenv
from livekit.agents import (
    Agent,
    AgentSession,
    JobContext,
    WorkerOptions,
    cli,
    function_tool
)
from livekit.plugins import deepgram, openai, cartesia, silero
from livekit.plugins import google

# Add backend directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
from backend_agent import process_function_call

load_dotenv()
logger = logging.getLogger("telephony-agent")

# Global session tracking
current_session_id = None

# Function tools to enhance your agent's capabilities
@function_tool
async def get_current_time() -> str:
    """Get the current time."""
    from datetime import datetime
    return f"The current time is {datetime.now().strftime('%I:%M %p')}"

@function_tool
async def share_information(
    information: str,
    category: str = "general",
    caller_id: str = "unknown"
) -> str:
    """
    Share important information from the call with the backend system.
    
    Args:
        information: The information shared by the customer (required)
        category: Category of information (e.g., "contact_details", "debt_info", "qualification", "personal_info")
        caller_id: Identifier for the caller (phone number or name)
    
    Use this function whenever the customer provides new information such as:
    - Personal details (name, address, phone)
    - Debt information (amounts, types, payment history)
    - Employment and income details
    - Banking information
    - Qualification status updates
    - Any other important customer data
    """
    global current_session_id
    
    try:
        logger.info(f"Sharing information: {information} (Category: {category})")
        
        result = await process_function_call(
            "share_information",
            {
                "information": information,
                "category": category,
                "caller_id": caller_id
            },
            current_session_id
        )
        
        if result.get("success"):
            return f"Information recorded successfully. {result.get('message', '')}"
        else:
            logger.error(f"Failed to share information: {result.get('error')}")
            return f"Failed to record information: {result.get('error', 'Unknown error')}"
            
    except Exception as e:
        logger.error(f"Error in share_information: {e}")
        return f"Error recording information: {str(e)}"

@function_tool
async def end_call(
    reason: str = "conversation_complete",
    caller_id: str = "unknown",
    duration: int = 0
) -> str:
    """
    End the current call and log the call completion.
    
    Args:
        reason: Reason for ending the call (e.g., "customer_qualified", "customer_not_qualified", "customer_hung_up", "transfer_complete")
        caller_id: Identifier for the caller
        duration: Call duration in seconds (optional)
    
    Use this function when:
    - Customer qualifies and is being transferred
    - Customer doesn't qualify and call should end
    - Customer hangs up or requests to end call
    - Call is completed for any other reason
    """
    global current_session_id
    
    try:
        logger.info(f"Ending call with reason: {reason}")
        
        result = await process_function_call(
            "end_call",
            {
                "reason": reason,
                "caller_id": caller_id,
                "duration": duration
            },
            current_session_id
        )
        
        if result.get("success"):
            return f"Call ended successfully. {result.get('message', '')} Information shared during call: {result.get('information_shared_count', 0)}"
        else:
            logger.error(f"Failed to end call: {result.get('error')}")
            return f"Failed to end call properly: {result.get('error', 'Unknown error')}"
            
    except Exception as e:
        logger.error(f"Error in end_call: {e}")
        return f"Error ending call: {str(e)}"

@function_tool
async def get_shared_information(
    category: str = None,
    limit: int = 5,
    caller_id: str = None
) -> str:
    """
    Retrieve previously shared information from the backend.
    
    Args:
        category: Filter by category (optional)
        limit: Maximum number of records to retrieve (default: 5)
        caller_id: Filter by caller ID (optional)
    
    Use this function to:
    - Check what information has already been collected
    - Avoid asking redundant questions
    - Review customer details during the call
    """
    global current_session_id
    
    try:
        result = await process_function_call(
            "get_shared_information",
            {
                "category": category,
                "limit": limit,
                "caller_id": caller_id
            },
            current_session_id
        )
        
        if result.get("success"):
            info_list = result.get("information", [])
            if not info_list:
                return "No information found matching the criteria."
            
            summary = f"Found {len(info_list)} records:\n"
            for info in info_list:
                summary += f"- {info.get('category', 'Unknown')}: {info.get('information', 'No details')}\n"
            
            return summary
        else:
            logger.error(f"Failed to get shared information: {result.get('error')}")
            return f"Failed to retrieve information: {result.get('error', 'Unknown error')}"
            
    except Exception as e:
        logger.error(f"Error in get_shared_information: {e}")
        return f"Error retrieving information: {str(e)}"

async def entrypoint(ctx: JobContext):
    """Main entry point for the telephony voice agent."""
    global current_session_id
    
    await ctx.connect()
    
    # Wait for participant (caller) to join
    participant = await ctx.wait_for_participant()
    logger.info(f"Phone call connected from participant: {participant.identity}")
    
    # Generate unique session ID for this call
    import uuid
    current_session_id = str(uuid.uuid4())
    logger.info(f"Generated session ID: {current_session_id}")
    
    # Initialize the conversational agent
    agent = Agent(
        instructions="""You are a professional debt relief Sales Development Representative (SDR) working for a debt relief company. You are making outbound calls to pre-qualified customers on a recorded line. Follow this exact script and conversation flow:

CRITICAL: You MUST call the share_information function whenever new information is provided by the customer. Use the available function tools to capture and structure all customer data throughout the conversation.

AVAILABLE FUNCTION TOOLS:
- share_information(information, category, caller_id): Record any new customer information immediately
- end_call(reason, caller_id, duration): End the call and log completion details
- get_shared_information(category, limit, caller_id): Check previously recorded information
- get_current_time(): Get current time if needed

CONVERSATION FLOW:
1. OPENING: "Hi, is this Samir? Perfect, this is Samir from SDR on a recorded line, it's just a courtesy call, to inform you about some good news. You have been pre-qualified for a fresh start program that is going to help ERASE a part of your tax or unsecured debt."
   → IMMEDIATELY call share_information with information: "Call started - opening script delivered", category: "conversation_flow"
   → When customer confirms identity, call share_information with their name, category: "contact_details"

2. INITIAL QUALIFICATION: "Are you currently dealing with debts over $10,000?"
   - If NO: Call share_information with disqualification reason, category: "qualification", then call end_call with reason: "not_qualified"
   - If YES: Call share_information with "Customer has debts over $10,000", category: "qualification"

3. DEBT TYPE IDENTIFICATION: "Would that be Tax Debt, Credit Card Debt or Both?"
   → Call share_information with debt types mentioned by customer, category: "debt_info"

4. ROUTING LOGIC:
   - If TAX DEBT mentioned and amount > $10K: Route to TAX DEBT flow
   - Otherwise: Continue with CREDIT CARD DEBT flow

TAX DEBT FLOW (if tax debt > $10K):
→ Call share_information with "Entering tax debt flow", category: "conversation_flow"
- "Have you received any letters from the IRS in the mail?" (Must be Yes)
  → Call share_information with IRS letters status, category: "debt_info"
- "What is the estimated total amount of tax debt owed?" (Must be more than $10K)
  → Call share_information with tax debt amount, category: "debt_info"
- "Are you currently on any debt relief program?" (Must be No)
  → Call share_information with existing program status, category: "qualification"
- "Do you have a source of income?" (Must be Yes)
- "Are you currently employed?" (Must be Yes)
  → Call share_information with employment and income details, category: "personal_info"
  - If No: "Are you receiving minimum $2000 per month of verifiable income such as social security, pensions or other?" (Must be Yes)
- "Do you have a valid checking account?" (Must be Yes)
  → Call share_information with banking information, category: "personal_info"

CREDIT CARD DEBT FLOW:
→ Call share_information with "Entering credit card debt flow", category: "conversation_flow"
- "What is the estimated total amount of credit card and unsecured debt? Such as credit cards, personal unsecured loans (from a Bank or Financial Institution), payday loans, repossessions and collection accounts."
  → Call share_information with total debt amount details, category: "debt_info"
- Ask about each debt type individually for specific amounts
  → Call share_information with debt breakdown for each type mentioned, category: "debt_info"
- "Does your debt have any collateral on it, like a federal student loan, auto loan, mortgage loan or pawn shop loans?"
  → Call share_information with collateral debt status, category: "debt_info"
- "What state do you live in?"
  → Call share_information with customer's state, category: "contact_details"
- "Have you been late on your credit card bills?" (Yes or No - both are OK)
  → Call share_information with payment history, category: "debt_info"
- "Do you currently have any source of income?" (Must be Yes, $1000+ per month)
  → Call share_information with income details, category: "personal_info"
- "Do you have an active checking or savings account?" (Must be Yes)
  → Call share_information with banking status, category: "personal_info"
- "Are you currently on any debt relief program?" (Must be No)
  → Call share_information with existing program status, category: "qualification"
- Confirm state: "I see you are in the state of ________, is that correct?"

CLOSING:
→ Call share_information with "Customer qualified for program", category: "qualification"
→ Call share_information with final qualification details, category: "qualification"
"CONGRATULATIONS, IT SEEMS LIKE YOU QUALIFY TO ERASE YOUR DEBTS! This means you can potentially ERASE up to 40percent  of your debt, through a debt relief program. So I'm now going to connect you to our verification department, they will quickly verify your eligibility and then connect you to a specialist that will help you get it done. Hold on a brief moment... >>> TRANSFER CALL"
→ Call end_call with reason: "customer_qualified_transfer", caller_id: [customer_name_or_phone]

TOOL USAGE REQUIREMENTS:
- Call share_information whenever you learn: name, phone, state, employment, income, banking info (use appropriate category)
- Call share_information whenever you learn: debt amounts, types, IRS letters, payment history, collateral info (category: "debt_info")
- Call share_information whenever determining qualification or next steps (category: "qualification")
- Call share_information at each major stage transition (category: "conversation_flow")
- Call end_call when conversation concludes for any reason
- Update tools with new information as it's provided - don't wait until the end
- Use get_shared_information to check what has already been collected before asking redundant questions

IMPORTANT RULES:
- Stay professional and courteous at all times
- If conversation goes off-topic, politely redirect back to the script
- Never ask redundant questions - track what the customer has already answered using the tools
- Only proceed if qualification criteria are met
- Keep customer engaged during transfer wait times
- Maintain the exact tone and language from the script
- Do not deviate from the qualification requirements
- ALWAYS call the appropriate tool functions when new customer information is provided`,
        """,
        tools=[get_current_time, share_information, end_call, get_shared_information]
    )
    
    # Configure the voice processing pipeline optimized for telephony
    session = AgentSession(
        # Voice Activity Detection
        llm=google.beta.realtime.RealtimeModel(
        model="gemini-2.5-flash-preview-native-audio-dialog",
        voice="zephyr",
        temperature=0.8,
        instructions="You are a awesoe friendly person ,",
    ),
    )
    
    # Start the agent session
    await session.start(agent=agent, room=ctx.room)
    
    # Generate personalized greeting based on time of day
    import datetime
    hour = datetime.datetime.now().hour
    if hour < 12:
        time_greeting = "Good morning"
    elif hour < 18:
        time_greeting = "Good afternoon"
    else:
        time_greeting = "Good evening"
    
    await session.generate_reply(
        instructions=f"""Say '{time_greeting}! Thank you for calling. Whats happening?'
        Speak warmly and professionally at a moderate pace."""
    )

if __name__ == "__main__":
    # Configure logging for better debugging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run the agent with the name that matches your dispatch rule
    cli.run_app(WorkerOptions(
        entrypoint_fnc=entrypoint,
        agent_name="telephony_agent"  # This must match your dispatch rule
    ))