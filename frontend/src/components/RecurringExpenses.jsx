import { useEffect, useState } from 'react'
import { FiPause, FiPlay, FiPlus, FiRepeat, FiTrash2 } from 'react-icons/fi'
import {
  getRecurringExpenses,
  addRecurringExpense,
  toggleRecurringExpense,
  deleteRecurringExpense,
} from '../api/budgetApi'

const emptyForm = {
  title: '',
  amount: '',
  category: '',
  payment_method: '',
  frequency: 'monthly',
  day_of_month: 1,
}

export default function RecurringExpenses({ token }) {
  const [items, setItems] = useState([])
  const [form, setForm] = useState(emptyForm)
  const [showForm, setShowForm] = useState(false)
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState('')

  useEffect(() => {
    loadItems()
  }, [token])

  async function loadItems() {
    try {
      const data = await getRecurringExpenses(token)
      setItems(Array.isArray(data) ? data : [])
    } catch (error) {
      console.log(error)
    }
  }

  function updateForm(field, value) {
    setForm((prev) => ({ ...prev, [field]: value }))
  }

  async function handleSubmit(event) {
    event.preventDefault()
    setLoading(true)
    setMessage('')
    try {
      await addRecurringExpense(token, {
        ...form,
        amount: Number(form.amount),
        day_of_month: Number(form.day_of_month),
      })
      setMessage('Recurring expense added')
      setForm(emptyForm)
      setShowForm(false)
      await loadItems()
    } catch (error) {
      setMessage(error.message)
    }
    setLoading(false)
  }

  async function handleToggle(id) {
    try {
      await toggleRecurringExpense(token, id)
      await loadItems()
    } catch (error) {
      console.log(error)
    }
  }

  async function handleDelete(id) {
    try {
      await deleteRecurringExpense(token, id)
      await loadItems()
    } catch (error) {
      console.log(error)
    }
  }

  return (
    <div className="panel">
      <div className="panel-heading">
        <div>
          <h2><FiRepeat style={{ marginRight: 6 }} />Recurring Expenses</h2>
          <p className="panel-subtitle">EMIs, rent, subscriptions — added automatically every cycle</p>
        </div>
        <button onClick={() => setShowForm((prev) => !prev)}>
          <FiPlus /> {showForm ? 'Cancel' : 'Add Recurring'}
        </button>
      </div>

      {showForm && (
        <form className="stack" onSubmit={handleSubmit} style={{ marginBottom: 18 }}>
          <input
            required
            placeholder="Title (e.g. Home Loan EMI)"
            value={form.title}
            onChange={(e) => updateForm('title', e.target.value)}
          />
          <input
            required
            type="number"
            min="0"
            step="0.01"
            placeholder="Amount"
            value={form.amount}
            onChange={(e) => updateForm('amount', e.target.value)}
          />
          <select
            required
            value={form.category}
            onChange={(e) => updateForm('category', e.target.value)}
          >
            <option value="" disabled>Select category</option>
            <option value="Loan">Loan/EMI</option>
            <option value="Food">Food</option>
            <option value="Travel">Travel</option>
            <option value="Shopping">Shopping</option>
            <option value="Health">Health</option>
            <option value="Adventure">Adventure</option>
          </select>
          <input
            placeholder="Payment method"
            value={form.payment_method}
            onChange={(e) => updateForm('payment_method', e.target.value)}
          />
          <select
            value={form.frequency}
            onChange={(e) => updateForm('frequency', e.target.value)}
          >
            <option value="monthly">Monthly</option>
            <option value="weekly">Weekly</option>
            <option value="yearly">Yearly</option>
          </select>
          {form.frequency !== 'weekly' && (
            <input
              type="number"
              min="1"
              max="28"
              placeholder="Day of month (1-28)"
              value={form.day_of_month}
              onChange={(e) => updateForm('day_of_month', e.target.value)}
            />
          )}
          <button disabled={loading} type="submit">
            {loading ? 'Saving...' : 'Save Recurring Expense'}
          </button>
          {message && <p className="status">{message}</p>}
        </form>
      )}

      {items.length === 0 ? (
        <p className="muted">No recurring expenses set up yet.</p>
      ) : (
        <div className="expense-list">
          {items.map((item) => (
            <div className="expense-row" key={item.id}>
              <div>
                <strong>{item.title}</strong>
                <span>
                  {item.category} • {item.frequency}
                  {item.frequency !== 'weekly' ? ` (day ${item.day_of_month})` : ''}
                </span>
              </div>
              <div className="expense-actions">
                <b>₹{Number(item.amount).toFixed(2)}</b>
                <span className={`status-badge ${item.is_active ? 'safe' : 'warning'}`}>
                  {item.is_active ? 'Active' : 'Paused'}
                </span>
                <button className="edit-button" type="button" onClick={() => handleToggle(item.id)}>
                  {item.is_active ? <FiPause /> : <FiPlay />}
                </button>
                <button className="delete-button" type="button" onClick={() => handleDelete(item.id)}>
                  <FiTrash2 />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}