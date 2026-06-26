function CategoryBudgetSetup({
  form,
  isOnboarding = false,
  onSave,
  onSkip,
  setForm,
}) {
  const updateField = (field, value) =>
    setForm((prev) => ({
      ...prev,
      [field]: value,
    }))

  const fields = [
    'food',
    'travel',
    'shopping',
    'health',
    'adventure',
    'loan',
    'bills',
    'grocery',
  ]

  const labels = {
    loan: 'Loan/EMI',
    grocery: 'Grocery/Household',
  }

  return (
    <div className={`card category-budget-setup ${isOnboarding ? 'onboarding-card' : ''}`}>
      <div className="panel-heading compact">
        <div>
          <p className="eyebrow">AI Budget Overspending Alert</p>
          <h2>Set Category Budgets</h2>
          {isOnboarding && (
            <p className="muted">
              Add limits for each category before opening your dashboard.
            </p>
          )}
        </div>
      </div>

      {fields.map((field) => {
        const label = labels[field] || (field.charAt(0).toUpperCase() + field.slice(1))
        return (
          <input
            key={field}
            type="number"
            placeholder={`${label} Budget`}
            value={form[field] || ''}
            onChange={(e) => updateField(field, e.target.value)}
          />
        )
      })}

      <div className="category-budget-actions">
        {isOnboarding && (
          <button
            className="secondary-button"
            onClick={onSkip}
            type="button"
          >
            Skip
          </button>
        )}
        <button onClick={onSave} type="button">
          Save Budgets
        </button>
      </div>
    </div>
  )
}

export default CategoryBudgetSetup
