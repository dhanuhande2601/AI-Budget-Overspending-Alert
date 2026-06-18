import { useState } from 'react'
import { FiPlus } from 'react-icons/fi'

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
  onSearchChange,
  onSubmit,
  onStartEdit,
  searchTerm,
}) {
  const [showExpenses, setShowExpenses] = useState(false)

  const SpeechRecognition =
    window.SpeechRecognition || window.webkitSpeechRecognition

  const recognition = SpeechRecognition ? new SpeechRecognition() : null

  if (recognition) {
    recognition.continuous = false
    recognition.lang = 'en-US'
  }

  const startListening = () => {
    if (!recognition) {
      alert('Speech Recognition is not supported in this browser. Please use Chrome.')
      return
    }

    recognition.onresult = (event) => {
      const text = event.results[0][0].transcript
      console.log('VOICE =', text)

      const lower = text.toLowerCase()
      const amountMatch = text.match(/\d+/)
      const amount = amountMatch ? amountMatch[0] : ''

      const categoryKeywords = {
        Food: ['swiggy', 'zomato', 'restaurant', 'cafe', 'food', 'pizza', 'hotel'],
        Travel: ['uber', 'ola', 'rapido', 'metro', 'fuel', 'petrol', 'diesel', 'parking', 'bus', 'train', 'flight'],
        Shopping: ['amazon', 'flipkart', 'myntra', 'shopping', 'store', 'mart'],
        Health: ['medical', 'pharmacy', 'hospital', 'clinic', 'medicine', 'doctor'],
        Adventure: ['movie', 'netflix', 'spotify', 'cinema', 'trip', 'trek', 'park'],
        Loan: ['emi', 'loan', 'installment'],
      }

      let category = ''
      for (const [cat, keywords] of Object.entries(categoryKeywords)) {
        if (keywords.some((word) => lower.includes(word))) {
          category = cat
          break
        }
      }

      let paymentMethod = ''
      if (
        lower.includes('upi') ||
        lower.includes('gpay') ||
        lower.includes('google pay') ||
        lower.includes('phonepe') ||
        lower.includes('paytm')
      ) {
        paymentMethod = 'UPI'
      } else if (
        lower.includes('card') ||
        lower.includes('credit card') ||
        lower.includes('debit card')
      ) {
        paymentMethod = 'Card'
      } else if (
        lower.includes('net banking') ||
        lower.includes('netbanking') ||
        lower.includes('neft') ||
        lower.includes('imps')
      ) {
        paymentMethod = 'Net Banking'
      }

      const title = text
        .replace(/\d+/g, '')
        .replace(/gpay|phonepe|paytm|upi|credit card|debit card/gi, '')
        .trim()

      onExpenseFormChange('title', title)
      onExpenseFormChange('amount', amount)
      onExpenseFormChange('category', category)
      onExpenseFormChange('payment_method', paymentMethod)

      console.log('Amount =', amount)
      console.log('Category =', category)
      console.log('Payment =', paymentMethod)
    }

    recognition.onerror = (event) => {
      console.error('Speech recognition error:', event.error)
      alert('Voice recognition error: ' + event.error + '. Please try again.')
    }

    recognition.start()
  }

  const categories = Array.from(
    new Set(expenses.map((expense) => expense.category).filter(Boolean))
  )

  return (
    <>
      <form className="expense-form" onSubmit={onSubmit}>
        <h2>{editingExpenseId ? 'Update expense' : 'Add expense'}</h2>
        <button type="button" className="voice-btn" onClick={startListening}>
          🎤 Voice Expense
        </button>
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