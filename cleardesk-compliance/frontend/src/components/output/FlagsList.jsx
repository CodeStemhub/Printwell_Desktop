export default function FlagsList({ flags }) {
  if (!flags || flags.length === 0) {
    return null
  }

  // Sort by severity
  const severityOrder = { critical: 0, high: 1, medium: 2, low: 3 }
  const sortedFlags = [...flags].sort(
    (a, b) => severityOrder[a.severity] - severityOrder[b.severity]
  )

  const getSeverityStyles = (severity) => {
    switch (severity) {
      case 'critical':
        return 'bg-red-900/30 border-red-700 text-red-300'
      case 'high':
        return 'bg-orange-900/30 border-orange-700 text-orange-300'
      case 'medium':
        return 'bg-yellow-900/30 border-yellow-700 text-yellow-300'
      case 'low':
        return 'bg-blue-900/30 border-blue-700 text-blue-300'
      default:
        return 'bg-gray-800 border-gray-600 text-gray-300'
    }
  }

  const getSeverityIcon = (severity) => {
    switch (severity) {
      case 'critical':
      case 'high':
        return (
          <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
          </svg>
        )
      default:
        return (
          <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
          </svg>
        )
    }
  }

  return (
    <div className="bg-[#151E32] rounded-lg border border-[#2D3B4E] overflow-hidden">
      <div className="px-4 py-3 bg-[#1A2744] border-b border-[#2D3B4E]">
        <h3 className="font-semibold text-white flex items-center gap-2">
          <svg className="w-5 h-5 text-yellow-500" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
          </svg>
          Validation Issues ({flags.length})
        </h3>
      </div>

      <div className="divide-y divide-[#2D3B4E]">
        {sortedFlags.map((flag, index) => (
          <div
            key={index}
            className={`p-4 border-l-4 ${getSeverityStyles(flag.severity)}`}
          >
            <div className="flex items-start gap-3">
              <div className="flex-shrink-0">{getSeverityIcon(flag.severity)}</div>
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <span className="font-semibold capitalize">{flag.type.replace(/_/g, ' ')}</span>
                  {flag.field_name && (
                    <span className="text-xs px-2 py-0.5 rounded bg-black/20 font-mono">
                      {flag.field_name}
                    </span>
                  )}
                </div>
                <p className="text-sm opacity-90">{flag.message}</p>
                <div className="mt-2 flex items-center gap-3 text-xs opacity-75">
                  <span className="capitalize">Severity: {flag.severity}</span>
                  {flag.is_resolved && (
                    <span className="text-green-400">✓ Resolved</span>
                  )}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
