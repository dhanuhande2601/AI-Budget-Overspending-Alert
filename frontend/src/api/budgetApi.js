
export const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:5000/api'
export function getAuthHeaders(token) {
  return {
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  }
}
 
export async function apiRequest(path, options = {}) {
  const headers = {
    ...(options.headers || {}),
  }
 
  if (options.body && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json'
  }
 
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  })
 
  const data = await response.json().catch(() => ({}))
 
  if (!response.ok) {
    throw new Error(data.message || 'Request failed')
  }
 
  return data
}
 
/* =========================
   DASHBOARD
========================= */
 
export async function fetchDashboardData(token) {
  if (!token) return null
 
  const headers = getAuthHeaders(token)
 
  const [
    profileData,
    expenseData,
    analyticsData,
    alertData,
  ] = await Promise.all([
    apiRequest('/auth/profile', { headers }),
    apiRequest('/expense/all', { headers }),
    apiRequest('/ai/dashboard-analytics', { headers }),
    apiRequest('/ai/overspending-alerts', { headers }),
  ])
 
  return {
    user: profileData,
    expenses: expenseData.expenses || [],
    analytics: analyticsData,
    alerts: alertData.alerts || [],
  }
}
 
/* =========================
   DOWNLOADS
========================= */
 
async function downloadFile(
  endpoint,
  filename,
  token
) {
  const response = await fetch(
    `${API_BASE}${endpoint}`,
    {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  )
 
  if (!response.ok) {
    throw new Error(
      `Failed to download ${filename}`
    )
  }
 
  const blob = await response.blob()
 
  const url =
    window.URL.createObjectURL(blob)
 
  const a =
    document.createElement('a')
 
  a.href = url
  a.download = filename
 
  document.body.appendChild(a)
 
  a.click()
 
  a.remove()
 
  window.URL.revokeObjectURL(url)
}
 
export async function downloadBudgetReport(
  token
) {
  return downloadFile(
    '/report/download',
    'budget_report.pdf',
    token
  )
}
 
export async function downloadExcel(
  token
) {
  return downloadFile(
    '/report/excel',
    'expenses.xlsx',
    token
  )
}
 
/* =========================
   AI / ANALYTICS
========================= */
 
export async function getMonthlyInsights(
  token
) {
  return apiRequest(
    '/ai/monthly-insights',
    {
      headers:
        getAuthHeaders(token),
    }
  )
}
 
export async function getCategoryPredictions(token) {
  return apiRequest('/ai/category-predictions', {
    method: 'GET',
    headers: getAuthHeaders(token)
  })
}
 
export async function getRecommendations(token) {
  return apiRequest('/ai/recommendations', {
    method: 'GET',
    headers: getAuthHeaders(token)
  })
}

export async function getFinancialReport(token) {
  return apiRequest('/ai/financial-report', {
    method: 'GET',
    headers: getAuthHeaders(token)
  })
}
/* =========================
   EXPENSES
========================= */
 
export async function getLatestExpenses(
  token
) {
  return apiRequest(
    '/expense/latest',
    {
      headers:
        getAuthHeaders(token),
    }
  )
}
 
export async function getLatestByCategory(
  token
) {
  return apiRequest(
    '/expense/latest-by-category',
    {
      headers:
        getAuthHeaders(token),
    }
  )
}
 
export async function getCategoryHistory(
  token
) {
  return apiRequest(
    '/expense/category-history',
    {
      headers:
        getAuthHeaders(token),
    }
  )
}
 
/* =========================
   CATEGORY BUDGETS
========================= */
 
export async function getCategoryBudgets(
  token
) {
  return apiRequest(
    '/category-budget/all',
    {
      headers:
        getAuthHeaders(token),
    }
  )
}
 
export async function getCategoryAlerts(
  token
) {
  return apiRequest(
    '/category-budget/alerts',
    {
      headers:
        getAuthHeaders(token),
    }
  )
}
 
export async function getCategoryBudgetAlerts(token) {
  return apiRequest('/category-budget/alerts', {
    method: 'GET',
    headers: getAuthHeaders(token)
  })
}
 
/* =========================
   USER
========================= */
 
export async function updateMonthlyBudget(
  token,
  monthlyBudget
) {
  return apiRequest(
    '/auth/update-budget',
    {
      method: 'PUT',
      headers:
        getAuthHeaders(token),
      body: JSON.stringify({
        monthly_budget:
          monthlyBudget,
      }),
    }
  )
}
 
export async function updateIncomeSavings(
  token,
  payload
) {
  return apiRequest(
    '/auth/update-budget',
    {
      method: 'PUT',
      headers: getAuthHeaders(token),
      body: JSON.stringify(payload),
    }
  )
}
 
export async function updateProfile(
  token,
  profileData
) {
  return apiRequest(
    '/auth/update-profile',
    {
      method: 'PUT',
      headers: getAuthHeaders(token),
      body: JSON.stringify(profileData),
    }
  )
}
 
export async function setCategoryBudgets(
  token,
  budgetData
) {
  return apiRequest(
    '/category-budget/set',
    {
      method: 'POST',
      headers: getAuthHeaders(token),
      body: JSON.stringify(budgetData),
    }
  )
}
// SMS Expense - Preview
export async function previewSMSExpense(smsText, token) {
  return apiRequest('/expense/sms/preview', {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ sms_text: smsText })
  })
}
 
// SMS Expense - Confirm & Save
export async function addSMSExpense(smsText, token) {
  return apiRequest('/expense/sms/add', {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ sms_text: smsText })
  })
}
 
// Budget History - get all month-wise records
export async function getBudgetHistory(token) {
  return apiRequest('/budget-history/all', {
    method: 'GET',
    headers: getAuthHeaders(token),
  })
}
 
// Budget History - get summary stats for charts
export async function getBudgetHistorySummary(token) {
  return apiRequest('/budget-history/summary', {
    method: 'GET',
    headers: getAuthHeaders(token),
  })
}
 
// Budget History - manually save current month snapshot
export async function saveBudgetSnapshot(token) {
  return apiRequest('/budget-history/snapshot', {
    method: 'POST',
    headers: getAuthHeaders(token),
  })
}
 
// Recurring Expense - get all
export async function getRecurringExpenses(token) {
  return apiRequest('/recurring-expense/all', {
    method: 'GET',
    headers: getAuthHeaders(token),
  })
}
 
// Recurring Expense - add new
export async function addRecurringExpense(token, payload) {
  return apiRequest('/recurring-expense/add', {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify(payload),
  })
}
 
// Recurring Expense - toggle active/paused
export async function toggleRecurringExpense(token, id) {
  return apiRequest(`/recurring-expense/toggle/${id}`, {
    method: 'PUT',
    headers: getAuthHeaders(token),
  })
}
 
// Recurring Expense - delete
export async function deleteRecurringExpense(token, id) {
  return apiRequest(`/recurring-expense/delete/${id}`, {
    method: 'DELETE',
    headers: getAuthHeaders(token),
  })
}
 
// Currency - get live exchange rates (base INR)
export async function getCurrencyRates(token) {
  return apiRequest('/auth/currency-rates', {
    method: 'GET',
    headers: getAuthHeaders(token),
  })
}
