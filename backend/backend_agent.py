import json
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
import uuid
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BackendAgent:
    def __init__(self, json_file_path: str = "shared_information.json"):
        self.json_file_path = json_file_path
        self.data = self._load_data()
        
    def _load_data(self) -> Dict[str, Any]:
        """Load data from JSON file"""
        try:
            if os.path.exists(self.json_file_path):
                with open(self.json_file_path, 'r') as f:
                    return json.load(f)
            else:
                # Create default structure if file doesn't exist
                default_data = {
                    "sessions": {},
                    "shared_data": {
                        "call_logs": [],
                        "information_shared": [],
                        "active_sessions": {}
                    },
                    "metadata": {
                        "created_at": datetime.now().isoformat(),
                        "version": "1.0",
                        "last_updated": None
                    }
                }
                self._save_data(default_data)
                return default_data
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            return {}
    
    def _save_data(self, data: Optional[Dict[str, Any]] = None) -> None:
        """Save data to JSON file"""
        try:
            save_data = data if data is not None else self.data
            save_data["metadata"]["last_updated"] = datetime.now().isoformat()
            
            # Ensure directory exists (only if path has directory)
            dir_path = os.path.dirname(self.json_file_path)
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)
            
            with open(self.json_file_path, 'w') as f:
                json.dump(save_data, f, indent=2)
            logger.info("Data saved successfully")
        except Exception as e:
            logger.error(f"Error saving data: {e}")
    
    async def handle_function_call(self, function_name: str, parameters: Dict[str, Any], session_id: str = None) -> Dict[str, Any]:
        """Handle incoming function calls from telephony agent"""
        try:
            if session_id is None:
                session_id = str(uuid.uuid4())
            
            logger.info(f"Handling function call: {function_name} with parameters: {parameters}")
            
            if function_name == "share_information":
                return await self._handle_share_information(parameters, session_id)
            elif function_name == "end_call":
                return await self._handle_end_call(parameters, session_id)
            elif function_name == "get_shared_information":
                return await self._handle_get_shared_information(parameters, session_id)
            else:
                return {
                    "success": False,
                    "error": f"Unknown function: {function_name}",
                    "session_id": session_id
                }
                
        except Exception as e:
            logger.error(f"Error handling function call: {e}")
            return {
                "success": False,
                "error": str(e),
                "session_id": session_id
            }
    
    async def _handle_share_information(self, parameters: Dict[str, Any], session_id: str) -> Dict[str, Any]:
        """Handle information sharing function call"""
        try:
            information = parameters.get("information", "")
            category = parameters.get("category", "general")
            caller_id = parameters.get("caller_id", "unknown")
            
            if not information:
                return {
                    "success": False,
                    "error": "No information provided",
                    "session_id": session_id
                }
            
            # Create information entry
            info_entry = {
                "id": str(uuid.uuid4()),
                "session_id": session_id,
                "caller_id": caller_id,
                "information": information,
                "category": category,
                "timestamp": datetime.now().isoformat(),
                "status": "received"
            }
            
            # Add to shared data
            self.data["shared_data"]["information_shared"].append(info_entry)
            
            # Update session info
            if session_id not in self.data["sessions"]:
                self.data["sessions"][session_id] = {
                    "created_at": datetime.now().isoformat(),
                    "caller_id": caller_id,
                    "information_count": 0,
                    "status": "active"
                }
            
            self.data["sessions"][session_id]["information_count"] += 1
            self.data["sessions"][session_id]["last_activity"] = datetime.now().isoformat()
            
            # Save data
            self._save_data()
            
            logger.info(f"Information shared successfully for session {session_id}")
            
            return {
                "success": True,
                "message": f"Information received and stored successfully. Category: {category}",
                "info_id": info_entry["id"],
                "session_id": session_id,
                "total_shared": len(self.data["shared_data"]["information_shared"])
            }
            
        except Exception as e:
            logger.error(f"Error in share_information: {e}")
            return {
                "success": False,
                "error": str(e),
                "session_id": session_id
            }
    
    async def _handle_end_call(self, parameters: Dict[str, Any], session_id: str) -> Dict[str, Any]:
        """Handle end call function call"""
        try:
            reason = parameters.get("reason", "user_requested")
            caller_id = parameters.get("caller_id", "unknown")
            duration = parameters.get("duration", 0)
            
            # Create call log entry
            call_log = {
                "id": str(uuid.uuid4()),
                "session_id": session_id,
                "caller_id": caller_id,
                "end_time": datetime.now().isoformat(),
                "reason": reason,
                "duration": duration,
                "information_shared_count": 0
            }
            
            # Count information shared in this session
            session_info_count = len([
                info for info in self.data["shared_data"]["information_shared"] 
                if info.get("session_id") == session_id
            ])
            call_log["information_shared_count"] = session_info_count
            
            # Add to call logs
            self.data["shared_data"]["call_logs"].append(call_log)
            
            # Update session status
            if session_id in self.data["sessions"]:
                self.data["sessions"][session_id]["status"] = "ended"
                self.data["sessions"][session_id]["end_time"] = datetime.now().isoformat()
                self.data["sessions"][session_id]["end_reason"] = reason
            
            # Remove from active sessions if exists
            if session_id in self.data["shared_data"]["active_sessions"]:
                del self.data["shared_data"]["active_sessions"][session_id]
            
            # Save data
            self._save_data()
            
            logger.info(f"Call ended for session {session_id}, reason: {reason}")
            
            return {
                "success": True,
                "message": f"Call ended successfully. Reason: {reason}",
                "call_log_id": call_log["id"],
                "session_id": session_id,
                "information_shared_count": session_info_count,
                "total_calls": len(self.data["shared_data"]["call_logs"])
            }
            
        except Exception as e:
            logger.error(f"Error in end_call: {e}")
            return {
                "success": False,
                "error": str(e),
                "session_id": session_id
            }
    
    async def _handle_get_shared_information(self, parameters: Dict[str, Any], session_id: str) -> Dict[str, Any]:
        """Handle get shared information function call"""
        try:
            category = parameters.get("category", None)
            limit = parameters.get("limit", 10)
            caller_id = parameters.get("caller_id", None)
            
            # Filter information based on parameters
            filtered_info = self.data["shared_data"]["information_shared"]
            
            if category:
                filtered_info = [info for info in filtered_info if info.get("category") == category]
            
            if caller_id:
                filtered_info = [info for info in filtered_info if info.get("caller_id") == caller_id]
            
            # Sort by timestamp (most recent first) and limit
            filtered_info = sorted(filtered_info, key=lambda x: x.get("timestamp", ""), reverse=True)
            filtered_info = filtered_info[:limit]
            
            return {
                "success": True,
                "information": filtered_info,
                "count": len(filtered_info),
                "total_available": len(self.data["shared_data"]["information_shared"]),
                "session_id": session_id
            }
            
        except Exception as e:
            logger.error(f"Error in get_shared_information: {e}")
            return {
                "success": False,
                "error": str(e),
                "session_id": session_id
            }
    
    def get_session_info(self, session_id: str) -> Dict[str, Any]:
        """Get information about a specific session"""
        return self.data["sessions"].get(session_id, {})
    
    def get_all_sessions(self) -> Dict[str, Any]:
        """Get all session information"""
        return self.data["sessions"]
    
    def get_call_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent call logs"""
        call_logs = self.data["shared_data"]["call_logs"]
        return sorted(call_logs, key=lambda x: x.get("end_time", ""), reverse=True)[:limit]
    
    def get_shared_information_summary(self) -> Dict[str, Any]:
        """Get summary of shared information"""
        info_list = self.data["shared_data"]["information_shared"]
        
        # Count by category
        category_counts = {}
        for info in info_list:
            category = info.get("category", "unknown")
            category_counts[category] = category_counts.get(category, 0) + 1
        
        return {
            "total_information_shared": len(info_list),
            "total_sessions": len(self.data["sessions"]),
            "total_calls": len(self.data["shared_data"]["call_logs"]),
            "category_breakdown": category_counts,
            "last_updated": self.data["metadata"].get("last_updated")
        }

# Initialize backend agent instance
backend_agent = BackendAgent()

# Function to handle incoming function calls (can be called from telephony agent)
async def process_function_call(function_name: str, parameters: Dict[str, Any], session_id: str = None) -> Dict[str, Any]:
    """Process function call from telephony agent"""
    return await backend_agent.handle_function_call(function_name, parameters, session_id)

if __name__ == "__main__":
    # Test the backend agent
    async def test_backend():
        # Test share information
        result1 = await backend_agent.handle_function_call(
            "share_information",
            {
                "information": "Customer wants to know about product pricing",
                "category": "sales_inquiry",
                "caller_id": "test_caller_001"
            },
            "test_session_001"
        )
        print("Share information result:", result1)
        
        # Test get shared information
        result2 = await backend_agent.handle_function_call(
            "get_shared_information",
            {"category": "sales_inquiry", "limit": 5},
            "test_session_001"
        )
        print("Get information result:", result2)
        
        # Test end call
        result3 = await backend_agent.handle_function_call(
            "end_call",
            {
                "reason": "customer_satisfied",
                "caller_id": "test_caller_001",
                "duration": 300
            },
            "test_session_001"
        )
        print("End call result:", result3)
        
        # Print summary
        summary = backend_agent.get_shared_information_summary()
        print("Summary:", summary)
    
    # Run test
    asyncio.run(test_backend())
