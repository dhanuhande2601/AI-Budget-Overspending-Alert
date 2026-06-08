function CategoryBudgetSetup({ form, setForm, onSave }) {
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
  ]

  return (
    <div className="card">
      <h2>Category Budgets</h2>

      {fields.map((field) => (
        <input
          key={field}
          type="number"
          placeholder={`${field.charAt(0).toUpperCase()}${field.slice(1)} Budget`}
          value={form[field] || ''}
          onChange={(e) => updateField(field, e.target.value)}
        />
      ))}

      <button onClick={onSave}>
        Save Budgets
      </button>
    </div>
  )
}

export default CategoryBudgetSetup