import { useState } from 'react'
import { MdSms } from 'react-icons/md'
import { previewSMSExpense, addSMSExpense } from '../api/budgetApi'

export default function SMSExpense({ onExpenseAdded, token }) {
  const [smsText, setSmsText] = useState('')
  const [preview, setPreview] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const handlePreview = async () => {
    if (!smsText.trim()) return
    setLoading(true)
    setError('')
    setPreview(null)
    try {
      const data = await previewSMSExpense(smsText, token)
      setPreview(data)
    } catch (err) {
      setError(err.message || 'Could not parse the SMS. Please try again.')
    }
    setLoading(false)
  }

  const handleConfirm = async () => {
    setLoading(true)
    setError('')
    try {
      await addSMSExpense(smsText, token)
      setSuccess('Expense added successfully!')
      setSmsText('')
      setPreview(null)
      onExpenseAdded()
    } catch (err) {
      setError(err.message || 'Could not save expense. Please try again.')
    }
    setLoading(false)
  }

  return (
    <div className="bg-white rounded-2xl p-5 shadow mb-4">
      <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
        <MdSms className="text-blue-500" />
        Add Expense from Bank SMS
      </h3>

      <textarea
        className="w-full border rounded-xl p-3 text-sm resize-none h-24"
        placeholder="Paste your bank SMS here... e.g. INR 500.00 debited from your account..."
        value={smsText}
        onChange={(e) => {
          setSmsText(e.target.value)
          setPreview(null)
          setSuccess('')
          setError('')
        }}
      />

      <button
        onClick={handlePreview}
        disabled={loading || !smsText.trim()}
        className="mt-2 bg-blue-500 text-white px-4 py-2 rounded-xl text-sm hover:bg-blue-600 disabled:opacity-50"
      >
        {loading ? 'Parsing...' : 'Preview SMS'}
      </button>

      {preview && (
        <div className="mt-4 bg-blue-50 rounded-xl p-4 text-sm">
          <p className="font-semibold text-blue-700 mb-2">Detected Expense:</p>
          <div className="grid grid-cols-2 gap-2 text-gray-700">
            <span>Amount:</span>
            <span className="font-medium">₹{preview.amount}</span>
            <span>Category:</span>
            <span className="font-medium">{preview.category}</span>
            <span>Description:</span>
            <span className="font-medium">{preview.description}</span>
            <span>Date:</span>
            <span className="font-medium">{preview.date}</span>
          </div>
          <button
            onClick={handleConfirm}
            disabled={loading}
            className="mt-3 bg-green-500 text-white px-4 py-2 rounded-xl text-sm hover:bg-green-600 disabled:opacity-50 w-full"
          >
            {loading ? 'Saving...' : '✅ Confirm & Save'}
          </button>
        </div>
      )}

      {error && <p className="text-red-500 text-sm mt-2">{error}</p>}
      {success && <p className="text-green-600 text-sm mt-2">{success}</p>}
    </div>
  )
}