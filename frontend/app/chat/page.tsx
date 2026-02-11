'use client';

import React, { useState, useRef, useEffect } from 'react';
import DashboardLayout from '@/src/components/dashboard/DashboardLayout';

const ChatPage = () => {
  const [messages, setMessages] = useState([
    {
      id: 1,
      sender: 'bot',
      text: 'Hi there! 👋 Ready to study smarter? I\'m your Study Buddy, here to help with your exam preparation.',
      timestamp: new Date().toISOString()
    },
    {
      id: 2,
      sender: 'bot',
      text: 'I can help you with concept explanations, question analysis, study planning, and more. What would you like to discuss?',
      timestamp: new Date().toISOString()
    }
  ]);
  const [inputText, setInputText] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<null | HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = () => {
    if (inputText.trim() === '') return;

    // Add user message
    const newUserMessage = {
      id: messages.length + 1,
      sender: 'user',
      text: inputText,
      timestamp: new Date().toISOString()
    };
    
    setMessages(prev => [...prev, newUserMessage]);
    setInputText('');
    setIsTyping(true);

    // Simulate bot response after delay
    setTimeout(() => {
      const botResponse = {
        id: messages.length + 2,
        sender: 'bot',
        text: `I understand you're asking about "${inputText}". For Linear Algebra, this is an important topic. Based on previous year papers, similar questions have appeared in 2022 and 2024. I recommend focusing on the key concepts and practicing related problems.`,
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, botResponse]);
      setIsTyping(false);
    }, 1500);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const suggestionCards = [
    '📚 Explain a concept',
    '📊 Analyze my weakness',
    '🗓️ Create study plan',
    '❓ Question analysis'
  ];

  const quickActions = [
    { icon: '📋', title: 'Create Study Plan', desc: 'Generate personalized study schedule' },
    { icon: '📊', title: 'Analyze My Performance', desc: 'Identify weak areas' },
    { icon: '🎯', title: 'View Weak Topics', desc: 'See topics from failed questions' },
    { icon: '📚', title: 'Revise This Topic', desc: 'Generate practice questions' },
    { icon: '🔄', title: 'Suggest Next Steps', desc: 'AI recommendations' },
    { icon: '💾', title: 'Save Conversation', desc: 'Export chat as PDF' },
  ];

  return (
    <DashboardLayout>
      <div className="flex h-[calc(100vh-160px)] max-w-7xl mx-auto">
        {/* Sidebar - Quick Actions */}
        <div className="w-1/4 bg-white border-r p-4 flex flex-col">
          <h2 className="text-xl font-semibold mb-4">Quick Actions</h2>
          
          <div className="space-y-3 flex-1">
            {quickActions.map((action, index) => (
              <div 
                key={index} 
                className="p-3 border rounded-lg hover:bg-gray-50 cursor-pointer"
              >
                <div className="flex items-center">
                  <span className="text-2xl mr-3">{action.icon}</span>
                  <div>
                    <h3 className="font-medium">{action.title}</h3>
                    <p className="text-xs text-gray-500">{action.desc}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
          
          <div className="mt-auto">
            <h3 className="font-semibold mb-2">Saved from Chat</h3>
            <ul className="text-sm space-y-1">
              <li className="text-gray-400">No saved conversations yet</li>
              <li className="text-blue-600 hover:underline cursor-pointer">Start chatting to save</li>
            </ul>
          </div>
        </div>

        {/* Main Chat Area */}
        <div className="flex-1 flex flex-col">
          {/* Header */}
          <div className="bg-white border-b p-4 flex justify-between items-center">
            <div className="flex items-center">
              <span className="text-2xl mr-3">🤖</span>
              <div>
                <h1 className="font-semibold">Study Buddy</h1>
                <div className="flex items-center text-sm text-gray-500">
                  <span className="w-2 h-2 bg-green-500 rounded-full mr-1"></span>
                  <span>Online • Ready to help</span>
                </div>
              </div>
            </div>
            <div className="flex space-x-2">
              <button className="p-2 rounded-full hover:bg-gray-100" title="Clear chat">
                🗑️
              </button>
              <button className="p-2 rounded-full hover:bg-gray-100" title="Chat info">
                ℹ️
              </button>
            </div>
          </div>

          {/* Chat Messages */}
          <div className="flex-1 overflow-y-auto p-4 bg-gray-50">
            {messages.map((message) => (
              <div 
                key={message.id} 
                className={`flex mb-4 ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div 
                  className={`max-w-[80%] rounded-lg p-4 ${
                    message.sender === 'user' 
                      ? 'bg-teal-600 text-white rounded-br-none' 
                      : 'bg-gray-200 text-gray-800 rounded-bl-none'
                  }`}
                >
                  <div className="whitespace-pre-wrap">{message.text}</div>
                  <div className={`text-xs mt-1 ${message.sender === 'user' ? 'text-teal-200' : 'text-gray-500'}`}>
                    {new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </div>
                </div>
              </div>
            ))}
            
            {isTyping && (
              <div className="flex justify-start mb-4">
                <div className="max-w-[80%] rounded-lg p-4 bg-gray-200 text-gray-800 rounded-bl-none">
                  <div className="flex items-center">
                    <span>Typing</span>
                    <span className="ml-1">...</span>
                  </div>
                </div>
              </div>
            )}
            
            {messages.length === 2 && (
              <div className="grid grid-cols-2 gap-2 mt-4">
                {suggestionCards.map((suggestion, index) => (
                  <div 
                    key={index}
                    className="bg-white border rounded-lg p-3 text-center cursor-pointer hover:bg-gray-50"
                    onClick={() => setInputText(suggestion.split(' ')[1])}
                  >
                    {suggestion}
                  </div>
                ))}
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>

          {/* Message Input Area */}
          <div className="bg-white border-t p-4">
            <div className="flex items-end space-x-2">
              <div className="flex-1">
                <textarea
                  value={inputText}
                  onChange={(e) => setInputText(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Ask me anything about your subjects..."
                  className="w-full p-3 border rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-teal-300"
                  rows={2}
                />
              </div>
              <div className="flex flex-col space-y-2">
                <button className="p-2 rounded-full hover:bg-gray-100" title="Attach image">
                  📎
                </button>
                <button 
                  onClick={handleSendMessage}
                  disabled={inputText.trim() === ''}
                  className={`p-2 rounded-full ${
                    inputText.trim() === '' 
                      ? 'bg-gray-200 text-gray-400' 
                      : 'bg-teal-600 text-white hover:bg-teal-700'
                  }`}
                  title="Send message"
                >
                  ➤
                </button>
              </div>
            </div>
            
            <div className="flex flex-wrap gap-2 mt-2">
              <span className="text-sm text-gray-500">Popular questions:</span>
              <button 
                className="text-sm bg-gray-100 hover:bg-gray-200 px-2 py-1 rounded"
                onClick={() => setInputText("How to manage exam time?")}
              >
                How to manage exam time?
              </button>
              <button 
                className="text-sm bg-gray-100 hover:bg-gray-200 px-2 py-1 rounded"
                onClick={() => setInputText("Solve this numerical")}
              >
                Solve this numerical
              </button>
              <button 
                className="text-sm bg-gray-100 hover:bg-gray-200 px-2 py-1 rounded"
                onClick={() => setInputText("Last-minute revision tips")}
              >
                Last-minute revision tips
              </button>
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
};

export default ChatPage;