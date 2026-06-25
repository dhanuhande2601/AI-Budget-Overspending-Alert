import { useRef, useState } from 'react'
import { FiPlus } from 'react-icons/fi'
import { addVoiceExpense } from '../api/budgetApi'

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
  token,
}) {
  const [showExpenses, setShowExpenses] = useState(false)
  const [isListening, setIsListening] = useState(false)
  const [voiceStatus, setVoiceStatus] = useState('')
  const recognitionRef = useRef(null)
  const voiceTranscriptRef = useRef('')
  const voiceSaveStartedRef = useRef(false)
  const voiceTimeoutRef = useRef(null)
  const micStreamRef = useRef(null)
  const mediaRecorderRef = useRef(null)
  const audioChunksRef = useRef([])

  const paymentMethods = [
    { value: 'UPI', keywords: ['upi', 'u p i', 'google pay', 'gpay', 'phonepe', 'phone pay', 'paytm'] },
    { value: 'Card', keywords: ['card', 'credit card', 'debit card'] },
    { value: 'Net Banking', keywords: ['net banking', 'netbanking', 'neft', 'imps'] },
    { value: 'Cash', keywords: ['cash'] },
  ]

  const categoryKeywords = {
    Food: [
      'swiggy', 'zomato', 'restaurant', 'cafe', 'food', 'pizza', 'hotel',
      'tea', 'coffee', 'lunch', 'dinner', 'breakfast', 'snacks',
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
      'grocery', 'groceries', 'vegetables', 'vegetable', 'milk',
      'household', 'fruit', 'fruits', 'bread', 'rice',
    ],
  }

  const amountPattern = /(?:rs\.?|rupees?|inr|₹)?\s*([0-9][0-9,]*(?:\.[0-9]{1,2})?)\s*(?:rs\.?|rupees?|inr)?/i

  const extractAmount = (text) => {
    const match = text.match(amountPattern)
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
      ten: 10,
      eleven: 11,
      twelve: 12,
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
      thirty: 30,
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
      } else if (word === 'thousand') {
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

  const detectPaymentMethod = (text) => {
    const lower = text.toLowerCase()
    const match = paymentMethods.find((method) =>
      method.keywords.some((keyword) => lower.includes(keyword))
    )
    return match?.value || ''
  }

  const stripPaymentWords = (text) =>
    paymentMethods.reduce(
      (current, method) =>
        method.keywords.reduce(
          (value, keyword) => value.replace(new RegExp(`\\b${keyword.replace(/\s+/g, '\\s+')}\\b`, 'gi'), ''),
          current
        ),
      text
    )

  const extractTitle = (text) => {
    const withoutAmount = text.replace(amountPattern, ' ')
    const withoutPayment = stripPaymentWords(withoutAmount)
    const afterPreposition = withoutPayment.match(/\b(?:for|on|at|from)\s+(.+)$/i)?.[1] || withoutPayment

    return afterPreposition
      .replace(/\b(i|a|an|the|please|add|create|record|expense|spend|spent|pay|paid|payment|buy|bought|purchase|purchased|using|with|by|via|through|rupee|rupees|rs|inr)\b/gi, ' ')
      .replace(/[^a-z0-9\s&-]/gi, ' ')
      .replace(/\s+/g, ' ')
      .trim()
  }

  const saveVoiceExpense = async (text) => {
    if (voiceSaveStartedRef.current) return
    voiceSaveStartedRef.current = true

    const cleanText = (text || '').trim()
    if (!cleanText) {
      voiceSaveStartedRef.current = false
      setVoiceStatus('No speech detected. Please try again closer to the microphone.')
      return
    }

    console.log('VOICE =', cleanText)
    setVoiceStatus(`Heard: ${cleanText}`)

    const lower = cleanText.toLowerCase()
    const amount = extractAmount(cleanText)
    const category = detectCategory(cleanText)
    const paymentMethod = detectPaymentMethod(lower)
    const title = extractTitle(cleanText)

    onExpenseFormChange('title', title)
    onExpenseFormChange('amount', amount)
    onExpenseFormChange('category', category)
    onExpenseFormChange('payment_method', paymentMethod)

    if (!amount) {
      voiceSaveStartedRef.current = false
      setVoiceStatus('Amount not detected. Say: "I paid 250 for lunch using UPI".')
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

  const stopMicStream = () => {
    if (micStreamRef.current) {
      micStreamRef.current.getTracks().forEach((track) => track.stop())
      micStreamRef.current = null
    }
  }

  const clearVoiceTimeout = () => {
    if (voiceTimeoutRef.current) {
      window.clearTimeout(voiceTimeoutRef.current)
      voiceTimeoutRef.current = null
    }
  }

  const recordVoiceExpense = async () => {
    if (!navigator.mediaDevices?.getUserMedia || !window.MediaRecorder) {
      return false
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      micStreamRef.current = stream
      audioChunksRef.current = []

      const mimeType = MediaRecorder.isTypeSupported('audio/webm')
        ? 'audio/webm'
        : ''
      const recorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined)
      mediaRecorderRef.current = recorder

      recorder.ondataavailable = (event) => {
        if (event.data?.size > 0) {
          audioChunksRef.current.push(event.data)
        }
      }

      recorder.onstop = async () => {
        clearVoiceTimeout()
        stopMicStream()
        mediaRecorderRef.current = null

        const audioBlob = new Blob(audioChunksRef.current, {
          type: mimeType || 'audio/webm',
        })

        if (!audioBlob.size) {
          setIsListening(false)
          setVoiceStatus('No audio was recorded. Check microphone permission and try again.')
          return
        }

        try {
          setVoiceStatus('AI is adding your expense...')
          const data = await addVoiceExpense(token, audioBlob)
          const createdExpense = data?.expense || {}
          setIsListening(false)

          onExpenseFormChange('title', createdExpense.title || '')
          onExpenseFormChange('amount', createdExpense.amount || '')
          onExpenseFormChange('category', createdExpense.category || '')
          onExpenseFormChange('payment_method', createdExpense.payment_method || '')

          await onVoiceExpense?.({
            alreadySaved: true,
            expense: createdExpense,
          })

          setVoiceStatus(
            data?.transcript
              ? `Voice expense added: ${createdExpense.category} Rs. ${createdExpense.amount}. Heard: ${data.transcript}`
              : `Voice expense added: ${createdExpense.category} Rs. ${createdExpense.amount}`
          )
        } catch (error) {
          setIsListening(false)
          setVoiceStatus(error.message || 'Voice transcription failed. Please try again.')
        }
      }

      setIsListening(true)
      setVoiceStatus('Recording for 6 seconds... say: "I paid 250 for lunch using UPI"')
      recorder.start()

      voiceTimeoutRef.current = window.setTimeout(() => {
        if (mediaRecorderRef.current?.state === 'recording') {
          mediaRecorderRef.current.stop()
        }
      }, 6000)

      return true
    } catch (error) {
      console.error('Audio recording failed:', error)
      stopMicStream()
      setIsListening(false)
      setVoiceStatus('Microphone is blocked. Allow mic permission, then click Voice Expense again.')
      return true
    }
  }

  const startListening = async () => {
    setVoiceStatus('')
    voiceTranscriptRef.current = ''
    voiceSaveStartedRef.current = false

    const didStartRecording = await recordVoiceExpense()
    if (didStartRecording) return

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

    if (navigator.mediaDevices?.getUserMedia) {
      try {
        micStreamRef.current = await navigator.mediaDevices.getUserMedia({
          audio: {
            echoCancellation: true,
            noiseSuppression: true,
            autoGainControl: true,
          },
        })
      } catch (error) {
        console.error('Microphone permission failed:', error)
        setVoiceStatus('Microphone is blocked. Allow mic permission, then click Voice Expense again.')
        return
      }
    }

    recognition.continuous = true
    recognition.interimResults = true
    recognition.maxAlternatives = 3
    recognition.lang = 'en-IN'
    recognitionRef.current = recognition

    recognition.onresult = async (event) => {
      let transcript = ''
      let hasFinalResult = false

      for (let index = 0; index < event.results.length; index += 1) {
        const result = event.results[index]
        transcript += `${result?.[0]?.transcript || ''} `
        if (result?.isFinal) {
          hasFinalResult = true
        }
      }

      const cleanTranscript = transcript.trim()
      if (cleanTranscript) {
        voiceTranscriptRef.current = cleanTranscript
        setVoiceStatus(`Heard: ${cleanTranscript}`)
      }

      if (hasFinalResult && cleanTranscript) {
        clearVoiceTimeout()
        recognition.stop()
        await saveVoiceExpense(cleanTranscript)
      }
    }

    recognition.onstart = () => {
      setIsListening(true)
      setVoiceStatus('Listening for 10 seconds... say: "I paid 250 for lunch using UPI"')
      voiceTimeoutRef.current = window.setTimeout(() => {
        if (recognitionRef.current === recognition) {
          recognition.stop()
        }
      }, 10000)
    }

    recognition.onend = async () => {
      clearVoiceTimeout()
      setIsListening(false)
      if (recognitionRef.current === recognition) {
        recognitionRef.current = null
      }
      stopMicStream()

      if (!voiceSaveStartedRef.current && voiceTranscriptRef.current) {
        await saveVoiceExpense(voiceTranscriptRef.current)
      }
    }

    recognition.onerror = (event) => {
      setIsListening(false)
      clearVoiceTimeout()

      // "no-speech" and "aborted" are normal, expected outcomes (the mic
      // just didn't pick up any words, or the user stopped it) - not
      // real errors worth interrupting the user with a popup for.
      if (event.error === 'aborted') {
        stopMicStream()
        return
      }

      if (event.error === 'no-speech') {
        if (!voiceTranscriptRef.current) {
          setVoiceStatus('No voice detected. Keep the mic close and speak after the Listening message appears.')
        }
        return
      }

      stopMicStream()
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
      stopMicStream()
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
          {isListening ? 'Listening...' : 'Voice Expense'}
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
