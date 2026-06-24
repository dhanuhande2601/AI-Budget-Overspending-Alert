import { useRef, useState } from 'react'
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
  onVoiceExpense,
  searchTerm,
}) {
  const [showExpenses, setShowExpenses] = useState(false)
  const [isListening, setIsListening] = useState(false)
  const [voiceStatus, setVoiceStatus] = useState('')
  const recognitionRef = useRef(null)
  const lastTranscriptRef = useRef('')

  const categoryKeywords = {
    Food: [
      'swiggy', 'zomato', 'restaurant', 'cafe', 'food', 'pizza', 'hotel',
      'chai', 'tea', 'coffee', 'lunch', 'dinner', 'breakfast', 'snacks',
      'burger', 'biryani', 'meal',
    ],
    Travel: [
      'uber', 'ola', 'rapido', 'metro', 'fuel', 'petrol', 'diesel',
      'parking', 'bus', 'train', 'flight', 'cab', 'taxi', 'auto',
      'rickshaw', 'toll',
    ],
    Shopping: [
      'amazon', 'flipkart', 'myntra', 'shopping', 'store', 'mart',
      'clothes', 'shirt', 'shoes', 'electronics',
    ],
    Health: [
      'medical', 'pharmacy', 'hospital', 'clinic', 'medicine', 'doctor',
      'tablet', 'health', 'checkup',
    ],
    Adventure: [
      'movie', 'netflix', 'spotify', 'cinema', 'trip', 'trek', 'park',
      'game', 'games', 'outing', 'entertainment',
    ],
    Loan: ['emi', 'loan', 'installment', 'instalment'],
    Bills: [
      'electricity', 'bill', 'recharge', 'broadband', 'wifi', 'mobile',
      'postpaid', 'gas bill', 'water bill', 'rent', 'subscription',
    ],
    Grocery: [
      'grocery', 'groceries', 'kirana', 'vegetables', 'vegetable', 'milk',
      'ration', 'household', 'fruit', 'fruits', 'bread', 'rice', 'dal',
    ],
  }

  const extractAmount = (text) => {
    const match = text.match(/(?:rs\.?|rupees?|inr)?\s*([0-9][0-9,]*(?:\.[0-9]{1,2})?)/i)
    if (match) return match[1].replace(/,/g, '')

    const smallNumbers = {
      zero: 0,
      one: 1,
      two: 2,
      three: 3,
      four: 4,
      five: 5,
      six: 6,
      seven: 7,
      eight: 8,
      nine: 9,
      ek: 1,
      do: 2,
      teen: 3,
      char: 4,
      chaar: 4,
      paanch: 5,
      panch: 5,
      che: 6,
      chhe: 6,
      saat: 7,
      aath: 8,
      nau: 9,
      ten: 10,
      das: 10,
      eleven: 11,
      gyarah: 11,
      twelve: 12,
      barah: 12,
      thirteen: 13,
      fourteen: 14,
      fifteen: 15,
      sixteen: 16,
      seventeen: 17,
      eighteen: 18,
      nineteen: 19,
    }
    const tens = {
      twenty: 20,
      bees: 20,
      thirty: 30,
      tees: 30,
      forty: 40,
      fifty: 50,
      sixty: 60,
      seventy: 70,
      eighty: 80,
      ninety: 90,
    }
    const words = text
      .toLowerCase()
      .replace(/-/g, ' ')
      .split(/\s+/)
      .map((word) => word.replace(/[^a-z]/g, ''))
      .filter(Boolean)

    let total = 0
    let current = 0
    let foundNumberWord = false

    for (const word of words) {
      if (word in smallNumbers) {
        current += smallNumbers[word]
        foundNumberWord = true
      } else if (word in tens) {
        current += tens[word]
        foundNumberWord = true
      } else if (word === 'hundred') {
        current = (current || 1) * 100
        foundNumberWord = true
      } else if (word === 'sau') {
        current = (current || 1) * 100
        foundNumberWord = true
      } else if (word === 'thousand') {
        total += (current || 1) * 1000
        current = 0
        foundNumberWord = true
      } else if (word === 'hazar' || word === 'hazaar') {
        total += (current || 1) * 1000
        current = 0
        foundNumberWord = true
      } else if (foundNumberWord && ['rupee', 'rupees', 'rs', 'inr'].includes(word)) {
        break
      }
    }

    const parsedAmount = total + current
    return parsedAmount > 0 ? String(parsedAmount) : ''
  }

  const detectCategory = (text) => {
    const lower = text.toLowerCase()
    for (const [cat, keywords] of Object.entries(categoryKeywords)) {
      if (keywords.some((word) => lower.includes(word))) {
        return cat
      }
    }
    return expenseForm.category || 'Shopping'
  }

  const saveVoiceExpense = async (text) => {
    const cleanText = (text || '').trim()
    if (!cleanText) {
      setVoiceStatus('No speech detected. Please try again closer to the microphone.')
      return
    }

    console.log('VOICE =', cleanText)
    setVoiceStatus(`Heard: ${cleanText}`)

    const lower = cleanText.toLowerCase()
    const amount = extractAmount(cleanText)
    const category = detectCategory(cleanText)

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

    const title = cleanText
      .replace(/(?:rs\.?|rupees?|inr)?\s*[0-9][0-9,]*(?:\.[0-9]{1,2})?/gi, '')
      .replace(/rs\.?|rupees?|inr/gi, '')
      .replace(/gpay|phonepe|paytm|upi|credit card|debit card/gi, '')
      .replace(/\b(add|expense|spent|paid|payment|for|on|by|using|rupee|rupees)\b/gi, '')
      .trim()

    onExpenseFormChange('title', title)
    onExpenseFormChange('amount', amount)
    onExpenseFormChange('category', category)
    onExpenseFormChange('payment_method', paymentMethod)

    if (!amount) {
      setVoiceStatus('Amount not detected. Say: "Swiggy 250 UPI".')
      return
    }

    setVoiceStatus(`Saving ${category} expense for Rs. ${amount}...`)
    const saved = await onVoiceExpense?.({
      title: title || `${category} expense`,
      amount,
      category,
      payment_method: paymentMethod,
    })

    setVoiceStatus(
      saved
        ? `Voice expense added: ${category} Rs. ${amount}`
        : 'Voice expense could not be saved. Check the message below.'
    )

    console.log('Amount =', amount)
    console.log('Category =', category)
    console.log('Payment =', paymentMethod)
  }

  const startListening = () => {
    setVoiceStatus('')
    lastTranscriptRef.current = ''

    const SpeechRecognition =
    window.SpeechRecognition || window.webkitSpeechRecognition
    const recognition = SpeechRecognition ? new SpeechRecognition() : null

    if (!recognition) {
      setVoiceStatus('Voice is not supported in this browser. Please use Chrome.')
      return
    }

    if (recognitionRef.current) {
      recognitionRef.current.abort()
    }

    recognition.continuous = false
    recognition.interimResults = true
    recognition.lang = 'en-US'
    recognition.maxAlternatives = 5
    recognitionRef.current = recognition

    recognition.onresult = async (event) => {
      const results = Array.from(event.results)
      const transcripts = results
        .map((result) => {
          const alternatives = Array.from(result || [])
          const bestMatch = alternatives.find((item) => extractAmount(item.transcript)) || alternatives[0]
          return bestMatch?.transcript || ''
        })
        .filter(Boolean)

      const text = transcripts.join(' ').trim()
      if (text) {
        lastTranscriptRef.current = text
        setVoiceStatus(`Heard: ${text}`)
      }

      const hasFinalResult = results.some((result) => result.isFinal)
      if (hasFinalResult) {
        const finalTranscript = lastTranscriptRef.current
        lastTranscriptRef.current = ''
        recognition.stop()
        await saveVoiceExpense(finalTranscript)
      }
    }

    recognition.onstart = () => {
      setIsListening(true)
      setVoiceStatus('Listening in English... speak now')
    }

    recognition.onend = async () => {
      setIsListening(false)
      if (recognitionRef.current === recognition) {
        recognitionRef.current = null
      }

      if (lastTranscriptRef.current) {
        const finalTranscript = lastTranscriptRef.current
        lastTranscriptRef.current = ''
        await saveVoiceExpense(finalTranscript)
      }
    }

    recognition.onerror = (event) => {
      setIsListening(false)

      // "no-speech" and "aborted" are normal, expected outcomes (the mic
      // just didn't pick up any words, or the user stopped it) - not
      // real errors worth interrupting the user with a popup for.
      if (event.error === 'aborted') {
        return
      }

      if (event.error === 'no-speech') {
        setVoiceStatus('No speech detected. Say: "Swiggy 250 UPI".')
        return
      }

      console.error('Speech recognition error:', event.error)

      const friendlyMessages = {
        'not-allowed': 'Microphone access was blocked. Please allow microphone permission in your browser settings.',
        'audio-capture': 'No microphone was found. Please connect a microphone and try again.',
        'network': 'A network error interrupted voice recognition. Please try again.',
      }

      setVoiceStatus(friendlyMessages[event.error] || 'Voice recognition had a problem. Please try again.')
    }

    try {
      recognition.start()
    } catch (error) {
      console.error('Speech recognition start failed:', error)
      setIsListening(false)
      setVoiceStatus('Voice could not start. Please wait a second and try again.')
    }
  }

  const categories = Array.from(
    new Set(expenses.map((expense) => expense.category).filter(Boolean))
  )

  return (
    <>
      <form className="expense-form" onSubmit={onSubmit}>
        <div className="panel-heading compact">
          <div>
            <h2>{editingExpenseId ? 'Update expense' : 'Add expense'}</h2>
            <p className="panel-subtitle">Capture spending manually or by voice.</p>
          </div>
        </div>
        <button
          type="button"
          className="voice-btn"
          onClick={() => startListening()}
          disabled={isListening || loading}
        >
          {isListening ? 'Listening in English...' : 'Voice Expense'}
        </button>
        {voiceStatus && <p className="status">{voiceStatus}</p>}
        <div className="expense-input-grid">
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
            <option value="Grocery">Grocery/Household</option>
          </select>
          <input
            placeholder="Payment method"
            value={expenseForm.payment_method}
            onChange={(event) => onExpenseFormChange('payment_method', event.target.value)}
          />
        </div>
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
        <div className="expense-list-heading">
          <h2>Recent Expenses</h2>
          <button className="secondary-button" type="button" onClick={() => setShowExpenses(!showExpenses)}>
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
