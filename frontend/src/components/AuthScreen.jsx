import { FiUser } from 'react-icons/fi'

function AuthScreen({
  authForm,
  loading,
  message,
  mode,
  onAuthFormChange,
  onForgotPassword,
  onModeChange,
  onSubmit,
}) {
  const isLogin = mode === 'login'

  return (
    <main className="auth-screen">
      <section className="auth-panel">
        <div className="auth-copy">
          <p className="eyebrow">AI Budget Overspending Alert</p>
          <h1>{isLogin ? 'Welcome back' : 'Create account'}</h1>
          <p>
            Track spending, watch risk, and keep your monthly budget in control.
          </p>
        </div>

        <form className="stack" onSubmit={onSubmit}>
          {!isLogin && (
            <>
              <input
                required
                placeholder="Name"
                value={authForm.name}
                onChange={(event) => onAuthFormChange('name', event.target.value)}
              />
              <input
                placeholder="Phone"
                value={authForm.phone}
                onChange={(event) => onAuthFormChange('phone', event.target.value)}
              />
              <input
                min="0"
                placeholder="Monthly Income"
                type="number"
                value={authForm.monthly_income}
                onChange={(event) =>
                  onAuthFormChange(
                    'monthly_income',
                    event.target.value
                  )
                }
              />

              <input
                min="0"
                placeholder="Monthly Savings Goal"
                type="number"
                value={authForm.monthly_savings}
                onChange={(event) =>
                  onAuthFormChange(
                    'monthly_savings',
                    event.target.value
                  )
                }
              />

              <input
                disabled
                placeholder="Available Budget"
                type="number"
                value={
                  (Number(authForm.monthly_income || 0)) -
                  (Number(authForm.monthly_savings || 0))
                }
              />
            </>
          )}

          <input
            required
            placeholder="Email"
            type="email"
            value={authForm.email}
            onChange={(event) => onAuthFormChange('email', event.target.value)}
          />
          <input
            required
            placeholder="Password"
            type="password"
            value={authForm.password}
            onChange={(event) => onAuthFormChange('password', event.target.value)}
          />

          {isLogin && (
            <button
              className="forgot-password-link"
              type="button"
              onClick={onForgotPassword}
            >
              Forgot password?
            </button>
          )}

          <button disabled={loading} type="submit">
            <FiUser aria-hidden="true" />
            {isLogin ? 'Log in' : 'Register'}
          </button>
        </form>

        <button
          className="link-button"
          type="button"
          onClick={() => onModeChange(isLogin ? 'register' : 'login')}
        >
          {isLogin ? 'Create account' : 'Already registered?'}
        </button>
        {message && <p className="status">{message}</p>}
      </section>
    </main>
  )
}

export default AuthScreen
