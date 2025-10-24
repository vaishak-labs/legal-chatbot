import requests
import sys
import json
from datetime import datetime
import uuid

class LegalChatbotAPITester:
    def __init__(self, base_url="https://consumer-defender.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.session_id = f"test_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED")
        else:
            print(f"❌ {name} - FAILED: {details}")
        
        self.test_results.append({
            "test": name,
            "success": success,
            "details": details
        })

    def test_root_endpoint(self):
        """Test the root API endpoint"""
        try:
            response = requests.get(f"{self.api_url}/", timeout=10)
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            if success:
                data = response.json()
                details += f", Response: {data}"
            self.log_test("Root API Endpoint", success, details)
            return success
        except Exception as e:
            self.log_test("Root API Endpoint", False, str(e))
            return False

    def test_chat_endpoint(self):
        """Test the chat endpoint with a consumer protection question"""
        try:
            test_message = "What are my rights if a product I bought is defective?"
            payload = {
                "session_id": self.session_id,
                "message": test_message
            }
            
            print(f"🔍 Testing chat with message: '{test_message}'")
            response = requests.post(
                f"{self.api_url}/chat", 
                json=payload, 
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            if success:
                data = response.json()
                if 'response' in data and 'session_id' in data:
                    ai_response = data['response']
                    print(f"📝 AI Response (first 200 chars): {ai_response[:200]}...")
                    details += f", Response length: {len(ai_response)} chars"
                    # Check if response contains legal/consumer protection content
                    legal_keywords = ['consumer', 'rights', 'warranty', 'refund', 'legal', 'protection', 'defective']
                    has_legal_content = any(keyword.lower() in ai_response.lower() for keyword in legal_keywords)
                    if has_legal_content:
                        details += ", Contains legal content: YES"
                    else:
                        details += ", Contains legal content: NO"
                        success = False
                else:
                    success = False
                    details += ", Missing required response fields"
            else:
                try:
                    error_data = response.json()
                    details += f", Error: {error_data}"
                except:
                    details += f", Raw response: {response.text[:200]}"
            
            self.log_test("Chat Endpoint", success, details)
            return success
        except Exception as e:
            self.log_test("Chat Endpoint", False, str(e))
            return False

    def test_chat_history_endpoint(self):
        """Test retrieving chat history"""
        try:
            response = requests.get(f"{self.api_url}/chat/history/{self.session_id}", timeout=10)
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            if success:
                data = response.json()
                if isinstance(data, list):
                    details += f", Messages count: {len(data)}"
                    if len(data) >= 2:  # Should have user message and assistant response
                        details += ", Has user and assistant messages"
                    else:
                        details += ", Missing expected messages"
                else:
                    success = False
                    details += ", Response is not a list"
            else:
                try:
                    error_data = response.json()
                    details += f", Error: {error_data}"
                except:
                    details += f", Raw response: {response.text[:200]}"
            
            self.log_test("Chat History Endpoint", success, details)
            return success
        except Exception as e:
            self.log_test("Chat History Endpoint", False, str(e))
            return False

    def test_clear_chat_history(self):
        """Test clearing chat history"""
        try:
            response = requests.delete(f"{self.api_url}/chat/history/{self.session_id}", timeout=10)
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            if success:
                data = response.json()
                if 'deleted_count' in data and 'session_id' in data:
                    details += f", Deleted count: {data['deleted_count']}"
                else:
                    success = False
                    details += ", Missing required response fields"
            else:
                try:
                    error_data = response.json()
                    details += f", Error: {error_data}"
                except:
                    details += f", Raw response: {response.text[:200]}"
            
            self.log_test("Clear Chat History", success, details)
            return success
        except Exception as e:
            self.log_test("Clear Chat History", False, str(e))
            return False

    def test_multiple_chat_messages(self):
        """Test sending multiple messages in sequence"""
        try:
            messages = [
                "How do I return a faulty product?",
                "What is a warranty?",
                "Can I get a refund for digital purchases?"
            ]
            
            all_success = True
            for i, message in enumerate(messages):
                payload = {
                    "session_id": self.session_id,
                    "message": message
                }
                
                response = requests.post(
                    f"{self.api_url}/chat", 
                    json=payload, 
                    headers={'Content-Type': 'application/json'},
                    timeout=30
                )
                
                if response.status_code != 200:
                    all_success = False
                    break
                    
                print(f"✅ Message {i+1}/3 sent successfully")
            
            details = f"Sent {len(messages)} messages"
            self.log_test("Multiple Chat Messages", all_success, details)
            return all_success
        except Exception as e:
            self.log_test("Multiple Chat Messages", False, str(e))
            return False

    def run_all_tests(self):
        """Run all backend API tests"""
        print("🚀 Starting Legal Chatbot Backend API Tests")
        print(f"📍 Testing against: {self.base_url}")
        print(f"🆔 Session ID: {self.session_id}")
        print("=" * 60)
        
        # Test sequence
        self.test_root_endpoint()
        self.test_chat_endpoint()
        self.test_chat_history_endpoint()
        self.test_multiple_chat_messages()
        self.test_clear_chat_history()
        
        # Final results
        print("=" * 60)
        print(f"📊 Backend API Test Results:")
        print(f"✅ Tests Passed: {self.tests_passed}/{self.tests_run}")
        print(f"❌ Tests Failed: {self.tests_run - self.tests_passed}/{self.tests_run}")
        
        success_rate = (self.tests_passed / self.tests_run) * 100 if self.tests_run > 0 else 0
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All backend tests passed!")
            return 0
        else:
            print("⚠️  Some backend tests failed!")
            return 1

def main():
    tester = LegalChatbotAPITester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())