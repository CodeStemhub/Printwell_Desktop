import { useState } from 'react'
import DocumentPanel from '../components/documents/DocumentPanel'
import ChatInterface from '../components/chat/ChatInterface'
import UploadZone from '../components/documents/UploadZone'

export default function ComplianceDashboard() {
  const [sessionId] = useState(() => `session-${Date.now()}`)
  const [showUpload, setShowUpload] = useState(false)

  return (
    <div className="h-screen flex flex-col bg-[#0A0F1E]">
      {/* Header */}
      <header className="flex items-center justify-between px-6 py-4 border-b border-[#2D3B4E] bg-[#151E32]">
        <div className="flex items-center gap-4">
          <h1 className="text-xl font-bold text-white">ClearDesk</h1>
          <span className="text-sm text-[#94A3B8]">Compliance Agent</span>
        </div>
        
        <button
          onClick={() => setShowUpload(true)}
          className="btn-primary flex items-center gap-2"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          Upload Document
        </button>
      </header>

      {/* Main Content - Two Panel Layout */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Panel - Documents */}
        <div className="w-1/3 border-r border-[#2D3B4E] overflow-y-auto">
          <DocumentPanel sessionId={sessionId} />
        </div>

        {/* Right Panel - Agent Chat */}
        <div className="flex-1 flex flex-col">
          <ChatInterface sessionId={sessionId} />
        </div>
      </div>

      {/* Upload Modal */}
      {showUpload && (
        <UploadZone 
          sessionId={sessionId}
          onClose={() => setShowUpload(false)}
        />
      )}
    </div>
  )
}
