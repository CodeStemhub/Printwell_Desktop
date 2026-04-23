import { useState, useRef } from 'react'

export default function UploadZone({ sessionId, onClose }) {
  const [isDragging, setIsDragging] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const fileInputRef = useRef(null)

  const handleDragOver = (e) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = () => {
    setIsDragging(false)
  }

  const handleDrop = (e) => {
    e.preventDefault()
    setIsDragging(false)
    
    const files = e.dataTransfer.files
    if (files.length > 0) {
      handleFiles(files)
    }
  }

  const handleFileSelect = (e) => {
    const files = e.target.files
    if (files.length > 0) {
      handleFiles(files)
    }
  }

  const handleFiles = async (files) => {
    setIsUploading(true)
    
    // TODO: Implement actual file upload API call
    for (const file of files) {
      console.log('Uploading:', file.name)
      // Simulate upload delay
      await new Promise(resolve => setTimeout(resolve, 1000))
    }
    
    setIsUploading(false)
    onClose()
  }

  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 animate-fade-in">
      <div className="card w-full max-w-lg mx-4 animate-slide-up">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-semibold text-white">Upload Documents</h2>
          <button
            onClick={onClose}
            className="text-[#94A3B8] hover:text-white transition-colors"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Drop Zone */}
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          className={`
            border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition-all
            ${isDragging 
              ? 'border-[#1A7F5A] bg-[#1A7F5A]/10' 
              : 'border-[#2D3B4E] hover:border-[#1A7F5A] hover:bg-[#151E32]'
            }
          `}
        >
          <input
            ref={fileInputRef}
            type="file"
            multiple
            accept=".pdf,.docx,.xlsx,.jpg,.jpeg,.png,.webp"
            onChange={handleFileSelect}
            className="hidden"
          />

          {isUploading ? (
            <div className="space-y-4">
              <svg className="animate-spin h-12 w-12 text-[#1A7F5A] mx-auto" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              <p className="text-white">Uploading documents...</p>
            </div>
          ) : (
            <>
              <svg 
                className={`w-16 h-16 mx-auto mb-4 ${isDragging ? 'text-[#1A7F5A]' : 'text-[#94A3B8]'}`}
                fill="none" 
                stroke="currentColor" 
                viewBox="0 0 24 24"
              >
                <path 
                  strokeLinecap="round" 
                  strokeLinejoin="round" 
                  strokeWidth={1.5} 
                  d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" 
                />
              </svg>
              
              <p className="text-white font-medium mb-2">
                {isDragging ? 'Drop files here' : 'Drag & drop files here'}
              </p>
              <p className="text-[#94A3B8] text-sm mb-4">or click to browse</p>
              
              <p className="text-xs text-[#94A3B8]">
                Supported: PDF, DOCX, XLSX, JPG, PNG, WEBP (Max 50MB)
              </p>
            </>
          )}
        </div>

        {/* Info */}
        <div className="mt-6 p-4 bg-[#0A0F1E] rounded-lg">
          <h3 className="text-sm font-medium text-white mb-2">What happens next?</h3>
          <ul className="space-y-2 text-sm text-[#94A3B8]">
            <li className="flex items-start gap-2">
              <span className="text-[#1A7F5A] mt-0.5">✓</span>
              Document is automatically classified
            </li>
            <li className="flex items-start gap-2">
              <span className="text-[#1A7F5A] mt-0.5">✓</span>
              Data is extracted and structured
            </li>
            <li className="flex items-start gap-2">
              <span className="text-[#1A7F5A] mt-0.5">✓</span>
              Validation checks run automatically
            </li>
            <li className="flex items-start gap-2">
              <span className="text-[#1A7F5A] mt-0.5">✓</span>
              Agent notifies you of any issues
            </li>
          </ul>
        </div>
      </div>
    </div>
  )
}
