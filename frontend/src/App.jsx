import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  apiRequest,
  downloadBudgetReport,
  downloadExcel,
  fetchDashboardData,
  getAuthHeaders,
  getCategoryBudgets,
  updateIncomeSavings,
  updateProfile,
  getCategoryAlerts,
  getCategoryPredictions,
} from './api/budgetApi'

import AlertsTrendSection from './components/AlertsTrendSection'
import AICoachPanel from './components/AICoachPanel'
import AuthScreen from './components/AuthScreen'
import DashboardHeader from './components/DashboardHeader'
import ExpenseSection from './components/ExpenseSection'
import Metrics from './components/Metrics'
import CategoryBudgetSetup from './components/CategoryBudgetSetup'
import LatestExpensesByCategory from './components/LatestExpensesByCategory'
import ProfileModal from './components/ProfileModal'
import CategoryPredictionsChart from './components/CategoryPredictionsChart'
import BudgetHistory from './components/BudgetHistory'
import FinancialIntelligenceReport from './components/FinancialIntelligenceReport'
import RecurringExpenses from './components/RecurringExpenses'
import { getCurrencyRates } from './api/budgetApi'
import { displayAmount } from './utils/currencyHelper'
import './App.css'

const emptyAuth = {
  name: '',
  email: '',
  password: '',
  phone: '',
  monthly_income: '',
  monthly_savings: '',
}

const emptyExpense = {
  title: '',
  amount: '',
  category: '',
  payment_method: '',
}

const emptyAnalytics = {
  total_spending: 0,
  category_summary: [],
  predicted_spending: 0,
}

