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
  const categories = Array.from(new Set(expenses.map((expense) => expense.category).filter(Boolean)))

  return (
    <>
      <form className="expense-form" onSubmit={onSubmit}>
        <h2>{editingExpenseId ? 'Update expense' : 'Add expense'}</h2>
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
        <h2>Recent expenses</h2>
        <div className="expense-list">
          {filteredExpenses.map((expense) => (
            <div className="expense-row" key={expense.id}>
              <div>
                <strong>{expense.title}</strong>
                <span>{expense.category}</span>
              </div>

              <div className="expense-actions">
                <b>Rs. {Number(expense.amount).toFixed(2)}</b>
                <button className="edit-button" type="button" onClick={() => onStartEdit(expense)}>
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
      </div>
    </>
  )
}

export default ExpenseSection
