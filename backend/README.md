# 📞 Telephony Agent Backend System

This backend system handles function calls from the telephony agent, stores customer information, and provides APIs for monitoring and data retrieval.

## 🏗️ Architecture

```
Telephony Agent (telephony_agent.py)
    ↓ Function Calls
Backend Agent (backend_agent.py)
    ↓ Data Storage
JSON Database (shared_information.json)
    ↓ API Access
Dashboard & API Server (api_server.py)
```

## 🚀 Features

### Function Calls
- **`share_information`**: Store customer information by category
- **`end_call`**: Log call completion with details
- **`get_shared_information`**: Retrieve stored information with filters

### Data Categories
- `contact_details`: Name, phone, address, state
- `debt_info`: Debt amounts, types, payment history
- `personal_info`: Employment, income, banking
- `qualification`: Qualification status and decisions
- `conversation_flow`: Call progress tracking

### API Dashboard
- Real-time data visualization
- Call logs and statistics
- Information breakdown by category
- Session monitoring

## 📁 Files

- **`backend_agent.py`**: Core backend logic and function call handling
- **`shared_information.json`**: JSON database for storing all data
- **`api_server.py`**: Flask API server and dashboard
- **`test_integration.py`**: Integration testing script

## 🔧 Installation & Setup

1. **Install Dependencies**:
   ```bash
   pip install -r ../req.txt
   ```

2. **Test the Backend**:
   ```bash
   python test_integration.py
   ```

3. **Start API Server**:
   ```bash
   python api_server.py
   ```

4. **Access Dashboard**:
   Open http://localhost:5000 in your browser

## 📡 API Endpoints

### Dashboard
- `GET /` - Main dashboard with visualizations

### Data APIs
- `GET /api/summary` - Summary statistics
- `GET /api/sessions` - All session data
- `GET /api/information?category=<cat>&limit=<n>&caller_id=<id>` - Filtered information
- `GET /api/calls?limit=<n>` - Call logs
- `GET /api/raw_data` - Raw JSON data

### Testing
- `POST /api/test_function` - Test function calls
  ```json
  {
    "function_name": "share_information",
    "parameters": {
      "information": "Test data",
      "category": "test",
      "caller_id": "test_caller"
    },
    "session_id": "test_session"
  }
  ```

## 🔄 Integration with Telephony Agent

The telephony agent automatically calls backend functions when:

1. **Call starts**: Records conversation flow progress
2. **Customer provides info**: Stores in appropriate category
3. **Qualification decisions**: Logs qualification status
4. **Call ends**: Creates call log with summary

### Function Call Examples

```python
# Share customer information
await share_information(
    information="Customer name is John Doe, lives in California",
    category="contact_details",
    caller_id="john_doe_555-1234"
)

# End call with qualification
await end_call(
    reason="customer_qualified_transfer",
    caller_id="john_doe_555-1234",
    duration=420
)

# Check existing information
await get_shared_information(
    category="debt_info",
    caller_id="john_doe_555-1234",
    limit=5
)
```

## 📊 Data Structure

### Session Data
```json
{
  "session_id": {
    "created_at": "2025-09-29T10:00:00",
    "caller_id": "customer_phone",
    "information_count": 5,
    "status": "active",
    "last_activity": "2025-09-29T10:05:00"
  }
}
```

### Information Records
```json
{
  "id": "unique_id",
  "session_id": "session_123",
  "caller_id": "customer_phone",
  "information": "Customer has $15,000 in credit card debt",
  "category": "debt_info",
  "timestamp": "2025-09-29T10:03:00",
  "status": "received"
}
```

### Call Logs
```json
{
  "id": "call_log_id",
  "session_id": "session_123",
  "caller_id": "customer_phone",
  "end_time": "2025-09-29T10:07:00",
  "reason": "customer_qualified_transfer",
  "duration": 420,
  "information_shared_count": 5
}
```

## 🧪 Testing

### Run Integration Tests
```bash
cd backend
python test_integration.py
```

### Test Scenarios Covered
1. **Full qualified customer flow**
2. **Disqualified customer flow**
3. **Error handling scenarios**
4. **Data retrieval and filtering**

### Manual Testing via API
```bash
# Test function call
curl -X POST http://localhost:5000/api/test_function \
  -H "Content-Type: application/json" \
  -d '{
    "function_name": "share_information",
    "parameters": {
      "information": "Test customer information",
      "category": "test",
      "caller_id": "test_caller_001"
    },
    "session_id": "manual_test_session"
  }'
```

## 🔍 Monitoring

### Dashboard Features
- **Real-time updates**: Auto-refresh every 30 seconds
- **Summary statistics**: Sessions, calls, information records
- **Recent activity**: Latest information shared and call logs
- **Category breakdown**: Information distribution by type
- **Status indicators**: Qualified vs not qualified calls

### Logging
All function calls and errors are logged with timestamps and details for debugging and monitoring.

## 🛠️ Customization

### Adding New Function Calls
1. Add function to `backend_agent.py`:
   ```python
   async def _handle_new_function(self, parameters, session_id):
       # Implementation
       return {"success": True, "message": "Function executed"}
   ```

2. Register in `handle_function_call` method
3. Add to telephony agent as `@function_tool`

### Adding New Data Categories
Simply use new category names in `share_information` calls - the system automatically handles new categories.

### Custom API Endpoints
Add new routes to `api_server.py` for custom data views or operations.

## 🚨 Error Handling

The system includes comprehensive error handling for:
- Missing required parameters
- Invalid function names
- File system errors
- JSON parsing errors
- Network connectivity issues

All errors are logged and returned with descriptive messages.
