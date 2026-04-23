import { useState, useEffect, useRef } from 'react'

export default function ChatInterface({ sessionId }) {
  const [messages, setMessages] = useState([
    {
      id: '1',
      role: 'agent',
      content: "Hello! I'm your ClearDesk compliance assistant. I've reviewed your uploaded documents:\n\n✓ GRA VAT Return Q1 2025 - 2 issues detected\n✓ SSNIT Contribution January - All valid\n⏳ Invoice INV-2025-001 - Still processing\n\nWhat would you like to do first?",
      timestamp: new Date()
    }
  ])
  const [inputValue, setInputValue] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSend = async () => {
    if (!inputValue.trim()) return

    const userMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: inputValue,
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInputValue('')
    setIsTyping(true)

    // TODO: Implement actual API call to agent endpoint
    // Simulate agent response
    setTimeout(() => {
      const agentMessage = {
        id: (Date.now() + 1).toString(),
        role: 'agent',
        content: "I can help you with that. Based on the documents you've uploaded, here's what I found:\n\nYour GRA VAT Return has a calculation discrepancy - the net VAT payable doesn't match output VAT minus input VAT. Would you like me to explain the issue in detail or help you draft a correction?",
        timestamp: new Date()
      }
      setMessages(prev => [...prev, agentMessage])
      setIsTyping(false)
    }, 1500)
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="flex flex-col h-full">
      {/* Chat Header */}
      <div className="px-6 py-4 border-b border-[#2D3B4E]">
        <h2 className="text-lg font-semibold text-white">Agent Chat</h2>
        <p className="text-sm text-[#94A3B8]">Ask about your documents, flagged issues, or next steps</p>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[80%] rounded-lg p-4 animate-slide-up ${
                message.role === 'user'
                  ? 'bg-[#1A7F5A] text-white'
                  : 'bg-[#151E32] text-white border border-[#2D3B4E]'
              }`}
            >
              {message.role === 'agent' && (
                <div className="flex items-center gap-2 mb-2">
                  <div className="w-6 h-6 rounded-full bg-[#1A7F5A] flex items-center justify-center">
                    <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                    </svg>
                  </div>
                  <span className="text-xs text-[#94A3B8]">ClearDesk Agent</span>
                </div>
              )}
              
              <p className="text-sm whitespace-pre-wrap">{message.content}</p>
              
              <p className={`text-xs mt-2 ${message.role === 'user' ? 'text-green-100' : 'text-[#94A3B8]'}`}>
                {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </p>
            </div>
          </div>
        ))}

        {isTyping && (
          <div className="flex justify-start">
            <div className="bg-[#151E32] border border-[#2D3B4E] rounded-lg p-4">
              <div className="flex items-center gap-2">
                <div className="flex space-x-1">
                  <div className="w-2 h-2 bg-[#94A3B8] rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                  <div className="w-2 h-2 bg-[#94A3B8] rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                  <div className="w-2 h-2 bg-[#94A3B8] rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
                <span className="text-xs text-[#94A3B8]">Agent is typing...</span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="border-t border-[#2D3B4E] p-4">
        <div className="flex gap-3">
          <textarea
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask about your documents, flagged issues, or request next steps..."
            rows={2}
            className="flex-1 px-4 py-3 bg-[#151E32] border border-[#2D3B4E] rounded-lg text-white placeholder-[#94A3B8] focus:outline-none focus:border-[#1A7F5A] transition-colors resize-none"
          />
          <button
            onClick={handleSend}
            disabled={!inputValue.trim() || isTyping}
            className="btn-primary px-6 disabled:opacity-50 disabled:cursor-not-allowed self-end"
          >
            Send
          </button>
        </div>
        <p className="text-xs text-[#94A3B8] mt-2">
          Press Enter to send, Shift+Enter for new line
        </p>
      </div>
    </div>
  )
}
