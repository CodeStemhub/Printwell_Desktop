import { useState } from 'react'

export default function ExtractedDataView({ document }) {
  const [expanded, setExpanded] = useState(false)

  if (!document?.extracted_data) {
    return null
  }

  const data = document.extracted_data

  // Format data into displayable fields
  const fields = Object.entries(data).map(([key, value]) => ({
    key,
    label: key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
    value: formatValue(value)
  }))

  function formatValue(value) {
    if (value === null || value === undefined) {
      return <span className="text-[#94A3B8] italic">Not found</span>
    }
    if (Array.isArray(value)) {
      return `${value.length} item(s)`
    }
    if (typeof value === 'number') {
      return `GHS ${value.toLocaleString('en-GH', { minimumFractionDigits: 2 })}`
    }
    return String(value)
  }

  return (
    <div className="bg-[#151E32] rounded-lg border border-[#2D3B4E] overflow-hidden">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full px-4 py-3 flex items-center justify-between bg-[#1A2744] hover:bg-[#1F2F52] transition-colors"
      >
        <h3 className="font-semibold text-white">Extracted Data</h3>
        <svg
          className={`w-5 h-5 text-[#94A3B8] transition-transform ${expanded ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {expanded && (
        <div className="p-4 space-y-2 max-h-96 overflow-y-auto">
          {fields.map(({ key, label, value }) => (
            <div
              key={key}
              className="grid grid-cols-3 gap-2 py-2 border-b border-[#2D3B4E] last:border-0"
            >
              <span className="text-sm text-[#94A3B8]">{label}</span>
              <span className="col-span-2 text-sm text-white font-mono">{value}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