function App() {
  const [token, setToken] = useState(
    () => localStorage.getItem('budget_token') || ''
  )

  const [darkMode, setDarkMode] = useState(
    () => localStorage.getItem('dark_mode') === 'true'
  )

  useEffect(() => {
    document.body.classList.toggle('dark', darkMode)
    localStorage.setItem('dark_mode', darkMode)
  }, [darkMode])

  const toggleDarkMode = () => setDarkMode(prev => !prev)

  const [currencyRates, setCurrencyRates] = useState(null)

  useEffect(() => {
    if (!token) return
    getCurrencyRates(token)
      .then((data) => setCurrencyRates(data?.rates || null))
      .catch((error) => console.log('Currency rates fetch error:', error))
  }, [token])

  const [mode, setMode] = useState('login')
  const [authForm, setAuthForm] = useState(emptyAuth)
  const [expenseForm, setExpenseForm] = useState(emptyExpense)
  const [editingExpenseId, setEditingExpenseId] = useState(null)
  const [user, setUser] = useState(null)

  // Use this everywhere instead of hardcoding currency symbols. It automatically
  // converts from INR (stored value) into the user's chosen currency.
  const formatAmount = useCallback(
    (amountInINR) => displayAmount(amountInINR, user?.currency || 'INR', currencyRates),
    [user?.currency, currencyRates]
  )
  const [expenses, setExpenses] = useState([])
  const [analytics, setAnalytics] = useState(emptyAnalytics)
  const [alerts, setAlerts] = useState([])
  const [message, setMessage] = useState('')
  const [loading, setLoading] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')
  const [categoryFilter, setCategoryFilter] = useState('')
  const [showCategoryBudget, setShowCategoryBudget] = useState(false)
  const [showProfile, setShowProfile] = useState(false)
  const [categoryPredictions, setCategoryPredictions] = useState(null)
  const [categoryBudgets, setCategoryBudgetsState] = useState([])
  const [categoryAlerts, setCategoryAlerts] = useState([])
  const [categoryBudgetForm, setCategoryBudgetForm] = useState({
    food: '',
    travel: '',
    shopping: '',
    health: '',
    adventure: '',
    loan: '',
    bills: '',
    grocery: '',
  })

  const authHeaders = useMemo(
    () => getAuthHeaders(token),
    [token]
  )

  const filteredExpenses = useMemo(
    () =>
      expenses.filter((expense) => {
        const matchesSearch = (expense.title || '')
          .toLowerCase()
          .includes(searchTerm.toLowerCase())
        const matchesCategory =
          !categoryFilter ||
          expense.category === categoryFilter
        return matchesSearch && matchesCategory
      }),
    [expenses, searchTerm, categoryFilter]
  )

  const trendData = useMemo(() => {
    const monthlyData = {}
    expenses.forEach((expense) => {
      const date = new Date(expense.created_at)
      const key = `${date.getFullYear()}-${date.getMonth()}`
      const label = date.toLocaleString('default', { month: 'short', year: '2-digit' })
      if (!monthlyData[key]) monthlyData[key] = { label, amount: 0, sortKey: key }
      monthlyData[key].amount += Number(expense.amount || 0)
    })
    return Object.values(monthlyData)
      .sort((a, b) => a.sortKey.localeCompare(b.sortKey))
      .map(({ label, amount }) => ({ month: label, amount }))
  }, [expenses])

  const weeklyTrendData = useMemo(() => {
    // ISO-week-of-year, paired with year, so weeks never merge across years.
    // We also compute the Monday of that week to show a readable date range
    // instead of a confusing "W24 '26" style label.
    function getWeekInfo(date) {
      const tempDate = new Date(date.getFullYear(), date.getMonth(), date.getDate())
      const dayNum = (tempDate.getDay() + 6) % 7 // Monday = 0
      const mondayOfWeek = new Date(tempDate)
      mondayOfWeek.setDate(tempDate.getDate() - dayNum)

      tempDate.setDate(tempDate.getDate() - dayNum + 3)
      const firstThursday = new Date(tempDate.getFullYear(), 0, 4)
      const weekNumber =
        1 +
        Math.round(
          ((tempDate - firstThursday) / 86400000 - 3 + ((firstThursday.getDay() + 6) % 7)) / 7
        )
      return { year: tempDate.getFullYear(), week: weekNumber, mondayOfWeek }
    }

    const weeklyData = {}
    expenses.forEach((expense) => {
      const date = new Date(expense.created_at)
      const { year, week, mondayOfWeek } = getWeekInfo(date)
      const key = `${year}-W${week}`
      // e.g. "Jun 8-14" — much clearer than a raw week number
      const sundayOfWeek = new Date(mondayOfWeek)
      sundayOfWeek.setDate(mondayOfWeek.getDate() + 6)
      const startLabel = mondayOfWeek.toLocaleString('default', { month: 'short', day: 'numeric' })
      const endLabel = sundayOfWeek.getDate()
      const label = `${startLabel}-${endLabel}`

      if (!weeklyData[key]) weeklyData[key] = { label, amount: 0, sortKey: key }
      weeklyData[key].amount += Number(expense.amount || 0)
    })

    return Object.values(weeklyData)
      .sort((a, b) => a.sortKey.localeCompare(b.sortKey))
      .slice(-12) // last 12 weeks, otherwise the chart gets unreadable
      .map(({ label, amount }) => ({ week: label, amount }))
  }, [expenses])

  const totalSpending = Number(analytics?.total_spending || 0)
  const monthlyBudget = Number(user?.available_budget || user?.monthly_budget || 0)
  const hasBudget = monthlyBudget > 0
  const isBudgetExceeded = hasBudget && totalSpending > monthlyBudget
  const isBudgetWarning = hasBudget && !isBudgetExceeded && totalSpending >= monthlyBudget * 0.8
  const alertCount = alerts.length + categoryAlerts.length

  const updateDashboard = useCallback((dashboardData) => {
    setUser(dashboardData?.user || null)
    setExpenses(dashboardData?.expenses || [])
    setAnalytics(dashboardData?.analytics || emptyAnalytics)
    setAlerts(dashboardData?.alerts || [])
    setCategoryBudgetsState(dashboardData?.category_budgets || [])
  }, [])

  const refreshDashboard = useCallback(async () => {
    if (!token) return
    try {
      const data = await fetchDashboardData(token)
      updateDashboard(data)

      const predData = await getCategoryPredictions(token).catch(() => null)
      setCategoryPredictions(predData)
    } catch (error) {
      console.log('Dashboard refresh error:', error)
    }
  }, [token, updateDashboard])

  const loadCategoryAlerts = useCallback(async () => {
    try {
      const data = await getCategoryAlerts(token)
      setCategoryAlerts(
        Array.isArray(data) ? data : data?.alerts || []
      )
    } catch (error) {
      console.log(error)
    }
  }, [token])

  const loadCategoryBudgets = useCallback(async () => {
    try {
      const data = await getCategoryBudgets(token)
      setCategoryBudgetsState(data || [])
      const formData = {
        food: '',
        travel: '',
        shopping: '',
        health: '',
        adventure: '',
        loan: '',
        bills: '',
        grocery: '',
      }
      if (Array.isArray(data)) {
        data.forEach((item) => {
          formData[item.category] = item.monthly_limit
        })
      }
      setCategoryBudgetForm(formData)
    } catch (error) {
      console.log(error)
    }
  }, [token])

  useEffect(() => {
    if (!token) return
    let isCurrent = true

    async function initializeData() {
      try {
        await refreshDashboard()
        if (!isCurrent) return
        await Promise.all([
          loadCategoryBudgets(),
          loadCategoryAlerts(),
        ])
      } catch (error) {
        console.log(error)
      }
    }

    initializeData()
    return () => { isCurrent = false }
  }, [token, refreshDashboard, loadCategoryBudgets, loadCategoryAlerts])

  function updateAuthForm(field, value) {
    setAuthForm((currentForm) => ({ ...currentForm, [field]: value }))
  }

  function updateExpenseForm(field, value) {
    setExpenseForm((currentForm) => ({ ...currentForm, [field]: value }))
  }

  async function handleAuth(event) {
    event.preventDefault()
    setLoading(true)
    setMessage('')
    try {
      const endpoint = mode === 'login' ? '/auth/login' : '/auth/register'
      const payload =
        mode === 'login'
          ? { email: authForm.email, password: authForm.password }
          : {
              name: authForm.name,
              email: authForm.email,
              password: authForm.password,
              phone: authForm.phone,
              monthly_income: Number(authForm.monthly_income || 0),
              monthly_savings: Number(authForm.monthly_savings || 0),
            }
      const data = await apiRequest(endpoint, {
        method: 'POST',
        body: JSON.stringify(payload),
      })
      if (mode === 'register') {
        setMode('login')
        setMessage('Account created successfully')
        return
      }
      localStorage.setItem('budget_token', data.token)
      setToken(data.token)
      setUser(data.user)
      setAuthForm(emptyAuth)
    } catch (error) {
      setMessage(error.message)
    } finally {
      setLoading(false)
    }
  }

  async function saveCategoryBudgets() {
    try {
      await apiRequest('/category-budget/set', {
        method: 'POST',
        headers: authHeaders,
        body: JSON.stringify(categoryBudgetForm),
      })
      setMessage('Category budgets saved')
      setShowCategoryBudget(false)
    } catch (error) {
      setMessage(error.message)
    }
  }

  async function handleUpdateProfile(profileData) {
    try {
      await updateProfile(token, {
        name: profileData.name,
        email: profileData.email,
        phone: profileData.phone,
        profile_photo: profileData.profile_photo,
        currency: profileData.currency,
      })
      // Income/savings go through a separate endpoint
      await updateIncomeSavings(token, {
        monthly_income: profileData.monthly_income,
        monthly_savings: profileData.monthly_savings,
      })
      setMessage('Profile updated successfully')
      await refreshDashboard()
    } catch (error) {
      setMessage(error.message)
    }
  }

  async function handleUpdateCategoryBudgets(budgets) {
    try {
      const budgetData = {}
      budgets.forEach((b) => { budgetData[b.category] = b.monthly_limit })
      await apiRequest('/category-budget/set', {
        method: 'POST',
        headers: authHeaders,
        body: JSON.stringify(budgetData),
      })
      setMessage('Category budgets updated successfully')
      await loadCategoryBudgets()
    } catch (error) {
      setMessage(error.message)
    }
  }

  async function handleLoadProfile() {
    setShowProfile(true)
  }

  async function saveExpense(payloadOverride = null, options = {}) {
    setLoading(true)
    setMessage('')
    try {
      const forceCreate = Boolean(options.forceCreate)
      const source = payloadOverride || expenseForm
      const payload = { ...source, amount: Number(source.amount) }
      const shouldUpdate = editingExpenseId && !forceCreate
      const path = shouldUpdate
        ? `/expense/update/${editingExpenseId}`
        : '/expense/add'
      const method = shouldUpdate ? 'PUT' : 'POST'
      await apiRequest(path, {
        method,
        headers: authHeaders,
        body: JSON.stringify(payload),
      })
      setMessage(shouldUpdate ? 'Expense updated successfully' : 'Expense added successfully')
      setExpenseForm(emptyExpense)
      setEditingExpenseId(null)
      await refreshDashboard()
      await loadCategoryAlerts()
      return true
    } catch (error) {
      setMessage(error.message)
      return false
    } finally {
      setLoading(false)
    }
  }

  async function handleSaveExpense(event) {
    event.preventDefault()
    await saveExpense()
  }

  async function handleDeleteExpense(expenseId) {
    try {
      await apiRequest(`/expense/delete/${expenseId}`, {
        method: 'DELETE',
        headers: authHeaders,
      })
      await refreshDashboard()
      await loadCategoryAlerts()
      setMessage('Expense deleted successfully')
    } catch (error) {
      setMessage(error.message)
    }
  }

  function startEditingExpense(expense) {
    setExpenseForm({
      title: expense.title,
      amount: expense.amount,
      category: expense.category,
      payment_method: expense.payment_method || '',
    })
    setEditingExpenseId(expense.id)
  }

  async function handleDownloadReport() {
    try {
      await downloadBudgetReport(token)
    } catch (error) {
      setMessage(error.message)
    }
  }

  async function handleDownloadExcel() {
    try {
      await downloadExcel(token)
    } catch (error) {
      setMessage(error.message)
    }
  }

  function logout() {
    localStorage.removeItem('budget_token')
    setToken('')
    setUser(null)
    setExpenses([])
    setAlerts([])
    setAnalytics(emptyAnalytics)
    setCategoryBudgetsState([])
    setCategoryAlerts([])
  }

  if (!token) {
    return (
      <AuthScreen
        authForm={authForm}
        loading={loading}
        message={message}
        mode={mode}
        onAuthFormChange={updateAuthForm}
        onModeChange={setMode}
        onSubmit={handleAuth}
      />
    )
  }

  return (
    <main className="app-shell">
      {showCategoryBudget && (
        <CategoryBudgetSetup
          form={categoryBudgetForm}
          setForm={setCategoryBudgetForm}
          onSave={saveCategoryBudgets}
        />
      )}
      <DashboardHeader
        analytics={analytics}
        darkMode={darkMode}
        formatAmount={formatAmount}
        onDownloadReport={handleDownloadReport}
        onDownloadExcel={handleDownloadExcel}
        onLogout={logout}
        onProfileClick={handleLoadProfile}
        onToggleDark={toggleDarkMode}
        user={user}
      />

      <Metrics
        alertCount={alertCount}
        analytics={analytics}
        formatAmount={formatAmount}
        isBudgetExceeded={isBudgetExceeded}
        isBudgetWarning={isBudgetWarning}
        monthlyBudget={monthlyBudget}
        totalSpending={totalSpending}
      />

      <section className="workspace">
        <div className="workspace-main">
          <ExpenseSection
            categoryFilter={categoryFilter}
            editingExpenseId={editingExpenseId}
            expenseForm={expenseForm}
            expenses={expenses}
            filteredExpenses={filteredExpenses}
            loading={loading}
            message={message}
            onCategoryFilterChange={setCategoryFilter}
            onDeleteExpense={handleDeleteExpense}
            onExpenseFormChange={updateExpenseForm}
            onSearchChange={setSearchTerm}
            onStartEdit={startEditingExpense}
            onSubmit={handleSaveExpense}
            searchTerm={searchTerm}
          />
        </div>

        <aside className="workspace-side">
          <RecurringExpenses token={token} />

          {categoryPredictions && (
            <CategoryPredictionsChart data={categoryPredictions} />
          )}
        </aside>

        <LatestExpensesByCategory
          data={expenses}
          alerts={categoryAlerts}
        />

        <div className="workspace-main workspace-full">
          <AlertsTrendSection
            alerts={(() => {
              const richAlerts = Array.isArray(categoryAlerts)
                ? categoryAlerts
                : categoryAlerts?.alerts || []

              const coveredCategories = new Set(
                richAlerts.map((a) => (a.category || '').toLowerCase())
              )

              const simpleAlerts = (alerts || []).filter(
                (a) => !coveredCategories.has((a.category || '').toLowerCase())
              )

              return [...simpleAlerts, ...richAlerts]
            })()}
            analytics={analytics}
            isBudgetExceeded={isBudgetExceeded}
            isBudgetWarning={isBudgetWarning}
            trendData={trendData}
            weeklyTrendData={weeklyTrendData}
          />

          <BudgetHistory token={token} />

          <div className="financial-ai-grid">
            <AICoachPanel
              formatAmount={formatAmount}
              token={token}
            />
            <FinancialIntelligenceReport token={token} />
          </div>
        </div>
      </section>

      {showProfile && (
        <ProfileModal
          user={user}
          categoryBudgets={categoryBudgets}
          formatAmount={formatAmount}
          onClose={() => setShowProfile(false)}
          onUpdateProfile={handleUpdateProfile}
          onUpdateCategoryBudgets={handleUpdateCategoryBudgets}
        />
      )}
    </main>
  )
}

export default App
