import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

export default function DocumentPanel({ sessionId }) {
  const [documents, setDocuments] = useState([
    // Demo data - will be replaced with actual API data
    {
      id: '1',
      filename: 'GRA_VAT_Return_Q1_2025.pdf',
      type: 'GRA_VAT_RETURN',
      status: 'complete',
      validationStatus: 'has_flags',
      flagsCount: 2,
      confidence: 0.94
    },
    {
      id: '2',
      filename: 'SSNIT_Contribution_January.pdf',
      type: 'SSNIT_CONTRIBUTION',
      status: 'complete',
      validationStatus: 'valid',
      flagsCount: 0,
      confidence: 0.97
    },
    {
      id: '3',
      filename: 'Invoice_INV-2025-001.jpg',
      type: 'SUPPLIER_INVOICE',
      status: 'processing',
      validationStatus: 'not_validated',
      flagsCount: 0,
      confidence: null
    }
  ])

  const getStatusIcon = (status) => {
    switch (status) {
      case 'complete':
        return <span className="text-green-500">✓</span>
      case 'processing':
        return (
          <svg className="animate-spin h-4 w-4 text-yellow-500" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
        )
      case 'error':
        return <span className="text-red-500">✗</span>
      default:
        return <span className="text-gray-500">•</span>
    }
  }

  const getValidationBadge = (doc) => {
    if (doc.validationStatus === 'valid') {
      return (
        <span className="px-2 py-0.5 text-xs bg-green-900/30 text-green-400 rounded-full">
          Valid
        </span>
      )
    } else if (doc.validationStatus === 'has_flags') {
      return (
        <span className="px-2 py-0.5 text-xs bg-red-900/30 text-red-400 rounded-full">
          {doc.flagsCount} Issue{doc.flagsCount > 1 ? 's' : ''}
        </span>
      )
    }
    return null
  }

  return (
    <div className="p-4">
      <h2 className="text-lg font-semibold text-white mb-4">Documents</h2>
      
      <div className="space-y-3">
        <AnimatePresence>
          {documents.map((doc) => (
            <motion.div
              key={doc.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="card cursor-pointer hover:border-[#1A7F5A] transition-colors group"
            >
              <div className="flex items-start gap-3">
                {/* Status Icon */}
                <div className="mt-1">
                  {getStatusIcon(doc.status)}
                </div>

                {/* Document Info */}
                <div className="flex-1 min-w-0">
                  <h3 className="text-sm font-medium text-white truncate group-hover:text-[#1A7F5A] transition-colors">
                    {doc.filename}
                  </h3>
                  
                  <div className="flex items-center gap-2 mt-1">
                    <span className="text-xs text-[#94A3B8]">
                      {doc.type ? doc.type.replace(/_/g, ' ') : 'Unknown'}
                    </span>
                    
                    {doc.confidence && (
                      <span className="text-xs text-[#94A3B8]">
                        ({Math.round(doc.confidence * 100)}%)
                      </span>
                    )}
                  </div>

                  <div className="flex items-center gap-2 mt-2">
                    {getValidationBadge(doc)}
                    
                    {doc.status === 'processing' && (
                      <span className="text-xs text-yellow-500">Processing...</span>
                    )}
                  </div>
                </div>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>

        {documents.length === 0 && (
          <div className="text-center py-8">
            <p className="text-[#94A3B8] text-sm">No documents yet</p>
            <p className="text-[#94A3B8] text-xs mt-1">Upload a document to get started</p>
          </div>
        )}
      </div>
    </div>
  )
}
