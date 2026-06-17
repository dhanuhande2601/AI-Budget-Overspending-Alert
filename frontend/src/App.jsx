import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  apiRequest,
  downloadBudgetReport,
  downloadExcel,
  fetchDashboardData,
  getAuthHeaders,
  getCategoryBudgets,
  updateMonthlyBudget,
  updateIncomeSavings,
  updateProfile,
  getCategoryAlerts,
  getMonthlyInsights,
  getLatestExpenses,
  setCategoryBudgets,
  getRecommendations,
  getCategoryPredictions,
} from './api/budgetApi'

import AlertsTrendSection from './components/AlertsTrendSection'
import AuthScreen from './components/AuthScreen'
import DashboardHeader from './components/DashboardHeader'
import ExpenseSection from './components/ExpenseSection'
import Metrics from './components/Metrics'
import CategoryBudgetSetup from './components/CategoryBudgetSetup'
import LatestExpensesByCategory from './components/LatestExpensesByCategory'
import MonthlyInsights from './components/MonthlyInsights'
import ProfileModal from './components/ProfileModal'
import SMSExpense from './components/SMSExpense'
import CategoryPredictionsChart from './components/CategoryPredictionsChart'
import BudgetHistory from './components/BudgetHistory'
import RecurringExpenses from './components/RecurringExpenses'
import { getCurrencyRates } from './api/budgetApi'
import { displayAmount } from './utils/currencyHelper'
import {
  requestNotificationPermission,
  showBudgetNotification,
} from './utils/notificationHelper'
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

  // Use this everywhere instead of hardcoding ₹ — automatically
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
  const [newBudget, setNewBudget] = useState('')
  const [newIncome, setNewIncome] = useState('')
  const [newSavings, setNewSavings] = useState('')
  const [recommendations, setRecommendations] = useState(null)
  const [categoryPredictions, setCategoryPredictions] = useState(null)
  const [monthlyInsights, setMonthlyInsights] = useState(null)
  const [categoryBudgets, setCategoryBudgetsState] = useState([])
  const [categoryAlerts, setCategoryAlerts] = useState([])
  const [latestExpenses, setLatestExpenses] = useState([])
  const [categoryBudgetForm, setCategoryBudgetForm] = useState({
    food: '',
    travel: '',
    shopping: '',
    health: '',
    adventure: '',
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
  const pieData = analytics?.category_summary || []
  const hasBudget = monthlyBudget > 0
  const isBudgetExceeded = hasBudget && totalSpending > monthlyBudget
  const isBudgetWarning = hasBudget && !isBudgetExceeded && totalSpending >= monthlyBudget * 0.8
  const alertCount = alerts.length + categoryAlerts.length

  // Ask for notification permission once user logs in
  useEffect(() => {
    if (token) {
      requestNotificationPermission()
    }
  }, [token])

  // Trigger a browser notification when budget crosses 80% or is exceeded
  useEffect(() => {
    if (!hasBudget) return

    if (isBudgetExceeded) {
      showBudgetNotification(
        '🚨 Budget Exceeded!',
        `You've spent ₹${totalSpending.toLocaleString()} out of ₹${monthlyBudget.toLocaleString()}. Time to cut back.`,
        'budget-exceeded'
      )
    } else if (isBudgetWarning) {
      showBudgetNotification(
        '⚠️ Budget Alert — 80% Used',
        `You've used ₹${totalSpending.toLocaleString()} of your ₹${monthlyBudget.toLocaleString()} budget.`,
        'budget-warning'
      )
    }
  }, [isBudgetExceeded, isBudgetWarning, hasBudget, totalSpending, monthlyBudget])

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

      const [recoData, predData, insightsData] = await Promise.all([
        getRecommendations(token).catch(() => null),
        getCategoryPredictions(token).catch(() => null),
        getMonthlyInsights(token).catch(() => null),
      ])
      setRecommendations(recoData)
      setCategoryPredictions(predData)
      setMonthlyInsights(insightsData)
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

  const loadLatestExpenses = useCallback(async () => {
    try {
      const data = await getLatestExpenses(token)
      setLatestExpenses(
        Array.isArray(data) ? data : data?.expenses || []
      )
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
          loadLatestExpenses(),
          loadCategoryAlerts(),
        ])
      } catch (error) {
        console.log(error)
      }
    }

    initializeData()
    return () => { isCurrent = false }
  }, [token, refreshDashboard, loadCategoryBudgets, loadLatestExpenses, loadCategoryAlerts])

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

  const handleUpdateSavings = async (amount) => {
    try {
      const response = await apiRequest('/auth/update-budget', {
        method: 'PUT',
        headers: authHeaders,
        body: JSON.stringify({ monthly_savings: Number(amount) }),
      })
      if (response?.success) {
        await refreshDashboard()
      }
    } catch (error) {
      console.error('Savings update failed:', error)
    }
  }

  async function handleUpdateIncome() {
    try {
      await updateIncomeSavings(token, { monthly_income: Number(newIncome) })
      setMessage('Monthly income updated successfully')
      setNewIncome('')
      await refreshDashboard()
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

  async function handleBudgetUpdate() {
    try {
      await updateMonthlyBudget(token, Number(newBudget))
      await refreshDashboard()
      setMessage('Budget updated successfully')
      setNewBudget('')
    } catch (error) {
      setMessage(error.message)
    }
  }

  async function handleSaveExpense(event) {
    event.preventDefault()
    setLoading(true)
    setMessage('')
    try {
      const payload = { ...expenseForm, amount: Number(expenseForm.amount) }
      const path = editingExpenseId
        ? `/expense/update/${editingExpenseId}`
        : '/expense/add'
      const method = editingExpenseId ? 'PUT' : 'POST'
      await apiRequest(path, {
        method,
        headers: authHeaders,
        body: JSON.stringify(payload),
      })
      setMessage(editingExpenseId ? 'Expense updated successfully' : 'Expense added successfully')
      setExpenseForm(emptyExpense)
      setEditingExpenseId(null)
      await refreshDashboard()
      await loadLatestExpenses()
      await loadCategoryAlerts()
    } catch (error) {
      setMessage(error.message)
    } finally {
      setLoading(false)
    }
  }

  async function handleDeleteExpense(expenseId) {
    try {
      await apiRequest(`/expense/delete/${expenseId}`, {
        method: 'DELETE',
        headers: authHeaders,
      })
      await refreshDashboard()
      await loadLatestExpenses()
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

        <SMSExpense onExpenseAdded={refreshDashboard} token={token} />

        <RecurringExpenses token={token} />

        <MonthlyInsights data={monthlyInsights} />

        {categoryPredictions && (
          <CategoryPredictionsChart data={categoryPredictions} />
        )}

        <LatestExpensesByCategory
          data={latestExpenses}
          alerts={categoryAlerts}
        />

        <AlertsTrendSection
          alerts={[
            ...(alerts || []),
            ...(Array.isArray(categoryAlerts)
              ? categoryAlerts
              : categoryAlerts?.alerts || []),
          ]}
          analytics={analytics}
          isBudgetExceeded={isBudgetExceeded}
          isBudgetWarning={isBudgetWarning}
          trendData={trendData}
          weeklyTrendData={weeklyTrendData}
        />

        <BudgetHistory token={token} />
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