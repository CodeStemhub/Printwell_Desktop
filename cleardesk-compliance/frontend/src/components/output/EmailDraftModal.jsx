import { useState } from 'react'

export default function EmailDraftModal({ isOpen, onClose, document, emailType }) {
  const [isGenerating, setIsGenerating] = useState(false)
  const [generatedEmail, setGeneratedEmail] = useState(null)

  if (!isOpen) return null

  const handleGenerate = async () => {
    setIsGenerating(true)
    
    // TODO: Call backend API to generate email
    // POST /api/compliance/email/draft
    // Body: { document_id, email_type, recipient, key_points }
    
    setTimeout(() => {
      // Mock response for now
      setGeneratedEmail({
        subject: `Regarding ${document?.classified_type?.replace(/_/g, ' ')} - ${document?.filename}`,
        body: `Dear Sir/Madam,\n\nI hope this email finds you well.\n\nI am writing regarding the above-mentioned document which has been processed through our compliance system.\n\n[Email content will be generated based on document type and flags]\n\nPlease do not hesitate to contact us should you require any clarification.\n\nBest regards,\n[Your Name]`
      })
      setIsGenerating(false)
    }, 1500)
  }

  const handleCopy = () => {
    if (generatedEmail) {
      navigator.clipboard.writeText(`${generatedEmail.subject}\n\n${generatedEmail.body}`)
      alert('Email copied to clipboard!')
    }
  }

  const handleSend = () => {
    // TODO: Integrate with email service
    alert('Email sending feature coming soon - will integrate with your email provider')
  }

  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
      <div className="bg-[#151E32] rounded-lg border border-[#2D3B4E] w-full max-w-2xl max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b border-[#2D3B4E] flex items-center justify-between">
          <h2 className="text-xl font-bold text-white">Draft Email</h2>
          <button
            onClick={onClose}
            className="text-[#94A3B8] hover:text-white transition-colors"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {!generatedEmail ? (
            <div className="text-center py-8">
              <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-[#1A2744] flex items-center justify-center">
                <svg className="w-8 h-8 text-[#94A3B8]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-white mb-2">Generate Professional Email</h3>
              <p className="text-[#94A3B8] mb-6">
                AI will draft a professional email based on this document's content and any flagged issues.
              </p>
              <button
                onClick={handleGenerate}
                disabled={isGenerating}
                className="btn-primary inline-flex items-center gap-2"
              >
                {isGenerating ? (
                  <>
                    <svg className="animate-spin w-5 h-5" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                    Generating...
                  </>
                ) : (
                  <>
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                    </svg>
                    Generate Email Draft
                  </>
                )}
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-[#94A3B8] mb-1">Subject</label>
                <input
                  type="text"
                  defaultValue={generatedEmail.subject}
                  className="w-full px-3 py-2 bg-[#1A2744] border border-[#2D3B4E] rounded-lg text-white focus:outline-none focus:border-[#1A7F5A]"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-[#94A3B8] mb-1">Email Body</label>
                <textarea
                  defaultValue={generatedEmail.body}
                  rows={12}
                  className="w-full px-3 py-2 bg-[#1A2744] border border-[#2D3B4E] rounded-lg text-white font-mono text-sm focus:outline-none focus:border-[#1A7F5A]"
                />
              </div>
            </div>
          )}
        </div>

        {/* Footer Actions */}
        {generatedEmail && (
          <div className="px-6 py-4 border-t border-[#2D3B4E] flex items-center justify-end gap-3">
            <button
              onClick={() => setGeneratedEmail(null)}
              className="px-4 py-2 text-[#94A3B8] hover:text-white transition-colors"
            >
              Regenerate
            </button>
            <button
              onClick={handleCopy}
              className="px-4 py-2 bg-[#2D3B4E] hover:bg-[#3D4B5E] text-white rounded-lg transition-colors"
            >
              Copy to Clipboard
            </button>
            <button
              onClick={handleSend}
              className="btn-primary"
            >
              Send Email
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
