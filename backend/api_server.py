#!/usr/bin/env python3
"""
Simple API server to view backend data and test function calls.
Run this to inspect the data collected by the telephony agent.
"""

from flask import Flask, jsonify, request, render_template_string
import json
import asyncio
from backend_agent import backend_agent, process_function_call
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# HTML template for the dashboard
DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Telephony Agent Backend Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; }
        .card { background: white; padding: 20px; margin: 20px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .header { text-align: center; color: #333; }
        .summary { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; }
        .stat-box { background: #007bff; color: white; padding: 15px; border-radius: 5px; text-align: center; }
        .stat-number { font-size: 2em; font-weight: bold; }
        .stat-label { font-size: 0.9em; opacity: 0.9; }
        .info-item { background: #f8f9fa; padding: 10px; margin: 5px 0; border-left: 4px solid #007bff; }
        .category { background: #28a745; color: white; padding: 2px 8px; border-radius: 12px; font-size: 0.8em; }
        .timestamp { color: #666; font-size: 0.9em; }
        .call-log { background: #fff3cd; border-left: 4px solid #ffc107; }
        .qualified { background: #d4edda; border-left: 4px solid #28a745; }
        .not-qualified { background: #f8d7da; border-left: 4px solid #dc3545; }
        .refresh-btn { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; }
        .refresh-btn:hover { background: #0056b3; }
    </style>
    <script>
        function refreshData() {
            location.reload();
        }
        
        // Auto-refresh every 30 seconds
        setInterval(refreshData, 30000);
    </script>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📞 Telephony Agent Backend Dashboard</h1>
            <p>Real-time monitoring of call data and customer information</p>
            <button class="refresh-btn" onclick="refreshData()">🔄 Refresh Data</button>
        </div>
        
        <div class="card">
            <h2>📊 Summary Statistics</h2>
            <div class="summary">
                <div class="stat-box">
                    <div class="stat-number">{{ summary.total_sessions }}</div>
                    <div class="stat-label">Total Sessions</div>
                </div>
                <div class="stat-box">
                    <div class="stat-number">{{ summary.total_calls }}</div>
                    <div class="stat-label">Completed Calls</div>
                </div>
                <div class="stat-box">
                    <div class="stat-number">{{ summary.total_information_shared }}</div>
                    <div class="stat-label">Info Records</div>
                </div>
                <div class="stat-box">
                    <div class="stat-number">{{ summary.category_breakdown|length }}</div>
                    <div class="stat-label">Categories</div>
                </div>
            </div>
        </div>
        
        <div class="card">
            <h2>📋 Recent Information Shared</h2>
            {% for info in recent_info %}
            <div class="info-item">
                <div>
                    <span class="category">{{ info.category }}</span>
                    <span class="timestamp">{{ info.timestamp }}</span>
                </div>
                <div><strong>{{ info.caller_id }}</strong>: {{ info.information }}</div>
            </div>
            {% endfor %}
        </div>
        
        <div class="card">
            <h2>📞 Recent Call Logs</h2>
            {% for call in recent_calls %}
            <div class="info-item call-log {% if 'qualified' in call.reason %}qualified{% elif 'not_qualified' in call.reason %}not-qualified{% endif %}">
                <div>
                    <strong>{{ call.caller_id }}</strong>
                    <span class="timestamp">{{ call.end_time }}</span>
                </div>
                <div>Reason: {{ call.reason }} | Duration: {{ call.duration }}s | Info Shared: {{ call.information_shared_count }}</div>
            </div>
            {% endfor %}
        </div>
        
        <div class="card">
            <h2>📈 Category Breakdown</h2>
            {% for category, count in summary.category_breakdown.items() %}
            <div class="info-item">
                <span class="category">{{ category }}</span>
                <strong>{{ count }}</strong> records
            </div>
            {% endfor %}
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def dashboard():
    """Main dashboard showing all backend data"""
    try:
        # Get summary data
        summary = backend_agent.get_shared_information_summary()
        
        # Get recent information (last 10)
        recent_info = backend_agent.data["shared_data"]["information_shared"][-10:]
        recent_info.reverse()  # Most recent first
        
        # Get recent call logs (last 10)
        recent_calls = backend_agent.get_call_logs(10)
        
        return render_template_string(
            DASHBOARD_HTML,
            summary=summary,
            recent_info=recent_info,
            recent_calls=recent_calls
        )
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/summary')
def api_summary():
    """Get summary statistics"""
    try:
        summary = backend_agent.get_shared_information_summary()
        return jsonify(summary)
    except Exception as e:
        logger.error(f"Summary API error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/sessions')
def api_sessions():
    """Get all session data"""
    try:
        sessions = backend_agent.get_all_sessions()
        return jsonify(sessions)
    except Exception as e:
        logger.error(f"Sessions API error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/information')
def api_information():
    """Get shared information with optional filtering"""
    try:
        category = request.args.get('category')
        limit = int(request.args.get('limit', 50))
        caller_id = request.args.get('caller_id')
        
        # Use the backend agent's get_shared_information method
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(
            backend_agent.handle_function_call(
                "get_shared_information",
                {
                    "category": category,
                    "limit": limit,
                    "caller_id": caller_id
                }
            )
        )
        
        loop.close()
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Information API error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/calls')
def api_calls():
    """Get call logs"""
    try:
        limit = int(request.args.get('limit', 50))
        calls = backend_agent.get_call_logs(limit)
        return jsonify(calls)
    except Exception as e:
        logger.error(f"Calls API error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/test_function', methods=['POST'])
def api_test_function():
    """Test function call endpoint"""
    try:
        data = request.json
        function_name = data.get('function_name')
        parameters = data.get('parameters', {})
        session_id = data.get('session_id')
        
        # Run the function call
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(
            process_function_call(function_name, parameters, session_id)
        )
        
        loop.close()
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Test function API error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/raw_data')
def api_raw_data():
    """Get raw backend data"""
    try:
        return jsonify(backend_agent.data)
    except Exception as e:
        logger.error(f"Raw data API error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("🚀 Starting Backend API Server...")
    print("📊 Dashboard: http://localhost:5000")
    print("🔍 API Endpoints:")
    print("  • GET  /api/summary - Summary statistics")
    print("  • GET  /api/sessions - All session data")
    print("  • GET  /api/information - Shared information (with filters)")
    print("  • GET  /api/calls - Call logs")
    print("  • POST /api/test_function - Test function calls")
    print("  • GET  /api/raw_data - Raw backend data")
    print("")
    
    # Run the Flask app
    app.run(debug=True, host='0.0.0.0', port=5000)
