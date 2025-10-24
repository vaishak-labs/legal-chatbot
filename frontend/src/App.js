import { useState, useEffect, useRef } from "react";
import "@/App.css";
import axios from "axios";
import { Send, Trash2, Scale } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { ScrollArea } from "@/components/ui/scroll-area";
import { toast } from "sonner";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function App() {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId] = useState(() => `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`);
  const scrollRef = useRef(null);

  useEffect(() => {
    loadChatHistory();
  }, []);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const loadChatHistory = async () => {
    try {
      const response = await axios.get(`${API}/chat/history/${sessionId}`);
      setMessages(response.data);
    } catch (error) {
      console.error("Error loading chat history:", error);
    }
  };

  const sendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    const userMessage = inputMessage.trim();
    setInputMessage("");
    
    // Add user message to UI immediately
    const tempUserMsg = {
      role: "user",
      message: userMessage,
      timestamp: new Date().toISOString()
    };
    setMessages(prev => [...prev, tempUserMsg]);
    setIsLoading(true);

    try {
      const response = await axios.post(`${API}/chat`, {
        session_id: sessionId,
        message: userMessage
      });

      // Add assistant response to UI
      const assistantMsg = {
        role: "assistant",
        message: response.data.response,
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, assistantMsg]);
    } catch (error) {
      console.error("Error sending message:", error);
      
      // Provide user-friendly error messages based on error type
      let errorMessage = "Failed to send message. Please try again.";
      
      if (error.response) {
        if (error.response.status === 429) {
          errorMessage = "API rate limit exceeded. Please wait a moment and try again.";
        } else if (error.response.status === 500) {
          const errorDetail = error.response.data?.detail || "";
          if (errorDetail.includes("quota") || errorDetail.includes("rate limit")) {
            errorMessage = "The AI service is currently experiencing high demand. Please wait a minute and try again.";
          } else {
            errorMessage = "An error occurred processing your request. Please try again.";
          }
        }
      } else if (error.request) {
        errorMessage = "Unable to reach the server. Please check your internet connection.";
      }
      
      toast.error(errorMessage);
      // Remove the temporary user message on error
      setMessages(prev => prev.slice(0, -1));
    } finally {
      setIsLoading(false);
    }
  };

  const clearChat = async () => {
    try {
      await axios.delete(`${API}/chat/history/${sessionId}`);
      setMessages([]);
      toast.success("Chat history cleared");
    } catch (error) {
      console.error("Error clearing chat:", error);
      toast.error("Failed to clear chat history");
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="app-container">
      {/* Header */}
      <header className="header">
        <div className="header-content">
          <div className="logo-section">
            <div className="logo-icon">
              <Scale size={32} strokeWidth={2} />
            </div>
            <div>
              <h1 className="logo-title">Consumer Defender</h1>
              <p className="logo-subtitle">Your Legal Rights Assistant</p>
            </div>
          </div>
          <Button
            data-testid="clear-chat-btn"
            onClick={clearChat}
            variant="outline"
            size="sm"
            className="clear-btn"
            disabled={messages.length === 0}
          >
            <Trash2 size={16} className="mr-2" />
            Clear Chat
          </Button>
        </div>
      </header>

      {/* Chat Container */}
      <div className="chat-container">
        {messages.length === 0 ? (
          <div className="welcome-screen" data-testid="welcome-screen">
            <div className="welcome-icon">
              <Scale size={64} strokeWidth={1.5} />
            </div>
            <h2 className="welcome-title">Welcome to Consumer Defender</h2>
            <p className="welcome-text">
              Your AI-powered legal assistant specializing in consumer protection law.
              Ask me anything about your consumer rights, warranties, refunds, fraud protection, and more.
            </p>
            <div className="example-questions">
              <p className="example-title">Example questions:</p>
              <div className="example-grid">
                <button 
                  className="example-card"
                  data-testid="example-question-1"
                  onClick={() => setInputMessage("What are my rights if a product I bought is defective?")}
                >
                  What are my rights if a product I bought is defective?
                </button>
                <button 
                  className="example-card"
                  data-testid="example-question-2"
                  onClick={() => setInputMessage("How do I get a refund for an online purchase?")}
                >
                  How do I get a refund for an online purchase?
                </button>
                <button 
                  className="example-card"
                  data-testid="example-question-3"
                  onClick={() => setInputMessage("What should I do if I'm a victim of consumer fraud?")}
                >
                  What should I do if I'm a victim of consumer fraud?
                </button>
                <button 
                  className="example-card"
                  data-testid="example-question-4"
                  onClick={() => setInputMessage("Explain warranty terms and conditions")}
                >
                  Explain warranty terms and conditions
                </button>
              </div>
            </div>
          </div>
        ) : (
          <ScrollArea className="messages-area">
            <div className="messages-container" ref={scrollRef} data-testid="messages-container">
              {messages.map((msg, index) => (
                <div
                  key={index}
                  className={`message ${msg.role === "user" ? "message-user" : "message-assistant"}`}
                  data-testid={`message-${msg.role}-${index}`}
                >
                  <div className="message-header">
                    <span className="message-role">
                      {msg.role === "user" ? "You" : "Legal Assistant"}
                    </span>
                  </div>
                  <div className="message-content">{msg.message}</div>
                </div>
              ))}
              {isLoading && (
                <div className="message message-assistant" data-testid="loading-indicator">
                  <div className="message-header">
                    <span className="message-role">Legal Assistant</span>
                  </div>
                  <div className="message-content typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                </div>
              )}
            </div>
          </ScrollArea>
        )}
      </div>

      {/* Input Area */}
      <div className="input-container">
        <div className="input-wrapper">
          <Textarea
            data-testid="chat-input"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask about your consumer rights..."
            className="chat-input"
            rows={3}
            disabled={isLoading}
          />
          <Button
            data-testid="send-btn"
            onClick={sendMessage}
            disabled={!inputMessage.trim() || isLoading}
            className="send-btn"
            size="lg"
          >
            <Send size={20} />
          </Button>
        </div>
      </div>
    </div>
  );
}

export default App;