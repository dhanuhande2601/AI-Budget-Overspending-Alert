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
  const SpeechRecognition =
    window.SpeechRecognition ||
    window.webkitSpeechRecognition
  const recognition = SpeechRecognition
    ? new SpeechRecognition()
    : null
    recognition.continuous = false
    recognition.lang = 'en-US'
  const startListening = () => {

    recognition.onresult = (event) => {

      const text =
        event.results[0][0].transcript

      console.log("VOICE =", text)

      const lower =
        text.toLowerCase()

      const amountMatch =
        text.match(/\d+/)

      const amount =
        amountMatch
          ? amountMatch[0]
          : ""

      const categoryKeywords = {
        Food: [
          "swiggy",
          "zomato",
          "restaurant",
          "cafe",
          "food",
          "pizza",
          "hotel"
        ],
        Transport: [
          "uber",
          "ola",
          "rapido",
          "metro",
          "fuel",
          "petrol",
          "diesel",
          "parking"
        ],
        Shopping: [
          "amazon",
          "flipkart",
          "myntra",
          "shopping",
          "store"
        ],
        Bills: [
          "electricity",
          "bill",
          "recharge",
          "wifi",
          "mobile"
        ],
        Entertainment: [
          "movie",
          "netflix",
          "spotify",
          "cinema"
        ],
        Health: [
          "medical",
          "pharmacy",
          "hospital",
          "clinic",
          "medicine"
        ]
      }

      let category = ""

      for (const [cat, keywords] of Object.entries(categoryKeywords)) {
        if (keywords.some(word => lower.includes(word))) {
          category = cat
          break
        }
      }

      let paymentMethod = ""

      if (
        lower.includes("upi") ||
        lower.includes("gpay") ||
        lower.includes("google pay") ||
        lower.includes("phonepe") ||
        lower.includes("paytm")
      ) {
        paymentMethod = "UPI"
      }
      else if (
        lower.includes("card") ||
        lower.includes("credit card") ||
        lower.includes("debit card")
      ) {
        paymentMethod = "Card"
      }
      else if (
        lower.includes("net banking") ||
        lower.includes("netbanking") ||
        lower.includes("neft") ||
        lower.includes("imps")
      ) {
        paymentMethod = "Net Banking"
      }

      const title =
        text.replace(/\d+/g, "")
            .replace(/gpay|phonepe|paytm|upi|credit card|debit card/gi, "")
            .trim()

      onExpenseFormChange("title", title)
      onExpenseFormChange("amount", amount)
      onExpenseFormChange("category", category)
      onExpenseFormChange("payment_method", paymentMethod)

      console.log("Amount =", amount)
      console.log("Category =", category)
      console.log("Payment =", paymentMethod)
}
     if (!recognition) {
      alert("Speech Recognition not supported")
      return
    }
    recognition.start()
  }

  const categories = Array.from(new Set(expenses.map((expense) => expense.category).filter(Boolean)))
  const [showExpenses, setShowExpenses] = useState(false)
  return (
    <>
      <form className="expense-form" onSubmit={onSubmit}>
        <h2>{editingExpenseId ? 'Update expense' : 'Add expense'}</h2>
        <button
          type="button"
          className="voice-btn"
          onClick={startListening}
        >
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
        <input
          required
          placeholder="Category"
          value={expenseForm.category}
          onChange={(event) => onExpenseFormChange('category', event.target.value)}
        />
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

        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center"
          }}
        >
          <h2>Recent Expenses</h2>

          <button
            type="button"
            onClick={() => setShowExpenses(!showExpenses)}
          >
            {showExpenses ? "Hide Expenses" : "Show Expenses"}
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

            {expenses.length === 0 && (
              <p className="muted">
                No expenses yet.
              </p>
            )}

          </div>
        )}

      </div>
    </>
  )
}

export default ExpenseSection
