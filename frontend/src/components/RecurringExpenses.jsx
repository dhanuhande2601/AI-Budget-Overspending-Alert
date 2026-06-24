import { useCallback, useEffect, useState } from 'react'
import { FiCalendar, FiPause, FiPlay, FiPlus, FiRepeat, FiTrash2 } from 'react-icons/fi'
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
  hasEndDate: false,
  end_date: '',
}

const today = new Date().toISOString().split('T')[0]

export default function RecurringExpenses({ token }) {
  const [items, setItems] = useState([])
  const [form, setForm] = useState(emptyForm)
  const [showForm, setShowForm] = useState(false)
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState('')

  const loadItems = useCallback(async () => {
    try {
      const data = await getRecurringExpenses(token)
      setItems(Array.isArray(data) ? data : [])
    } catch (error) {
      console.log(error)
    }
  }, [token])

  useEffect(() => {
    const timeoutId = window.setTimeout(loadItems, 0)
    return () => window.clearTimeout(timeoutId)
  }, [loadItems])

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
        // Only send end_date if the user actually toggled "has end date" on
        end_date: form.hasEndDate ? form.end_date : null,
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
            <option value="Bills">Bills</option>
            <option value="Grocery">Grocery/Household</option>
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

          {/* End date section — explicit choice between a fixed end date
              (for EMIs with a known tenure) or no end date at all
              (for things like rent that just continue indefinitely). */}
          <div
            style={{
              border: '1px solid var(--soft-border)',
              borderRadius: 10,
              padding: 12,
              display: 'flex',
              flexDirection: 'column',
              gap: 8,
            }}
          >
            <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={form.hasEndDate}
                onChange={(e) => updateForm('hasEndDate', e.target.checked)}
                style={{ width: 'auto', minHeight: 'auto' }}
              />
              This has a fixed end date (e.g. an EMI tenure)
            </label>

            {form.hasEndDate ? (
              <div>
                <label style={{ fontSize: 12, color: 'var(--muted)', display: 'block', marginBottom: 4 }}>
                  <FiCalendar style={{ verticalAlign: 'middle', marginRight: 4 }} />
                  Last date this should be charged
                </label>
                <input
                  type="date"
                  required
                  min={today}
                  value={form.end_date}
                  onChange={(e) => updateForm('end_date', e.target.value)}
                />
              </div>
            ) : (
              <p style={{ fontSize: 12, color: 'var(--muted)', margin: 0 }}>
                No end date — this will keep repeating every {form.frequency} cycle until you pause or delete it.
                Use this for things like rent or subscriptions with no fixed end.
              </p>
            )}
          </div>

          <button disabled={loading} type="submit">
            {loading ? 'Saving...' : 'Save Recurring Expense'}
          </button>
          {message && <p className="status">{message}</p>}
        </form>
      )}

      {items.length === 0 ? (
        <div style={{ padding: '24px 8px', textAlign: 'center' }}>
          <FiRepeat size={32} style={{ color: 'var(--muted)', marginBottom: 8 }} />
          <p style={{ fontWeight: 600, marginBottom: 6 }}>No recurring expenses set up yet</p>
          <p className="muted" style={{ maxWidth: 420, margin: '0 auto', lineHeight: 1.6 }}>
            Use this for anything that repeats automatically — like a home loan EMI, monthly
            rent, or a Netflix subscription. Once added, it gets logged as a real expense on
            its due date every cycle, without you having to enter it manually. EMIs can have
            a fixed end date; rent and subscriptions can repeat with no end date at all.
          </p>
        </div>
      ) : (
        <div className="expense-list">
          {items.map((item) => (
            <div className="expense-row" key={item.id}>
              <div>
                <strong>{item.title}</strong>
                <span>
                  {item.category} • {item.frequency}
                  {item.frequency !== 'weekly' ? ` (day ${item.day_of_month})` : ''}
                  {item.end_date ? (
                    <>
                      {' '}• <FiCalendar style={{ verticalAlign: 'middle' }} /> ends {item.end_date}
                    </>
                  ) : (
                    <> • no end date</>
                  )}
                </span>
              </div>
              <div className="expense-actions">
                <b>₹{Number(item.amount).toFixed(2)}</b>
                <span
                  className={`status-badge ${
                    item.is_expired ? 'danger' : item.is_active ? 'safe' : 'warning'
                  }`}
                >
                  {item.is_expired ? 'Expired' : item.is_active ? 'Active' : 'Paused'}
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
