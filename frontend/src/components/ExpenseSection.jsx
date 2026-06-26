import { useRef, useState } from 'react'
import { FiMic, FiPlus, FiSquare } from 'react-icons/fi'

function ExpenseSection({
  categoryFilter,
  editingExpenseId,
  expenseForm,
  expenses,
  filteredExpenses,
  loading,
  message,
  onCategoryFilterChange,
  onDeleteExpense,
  onExpenseFormChange,
  onVoiceError,
  onVoiceExpenseAdd,
  onSearchChange,
  onSubmit,
  onStartEdit,
  searchTerm,
}) {
  const [showExpenses, setShowExpenses] = useState(false)
  const [isRecording, setIsRecording] = useState(false)
  const mediaRecorderRef = useRef(null)
  const mediaStreamRef = useRef(null)
  const audioChunksRef = useRef([])

  const categories = Array.from(
    new Set(expenses.map((expense) => expense.category).filter(Boolean))
  )

  const getAudioFilename = (mimeType) => {
    if (mimeType.includes('mp4')) return 'voice-expense.mp4'
    if (mimeType.includes('ogg')) return 'voice-expense.ogg'
    return 'voice-expense.webm'
  }

  const stopStream = () => {
    mediaStreamRef.current?.getTracks().forEach((track) => track.stop())
    mediaStreamRef.current = null
  }

  async function startVoiceRecording() {
    if (!navigator.mediaDevices?.getUserMedia || !window.MediaRecorder) {
      onVoiceError?.('Voice recording is not supported in this browser.')
      return
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const recorder = new MediaRecorder(stream)

      mediaStreamRef.current = stream
      mediaRecorderRef.current = recorder
      audioChunksRef.current = []

      recorder.ondataavailable = (event) => {
        if (event.data?.size > 0) {
          audioChunksRef.current.push(event.data)
        }
      }

      recorder.onstop = async () => {
        const mimeType = recorder.mimeType || 'audio/webm'
        const audioBlob = new Blob(audioChunksRef.current, { type: mimeType })
        audioChunksRef.current = []
        stopStream()
        setIsRecording(false)

        if (!audioBlob.size) {
          onVoiceError?.('No voice audio was recorded.')
          return
        }

        await onVoiceExpenseAdd?.(audioBlob, getAudioFilename(mimeType))
      }

      recorder.start()
      setIsRecording(true)
    } catch (error) {
      stopStream()
      setIsRecording(false)
      onVoiceError?.(
        error?.name === 'NotAllowedError'
          ? 'Microphone permission was denied.'
          : 'Could not start voice recording.'
      )
    }
  }

  function stopVoiceRecording() {
    if (mediaRecorderRef.current?.state === 'recording') {
      mediaRecorderRef.current.stop()
    }
  }

  return (
    <>
      <form className="expense-form" onSubmit={onSubmit}>
        <div className="expense-form-header">
          <h2>{editingExpenseId ? 'Update expense' : 'Add expense'}</h2>
          <button
            className={`voice-btn ${isRecording ? 'recording' : ''}`}
            disabled={loading}
            onClick={isRecording ? stopVoiceRecording : startVoiceRecording}
            type="button"
          >
            {isRecording ? <FiSquare aria-hidden="true" /> : <FiMic aria-hidden="true" />}
            {isRecording ? 'Stop Recording' : 'Add Voice Expense'}
          </button>
        </div>
        <input
          required
          placeholder="Title"
          value={expenseForm.title}
          onChange={(event) => onExpenseFormChange('title', event.target.value)}
        />
        <input
          required
          min="0"
          step="0.01"
          placeholder="Amount"
          type="number"
          value={expenseForm.amount}
          onChange={(event) => onExpenseFormChange('amount', event.target.value)}
        />
        <select
          required
          value={expenseForm.category}
          onChange={(event) => onExpenseFormChange('category', event.target.value)}
        >
          <option value="" disabled>Select category</option>
          <option value="Food">Food</option>
          <option value="Travel">Travel</option>
          <option value="Shopping">Shopping</option>
          <option value="Health">Health</option>
          <option value="Adventure">Adventure</option>
          <option value="Loan">Loan/EMI</option>
          <option value="Bills">Bills</option>
          <option value="Grocery">Grocery</option>
        </select>
        <input
          placeholder="Payment method"
          value={expenseForm.payment_method}
          onChange={(event) => onExpenseFormChange('payment_method', event.target.value)}
        />
        <button disabled={loading} type="submit">
          <FiPlus aria-hidden="true" />
          {editingExpenseId ? 'Update Expense' : 'Add Expense'}
        </button>
        {message && <p className="status">{message}</p>}
      </form>

      <div className="filter-row">
        <input
          type="text"
          placeholder="Search Expense..."
          value={searchTerm}
          onChange={(event) => onSearchChange(event.target.value)}
        />
        <select
          value={categoryFilter}
          onChange={(event) => onCategoryFilterChange(event.target.value)}
        >
          <option value="">All Categories</option>
          {categories.map((category) => (
            <option key={category} value={category}>
              {category}
            </option>
          ))}
        </select>
      </div>

      <div className="panel">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h2>Recent Expenses</h2>
          <button type="button" onClick={() => setShowExpenses(!showExpenses)}>
            {showExpenses ? 'Hide Expenses' : 'Show Expenses'}
          </button>
        </div>

        {showExpenses && (
          <div className="expense-list">
            {filteredExpenses.map((expense) => (
              <div className="expense-row" key={expense.id}>
                <div>
                  <strong>{expense.title}</strong>
                  <span>{expense.category}</span>
                </div>
                <div className="expense-actions">
                  <b>Rs. {Number(expense.amount).toFixed(2)}</b>
                  <button
                    className="edit-button"
                    type="button"
                    onClick={() => onStartEdit(expense)}
                  >
                    Edit
                  </button>
                  <button
                    className="delete-button"
                    type="button"
                    onClick={() => onDeleteExpense(expense.id)}
                  >
                    Delete
                  </button>
                </div>
              </div>
            ))}
            {expenses.length === 0 && <p className="muted">No expenses yet.</p>}
          </div>
        )}
      </div>
    </>
  )
}

export default ExpenseSection
