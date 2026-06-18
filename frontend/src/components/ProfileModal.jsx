import { useState } from 'react'
import { FiX, FiCamera } from 'react-icons/fi'
import { CURRENCY_LABELS } from '../utils/currencyHelper'

function ProfileModal({
  user = {},
  categoryBudgets = [],
  formatAmount,
  onClose,
  onUpdateProfile,
  onUpdateCategoryBudgets,
}) {
  const [editMode, setEditMode] = useState(false)
  const [editForm, setEditForm] = useState({
    name: user?.name || '',
    email: user?.email || '',
    phone: user?.phone || '',
    monthly_income: user?.monthly_income || '',
    monthly_savings: user?.monthly_savings || '',
    currency: user?.currency || 'INR',
  })
  const [categoryForm, setCategoryForm] = useState(
    categoryBudgets.reduce((acc, cat) => ({
      ...acc,
      [cat.category]: cat.monthly_limit,
    }), {})
  )
  const [profilePhoto, setProfilePhoto] = useState(null)
  const [photoPreview, setPhotoPreview] = useState(user?.profile_photo || null)

  const money = formatAmount || ((amt) => `₹${Number(amt || 0).toLocaleString()}`)

  const handlePhotoChange = (e) => {
    const file = e.target.files?.[0]
    if (file) {
      setProfilePhoto(file)
      const reader = new FileReader()
      reader.onload = (event) => {
        setPhotoPreview(event.target?.result)
      }
      reader.readAsDataURL(file)
    }
  }

  const handleEditChange = (field, value) => {
    setEditForm((prev) => ({
      ...prev,
      [field]: value,
    }))
  }

  const handleCategoryChange = (category, value) => {
    setCategoryForm((prev) => ({
      ...prev,
      [category]: value,
    }))
  }

  const handleSaveProfile = async () => {
    try {
      await onUpdateProfile({
        ...editForm,
        monthly_income: Number(editForm.monthly_income),
        monthly_savings: Number(editForm.monthly_savings),
        profile_photo: photoPreview,
      })
      setEditMode(false)
    } catch (error) {
      console.error('Error updating profile:', error)
    }
  }

  const handleSaveCategoryBudgets = async () => {
    try {
      const budgets = Object.entries(categoryForm).map(([category, limit]) => ({
        category,
        monthly_limit: Number(limit),
      }))
      await onUpdateCategoryBudgets(budgets)
    } catch (error) {
      console.error('Error updating category budgets:', error)
    }
  }

  const income = Number(user?.monthly_income || 0)
  const savings = Number(user?.monthly_savings || 0)
  const availableBudget = Number(user?.available_budget || 0)

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content profile-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>My Profile</h2>
          <button className="icon-button close-btn" onClick={onClose}>
            <FiX />
          </button>
        </div>

        <div className="modal-body profile-body">
          {/* Profile Photo Section */}
          <div className="profile-photo-section">
            <div className="profile-photo">
              {photoPreview ? (
                <img src={photoPreview} alt="Profile" />
              ) : (
                <div className="photo-placeholder">
                  <FiCamera />
                </div>
              )}
            </div>
            {editMode && (
              <label className="photo-upload-label">
                <FiCamera /> Change Photo
                <input
                  type="file"
                  accept="image/*"
                  onChange={handlePhotoChange}
                  style={{ display: 'none' }}
                />
              </label>
            )}
          </div>

          {/* Personal Info Section */}
          <div className="profile-section">
            <h3>Personal Information</h3>
            <div className="profile-info-grid">
              <div className="info-block">
                <label>Name</label>
                {editMode ? (
                  <input
                    type="text"
                    value={editForm.name}
                    onChange={(e) => handleEditChange('name', e.target.value)}
                  />
                ) : (
                  <p>{user?.name}</p>
                )}
              </div>

              <div className="info-block">
                <label>Email</label>
                {editMode ? (
                  <input
                    type="email"
                    value={editForm.email}
                    onChange={(e) => handleEditChange('email', e.target.value)}
                  />
                ) : (
                  <p>{user?.email}</p>
                )}
              </div>

              <div className="info-block">
                <label>Phone</label>
                {editMode ? (
                  <input
                    type="tel"
                    value={editForm.phone}
                    onChange={(e) => handleEditChange('phone', e.target.value)}
                  />
                ) : (
                  <p>{user?.phone || '-'}</p>
                )}
              </div>

              <div className="info-block">
                <label>Preferred Currency</label>
                {editMode ? (
                  <select
                    value={editForm.currency}
                    onChange={(e) => handleEditChange('currency', e.target.value)}
                  >
                    {Object.entries(CURRENCY_LABELS).map(([code, label]) => (
                      <option key={code} value={code}>{label}</option>
                    ))}
                  </select>
                ) : (
                  <p>{CURRENCY_LABELS[user?.currency || 'INR']}</p>
                )}
              </div>
            </div>
          </div>

          {/* Financial Info Section */}
          <div className="profile-section">
            <h3>Financial Information</h3>
            <div className="profile-info-grid">
              <div className="info-block">
                <label>Monthly Income</label>
                {editMode ? (
                  <input
                    type="number"
                    value={editForm.monthly_income}
                    onChange={(e) => handleEditChange('monthly_income', e.target.value)}
                  />
                ) : (
                  <p>{money(income)}</p>
                )}
              </div>

              <div className="info-block">
                <label>Monthly Savings</label>
                {editMode ? (
                  <input
                    type="number"
                    value={editForm.monthly_savings}
                    onChange={(e) => handleEditChange('monthly_savings', e.target.value)}
                  />
                ) : (
                  <p>{money(savings)}</p>
                )}
              </div>

              <div className="info-block">
                <label>Available Budget</label>
                <p>{money(availableBudget)}</p>
              </div>
            </div>
          </div>

          {/* Category Budgets Section */}
          <div className="profile-section">
            <h3>Category-wise Budget</h3>
            <div className="category-budgets-grid">
              {['food', 'travel', 'shopping', 'health', 'adventure', 'loan'].map((category) => (
                <div key={category} className="category-budget-item">
                  <label>{category === 'loan' ? 'Loan/EMI' : category.charAt(0).toUpperCase() + category.slice(1)}</label>
                  {editMode ? (
                    <input
                      type="number"
                      value={categoryForm[category] || ''}
                      onChange={(e) => handleCategoryChange(category, e.target.value)}
                      placeholder="0"
                    />
                  ) : (
                    <p>{money(categoryForm[category] || 0)}</p>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Action Buttons */}
          <div className="profile-actions">
            {editMode ? (
              <>
                <button className="primary-button" onClick={handleSaveProfile}>
                  Save Profile
                </button>
                <button className="primary-button" onClick={handleSaveCategoryBudgets}>
                  Save Category Budgets
                </button>
                <button
                  className="secondary-button"
                  onClick={() => {
                    setEditMode(false)
                    setEditForm({
                      name: user?.name || '',
                      email: user?.email || '',
                      phone: user?.phone || '',
                      monthly_income: user?.monthly_income || '',
                      monthly_savings: user?.monthly_savings || '',
                      currency: user?.currency || 'INR',
                    })
                  }}
                >
                  Cancel
                </button>
              </>
            ) : (
              <button className="primary-button" onClick={() => setEditMode(true)}>
                Edit Profile
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default ProfileModal